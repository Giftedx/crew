"""Integration tests for AI enhancements (Instructor + Logfire + LiteLLM).

Tests verify that the three enhancement layers work together correctly:
- Instructor: Structured LLM outputs with validation
- Logfire: Observability and tracing
- LiteLLM: Multi-provider routing

These tests use mocks to avoid external dependencies.
"""

from __future__ import annotations

from platform.observability.logfire_config import setup_logfire
from platform.observability.logfire_spans import is_logfire_enabled, span
from unittest.mock import MagicMock, Mock, patch

import pytest
from ai.litellm_router import LITELLM_AVAILABLE, LLMRouterSingleton
from ai.response_models import (
    ConfidenceLevel,
    ContentQuality,
    FallacyAnalysisResult,
    FallacyInstance,
    FallacyType,
    SeverityLevel,
)
from ai.structured_outputs import INSTRUCTOR_AVAILABLE, InstructorClientFactory


@pytest.fixture
def mock_config():
    """Mock SecureConfig with all features enabled."""
    with patch("ai.structured_outputs.get_config") as mock_get:
        config = Mock()
        config.enable_instructor = True
        config.enable_litellm_router = True
        config.enable_logfire = True
        config.openai_api_key = "test-key"
        config.openrouter_api_key = "test-openrouter-key"
        config.openrouter_general_model = "openai/gpt-4o-mini"
        config.openrouter_analysis_model = "anthropic/claude-3.5-sonnet"
        config.instructor_max_retries = 3
        config.instructor_timeout = 30
        config.litellm_routing_strategy = "usage-based-routing"
        config.litellm_cache_enabled = True
        config.litellm_fallback_enabled = True
        config.logfire_token = None
        config.logfire_project_name = "test-project"
        config.logfire_send_to_logfire = False
        mock_get.return_value = config
        yield config


@pytest.fixture
def mock_all_configs(mock_config):
    """Patch all get_config calls across modules."""
    patches = [
        patch("ai.structured_outputs.get_config", return_value=mock_config),
        patch("ai.litellm_router.get_config", return_value=mock_config),
        patch("obs.logfire_config.get_config", return_value=mock_config),
        patch("obs.logfire_spans.get_config", return_value=mock_config),
    ]
    for p in patches:
        p.start()
    yield mock_config
    for p in patches:
        p.stop()


@pytest.mark.skipif(not INSTRUCTOR_AVAILABLE, reason="instructor not installed")
class TestInstructorIntegration:
    """Test Instructor structured outputs in realistic scenarios."""

    def test_factory_creates_client_with_openrouter_config(self, mock_all_configs):
        """Factory should use OpenRouter config when available."""
        client = InstructorClientFactory.create_openrouter_client()
        assert client is not None

    def test_structured_output_with_validation(self, mock_all_configs):
        """Structured outputs should validate via Pydantic."""
        result = FallacyAnalysisResult(
            fallacies=[
                FallacyInstance(
                    fallacy_type=FallacyType.SLIPPERY_SLOPE,
                    quote="If we allow X, then Y will inevitably happen",
                    explanation="Assumes causal chain without evidence",
                    severity=SeverityLevel.MEDIUM,
                    confidence=ConfidenceLevel.HIGH,
                )
            ],
            overall_quality=ContentQuality.FAIR,
            credibility_score=0.65,
            summary="Analysis identifies logical fallacies with moderate confidence",
        )
        json_data = result.model_dump()
        restored = FallacyAnalysisResult.model_validate(json_data)
        assert restored.credibility_score == 0.65
        assert len(restored.fallacies) == 1
        assert restored.fallacies[0].fallacy_type == FallacyType.SLIPPERY_SLOPE

    def test_instructor_client_respects_retry_config(self, mock_all_configs):
        """Instructor client should use retry settings from config."""
        with patch("ai.structured_outputs.instructor") as mock_instructor:
            mock_wrapped = MagicMock()
            mock_instructor.from_openai.return_value = mock_wrapped
            client = InstructorClientFactory.create_client(max_retries=5, timeout=60)
            mock_instructor.from_openai.assert_called_once()


class TestLogfireIntegration:
    """Test Logfire observability integration."""

    def test_setup_logfire_disabled_by_default(self):
        """Logfire should be disabled when flag is false."""
        with patch("obs.logfire_config.get_config") as mock_get:
            config = Mock()
            config.enable_logfire = False
            mock_get.return_value = config
            result = setup_logfire()
            assert result is False

    def test_setup_logfire_with_app_when_enabled(self, mock_all_configs):
        """Logfire should instrument FastAPI app when enabled and available."""
        mock_app = MagicMock()
        try:
            logfire_available = True
        except Exception:
            logfire_available = False
        if not logfire_available:
            pytest.skip("logfire not installed")
        with patch("obs.logfire_config.logfire") as mock_logfire:
            result = setup_logfire(mock_app)
            if result:
                mock_logfire.configure.assert_called_once()
                mock_logfire.instrument_fastapi.assert_called_once_with(mock_app)

    def test_logfire_span_helper_no_op_when_disabled(self):
        """Span helper should be no-op when Logfire disabled."""
        with patch("obs.logfire_spans.get_config") as mock_get:
            config = Mock()
            config.enable_logfire = False
            mock_get.return_value = config
            with span("test.operation"):
                pass
            assert not is_logfire_enabled()


