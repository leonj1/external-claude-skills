"""Skill routing service for handling user queries."""
from dataclasses import dataclass
from typing import List, Optional

from lib.skill_router.models import Manifest
from lib.skill_router.manifest_loader import ManifestLoader
from lib.skill_router.router.skill_router import SkillRouter
from lib.skill_router.router.normalizer import QueryNormalizer
from lib.skill_router.matching.direct_matcher import DirectSkillMatcher
from lib.skill_router.matching.task_matcher import TaskTriggerMatcher
from lib.skill_router.matching.tokenizer import WordTokenizer
from lib.skill_router.matching.scorer import WordOverlapScorer
from lib.skill_router.dependency_resolver import KahnsDependencyResolver
from lib.skill_router.interfaces.router import RouteResult, RouteType
from lib.skill_router.interfaces.discovery import ILLMDiscovery
from lib.skill_router.discovery.models import DiscoveryResult


@dataclass
class RouteResponse:
    """Response from the skill routing service."""
    matched_task: Optional[str]
    skills: List[str]
    execution_order: List[str]
    route_type: str
    tier: int
    confidence: float

    @classmethod
    def from_route_result(cls, result: RouteResult) -> "RouteResponse":
        return cls(
            matched_task=result.matched if result.matched else None,
            skills=result.skills,
            execution_order=result.execution_order,
            route_type=result.route_type.value,
            tier=result.tier,
            confidence=result.confidence,
        )

    @classmethod
    def no_match(cls) -> "RouteResponse":
        return cls(
            matched_task=None,
            skills=[],
            execution_order=[],
            route_type=RouteType.ERROR.value,
            tier=0,
            confidence=0.0,
        )


class NoOpLLMDiscovery(ILLMDiscovery):
    """No-op LLM discovery that always returns no match."""

    def discover(self, query: str, skill_summaries: list, max_results: int = 3) -> DiscoveryResult:
        return DiscoveryResult(matches=[], raw_response="", model_used="no-op")


class SkillRoutingService:
    """Service class that handles skill routing logic."""

    def __init__(self, manifest_path: str, llm_discovery: Optional[ILLMDiscovery] = None):
        """Initialize the service with a manifest path.

        Args:
            manifest_path: Path to the manifest YAML file
            llm_discovery: Optional LLM discovery for Tier 3. Defaults to no-op.
        """
        loader = ManifestLoader()
        self.manifest = loader.load(manifest_path)
        self.llm_discovery = llm_discovery or NoOpLLMDiscovery()
        self._router = self._create_router()

    def _create_router(self) -> SkillRouter:
        """Create and wire up the skill router with all dependencies."""
        normalizer = QueryNormalizer()
        direct_matcher = DirectSkillMatcher(normalizer)
        tokenizer = WordTokenizer()
        scorer = WordOverlapScorer()
        task_matcher = TaskTriggerMatcher(tokenizer, scorer)
        dependency_resolver = KahnsDependencyResolver()

        return SkillRouter(
            manifest=self.manifest,
            normalizer=normalizer,
            direct_matcher=direct_matcher,
            task_matcher=task_matcher,
            llm_discovery=self.llm_discovery,
            dependency_resolver=dependency_resolver,
        )

    def route(self, query: str) -> RouteResponse:
        """Route a user query to the appropriate skills.

        Args:
            query: User's natural language request

        Returns:
            RouteResponse with matched task/skills and execution order
        """
        result = self._router.route(query)
        return RouteResponse.from_route_result(result)

    def list_skills(self) -> List[dict]:
        """List all available skills from the manifest.

        Returns:
            List of skill dictionaries with name, description, and path
        """
        return [
            {
                "name": name,
                "description": skill.description,
                "path": skill.path,
            }
            for name, skill in self.manifest.skills.items()
        ]
