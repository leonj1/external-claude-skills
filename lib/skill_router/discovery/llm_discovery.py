"""LLM-based skill discovery orchestrator.

Coordinates prompt building, LLM invocation, and response parsing
for Tier 3 intelligent skill routing.
"""
from typing import List
from lib.skill_router.interfaces.discovery import (
    ILLMDiscovery,
    IPromptBuilder,
    ILLMClient,
    IResponseParser
)
from lib.skill_router.discovery.models import SkillSummary, DiscoveryResult
from lib.skill_router.exceptions import LLMClientError, ParseError


class LLMDiscovery(ILLMDiscovery):
    """Orchestrates LLM-based skill discovery.

    Composes prompt building, LLM invocation, and response parsing
    into a single cohesive workflow.
    """

    def __init__(
        self,
        prompt_builder: IPromptBuilder,
        llm_client: ILLMClient,
        response_parser: IResponseParser
    ):
        """Initialize LLMDiscovery with dependency injection.

        Args:
            prompt_builder: Component that builds LLM prompts
            llm_client: Component that invokes the LLM API
            response_parser: Component that parses LLM responses
        """
        self._prompt_builder = prompt_builder
        self._llm_client = llm_client
        self._response_parser = response_parser

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
            LLMClientError: If LLM API call fails (re-raised for caller to handle)
            ParseError: Caught and returned as empty DiscoveryResult with error in metadata
        """
        try:
            # Step 1: Build prompt
            prompt = self._prompt_builder.build_prompt(
                user_request=user_request,
                skill_summaries=skill_summaries,
                max_results=max_results
            )

            # Step 2: Invoke LLM
            llm_response = self._llm_client.invoke(prompt)

            # Step 3: Parse response
            discovery_result = self._response_parser.parse(llm_response)

            return discovery_result

        except LLMClientError:
            # Re-raise LLM client errors for caller to handle
            # (caller may want to implement retry logic or fallback)
            raise

        except ParseError as e:
            # ParseError: Return empty result with error metadata
            # This allows graceful degradation instead of crashing
            return DiscoveryResult(
                matches=[],
                raw_response=str(e),
                model_used="parse-error",
                prompt_tokens=None,
                completion_tokens=None
            )
