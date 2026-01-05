"""Word overlap scoring for task trigger matching."""
from typing import Set
from lib.skill_router.interfaces.matching import IWordOverlapScorer


class WordOverlapScorer(IWordOverlapScorer):
    """Computes word overlap scores between query and trigger phrases.

    Score calculation:
    - overlap = |query_words INTERSECT trigger_words| / |trigger_words|
    - Returns 1.0 for exact match (all trigger words present in query)
    - Returns 0.0 if score < threshold (default 0.6)
    """

    def __init__(self, threshold: float = 0.6):
        """Initialize scorer with overlap threshold.

        Args:
            threshold: Minimum overlap ratio to consider a match (default 0.6 = 60%)
        """
        self.threshold = threshold

    def score(self, query_words: Set[str], trigger_words: Set[str]) -> float:
        """Compute overlap score between query and trigger words.

        Args:
            query_words: Set of words from the user query
            trigger_words: Set of words from a trigger phrase

        Returns:
            Overlap score (0.0-1.0), where 1.0 means perfect match.
            Returns 0.0 if below threshold.
        """
        if not trigger_words:
            return 0.0

        if not query_words:
            return 0.0

        # Calculate overlap: intersection size / trigger size
        overlap = query_words.intersection(trigger_words)
        coverage = len(overlap) / len(trigger_words)

        # Return 0.0 if below threshold
        if coverage < self.threshold:
            return 0.0

        return coverage
