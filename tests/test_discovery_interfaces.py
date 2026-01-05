"""Tests for LLM discovery interface contracts and data models.

Following TDD approach, these tests define the interface contracts
before implementation based on BDD scenarios from llm-discovery.feature.
"""
import pytest
from abc import ABC
from typing import List, Optional
from dataclasses import FrozenInstanceError


class TestILLMDiscoveryInterface:
    """Test contract for ILLMDiscovery interface."""

    def test_interface_is_abstract(self):
        """ILLMDiscovery must be an ABC."""
        from lib.skill_router.interfaces.discovery import ILLMDiscovery
        assert issubclass(ILLMDiscovery, ABC)

    def test_discover_method_signature(self):
        """ILLMDiscovery.discover must have correct signature."""
        from lib.skill_router.interfaces.discovery import ILLMDiscovery
        from lib.skill_router.discovery.models import SkillSummary, DiscoveryResult
        import inspect

        sig = inspect.signature(ILLMDiscovery.discover)
        params = sig.parameters

        assert 'user_request' in params
        assert params['user_request'].annotation == str
        assert 'skill_summaries' in params
        assert 'max_results' in params
        assert params['max_results'].default == 3


class TestIPromptBuilderInterface:
    """Test contract for IPromptBuilder interface."""

    def test_interface_is_abstract(self):
        """IPromptBuilder must be an ABC."""
        from lib.skill_router.interfaces.discovery import IPromptBuilder
        assert issubclass(IPromptBuilder, ABC)

    def test_build_prompt_method_signature(self):
        """IPromptBuilder.build_prompt must have correct signature."""
        from lib.skill_router.interfaces.discovery import IPromptBuilder
        import inspect

        sig = inspect.signature(IPromptBuilder.build_prompt)
        params = sig.parameters

        assert 'user_request' in params
        assert params['user_request'].annotation == str
        assert 'skill_summaries' in params
        assert 'max_results' in params
        assert sig.return_annotation == str


class TestILLMClientInterface:
    """Test contract for ILLMClient interface."""

    def test_interface_is_abstract(self):
        """ILLMClient must be an ABC."""
        from lib.skill_router.interfaces.discovery import ILLMClient
        assert issubclass(ILLMClient, ABC)

    def test_invoke_method_signature(self):
        """ILLMClient.invoke must have correct signature."""
        from lib.skill_router.interfaces.discovery import ILLMClient
        import inspect

        sig = inspect.signature(ILLMClient.invoke)
        params = sig.parameters

        assert 'prompt' in params
        assert params['prompt'].annotation == str


class TestIResponseParserInterface:
    """Test contract for IResponseParser interface."""

    def test_interface_is_abstract(self):
        """IResponseParser must be an ABC."""
        from lib.skill_router.interfaces.discovery import IResponseParser
        assert issubclass(IResponseParser, ABC)

    def test_parse_method_signature(self):
        """IResponseParser.parse must have correct signature."""
        from lib.skill_router.interfaces.discovery import IResponseParser
        import inspect

        sig = inspect.signature(IResponseParser.parse)
        params = sig.parameters

        assert 'llm_response' in params


class TestSkillSummaryModel:
    """Test SkillSummary data model validation.

    BDD Scenario: LLM receives formatted task options
    The prompt must include all skill names and descriptions.
    """

    def test_skill_summary_is_frozen(self):
        """SkillSummary must be immutable (frozen dataclass)."""
        from lib.skill_router.discovery.models import SkillSummary

        summary = SkillSummary(name="docker-backend", description="Dockerize backend")

        with pytest.raises(FrozenInstanceError):
            summary.name = "changed"

    def test_skill_summary_creation_valid(self):
        """SkillSummary can be created with valid name and description."""
        from lib.skill_router.discovery.models import SkillSummary

        summary = SkillSummary(
            name="docker-backend",
            description="Dockerize backend projects"
        )

        assert summary.name == "docker-backend"
        assert summary.description == "Dockerize backend projects"

    def test_skill_summary_rejects_empty_name(self):
        """SkillSummary must reject empty name."""
        from lib.skill_router.discovery.models import SkillSummary

        with pytest.raises(ValueError, match="name cannot be empty"):
            SkillSummary(name="", description="Valid description")

    def test_skill_summary_rejects_empty_description(self):
        """SkillSummary must reject empty description."""
        from lib.skill_router.discovery.models import SkillSummary

        with pytest.raises(ValueError, match="description cannot be empty"):
            SkillSummary(name="docker-backend", description="")

    def test_skill_summary_rejects_whitespace_only_name(self):
        """SkillSummary must reject whitespace-only name."""
        from lib.skill_router.discovery.models import SkillSummary

        with pytest.raises(ValueError, match="name cannot be empty"):
            SkillSummary(name="   ", description="Valid description")

    def test_skill_summary_rejects_whitespace_only_description(self):
        """SkillSummary must reject whitespace-only description."""
        from lib.skill_router.discovery.models import SkillSummary

        with pytest.raises(ValueError, match="description cannot be empty"):
            SkillSummary(name="docker-backend", description="   ")


