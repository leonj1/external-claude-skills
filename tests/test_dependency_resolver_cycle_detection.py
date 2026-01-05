"""Tests for cycle detection in dependency resolution.

Based on Gherkin scenarios from tests/bdd/dependency-resolution.feature
Scenario filter: cycle_detection
"""
import pytest
from lib.skill_router.models import Skill
from lib.skill_router.dependency_resolver import KahnsDependencyResolver
from lib.skill_router.dependency_graph import DependencyResult


@pytest.fixture
def resolver():
    """Create dependency resolver instance."""
    return KahnsDependencyResolver()


class TestDetectSimpleCircularDependency:
    """Scenario: Detect simple circular dependency."""

    def test_detect_simple_circular_dependency(self, resolver):
        """
        Given a manifest with circular dependencies:
          | skill    | depends_on |
          | skill-a  | [skill-b]  |
          | skill-b  | [skill-a]  |
        When the dependency resolver checks for cycles
        Then a cycle is detected containing "skill-a" and "skill-b"
        """
        skills = {
            "skill-a": Skill(
                name="skill-a",
                description="Skill A",
                path="./skills/skill-a",
                depends_on=["skill-b"]
            ),
            "skill-b": Skill(
                name="skill-b",
                description="Skill B",
                path="./skills/skill-b",
                depends_on=["skill-a"]
            ),
        }

        cycles = resolver.detect_cycles(skills)

        assert len(cycles) > 0, "A cycle should be detected"

        # Check that the cycle contains skill-a and skill-b
        cycle = cycles[0]
        assert "skill-a" in cycle
        assert "skill-b" in cycle


class TestDetectComplexCircularDependency:
    """Scenario: Detect complex circular dependency."""

    def test_detect_complex_circular_dependency(self, resolver):
        """
        Given a manifest with circular dependencies:
          | skill    | depends_on |
          | skill-a  | [skill-b]  |
          | skill-b  | [skill-c]  |
          | skill-c  | [skill-a]  |
        When the dependency resolver checks for cycles
        Then a cycle is detected
        """
        skills = {
            "skill-a": Skill(
                name="skill-a",
                description="Skill A",
                path="./skills/skill-a",
                depends_on=["skill-b"]
            ),
            "skill-b": Skill(
                name="skill-b",
                description="Skill B",
                path="./skills/skill-b",
                depends_on=["skill-c"]
            ),
            "skill-c": Skill(
                name="skill-c",
                description="Skill C",
                path="./skills/skill-c",
                depends_on=["skill-a"]
            ),
        }

        cycles = resolver.detect_cycles(skills)

        assert len(cycles) > 0, "A cycle should be detected"

        # The cycle should involve all three skills
        cycle = cycles[0]
        assert len(cycle) >= 3, "Complex cycle should involve multiple skills"


class TestHandleCircularDependencyGracefullyDuringResolution:
    """Scenario: Handle circular dependency gracefully during resolution."""

    def test_handle_circular_dependency_gracefully_during_resolution(self, resolver):
        """
        Given a manifest with circular dependencies:
          | skill    | depends_on |
          | skill-a  | [skill-b]  |
          | skill-b  | [skill-a]  |
        When the dependency resolver processes skill "skill-a"
        Then resolution completes with a warning
        And all skills are included in the result
        """
        skills = {
            "skill-a": Skill(
                name="skill-a",
                description="Skill A",
                path="./skills/skill-a",
                depends_on=["skill-b"]
            ),
            "skill-b": Skill(
                name="skill-b",
                description="Skill B",
                path="./skills/skill-b",
                depends_on=["skill-a"]
            ),
        }

        # Resolution should not raise an exception
        result = resolver.resolve("skill-a", skills)

        assert isinstance(result, DependencyResult)

        # All skills should be included in the result
        assert "skill-a" in result.execution_order
        assert "skill-b" in result.execution_order

        # A warning should be present
        assert result.has_cycle is True
        assert len(result.warnings) > 0
        assert "Circular dependency detected" in result.warnings[0]
