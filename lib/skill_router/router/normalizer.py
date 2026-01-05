"""Query normalizer with whitespace collapsing."""
import re
from lib.skill_router.interfaces.matching import IQueryNormalizer


class QueryNormalizer(IQueryNormalizer):
    """Normalizes query strings for consistent matching.

    Applies three transformations:
    1. Lowercase conversion
    2. Trim leading/trailing whitespace
    3. Collapse multiple spaces to single space
    """

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
