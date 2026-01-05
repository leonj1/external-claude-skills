"""Main router orchestrating the 3-tier matching pipeline."""
from typing import List
from lib.skill_router.models import Manifest
from lib.skill_router.interfaces.router import IRouter, RouteResult
from lib.skill_router.interfaces.matching import IQueryNormalizer, ISkillMatcher, ITaskMatcher
from lib.skill_router.interfaces.dependency import IDependencyResolver
from lib.skill_router.interfaces.discovery import ILLMDiscovery
from lib.skill_router.discovery.models import SkillSummary


class SkillRouter(IRouter):
    """Main router orchestrating the 3-tier matching pipeline.

    Flow:
    1. Normalize query
    2. Tier 1: Direct skill match (short-circuit if found)
    3. Tier 2: Task trigger match (short-circuit if found)
    4. Tier 3: LLM discovery (fallback)
    5. Resolve dependencies for matched skill(s)
    6. Return RouteResult
    """

    def __init__(
        self,
        manifest: Manifest,
        normalizer: IQueryNormalizer,
        direct_matcher: ISkillMatcher,
        task_matcher: ITaskMatcher,
        llm_discovery: ILLMDiscovery,
        dependency_resolver: IDependencyResolver
    ):
        """Initialize with all routing components.

        Args:
            manifest: Loaded and validated manifest
            normalizer: Query normalizer
            direct_matcher: Tier 1 direct skill matcher
            task_matcher: Tier 2 task trigger matcher
            llm_discovery: Tier 3 LLM discovery
            dependency_resolver: Dependency resolver for execution order
        """
        self.manifest = manifest
        self.normalizer = normalizer
        self.direct_matcher = direct_matcher
        self.task_matcher = task_matcher
        self.llm_discovery = llm_discovery
        self.dependency_resolver = dependency_resolver

    def route(self, query: str) -> RouteResult:
        """Route query through 3-tier pipeline.

        Args:
            query: User's natural language request

        Returns:
            RouteResult with match details and execution order
        """
        # Step 1: Normalize query
        normalized = self.normalizer.normalize(query)
        if not normalized:
            return RouteResult.no_match()

        # Step 2: Tier 1 - Direct skill match
        tier1_result = self.direct_matcher.match(normalized, self.manifest.skills)
        if tier1_result.skill_name is not None:
            execution_order = self._resolve_skill_dependencies(tier1_result.skill_name)
            return RouteResult.skill_match(tier1_result.skill_name, execution_order)

        # Step 3: Tier 2 - Task trigger match
        tier2_result = self.task_matcher.match(normalized, self.manifest.tasks)
        if tier2_result.is_match():
            execution_order = self._resolve_multi_dependencies(tier2_result.skills)
            return RouteResult.task_match(
                tier2_result.task_name,
                tier2_result.skills,
                execution_order
            )

        # Step 4: Tier 3 - LLM discovery
        tier3_result = self._invoke_llm_discovery(query)
        if tier3_result.is_match():
            return tier3_result

        # No match at any tier
        return RouteResult.no_match()

    def _resolve_skill_dependencies(self, skill_name: str) -> List[str]:
        """Resolve dependencies for a single skill.

        Args:
            skill_name: Name of the skill

        Returns:
            Ordered list of skills (dependencies first)
        """
        result = self.dependency_resolver.resolve(skill_name, self.manifest.skills)
        return result.execution_order

    def _resolve_multi_dependencies(self, skill_names: List[str]) -> List[str]:
        """Resolve dependencies for multiple skills.

        Args:
            skill_names: List of skill names

        Returns:
            Ordered list of all skills (dependencies first)
        """
        result = self.dependency_resolver.resolve_multi(skill_names, self.manifest.skills)
        return result.execution_order

    def _invoke_llm_discovery(self, query: str) -> RouteResult:
        """Invoke LLM discovery as Tier 3 fallback.

        Args:
            query: Original user query (not normalized)

        Returns:
            RouteResult from LLM discovery or no_match
        """
        # Build skill summaries for LLM
        summaries = self._build_skill_summaries()

        # Invoke LLM discovery
        discovery_result = self.llm_discovery.discover(query, summaries, max_results=1)

        if not discovery_result.has_matches:
            return RouteResult.no_match()

        top_match = discovery_result.top_match
        skill_name = top_match.skill_name

        # Check if matched skill exists
        if skill_name not in self.manifest.skills:
            # LLM might have matched a task name instead
            if skill_name in self.manifest.tasks:
                task = self.manifest.tasks[skill_name]
                execution_order = self._resolve_multi_dependencies(task.skills)
                return RouteResult.task_match(skill_name, task.skills, execution_order)
            return RouteResult.no_match()

        execution_order = self._resolve_skill_dependencies(skill_name)
        return RouteResult.discovery_match(skill_name, execution_order, top_match.confidence)

    def _build_skill_summaries(self) -> List[SkillSummary]:
        """Build skill summaries for LLM prompt.

        Returns:
            List of SkillSummary objects
        """
        summaries = []
        for name, skill in self.manifest.skills.items():
            summaries.append(SkillSummary(name=name, description=skill.description))
        return summaries
