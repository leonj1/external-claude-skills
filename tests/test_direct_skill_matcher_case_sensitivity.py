"""Tests for DirectSkillMatcher case-insensitive matching.

Based on Gherkin scenarios from tests/bdd/direct-skill-matching.feature
Scenarios tested:
- Match skill name case-insensitively
- Match mixed case skill request
"""
import pytest
from lib.skill_router.models import Skill
from lib.skill_router.matching.result import MatchResult
from lib.skill_router.matching.normalizer import DefaultQueryNormalizer
from lib.skill_router.matching.patterns import DefaultPatternRegistry
from lib.skill_router.matching.direct_matcher import DirectSkillMatcher


class TestDirectSkillMatcherCaseSensitivity:
    """Test case-insensitive matching for Direct Skill Matcher."""

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

    def test_match_skill_name_case_insensitively(self, matcher, skills):
        """
        Scenario: Match skill name case-insensitively
        Given a user query "USE TERRAFORM-BASE"
        When the router processes the query
        Then the route type is "skill"
        And the matched item is "terraform-base"
        """
        query = "USE TERRAFORM-BASE"
        result = matcher.match(query, skills)

        # Original skill name from manifest should be returned
        assert result.skill_name == "terraform-base"
        assert result.match_type == "exact"
        assert result.confidence == 1.0

    def test_match_mixed_case_skill_request(self, matcher, skills):
        """
        Scenario: Match mixed case skill request
        Given a user query "Apply Aws-Ecs-Deployment to my service"
        When the router processes the query
        Then the route type is "skill"
        And the matched item is "aws-ecs-deployment"
        """
        query = "Apply Aws-Ecs-Deployment to my service"
        result = matcher.match(query, skills)

        # Original skill name from manifest should be returned
        assert result.skill_name == "aws-ecs-deployment"
        assert result.match_type in ["exact", "pattern"]
        assert result.confidence in [0.9, 1.0]


class TestCaseNormalizationIntegration:
    """Integration tests for case normalization across components."""

    @pytest.fixture
    def normalizer(self):
        """Create DefaultQueryNormalizer instance."""
        return DefaultQueryNormalizer()

    def test_all_caps_query_normalized_to_lowercase(self, normalizer):
        """Verify normalizer converts ALL CAPS to lowercase."""
        result = normalizer.normalize("USE TERRAFORM-BASE")
        assert result == "use terraform-base"

    def test_mixed_case_query_normalized_to_lowercase(self, normalizer):
        """Verify normalizer converts MixedCase to lowercase."""
        result = normalizer.normalize("Apply Aws-Ecs-Deployment")
        assert result == "apply aws-ecs-deployment"

    def test_skill_name_matching_preserves_original_casing(self):
        """Verify matched skill name preserves original casing from manifest."""
        skills = {
            "terraform-base": Skill(
                name="terraform-base",
                description="Test",
                path=".claude/skills/terraform-base"
            )
        }
        normalizer = DefaultQueryNormalizer()
        matcher = DirectSkillMatcher(normalizer)

        # Query in ALL CAPS
        result = matcher.match("USE TERRAFORM-BASE", skills)

        # Original skill name should be returned (not uppercased)
        assert result.skill_name == "terraform-base"
