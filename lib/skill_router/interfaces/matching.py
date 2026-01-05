"""Interfaces for skill matching components."""
from abc import ABC, abstractmethod
from typing import Dict, List, Set
from lib.skill_router.models import Skill, Task
from lib.skill_router.matching.result import MatchResult, TaskMatchResult


class IQueryNormalizer(ABC):
    """Interface for query normalization."""

    @abstractmethod
    def normalize(self, query: str) -> str:
        """Normalize a user query for matching.

        Args:
            query: Raw user query string

        Returns:
            Normalized query string (lowercase, stripped, etc.)
        """
        pass


class ISkillMatcher(ABC):
    """Interface for skill matching strategies."""

    @abstractmethod
    def match(self, query: str, skills: Dict[str, Skill]) -> MatchResult:
        """Match a query against available skills.

        Args:
            query: User query string
            skills: Dictionary mapping skill names to Skill objects

        Returns:
            MatchResult containing matched skill name, type, and confidence
        """
        pass


class IPatternRegistry(ABC):
    """Interface for pattern-based matching templates."""

    @abstractmethod
    def get_patterns(self) -> List[str]:
        """Get list of pattern templates.

        Returns:
            List of pattern strings with {skill} placeholder
        """
        pass

    @abstractmethod
    def expand_pattern(self, pattern: str, skill_name: str) -> str:
        """Expand a pattern template with a skill name.

        Args:
            pattern: Pattern template with {skill} placeholder
            skill_name: Skill name to substitute

        Returns:
            Expanded pattern string
        """
        pass


class IWordTokenizer(ABC):
    """Interface for tokenizing strings into word sets."""

    @abstractmethod
    def tokenize(self, text: str) -> Set[str]:
        """Tokenize text into a set of normalized words.

        Args:
            text: Input text to tokenize

        Returns:
            Set of normalized word tokens
        """
        pass


class IWordOverlapScorer(ABC):
    """Interface for computing word overlap scores."""

    @abstractmethod
    def score(self, query_words: Set[str], trigger_words: Set[str]) -> float:
        """Compute overlap score between query and trigger words.

        Args:
            query_words: Set of words from the user query
            trigger_words: Set of words from a trigger phrase

        Returns:
            Overlap score (0.0-1.0), where 1.0 means perfect match
        """
        pass


class ITaskMatcher(ABC):
    """Interface for task matching strategies."""

    @abstractmethod
    def match(self, query: str, tasks: Dict[str, Task]) -> "TaskMatchResult":
        """Match a query against available tasks.

        Args:
            query: User query string
            tasks: Dictionary mapping task names to Task objects

        Returns:
            TaskMatchResult containing matched task and score
        """
        pass
