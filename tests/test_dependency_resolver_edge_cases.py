"""Tests for edge case handling in dependency resolution.

Based on Gherkin scenarios from tests/bdd/dependency-resolution.feature
Scenario filter: edge_cases
"""
import pytest
from lib.skill_router.models import Skill
from lib.skill_router.dependency_resolver import KahnsDependencyResolver
from lib.skill_router.dependency_graph import DependencyResult


@pytest.fixture
def resolver():
    """Create dependency resolver instance."""
    return KahnsDependencyResolver()


class TestHandleSkillWithMissingDependencyReference:
    """Scenario: Handle skill with missing dependency reference."""

    def test_handle_skill_with_missing_dependency_reference(self, resolver):
        """
        Given skill "broken-skill" depends on "non-existent-skill"
        And "non-existent-skill" is not in the manifest
        When the dependency resolver processes "broken-skill"
        Then the missing dependency is skipped
        And a warning is logged
        """
        skills = {
            "broken-skill": Skill(
                name="broken-skill",
                description="Skill with missing dependency",
                path="./skills/broken-skill",
                depends_on=["non-existent-skill"]
            ),
        }

        result = resolver.resolve("broken-skill", skills)

        assert isinstance(result, DependencyResult)

        # The skill itself should be in the execution order
        assert "broken-skill" in result.execution_order

        # The missing dependency should not be in the execution order
        assert "non-existent-skill" not in result.execution_order

        # A warning should be logged
        assert len(result.warnings) > 0
        assert any("non-existent-skill" in warning for warning in result.warnings)
        assert any("broken-skill" in warning for warning in result.warnings)


class TestHandleEmptySkillsList:
    """Scenario: Handle empty skills list."""

    def test_handle_empty_skills_list(self, resolver):
        """
        Given a request for no skills
        When the dependency resolver processes the skills
        Then the execution order is empty
        """
        skills = {
            "some-skill": Skill(
                name="some-skill",
                description="Some skill",
                path="./skills/some-skill",
                depends_on=[]
            ),
        }

        # Resolve with empty list
        result = resolver.resolve_multi([], skills)

        assert isinstance(result, DependencyResult)
        assert result.execution_order == []
        assert len(result.execution_order) == 0


class TestHandleDeeplyNestedDependencies:
    """Scenario: Handle deeply nested dependencies."""

    def test_handle_deeply_nested_dependencies(self, resolver):
        """
        Given a chain of 5 dependent skills:
          | skill    | depends_on |
          | level-1  | []         |
          | level-2  | [level-1]  |
          | level-3  | [level-2]  |
          | level-4  | [level-3]  |
          | level-5  | [level-4]  |
        When the dependency resolver processes skill "level-5"
        Then the execution order contains 5 skills
        And skills appear in level order from 1 to 5
        """
        skills = {
            "level-1": Skill(
                name="level-1",
                description="Level 1",
                path="./skills/level-1",
                depends_on=[]
            ),
            "level-2": Skill(
                name="level-2",
                description="Level 2",
                path="./skills/level-2",
                depends_on=["level-1"]
            ),
            "level-3": Skill(
                name="level-3",
                description="Level 3",
                path="./skills/level-3",
                depends_on=["level-2"]
            ),
            "level-4": Skill(
                name="level-4",
                description="Level 4",
                path="./skills/level-4",
                depends_on=["level-3"]
            ),
            "level-5": Skill(
                name="level-5",
                description="Level 5",
                path="./skills/level-5",
                depends_on=["level-4"]
            ),
        }

        result = resolver.resolve("level-5", skills)

        assert isinstance(result, DependencyResult)

        # Execution order contains 5 skills
        assert len(result.execution_order) == 5

        # Skills appear in level order from 1 to 5
        assert result.execution_order == [
            "level-1",
            "level-2",
            "level-3",
            "level-4",
            "level-5"
        ]
