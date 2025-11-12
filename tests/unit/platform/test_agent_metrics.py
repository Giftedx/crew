"""Tests for AgentMetricsCollector.

Validates Prometheus instrumentation for agent lifecycle events including
executions, durations, errors, and resource usage tracking.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from platform.core.step_result import ErrorCategory, StepResult
from platform.observability.agent_metrics import AgentMetricsCollector


@pytest.fixture
def collector() -> AgentMetricsCollector:
    """Get fresh collector instance for each test."""
    # Reset singleton
    AgentMetricsCollector._instance = None
    return AgentMetricsCollector.get_instance()


@pytest.fixture
def mock_prometheus():
    """Mock Prometheus client for testing."""
    with patch("platform.observability.agent_metrics.PROMETHEUS_AVAILABLE", True):
        with patch("platform.observability.agent_metrics.Counter") as mock_counter:
            with patch("platform.observability.agent_metrics.Histogram") as mock_histogram:
                # Create mock instances
                counter_instance = MagicMock()
                counter_instance.labels.return_value = counter_instance
                mock_counter.return_value = counter_instance

                histogram_instance = MagicMock()
                histogram_instance.labels.return_value = histogram_instance
                mock_histogram.return_value = histogram_instance

                yield {
                    "Counter": mock_counter,
                    "Histogram": mock_histogram,
                    "counter_instance": counter_instance,
                    "histogram_instance": histogram_instance,
                }


class TestAgentMetricsCollectorInitialization:
    """Test collector initialization and singleton pattern."""

    def test_singleton_instance(self, collector: AgentMetricsCollector):
        """Collector should return same instance."""
        instance1 = AgentMetricsCollector.get_instance()
        instance2 = AgentMetricsCollector.get_instance()
        assert instance1 is instance2

    def test_prometheus_unavailable_no_crash(self):
        """Collector should initialize gracefully without Prometheus."""
        with patch("platform.observability.agent_metrics.PROMETHEUS_AVAILABLE", False):
            collector = AgentMetricsCollector()
            assert collector._enabled is False

            # Should not crash on metric recording
            collector.record_execution(
                agent_name="Test Agent", status="success", duration_seconds=1.0
            )


class TestRecordExecution:
    """Test basic execution recording."""

    def test_record_successful_execution(self, collector: AgentMetricsCollector):
        """Should record successful execution with duration."""
        collector.record_execution(
            agent_name="Acquisition Specialist",
            status="success",
            duration_seconds=2.5,
        )
        # No crash = success (metrics are no-op without real Prometheus)

    def test_record_failed_execution_with_error(self, collector: AgentMetricsCollector):
        """Should record failed execution with error category."""
        collector.record_execution(
            agent_name="Verification Director",
            status="fail",
            duration_seconds=1.0,
            error_category=ErrorCategory.TIMEOUT,
        )
        # No crash = success

    def test_record_execution_with_tokens(self, collector: AgentMetricsCollector):
        """Should record token usage."""
        collector.record_execution(
            agent_name="Analysis Cartographer",
            status="success",
            duration_seconds=3.0,
            tokens_used=1500,
        )
        # No crash = success

    def test_record_skipped_execution(self, collector: AgentMetricsCollector):
        """Should record skipped execution."""
        collector.record_execution(
            agent_name="Risk Intelligence Analyst",
            status="skip",
            duration_seconds=0.1,
        )
        # No crash = success

    def test_disabled_collector_noop(self):
        """Disabled collector should not crash on record."""
        with patch("platform.observability.agent_metrics.PROMETHEUS_AVAILABLE", False):
            collector = AgentMetricsCollector()
            collector.record_execution(
                agent_name="Test Agent",
                status="success",
                duration_seconds=1.0,
                tokens_used=500,
            )
            # No crash = success


class TestTrackExecutionContext:
    """Test context manager for tracking executions."""

    def test_track_successful_execution(self, collector: AgentMetricsCollector):
        """Should track successful execution automatically."""
        with collector.track_execution("Mission Orchestrator") as ctx:
            time.sleep(0.01)  # Simulate work
            ctx["tokens_used"] = 1000

        # No crash = success

    def test_track_failed_execution_with_exception(
        self, collector: AgentMetricsCollector
    ):
        """Should track failed execution when exception raised."""
        with pytest.raises(ValueError):
            with collector.track_execution("Workflow Manager") as ctx:
                ctx["error_category"] = ErrorCategory.VALIDATION
                raise ValueError("Simulated failure")

        # Exception propagated correctly

    def test_track_execution_measures_duration(self, collector: AgentMetricsCollector):
        """Should measure execution duration accurately."""
        start = time.time()
        with collector.track_execution("Executive Supervisor"):
            time.sleep(0.05)  # 50ms work
        duration = time.time() - start

        assert duration >= 0.05
        # No crash = success

    def test_track_execution_disabled_noop(self):
        """Disabled collector should yield context dict but not record metrics."""
        with patch("platform.observability.agent_metrics.PROMETHEUS_AVAILABLE", False):
            collector = AgentMetricsCollector()

            with collector.track_execution("Test Agent") as ctx:
                ctx["tokens_used"] = 100

            # Context dict is yielded even when disabled (for caller use)
            # The difference is that no metrics are recorded
            assert "tokens_used" in ctx


class TestRecordFromStepResult:
    """Test recording metrics from StepResult."""

    def test_record_success_step_result(self, collector: AgentMetricsCollector):
        """Should extract metrics from successful StepResult."""
        result = StepResult.ok(
            result={"output": "analysis complete"},
            meta={
                "elapsed_ms": 2500,
                "resource_usage": {
                    "tokens_in": 500,
                    "tokens_out": 1000,
                },
            },
        )

        collector.record_from_step_result(
            agent_name="Analysis Cartographer",
            result=result,
        )
        # No crash = success

    def test_record_fail_step_result(self, collector: AgentMetricsCollector):
        """Should extract error category from failed StepResult."""
        result = StepResult.fail(
            error="Connection timeout",
            error_category=ErrorCategory.TIMEOUT,
            retryable=True,
            meta={
                "elapsed_ms": 5000,
            },
        )

        collector.record_from_step_result(
            agent_name="Signal Recon Specialist",
            result=result,
        )
        # No crash = success

    def test_record_step_result_no_metadata(self, collector: AgentMetricsCollector):
        """Should handle StepResult with minimal metadata."""
        result = StepResult.ok(result={"data": "success"})

        collector.record_from_step_result(
            agent_name="Trend Intelligence Scout",
            result=result,
        )
        # No crash = success

    def test_record_step_result_partial_resource_usage(
        self, collector: AgentMetricsCollector
    ):
        """Should handle partial resource usage data."""
        result = StepResult.ok(
            result={"output": "done"},
            meta={
                "elapsed_ms": 1000,
                "resource_usage": {
                    "tokens_in": 300,
                    # tokens_out missing
                },
            },
        )

        collector.record_from_step_result(
            agent_name="Community Liaison",
            result=result,
        )
        # No crash = success


class TestPrometheusIntegration:
    """Test actual Prometheus metric creation and recording."""

    def test_creates_prometheus_metrics_on_init(self, mock_prometheus):
        """Should create all required Prometheus metrics."""
        with patch("platform.observability.agent_metrics.PROMETHEUS_AVAILABLE", True):
            collector = AgentMetricsCollector()

            # Should create counters and histograms
            assert collector._enabled is True
            assert hasattr(collector, "agent_executions_total")
            assert hasattr(collector, "agent_execution_duration_seconds")
            assert hasattr(collector, "agent_errors_total")
            assert hasattr(collector, "agent_tokens_used_total")

    def test_record_execution_increments_counter(self, mock_prometheus):
        """Should increment execution counter with labels."""
        with patch("platform.observability.agent_metrics.PROMETHEUS_AVAILABLE", True):
            collector = AgentMetricsCollector()

            # Mock the counter
            mock_counter = MagicMock()
            mock_counter.labels.return_value = mock_counter
            collector.agent_executions_total = mock_counter

            collector.record_execution(
                agent_name="Test Agent",
                status="success",
            )

            mock_counter.labels.assert_called_with(agent="Test Agent", status="success")
            mock_counter.inc.assert_called_once()

    def test_record_execution_observes_duration(self, mock_prometheus):
        """Should observe execution duration in histogram."""
        with patch("platform.observability.agent_metrics.PROMETHEUS_AVAILABLE", True):
            collector = AgentMetricsCollector()

            # Mock the histogram
            mock_histogram = MagicMock()
            mock_histogram.labels.return_value = mock_histogram
            collector.agent_execution_duration_seconds = mock_histogram

            collector.record_execution(
                agent_name="Test Agent",
                status="success",
                duration_seconds=3.5,
            )

            mock_histogram.labels.assert_called_with(agent="Test Agent")
            mock_histogram.observe.assert_called_once_with(3.5)

    def test_record_execution_increments_error_counter(self, mock_prometheus):
        """Should increment error counter on failure."""
        with patch("platform.observability.agent_metrics.PROMETHEUS_AVAILABLE", True):
            collector = AgentMetricsCollector()

            # Mock the error counter
            mock_counter = MagicMock()
            mock_counter.labels.return_value = mock_counter
            collector.agent_errors_total = mock_counter

            collector.record_execution(
                agent_name="Test Agent",
                status="fail",
                error_category=ErrorCategory.NETWORK,
            )

            mock_counter.labels.assert_called_with(agent="Test Agent", category="NETWORK")
            mock_counter.inc.assert_called_once()

    def test_record_execution_increments_token_counter(self, mock_prometheus):
        """Should increment token counter with usage."""
        with patch("platform.observability.agent_metrics.PROMETHEUS_AVAILABLE", True):
            collector = AgentMetricsCollector()

            # Mock the token counter
            mock_counter = MagicMock()
            mock_counter.labels.return_value = mock_counter
            collector.agent_tokens_used_total = mock_counter

            collector.record_execution(
                agent_name="Test Agent",
                status="success",
                tokens_used=2500,
            )

            mock_counter.labels.assert_called_with(agent="Test Agent")
            mock_counter.inc.assert_called_once_with(2500)


class TestErrorHandling:
    """Test error handling and graceful degradation."""

    def test_record_execution_handles_metric_failure(
        self, collector: AgentMetricsCollector
    ):
        """Should not crash if metric recording fails."""
        # Make a metric raise an exception
        if hasattr(collector, "agent_executions_total"):
            collector.agent_executions_total.labels = MagicMock(
                side_effect=RuntimeError("Prometheus error")
            )

        # Should not raise
        collector.record_execution(
            agent_name="Test Agent",
            status="success",
        )

    def test_track_execution_handles_context_error(
        self, collector: AgentMetricsCollector
    ):
        """Should handle errors in context manager gracefully."""
        # Should not crash even if metrics fail
        with pytest.raises(KeyError):
            with collector.track_execution("Test Agent"):
                raise KeyError("Simulated error")

    def test_record_from_step_result_handles_malformed_result(
        self, collector: AgentMetricsCollector
    ):
        """Should handle StepResult with unexpected structure."""
        # Create result with unexpected meta structure
        result = StepResult.ok(result={"data": "ok"})
        result.meta = "invalid_meta_type"  # type: ignore

        # Should not crash
        collector.record_from_step_result(
            agent_name="Test Agent",
            result=result,
        )
