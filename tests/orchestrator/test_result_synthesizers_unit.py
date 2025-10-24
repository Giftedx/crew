"""Unit tests for result synthesis methods.

This module tests the synthesis methods in autonomous_orchestrator.py that will be
extracted to result_synthesizers.py as part of Phase 2 Week 5.

Test Coverage (16 tests for Day 1):
- Core synthesis methods (12 tests)
- Fallback synthesis (4 tests)

These tests validate the current behavior before extraction to ensure
zero regressions during the refactoring.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from ultimate_discord_intelligence_bot.step_result import StepResult


# ========================================
# FIXTURES
# ========================================


@pytest.fixture
def mock_logger():
    """Create mock logger."""
    return MagicMock()


@pytest.fixture
def mock_synthesizer():
    """Create mock MultiModalSynthesizer."""
    return MagicMock()


@pytest.fixture
def mock_error_handler():
    """Create mock CrewErrorHandler."""
    handler = MagicMock()
    handler.get_recovery_metrics = Mock(return_value={})
    return handler


@pytest.fixture
def orchestrator(mock_logger, mock_synthesizer, mock_error_handler):
    """Create mock AutonomousIntelligenceOrchestrator with necessary dependencies."""
    from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
        AutonomousIntelligenceOrchestrator,
    )

    # Create minimal orchestrator instance
    orchestrator = MagicMock(spec=AutonomousIntelligenceOrchestrator)
    orchestrator.logger = mock_logger
    orchestrator.synthesizer = mock_synthesizer
    orchestrator.error_handler = mock_error_handler

    # Import actual methods we want to test
    from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
        AutonomousIntelligenceOrchestrator as RealOrchestrator,
    )

    real_instance = RealOrchestrator.__new__(RealOrchestrator)
    real_instance.logger = mock_logger
    real_instance.synthesizer = mock_synthesizer
    real_instance.error_handler = mock_error_handler

    # Bind real methods to our mock
    orchestrator._synthesize_autonomous_results = real_instance._synthesize_autonomous_results.__get__(orchestrator)
    orchestrator._synthesize_enhanced_autonomous_results = (
        real_instance._synthesize_enhanced_autonomous_results.__get__(orchestrator)
    )
    orchestrator._synthesize_specialized_intelligence_results = (
        real_instance._synthesize_specialized_intelligence_results.__get__(orchestrator)
    )
    orchestrator._fallback_basic_synthesis = real_instance._fallback_basic_synthesis.__get__(orchestrator)

    return orchestrator


@pytest.fixture
def sample_complete_results() -> dict[str, Any]:
    """Sample complete results with all stages."""
    return {
        "pipeline": {
            "status": "success",
            "transcript": "Sample transcript content",
            "duration": 120,
        },
        "fact_analysis": {
            "verified_claims": 5,
            "false_claims": 1,
            "accuracy_score": 0.85,
        },
        "deception_score": {
            "deception_detected": False,
            "confidence": 0.92,
            "indicators": [],
        },
        "cross_platform_intel": {
            "key_themes": ["technology", "innovation"],
            "sentiment": "positive",
            "complexity": "medium",
        },
        "knowledge_integration": {
            "entities": ["AI", "Machine Learning"],
            "relationships": [{"from": "AI", "to": "Machine Learning", "type": "includes"}],
        },
    }


@pytest.fixture
def sample_partial_results() -> dict[str, Any]:
    """Sample partial results with some stages missing."""
    return {
        "pipeline": {
            "status": "success",
            "transcript": "Sample transcript",
        },
        "cross_platform_intel": {
            "key_themes": ["technology"],
            "sentiment": "neutral",
        },
    }


@pytest.fixture
def sample_crew_result() -> MagicMock:
    """Sample CrewAI result object."""
    result = MagicMock()
    result.raw = "Sample crew output"
    result.json_dict = {"confidence": 0.88, "quality": "high"}
    result.tasks_output = [
        MagicMock(raw="Task 1 output"),
        MagicMock(raw="Task 2 output"),
    ]
    return result


# ========================================
# CORE SYNTHESIS TESTS
# ========================================


class TestCoreSynthesisMethods:
    """Test core synthesis methods."""

    @pytest.mark.asyncio
    async def test_synthesize_autonomous_results_complete_data(self, orchestrator, sample_complete_results):
        """Test synthesis with all stages present."""
        # Mock the delegate methods
        orchestrator._calculate_summary_statistics = Mock(return_value={"total_claims": 6, "accuracy": 0.85})
        orchestrator._generate_autonomous_insights = Mock(
            return_value=[
                "High accuracy in fact checking",
                "No deception detected",
                "Positive sentiment analysis",
            ]
        )

        result = await orchestrator._synthesize_autonomous_results(sample_complete_results)

        # Verify structure matches actual implementation
        assert isinstance(result, dict)
        assert "autonomous_analysis_summary" in result
        assert "detailed_results" in result
        assert "workflow_metadata" in result

        # Verify delegate calls
        orchestrator._calculate_summary_statistics.assert_called_once()
        orchestrator._generate_autonomous_insights.assert_called_once()

    @pytest.mark.asyncio
    async def test_synthesize_autonomous_results_partial_data(self, orchestrator, sample_partial_results):
        """Test synthesis with some stages missing."""
        orchestrator._calculate_summary_statistics = Mock(return_value={})
        orchestrator._generate_autonomous_insights = Mock(return_value=[])

        result = await orchestrator._synthesize_autonomous_results(sample_partial_results)

        assert isinstance(result, dict)
        # Should still return structure even with partial data
        assert "autonomous_analysis_summary" in result or "detailed_results" in result

    @pytest.mark.asyncio
    async def test_synthesize_autonomous_results_empty_results(self, orchestrator):
        """Test synthesis with empty results."""
        orchestrator._calculate_summary_statistics = Mock(return_value={})
        orchestrator._generate_autonomous_insights = Mock(return_value=[])

        result = await orchestrator._synthesize_autonomous_results({})

        assert isinstance(result, dict)
        # Should gracefully handle empty input (no error raised)
        assert "autonomous_analysis_summary" in result or "error" in result

    @pytest.mark.asyncio
    async def test_synthesize_autonomous_results_error_handling(self, orchestrator):
        """Test error handling in synthesis."""
        # Make delegate raise exception
        orchestrator._calculate_summary_statistics = Mock(side_effect=ValueError("Invalid data"))
        orchestrator._generate_autonomous_insights = Mock(return_value=[])

        # Should not raise, should log error
        result = await orchestrator._synthesize_autonomous_results({"test": "data"})

        assert isinstance(result, dict)
        orchestrator.logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_synthesize_enhanced_autonomous_results_success(self, orchestrator, sample_complete_results):
        """Test successful enhanced synthesis."""
        # Mock synthesizer success - returns (StepResult, quality_assessment)
        synthesized_data = {
            "enhanced_summary": "Comprehensive analysis",
            "key_findings": ["Finding 1", "Finding 2"],
        }
        orchestrator.synthesizer.synthesize_intelligence_results = AsyncMock(
            return_value=(
                StepResult.ok(data=synthesized_data),
                {
                    "overall_quality": 0.92,
                    "completeness": 0.88,
                    "overall_grade": "high",
                },
            )
        )
        orchestrator.error_handler.get_recovery_metrics = Mock(return_value={"recovery_count": 0})

        result = await orchestrator._synthesize_enhanced_autonomous_results(sample_complete_results)

        # Should be StepResult with orchestrator_metadata
        assert isinstance(result, StepResult)
        assert result.success is True
        # The synthesized data gets merged into enhanced_result_data
        # Check for either top-level or nested under 'data' key
        assert "enhanced_summary" in result.data or (
            "data" in result.data and "enhanced_summary" in result.data["data"]
        )
        assert "orchestrator_metadata" in result.data
        assert result.data.get("production_ready") is True

        # Verify synthesizer was called
        orchestrator.synthesizer.synthesize_intelligence_results.assert_called_once()

    @pytest.mark.asyncio
    async def test_synthesize_enhanced_autonomous_results_fallback(self, orchestrator, sample_complete_results):
        """Test fallback to basic synthesis on failure."""
        # Mock synthesizer failure
        orchestrator.synthesizer.synthesize_intelligence_results = AsyncMock(side_effect=Exception("Synthesis failed"))
        # Mock fallback
        orchestrator._fallback_basic_synthesis = AsyncMock(
            return_value=StepResult.ok(
                data={"basic_summary": "Fallback synthesis"},
                step="fallback_synthesis",
            )
        )

        result = await orchestrator._synthesize_enhanced_autonomous_results(sample_complete_results)

        # Should fallback
        assert isinstance(result, StepResult)
        orchestrator._fallback_basic_synthesis.assert_called_once()
        orchestrator.logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_synthesize_enhanced_autonomous_results_quality_assessment(
        self, orchestrator, sample_complete_results
    ):
        """Test quality assessment integration."""
        quality_assessment = {
            "overall_quality": 0.95,
            "completeness": 0.90,
            "overall_grade": "excellent",
        }
        orchestrator.synthesizer.synthesize_intelligence_results = AsyncMock(
            return_value=(
                StepResult.ok(data={"enhanced_summary": "High quality analysis"}),
                quality_assessment,
            )
        )
        orchestrator.error_handler.get_recovery_metrics = Mock(return_value={})

        result = await orchestrator._synthesize_enhanced_autonomous_results(sample_complete_results)

        assert isinstance(result, StepResult)
        assert result.success is True
        # Quality assessment should be in orchestrator_metadata
        assert "orchestrator_metadata" in result.data
        metadata = result.data["orchestrator_metadata"]
        assert "synthesis_quality" in metadata or "quality_assurance" in metadata

    @pytest.mark.asyncio
    async def test_synthesize_enhanced_autonomous_results_message_conflict(self, orchestrator, sample_complete_results):
        """Test message conflict handling (duplicate 'message' key)."""
        # Synthesizer returns result with 'message' key
        orchestrator.synthesizer.synthesize_intelligence_results = AsyncMock(
            return_value=(
                {
                    "message": "Synthesizer message",
                    "summary": "Test summary",
                },
                {"overall_quality": 0.85},
            )
        )
        orchestrator.error_handler.get_recovery_metrics = Mock(return_value={})

        result = await orchestrator._synthesize_enhanced_autonomous_results(sample_complete_results)

        # Should handle message key conflict gracefully
        assert isinstance(result, StepResult)
        assert result.success is True
        # Should not have duplicate 'message' keys causing errors

    @pytest.mark.asyncio
    async def test_synthesize_specialized_intelligence_results_complete(self, orchestrator, sample_complete_results):
        """Test specialized synthesis with complete results."""
        orchestrator._generate_specialized_insights = Mock(
            return_value=[
                "Specialized insight 1",
                "Specialized insight 2",
                "Specialized insight 3",
            ]
        )

        result = await orchestrator._synthesize_specialized_intelligence_results(sample_complete_results)

        assert isinstance(result, dict)
        assert "specialized_analysis_summary" in result
        assert "detailed_results" in result
        assert "workflow_metadata" in result
        orchestrator._generate_specialized_insights.assert_called_once()

    @pytest.mark.asyncio
    async def test_synthesize_specialized_intelligence_results_partial(self, orchestrator, sample_partial_results):
        """Test specialized synthesis with partial results."""
        orchestrator._generate_specialized_insights = Mock(return_value=["Limited insight"])

        result = await orchestrator._synthesize_specialized_intelligence_results(sample_partial_results)

        assert isinstance(result, dict)
        # Should handle partial data gracefully, still has required keys
        assert "specialized_analysis_summary" in result or "detailed_results" in result

    @pytest.mark.asyncio
    async def test_synthesize_specialized_intelligence_results_insights_generation(
        self, orchestrator, sample_complete_results
    ):
        """Test specialized insights generation."""
        expected_insights = [
            "Advanced pattern detected",
            "Cross-reference validated",
            "Expert analysis complete",
        ]
        orchestrator._generate_specialized_insights = Mock(return_value=expected_insights)

        result = await orchestrator._synthesize_specialized_intelligence_results(sample_complete_results)

        assert isinstance(result, dict)
        # Verify insights were integrated (now includes logger parameter)
        orchestrator._generate_specialized_insights.assert_called_once_with(
            sample_complete_results, orchestrator.logger
        )

    @pytest.mark.asyncio
    async def test_synthesize_specialized_intelligence_results_error_handling(self, orchestrator):
        """Test error handling in specialized synthesis."""
        orchestrator._generate_specialized_insights = Mock(side_effect=RuntimeError("Insight generation failed"))

        result = await orchestrator._synthesize_specialized_intelligence_results({})

        assert isinstance(result, dict)
        orchestrator.logger.error.assert_called()


# ========================================
# FALLBACK SYNTHESIS TESTS
# ========================================


class TestFallbackSynthesis:
    """Test fallback synthesis methods."""

    @pytest.mark.asyncio
    async def test_fallback_basic_synthesis_valid_results(self, orchestrator, sample_complete_results):
        """Test basic synthesis with valid results."""
        result = await orchestrator._fallback_basic_synthesis(sample_complete_results, "Synthesizer unavailable")

        assert isinstance(result, StepResult)
        assert result.success is True
        # CRITICAL: fallback must have production_ready=False
        assert result.data.get("production_ready") is False
        assert result.data.get("fallback_synthesis") is True
        assert result.data.get("quality_grade") == "limited"
        # Should include fallback_reason
        assert result.data.get("fallback_reason") == "Synthesizer unavailable"

    @pytest.mark.asyncio
    async def test_fallback_basic_synthesis_minimal_results(self, orchestrator):
        """Test basic synthesis with minimal results."""
        minimal_results = {"pipeline": {"status": "success"}}

        result = await orchestrator._fallback_basic_synthesis(minimal_results, "Partial failure")

        assert isinstance(result, StepResult)
        assert result.success is True
        # CRITICAL: fallback always has production_ready=False
        assert result.data.get("production_ready") is False

    @pytest.mark.asyncio
    async def test_fallback_basic_synthesis_error_context(self, orchestrator, sample_complete_results):
        """Test error context inclusion."""
        error_msg = "Advanced synthesis timed out after 30s"

        result = await orchestrator._fallback_basic_synthesis(sample_complete_results, error_msg)

        assert isinstance(result, StepResult)
        # Error context should be in fallback_reason or message
        assert result.data.get("fallback_reason") == error_msg or error_msg in result.data.get("message", "")

    @pytest.mark.asyncio
    async def test_fallback_basic_synthesis_production_ready_flag(self, orchestrator, sample_complete_results):
        """Test production_ready flag (CRITICAL: should always be False)."""
        result = await orchestrator._fallback_basic_synthesis(sample_complete_results, "Fallback triggered")

        assert isinstance(result, StepResult)
        # CRITICAL: Fallback results are NEVER production-ready
        assert result.data.get("production_ready") is False
        assert result.data.get("fallback_synthesis") is True
        assert result.data.get("requires_manual_review") is True


# Placeholder for remaining test classes (to be implemented in next iteration)
class TestInsightGeneration:
    """Test insight generation methods."""


class TestConfidenceCalculation:
    """Test confidence calculation methods."""


class TestSpecializedExecution:
    """Test specialized execution methods."""
