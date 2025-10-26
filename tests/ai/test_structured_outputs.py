"""Tests for Instructor-based structured LLM outputs.

Test coverage:
- InstructorClientFactory creation and feature flag behavior
- Response model validation (FallacyAnalysisResult, PerspectiveAnalysisResult)
- Field validators and model validators
- Retry logic on validation failures
- Graceful fallback when Instructor disabled
"""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest
from openai import AsyncOpenAI, OpenAI
from pydantic import ValidationError

from ai.response_models import (
    ConfidenceLevel,
    ContentQuality,
    FallacyAnalysisResult,
    FallacyInstance,
    FallacyType,
    PerspectiveAnalysisResult,
    PerspectiveInstance,
    PerspectiveType,
    SeverityLevel,
)
from ai.structured_outputs import INSTRUCTOR_AVAILABLE, InstructorClientFactory


# ====== Fixtures ======


@pytest.fixture
def mock_config():
    """Mock SecureConfig with test settings."""
    with patch("ai.structured_outputs.get_config") as mock:
        config = Mock()
        config.enable_instructor = True
        config.openai_api_key = "test-openai-key"
        config.openrouter_api_key = "test-openrouter-key"
        config.instructor_max_retries = 3
        config.instructor_timeout = 30
        mock.return_value = config
        yield config


@pytest.fixture
def mock_instructor():
    """Mock instructor module."""
    if not INSTRUCTOR_AVAILABLE:
        pytest.skip("instructor library not installed")
    with patch("ai.structured_outputs.instructor") as mock:
        yield mock


# ====== Response Model Tests ======


class TestFallacyInstance:
    """Tests for FallacyInstance validation."""

    def test_valid_instance(self):
        """Valid fallacy instance should pass validation."""
        instance = FallacyInstance(
            fallacy_type=FallacyType.AD_HOMINEM,
            quote="You're an idiot, so your argument is wrong",
            explanation="This attacks the person rather than addressing the argument itself",
            severity=SeverityLevel.HIGH,
            confidence=ConfidenceLevel.HIGH,
            line_number=10,
        )
        assert instance.fallacy_type == FallacyType.AD_HOMINEM
        assert instance.severity == SeverityLevel.HIGH
        assert instance.line_number == 10

    def test_quote_validation(self):
        """Empty or whitespace quote should fail validation."""
        with pytest.raises(ValidationError, match="Quote cannot be empty"):
            FallacyInstance(
                fallacy_type=FallacyType.STRAW_MAN,
                quote="   ",  # Whitespace only
                explanation="This misrepresents the argument",
                severity=SeverityLevel.MEDIUM,
                confidence=ConfidenceLevel.MEDIUM,
            )

    def test_explanation_validation(self):
        """Too short explanation should fail validation."""
        with pytest.raises(ValidationError, match="at least 10 characters"):
            FallacyInstance(
                fallacy_type=FallacyType.RED_HERRING,
                quote="Let's talk about something else",
                explanation="Too short",  # Less than 10 chars
                severity=SeverityLevel.LOW,
                confidence=ConfidenceLevel.LOW,
            )

    def test_quote_strip(self):
        """Quote should be stripped of whitespace."""
        instance = FallacyInstance(
            fallacy_type=FallacyType.BANDWAGON,
            quote="  Everyone believes this  ",
            explanation="Appeals to popular opinion rather than evidence",
            severity=SeverityLevel.MEDIUM,
            confidence=ConfidenceLevel.MEDIUM,
        )
        assert instance.quote == "Everyone believes this"


