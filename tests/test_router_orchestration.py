"""Tests for Router Orchestration (3-Tier Flow).

Tests cover all BDD scenarios from router-orchestration.feature:
- Tier flow and short-circuit logic
- Route result construction
- Query normalization
- Error handling
- Performance characteristics
- Edge cases
"""
import pytest
from unittest.mock import Mock, MagicMock
from lib.skill_router.models import Manifest, Skill, Task
from lib.skill_router.interfaces.router import RouteResult, RouteType
from lib.skill_router.router.normalizer import QueryNormalizer
from lib.skill_router.router.skill_router import SkillRouter
from lib.skill_router.matching.result import MatchResult, TaskMatchResult
from lib.skill_router.discovery.models import DiscoveryResult, SkillMatch, LLMResponse
from lib.skill_router.dependency_graph import DependencyResult


class TestTierFlowShortCircuit:
    """Test tier flow and short-circuit logic."""

    def test_tier1_match_short_circuits_remaining_tiers(self):
        """Tier 1 match should return immediately without invoking Tier 2 or 3."""
        # Arrange
        manifest = Manifest(
            skills={"terraform-base": Skill("terraform-base", "Terraform infrastructure", "/path", [])}
        )
        normalizer = QueryNormalizer()

        # Mock Tier 1 to return match
        direct_matcher = Mock()
        direct_matcher.match.return_value = MatchResult.exact_match("terraform-base")

        # Mock Tier 2 and 3 (should NOT be called)
        task_matcher = Mock()
        llm_discovery = Mock()

        # Mock dependency resolver
        dependency_resolver = Mock()
        dependency_resolver.resolve.return_value = DependencyResult(execution_order=["terraform-base"])

        router = SkillRouter(manifest, normalizer, direct_matcher, task_matcher, llm_discovery, dependency_resolver)

        # Act
        result = router.route("use terraform-base")

        # Assert
        assert result.route_type == RouteType.SKILL
        assert result.matched == "terraform-base"
        assert result.tier == 1

        # Verify Tier 2 and 3 were NOT invoked
        task_matcher.match.assert_not_called()
        llm_discovery.discover.assert_not_called()

    def test_tier2_executes_only_when_tier1_fails(self):
        """Tier 2 should execute only when Tier 1 finds no match."""
        # Arrange
        manifest = Manifest(
            skills={"fastapi-standards": Skill("fastapi-standards", "FastAPI standards", "/path", [])},
            tasks={"static-website": Task("static-website", "Build static website",
                                         ["build a static website"], ["fastapi-standards"])}
        )
        normalizer = QueryNormalizer()

        # Mock Tier 1 to return no match
        direct_matcher = Mock()
        direct_matcher.match.return_value = MatchResult.no_match()

        # Mock Tier 2 to return match
        task_matcher = Mock()
        task_matcher.match.return_value = TaskMatchResult.from_task(
            "static-website", 0.9, "build a static website", ["fastapi-standards"]
        )

        # Mock Tier 3 (should NOT be called)
        llm_discovery = Mock()

        # Mock dependency resolver
        dependency_resolver = Mock()
        dependency_resolver.resolve_multi.return_value = DependencyResult(execution_order=["fastapi-standards"])

        router = SkillRouter(manifest, normalizer, direct_matcher, task_matcher, llm_discovery, dependency_resolver)

        # Act
        result = router.route("build a static website")

        # Assert
        assert result.route_type == RouteType.TASK
        assert result.matched == "static-website"
        assert result.tier == 2

        # Verify Tier 1 was called, Tier 2 was called, Tier 3 was NOT called
        direct_matcher.match.assert_called_once()
        task_matcher.match.assert_called_once()
        llm_discovery.discover.assert_not_called()

    def test_tier3_executes_only_when_tier1_and_tier2_fail(self):
        """Tier 3 should execute only when both Tier 1 and Tier 2 find no match."""
        # Arrange
        manifest = Manifest(
            skills={"auth-cognito": Skill("auth-cognito", "AWS Cognito authentication", "/path", [])}
        )
        normalizer = QueryNormalizer()

        # Mock Tier 1 to return no match
        direct_matcher = Mock()
        direct_matcher.match.return_value = MatchResult.no_match()

        # Mock Tier 2 to return no match
        task_matcher = Mock()
        task_matcher.match.return_value = TaskMatchResult.no_match()

        # Mock Tier 3 to return match
        llm_discovery = Mock()
        llm_response = LLMResponse(text='{"skill": "auth-cognito", "confidence": 0.85}', model="test-model")
        llm_discovery.discover.return_value = DiscoveryResult(
            matches=[SkillMatch("auth-cognito", 0.85, "Handles user authentication")],
            raw_response=llm_response.text,
            model_used=llm_response.model
        )

        # Mock dependency resolver
        dependency_resolver = Mock()
        dependency_resolver.resolve.return_value = DependencyResult(execution_order=["auth-cognito"])

        router = SkillRouter(manifest, normalizer, direct_matcher, task_matcher, llm_discovery, dependency_resolver)

        # Act
        result = router.route("set up user authentication")

        # Assert
        assert result.route_type == RouteType.DISCOVERY
        assert result.matched == "auth-cognito"
        assert result.tier == 3
        assert result.confidence == 0.85

        # Verify all tiers were invoked
        direct_matcher.match.assert_called_once()
        task_matcher.match.assert_called_once()
        llm_discovery.discover.assert_called_once()