class TestSkillMatchModel:
    """Test SkillMatch data model validation.

    BDD Scenario: Successfully parse valid LLM JSON response
    The router must parse LLM response with confidence scores.
    """

    def test_skill_match_is_frozen(self):
        """SkillMatch must be immutable (frozen dataclass)."""
        from lib.skill_router.discovery.models import SkillMatch

        match = SkillMatch(
            skill_name="docker-backend",
            confidence=0.95,
            reasoning="User wants containerization"
        )

        with pytest.raises(FrozenInstanceError):
            match.confidence = 0.5

    def test_skill_match_creation_valid(self):
        """SkillMatch can be created with valid confidence."""
        from lib.skill_router.discovery.models import SkillMatch

        match = SkillMatch(
            skill_name="docker-backend",
            confidence=0.85,
            reasoning="Matches containerization intent"
        )

        assert match.skill_name == "docker-backend"
        assert match.confidence == 0.85
        assert match.reasoning == "Matches containerization intent"

    def test_skill_match_confidence_at_zero(self):
        """SkillMatch accepts confidence of 0.0."""
        from lib.skill_router.discovery.models import SkillMatch

        match = SkillMatch(
            skill_name="test-skill",
            confidence=0.0,
            reasoning="No match"
        )

        assert match.confidence == 0.0

    def test_skill_match_confidence_at_one(self):
        """SkillMatch accepts confidence of 1.0."""
        from lib.skill_router.discovery.models import SkillMatch

        match = SkillMatch(
            skill_name="test-skill",
            confidence=1.0,
            reasoning="Perfect match"
        )

        assert match.confidence == 1.0

    def test_skill_match_rejects_negative_confidence(self):
        """SkillMatch must reject confidence below 0.0."""
        from lib.skill_router.discovery.models import SkillMatch

        with pytest.raises(ValueError, match="confidence must be between 0.0 and 1.0"):
            SkillMatch(
                skill_name="test-skill",
                confidence=-0.1,
                reasoning="Invalid"
            )

    def test_skill_match_rejects_confidence_above_one(self):
        """SkillMatch must reject confidence above 1.0."""
        from lib.skill_router.discovery.models import SkillMatch

        with pytest.raises(ValueError, match="confidence must be between 0.0 and 1.0"):
            SkillMatch(
                skill_name="test-skill",
                confidence=1.1,
                reasoning="Invalid"
            )


class TestDiscoveryResultModel:
    """Test DiscoveryResult data model and properties.

    BDD Scenarios:
    - Successfully parse valid LLM JSON response
    - Handle malformed LLM JSON response (fallback behavior)
    """

    def test_discovery_result_is_frozen(self):
        """DiscoveryResult must be immutable (frozen dataclass)."""
        from lib.skill_router.discovery.models import DiscoveryResult, SkillMatch

        result = DiscoveryResult(
            matches=[],
            raw_response="{}",
            model_used="claude-3-haiku-20240307"
        )

        with pytest.raises(FrozenInstanceError):
            result.model_used = "different-model"

    def test_discovery_result_creation_with_matches(self):
        """DiscoveryResult stores matches in descending confidence order."""
        from lib.skill_router.discovery.models import DiscoveryResult, SkillMatch

        matches = [
            SkillMatch("skill-a", 0.95, "Best match"),
            SkillMatch("skill-b", 0.75, "Good match"),
            SkillMatch("skill-c", 0.50, "Weak match")
        ]

        result = DiscoveryResult(
            matches=matches,
            raw_response='{"matches": [...]}',
            model_used="claude-3-haiku-20240307",
            prompt_tokens=150,
            completion_tokens=75
        )

        assert len(result.matches) == 3
        assert result.matches[0].confidence == 0.95
        assert result.raw_response == '{"matches": [...]}'
        assert result.model_used == "claude-3-haiku-20240307"
        assert result.prompt_tokens == 150
        assert result.completion_tokens == 75

    def test_discovery_result_top_match_property_with_matches(self):
        """DiscoveryResult.top_match returns highest confidence match."""
        from lib.skill_router.discovery.models import DiscoveryResult, SkillMatch

        matches = [
            SkillMatch("skill-a", 0.95, "Best"),
            SkillMatch("skill-b", 0.75, "Good")
        ]

        result = DiscoveryResult(
            matches=matches,
            raw_response="{}",
            model_used="test-model"
        )

        assert result.top_match is not None
        assert result.top_match.skill_name == "skill-a"
        assert result.top_match.confidence == 0.95

    def test_discovery_result_top_match_property_empty(self):
        """DiscoveryResult.top_match returns None when no matches."""
        from lib.skill_router.discovery.models import DiscoveryResult

        result = DiscoveryResult(
            matches=[],
            raw_response="{}",
            model_used="test-model"
        )

        assert result.top_match is None

    def test_discovery_result_has_matches_property_true(self):
        """DiscoveryResult.has_matches returns True when matches exist."""
        from lib.skill_router.discovery.models import DiscoveryResult, SkillMatch

        result = DiscoveryResult(
            matches=[SkillMatch("skill-a", 0.5, "Match")],
            raw_response="{}",
            model_used="test-model"
        )

        assert result.has_matches is True

    def test_discovery_result_has_matches_property_false(self):
        """DiscoveryResult.has_matches returns False when no matches."""
        from lib.skill_router.discovery.models import DiscoveryResult

        result = DiscoveryResult(
            matches=[],
            raw_response="{}",
            model_used="test-model"
        )

        assert result.has_matches is False

    def test_discovery_result_optional_token_counts(self):
        """DiscoveryResult accepts None for optional token counts."""
        from lib.skill_router.discovery.models import DiscoveryResult

        result = DiscoveryResult(
            matches=[],
            raw_response="{}",
            model_used="test-model",
            prompt_tokens=None,
            completion_tokens=None
        )

        assert result.prompt_tokens is None
        assert result.completion_tokens is None