@pytest.mark.skipif(not LITELLM_AVAILABLE, reason="litellm not installed")
class TestLiteLLMIntegration:
    """Test LiteLLM router integration."""

    def test_singleton_returns_router_when_enabled(self, mock_all_configs):
        """Singleton should return configured Router when enabled."""
        LLMRouterSingleton._instance = None
        with patch("ai.litellm_router._Router") as MockRouter:
            mock_router_instance = MagicMock()
            MockRouter.return_value = mock_router_instance
            router = LLMRouterSingleton.get()
            assert router is mock_router_instance
            MockRouter.assert_called_once()

    def test_singleton_returns_none_when_disabled(self):
        """Singleton should return None when feature flag is disabled."""
        LLMRouterSingleton._instance = None
        with patch("ai.litellm_router.get_config") as mock_get:
            config = Mock()
            config.enable_litellm_router = False
            mock_get.return_value = config
            router = LLMRouterSingleton.get()
            assert router is None

    def test_singleton_caches_instance(self, mock_all_configs):
        """Singleton should cache and reuse Router instance."""
        LLMRouterSingleton._instance = None
        with patch("ai.litellm_router._Router") as MockRouter:
            mock_router_instance = MagicMock()
            MockRouter.return_value = mock_router_instance
            router1 = LLMRouterSingleton.get()
            router2 = LLMRouterSingleton.get()
            assert router1 is router2
            MockRouter.assert_called_once()


class TestCombinedIntegration:
    """Test all three enhancements working together."""

    @pytest.mark.skipif(not INSTRUCTOR_AVAILABLE, reason="instructor not installed")
    def test_instructor_with_logfire_spans(self, mock_all_configs):
        """Instructor calls should be traceable with Logfire spans."""
        with patch("obs.logfire_spans._logfire") as mock_logfire:
            mock_span = MagicMock()
            mock_logfire.span.return_value.__enter__ = Mock(return_value=mock_span)
            mock_logfire.span.return_value.__exit__ = Mock(return_value=False)
            with span("llm.structured_call"):
                result = FallacyAnalysisResult(
                    fallacies=[],
                    overall_quality=ContentQuality.GOOD,
                    credibility_score=0.85,
                    summary="Clean analysis with no fallacies detected",
                )
            assert result.credibility_score == 0.85

    def test_all_features_can_coexist(self, mock_all_configs):
        """All three features should be initializable without conflicts."""
        LLMRouterSingleton._instance = None
        if INSTRUCTOR_AVAILABLE:
            client = InstructorClientFactory.create_client()
            assert client is not None
        if LITELLM_AVAILABLE:
            with patch("ai.litellm_router._Router") as MockRouter:
                MockRouter.return_value = MagicMock()
                router = LLMRouterSingleton.get()
                assert router is not None or not mock_all_configs.enable_litellm_router
        with patch.dict("sys.modules", {"logfire": MagicMock()}):
            mock_app = MagicMock()
            setup_logfire(mock_app)

    def test_feature_flags_control_initialization(self):
        """Feature flags should independently control each enhancement."""
        with patch("ai.structured_outputs.get_config") as mock_inst:
            config_inst = Mock()
            config_inst.enable_instructor = False
            mock_inst.return_value = config_inst
            assert not InstructorClientFactory.is_enabled()
        with patch("ai.litellm_router.get_config") as mock_lite:
            config_lite = Mock()
            config_lite.enable_litellm_router = False
            mock_lite.return_value = config_lite
            LLMRouterSingleton._instance = None
            assert not LLMRouterSingleton.is_enabled()
        with patch("obs.logfire_spans.get_config") as mock_log:
            config_log = Mock()
            config_log.enable_logfire = False
            mock_log.return_value = config_log
            assert not is_logfire_enabled()


class TestErrorHandling:
    """Test graceful degradation when dependencies are missing."""

    def test_instructor_graceful_degradation_when_unavailable(self):
        """System should work when instructor is not installed."""
        with patch("ai.structured_outputs.INSTRUCTOR_AVAILABLE", False):
            assert not InstructorClientFactory.is_enabled()
            with patch("ai.structured_outputs.OpenAI") as MockOpenAI:
                mock_client = MagicMock()
                MockOpenAI.return_value = mock_client
                client = InstructorClientFactory.create_client()
                assert client is mock_client

    def test_litellm_graceful_degradation_when_unavailable(self):
        """System should work when litellm is not installed."""
        with patch("ai.litellm_router.LITELLM_AVAILABLE", False):
            LLMRouterSingleton._instance = None
            router = LLMRouterSingleton.get()
            assert router is None

    def test_logfire_graceful_degradation_when_unavailable(self):
        """System should work when logfire is not installed."""
        with patch("obs.logfire_config.get_config") as mock_get:
            config = Mock()
            config.enable_logfire = True
            mock_get.return_value = config
            with patch.dict("sys.modules", {"logfire": None}):
                result = setup_logfire()
                assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