class TestRouteResultConstruction:
    """Test route result construction for different match types."""

    def test_skill_match_returns_correct_route_result(self):
        """Skill match should return RouteResult with correct structure."""
        # Arrange
        manifest = Manifest(
            skills={
                "ecr-setup": Skill("ecr-setup", "AWS ECR setup", "/path", ["aws-base"]),
                "aws-base": Skill("aws-base", "AWS base config", "/path", [])
            }
        )
        normalizer = QueryNormalizer()
        direct_matcher = Mock()
        direct_matcher.match.return_value = MatchResult.exact_match("ecr-setup")
        task_matcher = Mock()
        llm_discovery = Mock()
        dependency_resolver = Mock()
        dependency_resolver.resolve.return_value = DependencyResult(execution_order=["aws-base", "ecr-setup"])

        router = SkillRouter(manifest, normalizer, direct_matcher, task_matcher, llm_discovery, dependency_resolver)

        # Act
        result = router.route("apply ecr-setup")

        # Assert
        assert result.route_type == RouteType.SKILL
        assert result.matched == "ecr-setup"
        assert result.skills == ["ecr-setup"]
        assert result.execution_order == ["aws-base", "ecr-setup"]
        assert result.tier == 1
        assert result.confidence == 1.0

    def test_task_match_returns_correct_route_result(self):
        """Task match should return RouteResult with all task skills."""
        # Arrange
        manifest = Manifest(
            skills={
                "fastapi-standards": Skill("fastapi-standards", "FastAPI standards", "/path", []),
                "aws-ecs-deployment": Skill("aws-ecs-deployment", "ECS deployment", "/path", []),
                "rds-postgres": Skill("rds-postgres", "PostgreSQL on RDS", "/path", [])
            },
            tasks={
                "rest-api": Task("rest-api", "Create REST API",
                               ["create a REST API"],
                               ["fastapi-standards", "aws-ecs-deployment", "rds-postgres"])
            }
        )
        normalizer = QueryNormalizer()
        direct_matcher = Mock()
        direct_matcher.match.return_value = MatchResult.no_match()
        task_matcher = Mock()
        task_matcher.match.return_value = TaskMatchResult.from_task(
            "rest-api", 0.95, "create a REST API",
            ["fastapi-standards", "aws-ecs-deployment", "rds-postgres"]
        )
        llm_discovery = Mock()
        dependency_resolver = Mock()
        dependency_resolver.resolve_multi.return_value = DependencyResult(
            execution_order=["fastapi-standards", "aws-ecs-deployment", "rds-postgres"]
        )

        router = SkillRouter(manifest, normalizer, direct_matcher, task_matcher, llm_discovery, dependency_resolver)

        # Act
        result = router.route("create a REST API")

        # Assert
        assert result.route_type == RouteType.TASK
        assert result.matched == "rest-api"
        assert result.skills == ["fastapi-standards", "aws-ecs-deployment", "rds-postgres"]
        assert result.execution_order == ["fastapi-standards", "aws-ecs-deployment", "rds-postgres"]
        assert result.tier == 2

    def test_discovery_match_returns_correct_route_result(self):
        """Discovery match should return RouteResult with LLM confidence."""
        # Arrange
        manifest = Manifest(
            skills={"rds-postgres": Skill("rds-postgres", "PostgreSQL on RDS", "/path", [])}
        )
        normalizer = QueryNormalizer()
        direct_matcher = Mock()
        direct_matcher.match.return_value = MatchResult.no_match()
        task_matcher = Mock()
        task_matcher.match.return_value = TaskMatchResult.no_match()
        llm_discovery = Mock()
        llm_discovery.discover.return_value = DiscoveryResult(
            matches=[SkillMatch("rds-postgres", 0.78, "Database setup skill")],
            raw_response="{}",
            model_used="test-model"
        )
        dependency_resolver = Mock()
        dependency_resolver.resolve.return_value = DependencyResult(execution_order=["rds-postgres"])

        router = SkillRouter(manifest, normalizer, direct_matcher, task_matcher, llm_discovery, dependency_resolver)

        # Act
        result = router.route("help with database setup")

        # Assert
        assert result.route_type == RouteType.DISCOVERY
        assert result.matched == "rds-postgres"
        assert result.tier == 3
        assert result.confidence == 0.78


