# DRAFT: Router Orchestration (3-Tier Flow)

## Overview

The Router Orchestration component wires together all routing subsystems (Tier 1 Direct Skill Matcher, Tier 2 Task Trigger Matcher, Tier 3 LLM Discovery) into a cohesive 3-tier routing pipeline. It implements short-circuit logic, query normalization, and constructs unified RouteResult objects with dependency-resolved execution orders.

## Traces to Root Request

- **Root**: "Read specs.md and implement the **Skill Router system** with YAML manifest, **3-tier routing**, dependency resolution, and hook integration"
- **This sub-task**: Orchestrates the complete "Skill Router system" by wiring "3-tier routing" together

## Context Budget

| Metric | Estimate |
|--------|----------|
| Files to read | 5 (~300 lines) |
| New code to write | ~180 lines |
| Test code to write | ~250 lines |
| Estimated context usage | ~25% |

**Verdict**: APPROVED (under 60% threshold)

---

## Interfaces Needed

### IRouter (New)

```python
from abc import ABC, abstractmethod


class IRouter(ABC):
    """Interface for the top-level skill routing orchestrator.

    Coordinates the 3-tier matching flow and constructs unified RouteResult.
    """

    @abstractmethod
    def route(self, query: str) -> "RouteResult":
        """Route a user query through the 3-tier matching pipeline.

        Args:
            query: User's natural language request

        Returns:
            RouteResult containing match type, matched entity, skills, and execution order

        Raises:
            ManifestError: If manifest loading or validation fails
        """
        pass


class IQueryNormalizer(ABC):
    """Interface for query normalization before routing."""

    @abstractmethod
    def normalize(self, query: str) -> str:
        """Normalize a query string for consistent matching.

        Args:
            query: Raw user query

        Returns:
            Normalized query (lowercase, trimmed, collapsed whitespace)
        """
        pass
```

### IDirectSkillMatcher (Existing - from Tier 1)

```python
from abc import ABC, abstractmethod
from typing import Dict
from lib.skill_router.models import Skill


class IDirectSkillMatcher(ABC):
    """Interface for Tier 1 direct skill name matching."""

    @abstractmethod
    def match(self, query: str, skills: Dict[str, Skill]) -> "SkillMatchResult":
        """Match query against skill names directly.

        Args:
            query: Normalized user query
            skills: Dictionary of available skills

        Returns:
            SkillMatchResult with matched skill name or None
        """
        pass
```

### ITaskMatcher (Existing - from Tier 2)

```python
from abc import ABC, abstractmethod
from typing import Dict
from lib.skill_router.models import Task


class ITaskMatcher(ABC):
    """Interface for Tier 2 task trigger matching."""

    @abstractmethod
    def match(self, query: str, tasks: Dict[str, Task]) -> "TaskMatchResult":
        """Match query against task triggers.

        Args:
            query: Normalized user query
            tasks: Dictionary of available tasks

        Returns:
            TaskMatchResult with matched task and skills
        """
        pass
```

### ILLMDiscovery (Existing - from Tier 3)

Already defined in `lib/skill_router/interfaces/discovery.py`.

---

## Data Models

### RouteResult (New)

```python
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class RouteType(Enum):
    """Type of route match."""
    SKILL = "skill"      # Tier 1: Direct skill match
    TASK = "task"        # Tier 2: Task trigger match
    DISCOVERY = "discovery"  # Tier 3: LLM discovery
    ERROR = "error"      # No match found


@dataclass(frozen=True)
class RouteResult:
    """Represents the result of routing a user query.

    Attributes:
        route_type: How the match was found (skill, task, discovery, error)
        matched: Name of matched skill or task
        skills: List of skill names to load
        execution_order: Dependency-resolved order for skill loading
        tier: Which tier produced the match (1, 2, or 3)
        confidence: Match confidence (1.0 for tier 1/2, LLM confidence for tier 3)
    """
    route_type: RouteType
    matched: str
    skills: List[str] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    tier: int = 0
    confidence: float = 1.0

    @classmethod
    def skill_match(cls, skill_name: str, execution_order: List[str]) -> "RouteResult":
        """Factory for Tier 1 skill match."""
        return cls(
            route_type=RouteType.SKILL,
            matched=skill_name,
            skills=[skill_name],
            execution_order=execution_order,
            tier=1,
            confidence=1.0
        )

    @classmethod
    def task_match(cls, task_name: str, skills: List[str], execution_order: List[str]) -> "RouteResult":
        """Factory for Tier 2 task match."""
        return cls(
            route_type=RouteType.TASK,
            matched=task_name,
            skills=skills,
            execution_order=execution_order,
            tier=2,
            confidence=1.0
        )

    @classmethod
    def discovery_match(cls, skill_name: str, execution_order: List[str], confidence: float) -> "RouteResult":
        """Factory for Tier 3 LLM discovery match."""
        return cls(
            route_type=RouteType.DISCOVERY,
            matched=skill_name,
            skills=[skill_name],
            execution_order=execution_order,
            tier=3,
            confidence=confidence
        )

    @classmethod
    def no_match(cls) -> "RouteResult":
        """Factory for no match (error) result."""
        return cls(
            route_type=RouteType.ERROR,
            matched="",
            skills=[],
            execution_order=[],
            tier=0,
            confidence=0.0
        )

    def is_match(self) -> bool:
        """Check if this result represents a valid match."""
        return self.route_type != RouteType.ERROR
```

