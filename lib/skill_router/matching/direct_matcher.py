"""Direct skill matcher implementation."""
from typing import Dict, Optional
from lib.skill_router.models import Skill
from lib.skill_router.interfaces.matching import ISkillMatcher, IQueryNormalizer, IPatternRegistry
from lib.skill_router.matching.result import MatchResult


class DirectSkillMatcher(ISkillMatcher):
    """Matches user queries containing skill names directly.

    This matcher supports two strategies:
    1. Exact match: Skill name appears anywhere in the query
    2. Pattern match: Query follows common patterns like "use {skill}"

    Longer skill names are prioritized over shorter ones to handle
    substring matches correctly (e.g., "terraform-base" vs "terraform").
    """

    def __init__(self, normalizer: IQueryNormalizer, pattern_registry: Optional[IPatternRegistry] = None):
        """Initialize DirectSkillMatcher.

        Args:
            normalizer: Query normalizer instance
            pattern_registry: Optional pattern registry for pattern-based matching
        """
        self.normalizer = normalizer
        self.pattern_registry = pattern_registry

    def match(self, query: str, skills: Dict[str, Skill]) -> MatchResult:
        """Match a query against available skills using exact and pattern matching.

        Args:
            query: User query string
            skills: Dictionary mapping skill names to Skill objects

        Returns:
            MatchResult containing matched skill name, type, and confidence
        """
        # Normalize the query
        normalized_query = self.normalizer.normalize(query)

        # Sort skill names by length descending (longer names first)
        # This ensures "terraform-base" matches before "terraform"
        skill_names = sorted(skills.keys(), key=len, reverse=True)

        # Try exact match first (confidence 1.0)
        for skill_name in skill_names:
            normalized_skill_name = skill_name.lower()
            if normalized_skill_name in normalized_query:
                return MatchResult.exact_match(skill_name)

        # Try pattern matching if pattern registry available (confidence 0.9)
        if self.pattern_registry:
            for skill_name in skill_names:
                for pattern in self.pattern_registry.get_patterns():
                    expanded = self.pattern_registry.expand_pattern(pattern, skill_name)
                    normalized_pattern = self.normalizer.normalize(expanded)
                    if normalized_pattern in normalized_query:
                        return MatchResult.pattern_match(skill_name)

        # No match found
        return MatchResult.no_match()
