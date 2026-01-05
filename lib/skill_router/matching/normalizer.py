"""Query normalization implementation."""
from lib.skill_router.interfaces.matching import IQueryNormalizer


class DefaultQueryNormalizer(IQueryNormalizer):
    """Default query normalizer implementation.

    Normalizes queries by:
    - Converting to lowercase
    - Stripping leading/trailing whitespace
    - Preserving hyphens in skill names
    """

    def normalize(self, query: str) -> str:
        """Normalize a user query for matching.

        Args:
            query: Raw user query string

        Returns:
            Normalized query string (lowercase, stripped)
        """
        # Convert to lowercase
        normalized = query.lower()

        # Strip leading/trailing whitespace
        normalized = normalized.strip()

        return normalized