class TestQueryNormalization:
    """Test query normalization behavior."""

    def test_normalize_query_to_lowercase(self):
        """Normalizer should convert query to lowercase."""
        normalizer = QueryNormalizer()

        result = normalizer.normalize("USE TERRAFORM-BASE")

        assert result == "use terraform-base"

    def test_normalize_query_whitespace(self):
        """Normalizer should trim and collapse whitespace."""
        normalizer = QueryNormalizer()

        result = normalizer.normalize("  build   a   website  ")

        assert result == "build a website"
        assert result[0] != " "  # No leading whitespace
        assert result[-1] != " "  # No trailing whitespace
        assert "  " not in result  # No double spaces


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_return_error_when_no_match_found_at_any_tier(self):
        """Router should return error result when no tier finds a match."""
        # Arrange
        manifest = Manifest(skills={}, tasks={})
        normalizer = QueryNormalizer()
        direct_matcher = Mock()
        direct_matcher.match.return_value = MatchResult.no_match()
        task_matcher = Mock()
        task_matcher.match.return_value = TaskMatchResult.no_match()
        llm_discovery = Mock()
        llm_discovery.discover.return_value = DiscoveryResult(matches=[], raw_response="", model_used="test")
        dependency_resolver = Mock()

        router = SkillRouter(manifest, normalizer, direct_matcher, task_matcher, llm_discovery, dependency_resolver)

        # Act
        result = router.route("random nonsense query")

        # Assert
        assert result.route_type == RouteType.ERROR
        assert result.matched == ""
        assert result.skills == []
        assert result.execution_order == []
        assert result.tier == 0
        assert result.confidence == 0.0

    def test_handle_empty_query(self):
        """Router should return error for empty query."""
        # Arrange
        manifest = Manifest()
        normalizer = QueryNormalizer()
        direct_matcher = Mock()
        task_matcher = Mock()
        llm_discovery = Mock()
        dependency_resolver = Mock()

        router = SkillRouter(manifest, normalizer, direct_matcher, task_matcher, llm_discovery, dependency_resolver)

        # Act
        result = router.route("")

        # Assert
        assert result.route_type == RouteType.ERROR

        # Verify no matchers were invoked
        direct_matcher.match.assert_not_called()
        task_matcher.match.assert_not_called()
        llm_discovery.discover.assert_not_called()


