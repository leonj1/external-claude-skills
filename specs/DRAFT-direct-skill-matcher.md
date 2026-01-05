# DRAFT: Direct Skill Matcher (Tier 1 Routing)

## Overview

The Direct Skill Matcher is Tier 1 of the 3-tier routing system. It matches user queries that explicitly reference skill names, allowing power users to bypass discovery and directly invoke specific capabilities.

## Traces to Root Request

| Root Term | How This Satisfies It |
|-----------|----------------------|
| "3-tier routing" | Implements Tier 1 (direct skill matching) |
| "Skill Router system" | Core matcher component of the router |

---

## Interfaces Needed

### ISkillMatcher

```python
from abc import ABC, abstractmethod
from typing import Dict, Optional
from lib.skill_router.models import Skill

class MatchResult:
    """Result of a skill matching operation.

    Attributes:
        skill_name: Name of matched skill, or None if no match
        match_type: Type of match ("exact", "pattern", None)
        confidence: Match confidence (1.0 for exact, 0.9 for pattern)
    """
    skill_name: Optional[str]
    match_type: Optional[str]
    confidence: float

class ISkillMatcher(ABC):
    """Interface for Tier 1 direct skill matching."""

    @abstractmethod
    def match(self, query: str, skills: Dict[str, Skill]) -> Optional[MatchResult]:
        """Attempt to match query to a skill by name.

        Args:
            query: User query string
            skills: Dictionary mapping skill names to Skill objects

        Returns:
            MatchResult if skill found, None if no match
        """
        pass
```

### IPatternRegistry

```python
from abc import ABC, abstractmethod
from typing import List

class IPatternRegistry(ABC):
    """Interface for managing match patterns."""

    @abstractmethod
    def get_patterns(self) -> List[str]:
        """Return list of pattern templates.

        Returns:
            List of pattern strings with {skill} placeholder
        """
        pass

    @abstractmethod
    def expand_pattern(self, pattern: str, skill_name: str) -> str:
        """Expand a pattern template with skill name.

        Args:
            pattern: Pattern template with {skill} placeholder
            skill_name: Skill name to substitute

        Returns:
            Expanded pattern string
        """
        pass
```

### IQueryNormalizer

```python
from abc import ABC, abstractmethod

class IQueryNormalizer(ABC):
    """Interface for query normalization."""

    @abstractmethod
    def normalize(self, query: str) -> str:
        """Normalize query for matching.

        Args:
            query: Raw user query

        Returns:
            Normalized query (lowercase, stripped, punctuation handled)
        """
        pass
```

---

## Data Models

### MatchResult

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class MatchResult:
    """Result of a skill matching operation."""
    skill_name: Optional[str]
    match_type: Optional[str]  # "exact", "pattern", None
    confidence: float  # 1.0 for exact, 0.9 for pattern

    @classmethod
    def no_match(cls) -> "MatchResult":
        """Factory for no-match result."""
        return cls(skill_name=None, match_type=None, confidence=0.0)

    @classmethod
    def exact_match(cls, skill_name: str) -> "MatchResult":
        """Factory for exact name match."""
        return cls(skill_name=skill_name, match_type="exact", confidence=1.0)

    @classmethod
    def pattern_match(cls, skill_name: str) -> "MatchResult":
        """Factory for pattern-based match."""
        return cls(skill_name=skill_name, match_type="pattern", confidence=0.9)
```

---

## Logic Flow

### match(query, skills)

```
FUNCTION match(query: str, skills: Dict[str, Skill]) -> MatchResult:

    # Step 1: Normalize query
    normalized_query = normalizer.normalize(query)

    # Step 2: Get all skill names, sorted by length descending
    # (Longer names have priority to avoid partial matches)
    skill_names = sorted(skills.keys(), key=len, reverse=True)

    # Step 3: Try exact name match first
    FOR skill_name IN skill_names:
        normalized_skill = skill_name.lower()
        IF normalized_skill IN normalized_query:
            RETURN MatchResult.exact_match(skill_name)

    # Step 4: Try pattern-based match
    patterns = pattern_registry.get_patterns()
    FOR skill_name IN skill_names:
        FOR pattern IN patterns:
            expanded = pattern_registry.expand_pattern(pattern, skill_name.lower())
            IF expanded IN normalized_query:
                RETURN MatchResult.pattern_match(skill_name)

    # Step 5: No match found
    RETURN MatchResult.no_match()