### SkillMatchResult (Tier 1 - Direct Skill)

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class SkillMatchResult:
    """Result of Tier 1 direct skill matching.

    Attributes:
        skill_name: Name of matched skill, or None if no match
        pattern_matched: The pattern that matched (e.g., "use {skill}")
    """
    skill_name: Optional[str]
    pattern_matched: Optional[str]

    @classmethod
    def no_match(cls) -> "SkillMatchResult":
        """Factory for no match."""
        return cls(skill_name=None, pattern_matched=None)

    @classmethod
    def matched(cls, skill_name: str, pattern: str) -> "SkillMatchResult":
        """Factory for successful match."""
        return cls(skill_name=skill_name, pattern_matched=pattern)

    def is_match(self) -> bool:
        """Check if a skill was matched."""
        return self.skill_name is not None
```

---

## Implementation Classes

### QueryNormalizer

```python
import re


class QueryNormalizer(IQueryNormalizer):
    """Normalizes query strings for consistent matching."""

    def normalize(self, query: str) -> str:
        """Normalize query: lowercase, trim, collapse whitespace.

        Args:
            query: Raw user query

        Returns:
            Normalized query string
        """
        if not query:
            return ""

        # Lowercase
        normalized = query.lower()

        # Strip leading/trailing whitespace
        normalized = normalized.strip()

        # Collapse multiple spaces to single space
        normalized = re.sub(r'\s+', ' ', normalized)

        return normalized
```

### DirectSkillMatcher

```python
from typing import Dict, List
from lib.skill_router.models import Skill


class DirectSkillMatcher(IDirectSkillMatcher):
    """Tier 1: Direct skill name matching.

    Matches queries that explicitly reference a skill by name.
    Patterns: "use {skill}", "apply {skill}", "run {skill}", etc.
    """

    DEFAULT_PATTERNS: List[str] = [
        "use {skill}",
        "apply {skill}",
        "run {skill}",
        "execute {skill}",
        "{skill} skill",
        "deploy with {skill}",
        "set up {skill}",
        "configure {skill}",
    ]

    def __init__(self, patterns: List[str] = None):
        """Initialize with optional custom patterns.

        Args:
            patterns: List of patterns with {skill} placeholder (default: DEFAULT_PATTERNS)
        """
        self.patterns = patterns or self.DEFAULT_PATTERNS

    def match(self, query: str, skills: Dict[str, Skill]) -> SkillMatchResult:
        """Match query against skill names.

        First checks for exact skill name in query, then checks patterns.

        Args:
            query: Normalized user query
            skills: Dictionary of available skills

        Returns:
            SkillMatchResult with matched skill or no_match
        """
        for skill_name in skills.keys():
            # Check exact name presence
            if skill_name in query:
                return SkillMatchResult.matched(skill_name, f"contains '{skill_name}'")

            # Check pattern matches
            for pattern in self.patterns:
                expanded = pattern.format(skill=skill_name)
                if expanded in query:
                    return SkillMatchResult.matched(skill_name, pattern)

        return SkillMatchResult.no_match()