class TestEdgeCases:
    """Test edge cases."""

    def test_handle_very_long_query(self):
        """Router should handle very long queries without error."""
        # Arrange
        manifest = Manifest()
        normalizer = QueryNormalizer()
        direct_matcher = Mock()
        direct_matcher.match.return_value = MatchResult.no_match()
        task_matcher = Mock()
        task_matcher.match.return_value = TaskMatchResult.no_match()
        llm_discovery = Mock()
        llm_discovery.discover.return_value = DiscoveryResult(matches=[], raw_response="", model_used="test")
        dependency_resolver = Mock()

        router = SkillRouter(manifest, normalizer, direct_matcher, task_matcher, llm_discovery, dependency_resolver)

        long_query = "a" * 1000

        # Act
        result = router.route(long_query)

        # Assert - Should complete without error
        assert isinstance(result, RouteResult)

    def test_handle_special_characters_in_query(self):
        """Router should handle special characters safely."""
        # Arrange
        manifest = Manifest()
        normalizer = QueryNormalizer()
        direct_matcher = Mock()
        direct_matcher.match.return_value = MatchResult.no_match()
        task_matcher = Mock()
        task_matcher.match.return_value = TaskMatchResult.no_match()
        llm_discovery = Mock()
        llm_discovery.discover.return_value = DiscoveryResult(matches=[], raw_response="", model_used="test")
        dependency_resolver = Mock()

        router = SkillRouter(manifest, normalizer, direct_matcher, task_matcher, llm_discovery, dependency_resolver)

        # Act
        result = router.route("build website <script>alert('xss')</script>")

        # Assert - Should complete without error
        assert isinstance(result, RouteResult)
        direct_matcher.match.assert_called_once()


class TestLLMDiscoveryTaskFallback:
    """Test LLM discovery can match tasks if skill doesn't exist."""

    def test_llm_discovery_matches_task_when_skill_not_found(self):
        """If LLM returns a task name instead of skill, router should handle it."""
        # Arrange
        manifest = Manifest(
            skills={"fastapi-standards": Skill("fastapi-standards", "FastAPI", "/path", [])},
            tasks={"rest-api": Task("rest-api", "REST API", ["api"], ["fastapi-standards"])}
        )
        normalizer = QueryNormalizer()
        direct_matcher = Mock()
        direct_matcher.match.return_value = MatchResult.no_match()
        task_matcher = Mock()
        task_matcher.match.return_value = TaskMatchResult.no_match()

        # LLM returns task name instead of skill name
        llm_discovery = Mock()
        llm_discovery.discover.return_value = DiscoveryResult(
            matches=[SkillMatch("rest-api", 0.9, "Task for API")],
            raw_response="{}",
            model_used="test"
        )
        dependency_resolver = Mock()
        dependency_resolver.resolve_multi.return_value = DependencyResult(execution_order=["fastapi-standards"])

        router = SkillRouter(manifest, normalizer, direct_matcher, task_matcher, llm_discovery, dependency_resolver)

        # Act
        result = router.route("help me build api")

        # Assert
        assert result.route_type == RouteType.TASK
        assert result.matched == "rest-api"
        assert result.skills == ["fastapi-standards"]


class TestRouteResultIsMatch:
    """Test the is_match() method on RouteResult."""

    def test_is_match_returns_true_for_skill_match(self):
        """is_match() should return True for skill matches."""
        result = RouteResult.skill_match("test-skill", ["test-skill"])
        assert result.is_match() is True

    def test_is_match_returns_true_for_task_match(self):
        """is_match() should return True for task matches."""
        result = RouteResult.task_match("test-task", ["skill1"], ["skill1"])
        assert result.is_match() is True

    def test_is_match_returns_true_for_discovery_match(self):
        """is_match() should return True for discovery matches."""
        result = RouteResult.discovery_match("test-skill", ["test-skill"], 0.8)
        assert result.is_match() is True

    def test_is_match_returns_false_for_error(self):
        """is_match() should return False for error results."""
        result = RouteResult.no_match()
        assert result.is_match() is False
