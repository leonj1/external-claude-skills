"""Match result data structures."""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class MatchResult:
    """Represents the result of a skill matching operation.

    Attributes:
        skill_name: Name of matched skill, or None if no match
        match_type: Type of match ("exact", "pattern", or None)
        confidence: Confidence score (0.0-1.0)
    """
    skill_name: Optional[str]
    match_type: Optional[str]
    confidence: float

    @classmethod
    def no_match(cls) -> "MatchResult":
        """Factory method for no match result.

        Returns:
            MatchResult with no skill name, no type, and 0.0 confidence
        """
        return cls(skill_name=None, match_type=None, confidence=0.0)

    @classmethod
    def exact_match(cls, skill_name: str) -> "MatchResult":
        """Factory method for exact match result.

        Args:
            skill_name: Name of the matched skill

        Returns:
            MatchResult with exact match type and 1.0 confidence
        """
        return cls(skill_name=skill_name, match_type="exact", confidence=1.0)

    @classmethod
    def pattern_match(cls, skill_name: str) -> "MatchResult":
        """Factory method for pattern match result.

        Args:
            skill_name: Name of the matched skill

        Returns:
            MatchResult with pattern match type and 0.9 confidence
        """
        return cls(skill_name=skill_name, match_type="pattern", confidence=0.9)


@dataclass
class TaskMatchResult:
    """Represents the result of a task matching operation.

    Attributes:
        task_name: Name of matched task, or None if no match
        score: Match score (0.0-1.0)
        matched_trigger: The trigger phrase that matched, or None
        skills: List of skill names required by the matched task
    """
    task_name: Optional[str]
    score: float
    matched_trigger: Optional[str]
    skills: List[str] = field(default_factory=list)

    @classmethod
    def no_match(cls) -> "TaskMatchResult":
        """Factory method for no match result.

        Returns:
            TaskMatchResult with no task name, 0.0 score, and empty skills
        """
        return cls(task_name=None, score=0.0, matched_trigger=None, skills=[])

    @classmethod
    def from_task(cls, task_name: str, score: float, matched_trigger: str, skills: List[str]) -> "TaskMatchResult":
        """Factory method for creating result from a matched task.

        Args:
            task_name: Name of the matched task
            score: Match score (0.0-1.0)
            matched_trigger: The trigger phrase that matched
            skills: List of skill names required by the task

        Returns:
            TaskMatchResult populated with task data
        """
        return cls(
            task_name=task_name,
            score=score,
            matched_trigger=matched_trigger,
            skills=skills.copy()  # Copy to avoid reference issues
        )

    def is_match(self) -> bool:
        """Check if this result represents a successful match.

        Returns:
            True if a task was matched (task_name is not None), False otherwise
        """
        return self.task_name is not None
