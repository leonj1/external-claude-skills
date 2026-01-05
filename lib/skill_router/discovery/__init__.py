"""LLM-based skill discovery module for Tier 3 routing."""

# Only export models to avoid circular imports
# Import implementations lazily when needed
from lib.skill_router.discovery.models import (
    SkillSummary,
    SkillMatch,
    LLMResponse,
    DiscoveryResult
)


def __getattr__(name):
    """Lazy import of implementation classes to avoid circular imports."""
    if name == 'DiscoveryPromptBuilder':
        from lib.skill_router.discovery.prompt_builder import DiscoveryPromptBuilder
        return DiscoveryPromptBuilder
    elif name == 'ClaudeHaikuClient':
        from lib.skill_router.discovery.llm_client import ClaudeHaikuClient
        return ClaudeHaikuClient
    elif name == 'JSONResponseParser':
        from lib.skill_router.discovery.response_parser import JSONResponseParser
        return JSONResponseParser
    elif name == 'LLMDiscovery':
        from lib.skill_router.discovery.llm_discovery import LLMDiscovery
        return LLMDiscovery
    elif name == 'create_llm_discovery':
        from lib.skill_router.discovery.factory import create_llm_discovery
        return create_llm_discovery
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Data models
    'SkillSummary',
    'SkillMatch',
    'LLMResponse',
    'DiscoveryResult',
    # Components
    'DiscoveryPromptBuilder',
    'ClaudeHaikuClient',
    'JSONResponseParser',
    'LLMDiscovery',
    # Factory
    'create_llm_discovery',
]