class TestLLMResponseModel:
    """Test LLMResponse data model.

    BDD Scenario: Successfully parse valid LLM JSON response
    The parser receives LLMResponse from the client.
    """

    def test_llm_response_is_frozen(self):
        """LLMResponse must be immutable (frozen dataclass)."""
        from lib.skill_router.discovery.models import LLMResponse

        response = LLMResponse(
            text='{"matches": []}',
            model="claude-3-haiku-20240307"
        )

        with pytest.raises(FrozenInstanceError):
            response.text = "different"

    def test_llm_response_creation_minimal(self):
        """LLMResponse can be created with required fields only."""
        from lib.skill_router.discovery.models import LLMResponse

        response = LLMResponse(
            text='{"skill": "docker-backend"}',
            model="claude-3-haiku-20240307"
        )

        assert response.text == '{"skill": "docker-backend"}'
        assert response.model == "claude-3-haiku-20240307"
        assert response.prompt_tokens is None
        assert response.completion_tokens is None
        assert response.finish_reason is None

    def test_llm_response_creation_full(self):
        """LLMResponse stores all fields including optional ones."""
        from lib.skill_router.discovery.models import LLMResponse

        response = LLMResponse(
            text='{"skill": "docker-backend"}',
            model="claude-3-haiku-20240307",
            prompt_tokens=100,
            completion_tokens=50,
            finish_reason="stop"
        )

        assert response.text == '{"skill": "docker-backend"}'
        assert response.model == "claude-3-haiku-20240307"
        assert response.prompt_tokens == 100
        assert response.completion_tokens == 50
        assert response.finish_reason == "stop"


class TestLLMDiscoveryExceptions:
    """Test LLM discovery exception hierarchy.

    BDD Scenario: Handle malformed LLM JSON response
    Parser must raise ParseError for invalid responses.
    """

    def test_llm_discovery_error_is_exception(self):
        """LLMDiscoveryError must inherit from Exception."""
        from lib.skill_router.exceptions import LLMDiscoveryError

        assert issubclass(LLMDiscoveryError, Exception)

    def test_llm_client_error_inherits_from_llm_discovery_error(self):
        """LLMClientError must inherit from LLMDiscoveryError."""
        from lib.skill_router.exceptions import LLMClientError, LLMDiscoveryError

        assert issubclass(LLMClientError, LLMDiscoveryError)

    def test_parse_error_inherits_from_llm_discovery_error(self):
        """ParseError must inherit from LLMDiscoveryError."""
        from lib.skill_router.exceptions import ParseError, LLMDiscoveryError

        assert issubclass(ParseError, LLMDiscoveryError)

    def test_llm_client_error_can_be_raised(self):
        """LLMClientError can be instantiated and raised."""
        from lib.skill_router.exceptions import LLMClientError

        with pytest.raises(LLMClientError, match="API timeout"):
            raise LLMClientError("API timeout")

    def test_parse_error_can_be_raised(self):
        """ParseError can be instantiated and raised."""
        from lib.skill_router.exceptions import ParseError

        with pytest.raises(ParseError, match="Invalid JSON"):
            raise ParseError("Invalid JSON")

    def test_llm_discovery_error_can_be_caught_as_base(self):
        """All LLM discovery errors can be caught as LLMDiscoveryError."""
        from lib.skill_router.exceptions import (
            LLMDiscoveryError,
            LLMClientError,
            ParseError
        )

        # Test LLMClientError
        with pytest.raises(LLMDiscoveryError):
            raise LLMClientError("Client error")

        # Test ParseError
        with pytest.raises(LLMDiscoveryError):
            raise ParseError("Parse error")
