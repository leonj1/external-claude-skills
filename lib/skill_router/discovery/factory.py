"""Factory functions for creating LLM discovery components.

Provides convenient factory methods for wiring up discovery components
with sensible defaults.
"""
from typing import Optional
from lib.skill_router.interfaces.discovery import ILLMDiscovery
from lib.skill_router.discovery.prompt_builder import DiscoveryPromptBuilder
from lib.skill_router.discovery.llm_client import ClaudeHaikuClient
from lib.skill_router.discovery.response_parser import JSONResponseParser
from lib.skill_router.discovery.llm_discovery import LLMDiscovery


def create_llm_discovery(api_key: Optional[str] = None) -> ILLMDiscovery:
    """Create default LLMDiscovery instance with Claude Haiku.

    This factory method creates a fully wired LLMDiscovery instance
    using the default components:
    - DiscoveryPromptBuilder for prompt construction
    - ClaudeHaikuClient for LLM API invocation
    - JSONResponseParser for response parsing

    Args:
        api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var

    Returns:
        Fully configured ILLMDiscovery instance ready to use

    Raises:
        AuthenticationError: If no API key provided and env var not set

    Example:
        >>> discovery = create_llm_discovery()
        >>> result = discovery.discover("set up authentication", skill_summaries)
    """
    prompt_builder = DiscoveryPromptBuilder()
    llm_client = ClaudeHaikuClient(api_key)
    response_parser = JSONResponseParser()

    return LLMDiscovery(prompt_builder, llm_client, response_parser)