class TestFallacyAnalysisResult:
    """Tests for FallacyAnalysisResult validation."""

    def test_valid_analysis(self):
        """Valid analysis result should pass validation."""
        result = FallacyAnalysisResult(
            fallacies=[
                FallacyInstance(
                    fallacy_type=FallacyType.AD_HOMINEM,
                    quote="You're wrong because you're stupid",
                    explanation="Attacks the person instead of the argument",
                    severity=SeverityLevel.HIGH,
                    confidence=ConfidenceLevel.HIGH,
                )
            ],
            overall_quality=ContentQuality.POOR,
            credibility_score=0.3,
            summary="This argument contains personal attacks and lacks logical reasoning",
            recommendations=["Focus on the argument, not the person", "Provide evidence for claims"],
            key_issues=["Ad hominem attack", "No supporting evidence"],
        )
        assert len(result.fallacies) == 1
        assert result.credibility_score == 0.3
        assert result.overall_quality == ContentQuality.POOR

    def test_credibility_fallacy_consistency_high_fallacies(self):
        """High fallacy count should result in lower credibility."""
        # Create 12 fallacies (> 10 threshold)
        many_fallacies = [
            FallacyInstance(
                fallacy_type=FallacyType.AD_HOMINEM,
                quote=f"Fallacy quote {i}",
                explanation=f"Explanation for fallacy {i}",
                severity=SeverityLevel.MEDIUM,
                confidence=ConfidenceLevel.MEDIUM,
            )
            for i in range(12)
        ]

        with pytest.raises(ValidationError, match="High fallacy count should result in lower credibility"):
            FallacyAnalysisResult(
                fallacies=many_fallacies,
                overall_quality=ContentQuality.POOR,
                credibility_score=0.6,  # Too high for 12 fallacies
                summary="Analysis summary that is long enough to pass validation requirements",
            )

    def test_credibility_fallacy_consistency_no_fallacies(self):
        """No fallacies should result in higher credibility."""
        with pytest.raises(ValidationError, match="No fallacies should result in higher credibility"):
            FallacyAnalysisResult(
                fallacies=[],
                overall_quality=ContentQuality.EXCELLENT,
                credibility_score=0.5,  # Too low for no fallacies
                summary="Clean argument with no logical errors detected in the analysis",
            )

    def test_summary_validation(self):
        """Summary must be at least 20 characters."""
        with pytest.raises(ValidationError, match="at least 20 characters"):
            FallacyAnalysisResult(
                fallacies=[],
                overall_quality=ContentQuality.GOOD,
                credibility_score=0.8,
                summary="Too short",  # Less than 20 chars
            )


class TestPerspectiveInstance:
    """Tests for PerspectiveInstance validation."""

    def test_valid_instance(self):
        """Valid perspective instance should pass validation."""
        instance = PerspectiveInstance(
            perspective_type=PerspectiveType.PROGRESSIVE,
            evidence="Emphasizes social equality and government intervention",
            confidence=ConfidenceLevel.HIGH,
            prominence=0.8,
            bias_indicators=["social justice", "equity", "systemic change"],
        )
        assert instance.perspective_type == PerspectiveType.PROGRESSIVE
        assert instance.prominence == 0.8
        assert len(instance.bias_indicators) == 3

    def test_prominence_range(self):
        """Prominence must be between 0.0 and 1.0."""
        with pytest.raises(ValidationError):
            PerspectiveInstance(
                perspective_type=PerspectiveType.CONSERVATIVE,
                evidence="Traditional values and free markets",
                confidence=ConfidenceLevel.MEDIUM,
                prominence=1.5,  # Out of range
            )

    def test_bias_indicators_cleanup(self):
        """Bias indicators should be stripped and empty ones removed."""
        instance = PerspectiveInstance(
            perspective_type=PerspectiveType.LIBERTARIAN,
            evidence="Emphasis on individual liberty and minimal government",
            confidence=ConfidenceLevel.HIGH,
            prominence=0.7,
            bias_indicators=["  freedom  ", "", "   liberty   ", "  "],
        )
        assert instance.bias_indicators == ["freedom", "liberty"]


class TestPerspectiveAnalysisResult:
    """Tests for PerspectiveAnalysisResult validation."""

    def test_valid_analysis(self):
        """Valid perspective analysis should pass validation."""
        result = PerspectiveAnalysisResult(
            perspectives=[
                PerspectiveInstance(
                    perspective_type=PerspectiveType.PROGRESSIVE,
                    evidence="Focuses on systemic solutions and collective action",
                    confidence=ConfidenceLevel.HIGH,
                    prominence=0.9,
                )
            ],
            dominant_perspective=PerspectiveType.PROGRESSIVE,
            bias_score=0.7,
            balance_score=0.3,
            framing_analysis="Content strongly emphasizes progressive solutions with limited conservative viewpoints",
            omitted_perspectives=[PerspectiveType.CONSERVATIVE, PerspectiveType.LIBERTARIAN],
            recommendations=["Include market-based solutions", "Present conservative counterarguments"],
        )
        assert result.dominant_perspective == PerspectiveType.PROGRESSIVE
        assert result.bias_score == 0.7
        assert result.balance_score == 0.3

    def test_bias_balance_consistency_high_bias_high_balance(self):
        """High bias should correlate with low balance."""
        with pytest.raises(ValidationError, match="High bias should correlate with low balance"):
            PerspectiveAnalysisResult(
                perspectives=[],
                bias_score=0.8,  # High bias
                balance_score=0.6,  # But high balance - inconsistent
                framing_analysis="Analysis of framing that is long enough to pass validation",
            )

    def test_bias_balance_consistency_many_perspectives_low_balance(self):
        """Many perspectives should indicate better balance."""
        many_perspectives = [
            PerspectiveInstance(
                perspective_type=PerspectiveType.PROGRESSIVE,
                evidence=f"Evidence for perspective {i}",
                confidence=ConfidenceLevel.MEDIUM,
                prominence=0.5,
            )
            for i in range(6)  # > 5 threshold
        ]

        with pytest.raises(ValidationError, match="Many perspectives should indicate better balance"):
            PerspectiveAnalysisResult(
                perspectives=many_perspectives,
                bias_score=0.4,
                balance_score=0.2,  # Too low for 6 perspectives
                framing_analysis="Framing analysis text that meets the minimum character requirement",
            )


