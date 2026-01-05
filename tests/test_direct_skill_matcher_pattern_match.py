"""Tests for DirectSkillMatcher pattern-based matching.

Based on Gherkin scenarios from tests/bdd/direct-skill-matching.feature
Scenarios tested:
- Match skill using common request patterns (8 pattern examples)
"""
import pytest
from lib.skill_router.models import Skill
from lib.skill_router.matching.result import MatchResult
from lib.skill_router.matching.normalizer import DefaultQueryNormalizer
from lib.skill_router.matching.patterns import DefaultPatternRegistry
from lib.skill_router.matching.direct_matcher import DirectSkillMatcher


class TestDirectSkillMatcherPatternMatch:
    """Test pattern-based matching for Direct Skill Matcher."""

    @pytest.fixture
    def skills(self):
        """Background: Manifest contains skills."""
        return {
            "terraform-base": Skill(
                name="terraform-base",
                description="Terraform state backend setup",
                path=".claude/skills/terraform-base"
            ),
            "aws-ecs-deployment": Skill(
                name="aws-ecs-deployment",
                description="ECS Fargate deployment",
                path=".claude/skills/aws-ecs-deployment"
            ),
            "auth-cognito": Skill(
                name="auth-cognito",
                description="AWS Cognito authentication",
                path=".claude/skills/auth-cognito"
            ),
            "nextjs-standards": Skill(
                name="nextjs-standards",
                description="Next.js project conventions",
                path=".claude/skills/nextjs-standards"
            ),
        }

    @pytest.fixture
    def matcher(self):
        """Create DirectSkillMatcher with DefaultQueryNormalizer and DefaultPatternRegistry."""
        normalizer = DefaultQueryNormalizer()
        pattern_registry = DefaultPatternRegistry()
        return DirectSkillMatcher(normalizer, pattern_registry)

    @pytest.mark.parametrize("query,expected_skill", [
        ("use terraform-base", "terraform-base"),
        ("apply aws-ecs-deployment", "aws-ecs-deployment"),
        ("run terraform-base setup", "terraform-base"),
        ("execute auth-cognito configuration", "auth-cognito"),
        ("terraform-base skill", "terraform-base"),
        ("deploy with aws-ecs-deployment", "aws-ecs-deployment"),
        ("set up auth-cognito", "auth-cognito"),
        ("configure nextjs-standards", "nextjs-standards"),
    ])
    def test_match_skill_using_common_patterns(self, matcher, skills, query, expected_skill):
        """
        Scenario Outline: Match skill using common request patterns
        Given a user query "<query>"
        When the router processes the query
        Then the route type is "skill"
        And the matched item is "<expected_skill>"
        """
        result = matcher.match(query, skills)

        assert result.skill_name == expected_skill
        # Pattern matches should have confidence 0.9 (or 1.0 if exact match first)
        assert result.match_type in ["exact", "pattern"]
        assert result.confidence in [0.9, 1.0]


class TestDefaultPatternRegistry:
    """Test DefaultPatternRegistry implementation."""

    @pytest.fixture
    def registry(self):
        """Create DefaultPatternRegistry instance."""
        return DefaultPatternRegistry()

    def test_get_patterns_returns_list(self, registry):
        """Registry should return list of pattern templates."""
        patterns = registry.get_patterns()
        assert isinstance(patterns, list)
        assert len(patterns) == 8

    def test_patterns_contain_placeholder(self, registry):
        """All patterns should contain {skill} placeholder."""
        patterns = registry.get_patterns()
        for pattern in patterns:
            assert "{skill}" in pattern

    def test_expand_pattern_substitutes_skill_name(self, registry):
        """Expand pattern should substitute {skill} with skill name."""
        pattern = "use {skill}"
        expanded = registry.expand_pattern(pattern, "terraform-base")
        assert expanded == "use terraform-base"

    def test_default_patterns_include_expected_phrases(self, registry):
        """Registry should include common request patterns."""
        patterns = registry.get_patterns()
        expected = [
            "use {skill}",
            "apply {skill}",
            "run {skill}",
            "execute {skill}",
            "{skill} skill",
            "deploy with {skill}",
            "set up {skill}",
            "configure {skill}",
        ]
        assert set(patterns) == set(expected)
