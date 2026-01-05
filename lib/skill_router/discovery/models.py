"""Data models for LLM-based skill discovery.

These models represent the data structures used in Tier 3 LLM-based routing,
including skill summaries, match results, and LLM responses.
"""
from dataclasses import dataclass
from typing import List, Optional


def __post_init_skill_summary__(self):
    """Validate SkillSummary fields after initialization."""
    if not self.name or not self.name.strip():
        raise ValueError("name cannot be empty")
    if not self.description or not self.description.strip():
        raise ValueError("description cannot be empty")


def __post_init_skill_match__(self):
    """Validate SkillMatch confidence score after initialization."""
    if not (0.0 <= self.confidence <= 1.0):
        raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class SkillSummary:
    """Represents a skill summary for LLM prompting.

    Used to provide the LLM with minimal skill information for matching.

    Attributes:
        name: Unique skill identifier (e.g., "docker-backend")
        description: Brief description of what the skill does

    Raises:
        ValueError: If name or description are empty or whitespace-only
    """
    name: str
    description: str

    __post_init__ = __post_init_skill_summary__


@dataclass(frozen=True)
class SkillMatch:
    """Represents a matched skill with confidence and reasoning.

    Attributes:
        skill_name: Name of the matched skill
        confidence: Confidence score from 0.0 (no match) to 1.0 (perfect match)
        reasoning: LLM's explanation for why this skill matched

    Raises:
        ValueError: If confidence is not in range 0.0 to 1.0
    """
    skill_name: str
    confidence: float
    reasoning: str

    __post_init__ = __post_init_skill_match__


@dataclass(frozen=True)
class LLMResponse:
    """Represents a raw response from an LLM API.

    Attributes:
        text: The response content from the LLM
        model: Model identifier that generated the response
        prompt_tokens: Number of tokens in the prompt (optional, for cost tracking)
        completion_tokens: Number of tokens in the completion (optional, for cost tracking)
        finish_reason: Reason the generation stopped (e.g., "stop", "length")
    """
    text: str
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    finish_reason: Optional[str] = None


@dataclass(frozen=True)
class DiscoveryResult:
    """Represents the result of LLM-based skill discovery.

    Contains matched skills ranked by confidence, along with metadata
    for debugging and cost tracking.

    Attributes:
        matches: List of SkillMatch objects, sorted by confidence descending
        raw_response: Original LLM response text for debugging
        model_used: Model identifier used for discovery
        prompt_tokens: Number of tokens in the prompt (optional, for cost tracking)
        completion_tokens: Number of tokens in the completion (optional, for cost tracking)
    """
    matches: List[SkillMatch]
    raw_response: str
    model_used: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None

    @property
    def top_match(self) -> Optional[SkillMatch]:
        """Return the highest confidence match, or None if no matches.

        Returns:
            The first SkillMatch from matches list, or None if empty
        """
        return self.matches[0] if self.matches else None

    @property
    def has_matches(self) -> bool:
        """Check if any skills were matched.

        Returns:
            True if matches list is non-empty, False otherwise
        """
        return len(self.matches) > 0
