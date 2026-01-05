"""Factory function for creating a fully-wired SkillRouter for hooks."""
from typing import Optional

from lib.skill_router.models import Manifest
from lib.skill_router.interfaces.router import IRouter
from lib.skill_router.router.skill_router import SkillRouter
from lib.skill_router.matching.normalizer import DefaultQueryNormalizer
from lib.skill_router.matching.direct_matcher import DirectSkillMatcher
from lib.skill_router.matching.task_matcher import TaskTriggerMatcher
from lib.skill_router.matching.tokenizer import WordTokenizer
from lib.skill_router.matching.scorer import WordOverlapScorer
from lib.skill_router.dependency_resolver import KahnsDependencyResolver
from lib.skill_router.discovery.factory import create_llm_discovery


def create_router(manifest: Manifest, api_key: Optional[str] = None) -> IRouter:
    """Create a fully-wired SkillRouter instance for hook integration.

    This factory creates all necessary dependencies with sensible defaults:
    - DefaultQueryNormalizer for query normalization
    - DirectSkillMatcher for Tier 1 matching
    - TaskTriggerMatcher for Tier 2 matching
    - LLMDiscovery for Tier 3 matching
    - KahnsDependencyResolver for dependency resolution

    Args:
        manifest: Loaded and validated Manifest object
        api_key: Optional Anthropic API key for LLM discovery.
                 If None, reads from ANTHROPIC_API_KEY env var

    Returns:
        Fully configured IRouter instance ready to route queries
    """
    # Create normalizer
    normalizer = DefaultQueryNormalizer()

    # Create Tier 1 direct skill matcher
    direct_matcher = DirectSkillMatcher(normalizer, pattern_registry=None)

    # Create Tier 2 task trigger matcher
    tokenizer = WordTokenizer()
    scorer = WordOverlapScorer(threshold=0.6)
    task_matcher = TaskTriggerMatcher(tokenizer, scorer)

    # Create Tier 3 LLM discovery
    llm_discovery = create_llm_discovery(api_key)

    # Create dependency resolver
    dependency_resolver = KahnsDependencyResolver()

    # Wire everything together
    router = SkillRouter(
        manifest=manifest,
        normalizer=normalizer,
        direct_matcher=direct_matcher,
        task_matcher=task_matcher,
        llm_discovery=llm_discovery,
        dependency_resolver=dependency_resolver
    )

    return router
