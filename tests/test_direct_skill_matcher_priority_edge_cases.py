"""Tests for DirectSkillMatcher priority handling and edge cases.

Based on Gherkin scenarios from tests/bdd/direct-skill-matching.feature
Scenarios tested:
- Prioritize longer skill name when multiple match
- No match when skill name not in query
- Handle query with only skill name
- Handle skill name with surrounding punctuation
"""
import pytest
from lib.skill_router.models import Skill
from lib.skill_router.matching.result import MatchResult
from lib.skill_router.matching.normalizer import DefaultQueryNormalizer
from lib.skill_router.matching.patterns import DefaultPatternRegistry
from lib.skill_router.matching.direct_matcher import DirectSkillMatcher


class TestDirectSkillMatcherPriorityAndEdgeCases:
    """Test priority handling and edge cases for Direct Skill Matcher."""

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

    def test_prioritize_longer_skill_name_when_multiple_match(self, matcher):
        """
        Scenario: Prioritize longer skill name when multiple match
        Given the manifest also contains skill "terraform"
        And a user query "use terraform-base for infrastructure"
        When the router processes the query
        Then the matched item is "terraform-base"
        """
        # Add "terraform" as shorter skill
        skills_with_terraform = {
            "terraform": Skill(
                name="terraform",
                description="Terraform tool",
                path=".claude/skills/terraform"
            ),
            "terraform-base": Skill(
                name="terraform-base",
                description="Terraform state backend setup",
                path=".claude/skills/terraform-base"
            ),
        }

        query = "use terraform-base for infrastructure"
        result = matcher.match(query, skills_with_terraform)

        # Longer skill name should match first
        assert result.skill_name == "terraform-base"

    def test_no_match_when_skill_name_not_in_query(self, matcher, skills):
        """
        Scenario: No match when skill name not in query
        Given a user query "build a website for my company"
        When the router processes the query at tier 1
        Then no direct skill match is found
        """
        query = "build a website for my company"
        result = matcher.match(query, skills)

        assert result.skill_name is None
        assert result.match_type is None
        assert result.confidence == 0.0

    def test_handle_query_with_only_skill_name(self, matcher, skills):
        """
        Scenario: Handle query with only skill name
        Given a user query "terraform-base"
        When the router processes the query
        Then the route type is "skill"
        And the matched item is "terraform-base"
        """
        query = "terraform-base"
        result = matcher.match(query, skills)

        assert result.skill_name == "terraform-base"
        assert result.match_type == "exact"
        assert result.confidence == 1.0

    def test_handle_skill_name_with_surrounding_punctuation(self, matcher, skills):
        """
        Scenario: Handle skill name with surrounding punctuation
        Given a user query "Can you apply 'aws-ecs-deployment'?"
        When the router processes the query
        Then the route type is "skill"
        And the matched item is "aws-ecs-deployment"
        """
        query = "Can you apply 'aws-ecs-deployment'?"
        result = matcher.match(query, skills)

        # Should match despite quotes
        assert result.skill_name == "aws-ecs-deployment"
        assert result.match_type in ["exact", "pattern"]


class TestQueryNormalizerPunctuation:
    """Test punctuation handling in query normalizer."""

    @pytest.fixture
    def normalizer(self):
        """Create DefaultQueryNormalizer instance."""
        return DefaultQueryNormalizer()

    def test_preserve_skill_name_with_quotes(self, normalizer):
        """Normalizer should preserve skill names even with surrounding quotes."""
        query = "Can you apply 'aws-ecs-deployment'?"
        result = normalizer.normalize(query)

        # The skill name should still be detectable in normalized query
        assert "aws-ecs-deployment" in result

    def test_handle_double_quotes(self, normalizer):
        """Normalizer should handle double quotes."""
        query = 'Use "terraform-base" for this'
        result = normalizer.normalize(query)

        assert "terraform-base" in result

    def test_handle_question_marks(self, normalizer):
        """Normalizer should handle question marks."""
        query = "terraform-base?"
        result = normalizer.normalize(query)

        assert "terraform-base" in result


class TestMatchResultNoMatch:
    """Test no-match result behavior."""

    def test_no_match_factory_returns_correct_values(self):
        """Verify no_match() factory returns expected values."""
        result = MatchResult.no_match()

        assert result.skill_name is None
        assert result.match_type is None
        assert result.confidence == 0.0


class TestSkillNameSorting:
    """Test skill name sorting by length."""

    def test_skill_names_sorted_by_length_descending(self):
        """Verify longer skill names are checked first."""
        skills = {
            "terraform": Skill(name="terraform", description="", path=""),
            "terraform-base": Skill(name="terraform-base", description="", path=""),
            "terraform-base-aws": Skill(name="terraform-base-aws", description="", path=""),
        }

        normalizer = DefaultQueryNormalizer()
        matcher = DirectSkillMatcher(normalizer)

        # Query contains all three as substrings
        query = "use terraform-base-aws here"
        result = matcher.match(query, skills)

        # Longest should match first
        assert result.skill_name == "terraform-base-aws"
