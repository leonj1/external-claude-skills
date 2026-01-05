"""Word tokenization for task trigger matching."""
from typing import Set
from lib.skill_router.interfaces.matching import IWordTokenizer


class WordTokenizer(IWordTokenizer):
    """Tokenizes text into normalized word sets.

    Normalizes text by:
    - Converting to lowercase
    - Stripping leading/trailing whitespace
    - Splitting on whitespace (handles multiple spaces)
    """

    def tokenize(self, text: str) -> Set[str]:
        """Tokenize text into a set of normalized words.

        Args:
            text: Input text to tokenize

        Returns:
            Set of normalized word tokens
        """
        if not text:
            return set()

        # Normalize: lowercase and strip
        normalized = text.lower().strip()

        if not normalized:
            return set()

        # Split on whitespace and filter empty strings
        words = normalized.split()

        return set(words)
