"""Tests for DirectSkillMatcher exact name matching.

Based on Gherkin scenarios from tests/bdd/direct-skill-matching.feature
Scenarios tested:
- Match skill by exact name in query
- Match skill name embedded in query
- Match skill with hyphenated name
"""
import pytest
from lib.skill_router.models import Skill
from lib.skill_router.matching.result import MatchResult
from lib.skill_router.matching.normalizer import DefaultQueryNormalizer
from lib.skill_router.matching.direct_matcher import DirectSkillMatcher


class TestDirectSkillMatcherExactMatch:
    """Test exact name matching for Direct Skill Matcher."""

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
        """Create DirectSkillMatcher with DefaultQueryNormalizer."""
        normalizer = DefaultQueryNormalizer()
        return DirectSkillMatcher(normalizer)

    def test_match_skill_by_exact_name_in_query(self, matcher, skills):
        """
        Scenario: Match skill by exact name in query
        Given a user query "use terraform-base for this project"
        When the router processes the query
        Then the route type is "skill"
        And the matched item is "terraform-base"
        """
        query = "use terraform-base for this project"
        result = matcher.match(query, skills)

        assert result.skill_name == "terraform-base"
        assert result.match_type == "exact"
        assert result.confidence == 1.0

    def test_match_skill_name_embedded_in_query(self, matcher, skills):
        """
        Scenario: Match skill name embedded in query
        Given a user query "I want to deploy with aws-ecs-deployment"
        When the router processes the query
        Then the route type is "skill"
        And the matched item is "aws-ecs-deployment"
        """
        query = "I want to deploy with aws-ecs-deployment"
        result = matcher.match(query, skills)

        assert result.skill_name == "aws-ecs-deployment"
        assert result.match_type == "exact"
        assert result.confidence == 1.0

    def test_match_skill_with_hyphenated_name(self, matcher, skills):
        """
        Scenario: Match skill with hyphenated name
        Given a user query "configure auth-cognito for login"
        When the router processes the query
        Then the route type is "skill"
        And the matched item is "auth-cognito"
        """
        query = "configure auth-cognito for login"
        result = matcher.match(query, skills)

        assert result.skill_name == "auth-cognito"
        assert result.match_type == "exact"
        assert result.confidence == 1.0


class TestMatchResult:
    """Test MatchResult dataclass and factory methods."""

    def test_no_match_factory(self):
        """Test MatchResult.no_match() factory method."""
        result = MatchResult.no_match()

        assert result.skill_name is None
        assert result.match_type is None
        assert result.confidence == 0.0

    def test_exact_match_factory(self):
        """Test MatchResult.exact_match() factory method."""
        result = MatchResult.exact_match("terraform-base")

        assert result.skill_name == "terraform-base"
        assert result.match_type == "exact"
        assert result.confidence == 1.0

    def test_pattern_match_factory(self):
        """Test MatchResult.pattern_match() factory method."""
        result = MatchResult.pattern_match("aws-ecs-deployment")

        assert result.skill_name == "aws-ecs-deployment"
        assert result.match_type == "pattern"
        assert result.confidence == 0.9


class TestDefaultQueryNormalizer:
    """Test DefaultQueryNormalizer implementation."""

    @pytest.fixture
    def normalizer(self):
        """Create DefaultQueryNormalizer instance."""
        return DefaultQueryNormalizer()

    def test_convert_to_lowercase(self, normalizer):
        """Normalizer should convert query to lowercase."""
        result = normalizer.normalize("USE TERRAFORM-BASE")
        assert result == "use terraform-base"

    def test_strip_whitespace(self, normalizer):
        """Normalizer should strip leading/trailing whitespace."""
        result = normalizer.normalize("  use terraform-base  ")
        assert result == "use terraform-base"

    def test_preserve_hyphens(self, normalizer):
        """Normalizer should preserve hyphens in skill names."""
        result = normalizer.normalize("auth-cognito")
        assert "auth-cognito" in result

    def test_normalize_mixed_case(self, normalizer):
        """Normalizer should handle mixed case input."""
        result = normalizer.normalize("Apply Aws-Ecs-Deployment")
        assert result == "apply aws-ecs-deployment"
