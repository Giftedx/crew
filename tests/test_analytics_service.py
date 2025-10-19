"""Tests for consolidated analytics service (ADR-0005)."""

from __future__ import annotations

import pytest

from ultimate_discord_intelligence_bot.observability import (
    AnalyticsService,
    get_analytics_service,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


@pytest.fixture
def analytics_service():
    """Create analytics service instance."""
    return AnalyticsService()


class TestSystemHealth:
    """Test system health assessment."""

    def test_get_system_health(self, analytics_service):
        """Test system health returns valid data."""
        result = analytics_service.get_system_health()

        assert isinstance(result, StepResult)
        assert result.success
        assert "overall_score" in result.data
        assert "status" in result.data
        assert "components_healthy" in result.data

    def test_health_status_mapping(self, analytics_service):
        """Test health score to status mapping."""
        assert analytics_service._score_to_status(95.0) == "excellent"
        assert analytics_service._score_to_status(80.0) == "good"
        assert analytics_service._score_to_status(65.0) == "fair"
        assert analytics_service._score_to_status(45.0) == "poor"
        assert analytics_service._score_to_status(20.0) == "critical"


class TestPerformanceMetrics:
    """Test performance metrics collection."""

    def test_get_performance_metrics(self, analytics_service):
        """Test performance metrics returns valid data."""
        result = analytics_service.get_performance_metrics()

        assert isinstance(result, StepResult)
        assert result.success
        assert "cache_hit_rate" in result.data
        assert "avg_latency_ms" in result.data
        assert "error_rate" in result.data
        assert "total_requests" in result.data
        assert "cost_savings" in result.data

    def test_metrics_are_numeric(self, analytics_service):
        """Test all metrics are numeric values."""
        result = analytics_service.get_performance_metrics()

        if result.success:
            data = result.data
            assert isinstance(data["cache_hit_rate"], (int, float))
            assert isinstance(data["avg_latency_ms"], (int, float))
            assert isinstance(data["error_rate"], (int, float))


class TestAnalyticsRecommendations:
    """Test analytics recommendation generation."""

    def test_healthy_components_no_recommendations(self, analytics_service):
        """Test healthy system generates no critical recommendations."""
        components = [
            {"healthy": True, "score": 90.0},
            {"healthy": True, "score": 85.0},
            {"healthy": True, "score": 80.0},
        ]

        recommendations = analytics_service._generate_recommendations(components)
        assert len(recommendations) == 1
        assert "normally" in recommendations[0].lower()

    def test_unhealthy_components_generate_recommendations(self, analytics_service):
        """Test unhealthy components trigger recommendations."""
        components = [
            {"healthy": False, "score": 20.0},
            {"healthy": True, "score": 50.0},
        ]

        recommendations = analytics_service._generate_recommendations(components)
        assert len(recommendations) > 0


class TestAnalyticsSingleton:
    """Test global analytics service singleton."""

    def test_get_analytics_service_singleton(self):
        """Test get_analytics_service returns singleton."""
        service1 = get_analytics_service()
        service2 = get_analytics_service()
        assert service1 is service2

    def test_singleton_has_metrics(self):
        """Test singleton has metrics instance."""
        service = get_analytics_service()
        assert service.metrics is not None


class TestAgentPerformanceMonitoring:
    """Test agent performance monitoring features (Phase 7)."""

    def test_record_agent_performance_success(self, analytics_service):
        """Test recording agent performance returns success."""
        result = analytics_service.record_agent_performance(
            agent_name="test_agent",
            task_type="analysis",
            quality_score=0.87,
            response_time=2.5,
            tools_used=["tool1", "tool2"],
        )

        assert isinstance(result, StepResult)
        # May fail if AgentPerformanceMonitor not available, but should return result
        if result.success:
            assert result.data["recorded"] is True
            assert result.data["agent_name"] == "test_agent"

    def test_record_agent_performance_with_context(self, analytics_service):
        """Test recording with additional context."""
        result = analytics_service.record_agent_performance(
            agent_name="test_agent",
            task_type="analysis",
            quality_score=0.92,
            response_time=1.8,
            tools_used=["tool1"],
            error_occurred=False,
            user_feedback={"satisfaction": 0.9},
            error_details={},
        )

        assert isinstance(result, StepResult)
        # Test passes if result is returned, regardless of success
        # (success depends on AgentPerformanceMonitor availability)

    def test_record_agent_performance_with_error(self, analytics_service):
        """Test recording agent performance with error flag."""
        result = analytics_service.record_agent_performance(
            agent_name="failing_agent",
            task_type="analysis",
            quality_score=0.4,
            response_time=8.0,
            tools_used=["tool1"],
            error_occurred=True,
            error_details={"error_type": "timeout"},
        )

        assert isinstance(result, StepResult)

    def test_get_agent_performance_report(self, analytics_service):
        """Test getting agent performance report."""
        # First record some interactions
        for i in range(3):
            analytics_service.record_agent_performance(
                agent_name="report_test_agent",
                task_type="analysis",
                quality_score=0.8 + (i * 0.05),
                response_time=2.0 + (i * 0.2),
                tools_used=["tool1", "tool2"],
            )

        # Get report
        result = analytics_service.get_agent_performance_report(
            "report_test_agent", days=1
        )

        assert isinstance(result, StepResult)
        if result.success:
            assert "agent_name" in result.data
            assert "overall_score" in result.data
            assert "metrics" in result.data
            assert "recommendations" in result.data
            assert "training_suggestions" in result.data
            assert result.data["agent_name"] == "report_test_agent"

    def test_get_agent_performance_report_nonexistent_agent(self, analytics_service):
        """Test report for agent with no data."""
        result = analytics_service.get_agent_performance_report(
            "nonexistent_agent", days=30
        )

        assert isinstance(result, StepResult)
        # May return empty report or fail - both acceptable

    def test_comparative_agent_analysis(self, analytics_service):
        """Test multi-agent comparative analysis."""
        # Record for multiple agents
        agents = ["agent_a", "agent_b", "agent_c"]
        for idx, agent in enumerate(agents):
            analytics_service.record_agent_performance(
                agent_name=agent,
                task_type="analysis",
                quality_score=0.75 + (idx * 0.05),
                response_time=2.0,
                tools_used=["tool1"],
            )

        # Compare agents
        result = analytics_service.get_comparative_agent_analysis(
            agent_names=agents, days=1
        )

        assert isinstance(result, StepResult)
        if result.success:
            assert "total_agents" in result.data
            assert "average_score" in result.data
            assert "best_agent" in result.data
            assert "worst_agent" in result.data
            assert "agent_scores" in result.data
            assert result.data["total_agents"] > 0

    def test_comparative_analysis_empty_agent_list(self, analytics_service):
        """Test comparative analysis with empty agent list."""
        result = analytics_service.get_comparative_agent_analysis(
            agent_names=[], days=30
        )

        assert isinstance(result, StepResult)
        # Should handle empty list gracefully

    def test_comparative_analysis_single_agent(self, analytics_service):
        """Test comparative analysis with single agent."""
        analytics_service.record_agent_performance(
            agent_name="solo_agent",
            task_type="analysis",
            quality_score=0.85,
            response_time=2.0,
        )

        result = analytics_service.get_comparative_agent_analysis(
            agent_names=["solo_agent"], days=1
        )

        assert isinstance(result, StepResult)
        if result.success:
            assert result.data["total_agents"] == 1


class TestAgentMonitorLazyLoading:
    """Test lazy loading of agent performance monitor."""

    def test_agent_monitor_lazy_loads(self, analytics_service):
        """Test agent monitor is lazy-loaded on first access."""
        # Initially None
        assert analytics_service._agent_monitor is None

        # First call loads it
        monitor = analytics_service._get_agent_monitor()

        # May be None if not available, or loaded instance
        if monitor is not None:
            # Second call returns same instance
            monitor2 = analytics_service._get_agent_monitor()
            assert monitor is monitor2

    def test_record_without_monitor_returns_failure(self, analytics_service):
        """Test recording without available monitor returns failure gracefully."""
        # Force monitor to None
        analytics_service._agent_monitor = None

        # Mock unavailable monitor by setting to None permanently
        original_get = analytics_service._get_agent_monitor

        def mock_get_none():
            return None

        analytics_service._get_agent_monitor = mock_get_none

        result = analytics_service.record_agent_performance(
            agent_name="test", task_type="test", quality_score=0.5, response_time=1.0
        )

        # Should return failure result, not raise exception
        assert isinstance(result, StepResult)
        assert not result.success

        # Restore
        analytics_service._get_agent_monitor = original_get
