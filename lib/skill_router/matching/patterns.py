"""Pattern registry for skill matching."""
from typing import List
from lib.skill_router.interfaces.matching import IPatternRegistry


# Default pattern templates with {skill} placeholder
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


class DefaultPatternRegistry(IPatternRegistry):
    """Default pattern registry with common request patterns.

    Provides templates for matching user queries that follow
    common command patterns like "use X", "apply X", etc.
    """

    def __init__(self, patterns: List[str] = None):
        """Initialize pattern registry.

        Args:
            patterns: Optional list of pattern templates.
                     Defaults to DEFAULT_PATTERNS if not provided.
        """
        self.patterns = patterns if patterns is not None else DEFAULT_PATTERNS

    def get_patterns(self) -> List[str]:
        """Get list of pattern templates.

        Returns:
            List of pattern strings with {skill} placeholder
        """
        return self.patterns.copy()

    def expand_pattern(self, pattern: str, skill_name: str) -> str:
        """Expand a pattern template with a skill name.

        Args:
            pattern: Pattern template with {skill} placeholder
            skill_name: Skill name to substitute

        Returns:
            Expanded pattern string
        """
        return pattern.replace("{skill}", skill_name)