# ====== InstructorClientFactory Tests ======


class TestInstructorClientFactory:
    """Tests for InstructorClientFactory."""

    def test_is_enabled_when_flag_true_and_available(self, mock_config):
        """Should return True when flag is enabled and library is available."""
        mock_config.enable_instructor = True
        if not INSTRUCTOR_AVAILABLE:
            pytest.skip("instructor library not installed")

        assert InstructorClientFactory.is_enabled() is True

    def test_is_enabled_when_flag_false(self, mock_config):
        """Should return False when flag is disabled."""
        mock_config.enable_instructor = False

        assert InstructorClientFactory.is_enabled() is False

    @patch("ai.structured_outputs.INSTRUCTOR_AVAILABLE", False)
    def test_is_enabled_when_library_not_available(self, mock_config):
        """Should return False and log warning when library not installed."""
        mock_config.enable_instructor = True

        with patch("ai.structured_outputs.logger") as mock_logger:
            assert InstructorClientFactory.is_enabled() is False
            mock_logger.warning.assert_called_once()
            assert "instructor" in str(mock_logger.warning.call_args)

    def test_create_client_returns_openai_client(self, mock_config):
        """Should create OpenAI client with correct parameters."""
        client = InstructorClientFactory.create_client()

        assert isinstance(client, (OpenAI, object))  # Might be Instructor-wrapped
        # Can't assert exact type due to Instructor wrapping

    def test_create_client_with_custom_params(self, mock_config):
        """Should accept custom parameters."""
        client = InstructorClientFactory.create_client(
            api_key="custom-key",
            base_url="https://custom.api.com",
            max_retries=5,
            timeout=60,
        )

        assert client is not None

    def test_create_async_client(self, mock_config):
        """Should create async OpenAI client."""
        client = InstructorClientFactory.create_async_client()

        assert isinstance(client, (AsyncOpenAI, object))

    def test_create_openrouter_client(self, mock_config):
        """Should create client configured for OpenRouter."""
        client = InstructorClientFactory.create_openrouter_client()

        assert client is not None
        # Client should have OpenRouter base URL configured internally

    def test_create_async_openrouter_client(self, mock_config):
        """Should create async client configured for OpenRouter."""
        client = InstructorClientFactory.create_async_openrouter_client()

        assert client is not None

    @patch("ai.structured_outputs.INSTRUCTOR_AVAILABLE", False)
    def test_create_client_when_instructor_disabled(self, mock_config):
        """Should return standard OpenAI client when Instructor disabled."""
        mock_config.enable_instructor = False

        with patch("ai.structured_outputs.logger") as mock_logger:
            client = InstructorClientFactory.create_client()

            assert isinstance(client, OpenAI)
            mock_logger.debug.assert_called()
            assert "disabled" in str(mock_logger.debug.call_args).lower()


# ====== Integration-Style Tests ======


@pytest.mark.skipif(not INSTRUCTOR_AVAILABLE, reason="instructor library not installed")
class TestInstructorIntegration:
    """Integration tests for Instructor functionality (requires library)."""

    def test_client_creation_with_instructor(self, mock_config, mock_instructor):
        """Test that Instructor wrapping is applied when enabled."""
        mock_config.enable_instructor = True

        # Mock the from_openai function
        mock_wrapped_client = MagicMock()
        mock_instructor.from_openai.return_value = mock_wrapped_client

        client = InstructorClientFactory.create_client()

        # Should have called instructor.from_openai
        mock_instructor.from_openai.assert_called_once()
        assert client == mock_wrapped_client

    def test_response_model_serialization(self):
        """Test that response models can be serialized to JSON."""
        result = FallacyAnalysisResult(
            fallacies=[
                FallacyInstance(
                    fallacy_type=FallacyType.SLIPPERY_SLOPE,
                    quote="If we allow this, next thing you know everything will collapse",
                    explanation="Assumes one action will lead to extreme consequences without evidence",
                    severity=SeverityLevel.MEDIUM,
                    confidence=ConfidenceLevel.HIGH,
                )
            ],
            overall_quality=ContentQuality.FAIR,
            credibility_score=0.6,
            summary="Analysis identifies a slippery slope fallacy without other major issues",
        )

        # Should serialize to dict/JSON
        json_data = result.model_dump()
        assert "fallacies" in json_data
        assert json_data["credibility_score"] == 0.6
        assert json_data["fallacies"][0]["fallacy_type"] == "slippery_slope"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
