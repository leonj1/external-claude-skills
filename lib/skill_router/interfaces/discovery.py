"""Interfaces for LLM-based skill discovery components.

These interfaces define the contracts for components involved in Tier 3
LLM-based routing: prompt building, LLM invocation, and response parsing.
"""
from abc import ABC, abstractmethod
from typing import List
from lib.skill_router.discovery.models import (
    SkillSummary,
    DiscoveryResult,
    LLMResponse
)


class ILLMDiscovery(ABC):
    """Interface for LLM-based skill discovery orchestration.

    Coordinates the complete discovery flow:
    1. Build prompt with skill summaries
    2. Invoke LLM with prompt
    3. Parse LLM response into structured result

    This is the top-level interface that clients interact with.
    """

    @abstractmethod
    def discover(
        self,
        user_request: str,
        skill_summaries: List[SkillSummary],
        max_results: int = 3
    ) -> DiscoveryResult:
        """Discover skills matching a user request using LLM.

        Args:
            user_request: The user's natural language request
            skill_summaries: List of available skills with descriptions
            max_results: Maximum number of skills to return (default: 3)

        Returns:
            DiscoveryResult containing matched skills and metadata

        Raises:
            LLMClientError: If LLM API call fails
            ParseError: If LLM response cannot be parsed
        """
        pass


class IPromptBuilder(ABC):
    """Interface for building LLM prompts for skill discovery.

    Implementations can use different prompting strategies:
    - Zero-shot prompting
    - Few-shot prompting with examples
    - Chain-of-thought prompting
    """

    @abstractmethod
    def build_prompt(
        self,
        user_request: str,
        skill_summaries: List[SkillSummary],
        max_results: int
    ) -> str:
        """Build a prompt for LLM skill discovery.

        Args:
            user_request: The user's natural language request
            skill_summaries: List of available skills with descriptions
            max_results: Maximum number of skills to return

        Returns:
            Formatted prompt string ready for LLM invocation
        """
        pass


class ILLMClient(ABC):
    """Interface for LLM API invocation.

    Abstracts the specific LLM provider (Anthropic, OpenAI, etc.)
    to enable testing, provider switching, and retry logic.
    """

    @abstractmethod
    def invoke(self, prompt: str) -> LLMResponse:
        """Invoke the LLM with a prompt and return the response.

        Args:
            prompt: The prompt string to send to the LLM

        Returns:
            LLMResponse containing the response text and metadata

        Raises:
            LLMClientError: If API call fails (network, auth, rate limit, timeout)
        """
        pass


class IResponseParser(ABC):
    """Interface for parsing LLM responses into structured results.

    Handles malformed responses gracefully and extracts structured
    skill matches with confidence scores.
    """

    @abstractmethod
    def parse(self, llm_response: LLMResponse) -> DiscoveryResult:
        """Parse an LLM response into a structured discovery result.

        Args:
            llm_response: The raw response from the LLM

        Returns:
            DiscoveryResult with parsed matches and metadata

        Raises:
            ParseError: If the response cannot be parsed into valid structure
        """
        pass