```

### SkillRouter (Main Orchestrator)

```python
from typing import List
from lib.skill_router.models import Manifest
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
        direct_matcher: IDirectSkillMatcher,
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
        if tier1_result.is_match():
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
```

---

## Logic Flow (Pseudocode)

```
FUNCTION route(query):
    # Step 1: Normalize
    normalized = normalize(query)
    IF normalized is empty:
        RETURN no_match

    # Step 2: Tier 1 - Direct skill match (short-circuit)
    tier1_result = direct_matcher.match(normalized, manifest.skills)
    IF tier1_result.is_match():
        execution_order = resolve_dependencies(tier1_result.skill_name)
        RETURN RouteResult.skill_match(tier1_result.skill_name, execution_order)

    # Step 3: Tier 2 - Task trigger match (short-circuit)
    tier2_result = task_matcher.match(normalized, manifest.tasks)
    IF tier2_result.is_match():
        execution_order = resolve_multi_dependencies(tier2_result.skills)
        RETURN RouteResult.task_match(tier2_result.task_name, tier2_result.skills, execution_order)

    # Step 4: Tier 3 - LLM discovery (fallback)
    skill_summaries = build_summaries(manifest.skills)
    discovery_result = llm_discovery.discover(query, skill_summaries)
    IF discovery_result.has_matches:
        top_match = discovery_result.top_match
        execution_order = resolve_dependencies(top_match.skill_name)
        RETURN RouteResult.discovery_match(top_match.skill_name, execution_order, top_match.confidence)

    # No match at any tier
    RETURN RouteResult.no_match()
```

---

## Short-Circuit Logic

The 3-tier flow uses short-circuit evaluation:

| Tier | Match Found | Next Action |
|------|-------------|-------------|
| 1 | Yes | Return immediately, skip Tier 2 and 3 |
| 1 | No | Continue to Tier 2 |
| 2 | Yes | Return immediately, skip Tier 3 |
| 2 | No | Continue to Tier 3 |
| 3 | Yes | Return with discovery match |
| 3 | No | Return error (no match) |

Benefits:
- **Performance**: Direct matches avoid LLM API latency (~500ms saved)
- **Cost**: Tier 1/2 matches avoid LLM API costs
- **Predictability**: Known patterns return deterministic results

---

## Query Normalization Rules

| Transformation | Example |
|----------------|---------|
| Lowercase | "USE TERRAFORM-BASE" -> "use terraform-base" |
| Trim whitespace | "  query  " -> "query" |
| Collapse spaces | "build   a   website" -> "build a website" |
| Empty handling | "" or "   " -> "" (triggers no_match) |

Note: Special characters are preserved to allow matching skill names like "aws-ecs-deployment".

---

## Error Handling

### Manifest Errors
If the manifest is invalid, the router cannot function. Errors propagate from the ManifestLoader.

### LLM Discovery Errors
If Tier 3 LLM call fails:
1. Log the error (network, auth, rate limit, parse failure)
2. Return `RouteResult.no_match()` instead of raising
3. Caller can retry or handle gracefully

### Empty/Invalid Queries
Empty or whitespace-only queries return `RouteResult.no_match()` immediately without invoking any tier.

---

## File Structure

```
lib/skill_router/
  router/
    __init__.py
    interfaces.py          # IRouter, IQueryNormalizer, IDirectSkillMatcher
    models.py              # RouteResult, RouteType, SkillMatchResult
    normalizer.py          # QueryNormalizer implementation
    direct_matcher.py      # DirectSkillMatcher implementation
    skill_router.py        # SkillRouter orchestrator
```

---

## Integration Points

### With Manifest Loader (Task 1.1)
Router receives a validated `Manifest` object with `skills` and `tasks` dictionaries.

### With Dependency Resolver (Task 1.2)
Router calls `resolve()` for single skills and `resolve_multi()` for task skill lists.

### With Task Trigger Matcher (Task 1.4)
Router invokes `task_matcher.match()` in Tier 2.

### With LLM Discovery (Task 1.5)
Router invokes `llm_discovery.discover()` in Tier 3 with skill summaries.

### With Hook Integration (Task 1.7)
Hooks receive `RouteResult` and use `execution_order` to inject skill contents.

---

## Test Scenarios (from BDD)

| Scenario | Query | Expected Tier | Expected Result |
|----------|-------|---------------|-----------------|
| Tier 1 match | "use terraform-base" | 1 | skill: terraform-base |
| Tier 2 match | "build a static website" | 2 | task: static-website |
| Tier 3 match | "set up user authentication" | 3 | skill: auth-cognito (via LLM) |
| Short-circuit | "use terraform-base" | 1 | Tier 2/3 not invoked |
| Empty query | "" | - | error: no match |
| Case insensitive | "USE TERRAFORM-BASE" | 1 | skill: terraform-base |
| Whitespace normalized | "  build   a   website  " | 2 | task: static-website |
| No match anywhere | "random nonsense" | - | error: no match |
| XSS in query | "build <script>" | - | Handled safely |

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Short-circuit evaluation | Minimize latency and API costs |
| Normalize before matching | Consistent behavior regardless of user input style |
| RouteResult.tier field | Allows debugging which tier produced the match |
| Factory methods | Clear construction patterns for different match types |
| LLM fallback returns no_match on error | Graceful degradation over hard failure |
| Preserve original query for LLM | LLM benefits from natural language, not normalized form |