```

### normalize(query)

```
FUNCTION normalize(query: str) -> str:
    # Step 1: Convert to lowercase
    result = query.lower()

    # Step 2: Strip leading/trailing whitespace
    result = result.strip()

    # Step 3: Remove surrounding quotes from potential skill names
    # Handles: Can you apply 'aws-ecs-deployment'?
    result = result.replace("'", " ").replace('"', " ")

    # Step 4: Normalize multiple spaces
    result = " ".join(result.split())

    RETURN result
```

---

## Default Pattern Registry

```python
DEFAULT_PATTERNS = [
    "use {skill}",
    "apply {skill}",
    "run {skill}",
    "execute {skill}",
    "{skill} skill",
    "deploy with {skill}",
    "set up {skill}",
    "configure {skill}",
]
```

---

## Implementation Classes

### DirectSkillMatcher

```python
class DirectSkillMatcher(ISkillMatcher):
    """Tier 1 matcher: Direct skill name matching."""

    def __init__(
        self,
        normalizer: IQueryNormalizer,
        pattern_registry: IPatternRegistry
    ):
        self.normalizer = normalizer
        self.pattern_registry = pattern_registry

    def match(self, query: str, skills: Dict[str, Skill]) -> Optional[MatchResult]:
        # Implementation per logic flow above
        pass
```

### DefaultQueryNormalizer

```python
class DefaultQueryNormalizer(IQueryNormalizer):
    """Default implementation of query normalization."""

    def normalize(self, query: str) -> str:
        # Implementation per logic flow above
        pass
```

### DefaultPatternRegistry

```python
class DefaultPatternRegistry(IPatternRegistry):
    """Default pattern registry with common request patterns."""

    DEFAULT_PATTERNS = [
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
        self.patterns = patterns or self.DEFAULT_PATTERNS

    def get_patterns(self) -> List[str]:
        return self.patterns

    def expand_pattern(self, pattern: str, skill_name: str) -> str:
        return pattern.format(skill=skill_name)
```

---

## File Structure

```
lib/skill_router/
    interfaces/
        __init__.py
        dependency.py      # (existing)
        matching.py        # NEW: ISkillMatcher, IPatternRegistry, IQueryNormalizer
    matching/
        __init__.py
        result.py          # NEW: MatchResult dataclass
        direct_matcher.py  # NEW: DirectSkillMatcher
        normalizer.py      # NEW: DefaultQueryNormalizer
        patterns.py        # NEW: DefaultPatternRegistry
```

---

## Integration Points

### With Existing Models

- Uses `Skill` from `lib/skill_router/models.py`
- Matcher receives `Dict[str, Skill]` from manifest loader

### With Router Orchestration (Task 1.6)

- Router calls `ISkillMatcher.match()` first
- If `MatchResult.skill_name` is not None, skip Tier 2 and Tier 3
- Pass matched skill to `IDependencyResolver.resolve()` for execution order

---

## BDD Scenario Coverage

| Scenario | Implementation Concern |
|----------|----------------------|
| Match skill by exact name | Exact match loop with skill_name in normalized_query |
| Match skill name embedded in query | Same as above |
| Match skill with hyphenated name | Hyphen preserved in normalization |
| Match using common request patterns | Pattern expansion and matching |
| Case insensitivity | Query normalization (lowercase) |
| Prioritize longer skill name | skill_names sorted by length descending |
| No match when skill name not present | Return MatchResult.no_match() |
| Handle query with only skill name | Exact match handles this |
| Handle surrounding punctuation | Normalization removes quotes |

---

## Context Budget

| Category | Estimate |
|----------|----------|
| Files to read | 4 (~200 lines) |
| New code to write | ~150 lines |
| Test code to write | ~200 lines |
| **Estimated context usage** | **15%** |

---

## Acceptance Criteria

1. All scenarios in `tests/bdd/direct-skill-matching.feature` pass
2. Longer skill names take priority over shorter matches
3. Case-insensitive matching works for all patterns
4. Punctuation (quotes) around skill names handled gracefully
5. Integration with existing `Skill` model maintained
