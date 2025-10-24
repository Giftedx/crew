"""Tests for crew analytics system."""

import time

from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags
from ultimate_discord_intelligence_bot.features.crew_analytics import (
    CrewAnalytics,
    CrewComparison,
    CrewExecution,
    CrewMetrics,
    CrewType,
    ExecutionStatus,
)


class TestCrewAnalytics:
    """Test suite for CrewAnalytics system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.feature_flags = FeatureFlags()
        self.feature_flags.ENABLE_CREW_ANALYTICS = True
        self.analytics = CrewAnalytics(self.feature_flags)

    def test_initialization(self):
        """Test analytics system initialization."""
        assert self.analytics.feature_flags == self.feature_flags
        assert self.analytics.is_enabled() is True
        assert len(self.analytics.executions) == 0
        assert len(self.analytics.metrics) == len(CrewType)
        assert len(self.analytics.comparisons) == 0

    def test_disabled_analytics(self):
        """Test behavior when analytics is disabled."""
        self.feature_flags.ENABLE_CREW_ANALYTICS = False
        analytics = CrewAnalytics(self.feature_flags)

        assert analytics.is_enabled() is False

    def test_start_execution(self):
        """Test starting execution tracking."""
        execution_id = self.analytics.start_execution(CrewType.CANONICAL, task_count=5, metadata={"test": "data"})

        assert execution_id != ""
        assert execution_id in self.analytics.executions

        execution = self.analytics.executions[execution_id]
        assert execution.crew_type == CrewType.CANONICAL
        assert execution.task_count == 5
        assert execution.metadata == {"test": "data"}
        assert execution.status == ExecutionStatus.PENDING

    def test_start_execution_disabled(self):
        """Test starting execution when analytics is disabled."""
        self.feature_flags.ENABLE_CREW_ANALYTICS = False
        analytics = CrewAnalytics(self.feature_flags)

        execution_id = analytics.start_execution(CrewType.CANONICAL)
        assert execution_id == ""

    def test_update_execution(self):
        """Test updating execution metrics."""
        execution_id = self.analytics.start_execution(CrewType.CANONICAL)

        result = self.analytics.update_execution(
            execution_id,
            ExecutionStatus.RUNNING,
            success_count=3,
            failure_count=1,
            memory_usage=100.0,
            cpu_usage=50.0,
            error_messages=["test error"],
        )

        assert result.success
        execution = self.analytics.executions[execution_id]
        assert execution.status == ExecutionStatus.RUNNING
        assert execution.success_count == 3
        assert execution.failure_count == 1
        assert execution.memory_usage_peak == 100.0
        assert execution.cpu_usage_peak == 50.0
        assert "test error" in execution.error_messages

    def test_update_execution_not_found(self):
        """Test updating non-existent execution."""
        result = self.analytics.update_execution("nonexistent", ExecutionStatus.RUNNING)

        assert not result.success
        assert "not found" in result.error

    def test_complete_execution(self):
        """Test completing execution tracking."""
        execution_id = self.analytics.start_execution(CrewType.CANONICAL)

        result = self.analytics.complete_execution(
            execution_id, success_count=4, failure_count=1, final_memory_usage=150.0, final_cpu_usage=75.0
        )

        assert result.success
        execution = self.analytics.executions[execution_id]
        assert execution.status == ExecutionStatus.COMPLETED
        assert execution.end_time is not None
        assert execution.total_execution_time > 0
        assert execution.memory_usage_peak == 150.0
        assert execution.cpu_usage_peak == 75.0

    def test_fail_execution(self):
        """Test marking execution as failed."""
        execution_id = self.analytics.start_execution(CrewType.CANONICAL)

        result = self.analytics.fail_execution(execution_id, "Test failure", failure_count=2)

        assert result.success
        execution = self.analytics.executions[execution_id]
        assert execution.status == ExecutionStatus.FAILED
        assert execution.end_time is not None
        assert execution.failure_count == 2
        assert "Test failure" in execution.error_messages

    def test_get_crew_metrics(self):
        """Test getting crew metrics."""
        # Complete some executions to generate metrics
        execution_id1 = self.analytics.start_execution(CrewType.CANONICAL)
        self.analytics.complete_execution(execution_id1, 2, 0, 100.0, 50.0)

        execution_id2 = self.analytics.start_execution(CrewType.CANONICAL)
        self.analytics.complete_execution(execution_id2, 1, 1, 120.0, 60.0)

        result = self.analytics.get_crew_metrics(CrewType.CANONICAL)

        assert result.success
        data = result.data
        assert data["total_executions"] == 2
        assert data["successful_executions"] == 2
        assert data["failed_executions"] == 0
        assert data["success_rate"] == 1.0
        assert data["error_rate"] == 0.0
        assert data["average_execution_time"] > 0
        assert data["performance_score"] > 0

    def test_get_crew_metrics_not_found(self):
        """Test getting metrics for non-existent crew type."""
        # This shouldn't happen in normal operation, but test error handling
        result = self.analytics.get_crew_metrics(CrewType.CANONICAL)
        assert result.success  # Should return default metrics

    def test_compare_crews(self):
        """Test comparing two crew implementations."""
        # Set up metrics for both crews
        execution_id1 = self.analytics.start_execution(CrewType.CANONICAL)
        self.analytics.complete_execution(execution_id1, 3, 0, 100.0, 50.0)

        execution_id2 = self.analytics.start_execution(CrewType.NEW)
        self.analytics.complete_execution(execution_id2, 3, 0, 80.0, 40.0)

        result = self.analytics.compare_crews(CrewType.CANONICAL, CrewType.NEW)

        assert result.success
        data = result.data
        assert data["baseline_crew"] == CrewType.CANONICAL.value
        assert data["comparison_crew"] == CrewType.NEW.value
        assert "performance_improvement" in data
        assert "memory_efficiency" in data
        assert "reliability_score" in data
        assert "recommendation" in data
        assert "detailed_metrics" in data

    def test_compare_crews_insufficient_metrics(self):
        """Test comparing crews with insufficient metrics."""
        result = self.analytics.compare_crews(CrewType.CANONICAL, CrewType.NEW)

        # Should still work with default metrics
        assert result.success

    def test_get_dashboard_data(self):
        """Test getting comprehensive dashboard data."""
        # Set up some executions
        execution_id1 = self.analytics.start_execution(CrewType.CANONICAL)
        self.analytics.complete_execution(execution_id1, 2, 0, 100.0, 50.0)

        execution_id2 = self.analytics.start_execution(CrewType.NEW)
        self.analytics.complete_execution(execution_id2, 3, 0, 80.0, 40.0)

        # Add a comparison
        self.analytics.compare_crews(CrewType.CANONICAL, CrewType.NEW)

        result = self.analytics.get_dashboard_data()

        assert result.success
        data = result.data
        assert "crews" in data
        assert "comparisons" in data
        assert "summary" in data

        # Check crews data
        assert CrewType.CANONICAL.value in data["crews"]
        assert CrewType.NEW.value in data["crews"]

        # Check summary
        summary = data["summary"]
        assert summary["total_executions"] >= 2
        assert summary["active_executions"] >= 0
        assert "best_performing_crew" in summary
        assert "most_reliable_crew" in summary

    def test_get_dashboard_data_disabled(self):
        """Test getting dashboard data when analytics is disabled."""
        self.feature_flags.ENABLE_CREW_ANALYTICS = False
        analytics = CrewAnalytics(self.feature_flags)

        result = analytics.get_dashboard_data()
        assert not result.success
        assert "disabled" in result.error

    def test_crew_execution_creation(self):
        """Test CrewExecution creation and properties."""
        execution = CrewExecution(
            execution_id="test_id",
            crew_type=CrewType.CANONICAL,
            start_time=time.time(),
            end_time=time.time() + 10.0,
            status=ExecutionStatus.COMPLETED,
            task_count=5,
            success_count=4,
            failure_count=1,
            total_execution_time=10.0,
            memory_usage_peak=100.0,
            cpu_usage_peak=50.0,
            error_messages=["error1", "error2"],
            metadata={"test": "data"},
        )

        assert execution.execution_id == "test_id"
        assert execution.crew_type == CrewType.CANONICAL
        assert execution.status == ExecutionStatus.COMPLETED
        assert execution.task_count == 5
        assert execution.success_count == 4
        assert execution.failure_count == 1
        assert execution.total_execution_time == 10.0
        assert execution.memory_usage_peak == 100.0
        assert execution.cpu_usage_peak == 50.0
        assert execution.error_messages == ["error1", "error2"]
        assert execution.metadata == {"test": "data"}

    def test_crew_metrics_creation(self):
        """Test CrewMetrics creation and properties."""
        metrics = CrewMetrics(
            crew_type=CrewType.CANONICAL,
            total_executions=10,
            successful_executions=8,
            failed_executions=2,
            average_execution_time=5.0,
            average_memory_usage=100.0,
            average_cpu_usage=50.0,
            success_rate=0.8,
            error_rate=0.2,
            last_execution=time.time(),
            performance_score=0.85,
        )

        assert metrics.crew_type == CrewType.CANONICAL
        assert metrics.total_executions == 10
        assert metrics.successful_executions == 8
        assert metrics.failed_executions == 2
        assert metrics.average_execution_time == 5.0
        assert metrics.average_memory_usage == 100.0
        assert metrics.average_cpu_usage == 50.0
        assert metrics.success_rate == 0.8
        assert metrics.error_rate == 0.2
        assert metrics.performance_score == 0.85

    def test_crew_comparison_creation(self):
        """Test CrewComparison creation and properties."""
        comparison = CrewComparison(
            baseline_crew=CrewType.CANONICAL,
            comparison_crew=CrewType.NEW,
            performance_improvement=15.0,
            memory_efficiency=20.0,
            reliability_score=5.0,
            recommendation="Recommend NEW crew",
            detailed_metrics={"metric1": "value1"},
        )

        assert comparison.baseline_crew == CrewType.CANONICAL
        assert comparison.comparison_crew == CrewType.NEW
        assert comparison.performance_improvement == 15.0
        assert comparison.memory_efficiency == 20.0
        assert comparison.reliability_score == 5.0
        assert comparison.recommendation == "Recommend NEW crew"
        assert comparison.detailed_metrics == {"metric1": "value1"}

    def test_metrics_update_logic(self):
        """Test the internal metrics update logic."""
        # Create a mock execution
        execution = CrewExecution(
            execution_id="test_id",
            crew_type=CrewType.CANONICAL,
            start_time=time.time() - 10.0,
            end_time=time.time(),
            status=ExecutionStatus.COMPLETED,
            task_count=5,
            success_count=4,
            failure_count=1,
            total_execution_time=10.0,
            memory_usage_peak=100.0,
            cpu_usage_peak=50.0,
        )

        # Update metrics
        self.analytics._update_crew_metrics(execution)

        metrics = self.analytics.metrics[CrewType.CANONICAL]
        assert metrics.total_executions == 1
        assert metrics.successful_executions == 1
        assert metrics.failed_executions == 0
        assert metrics.success_rate == 1.0
        assert metrics.average_execution_time == 10.0
        assert metrics.average_memory_usage == 100.0
        assert metrics.average_cpu_usage == 50.0
        assert metrics.performance_score > 0

    def test_recommendation_generation(self):
        """Test recommendation generation logic."""
        # Test strong recommendation
        recommendation = self.analytics._generate_recommendation(25.0, 15.0, 10.0, CrewType.CANONICAL, CrewType.NEW)
        assert "Strongly recommend" in recommendation
        assert CrewType.NEW.value in recommendation

        # Test no clear advantage
        recommendation = self.analytics._generate_recommendation(2.0, 1.0, -1.0, CrewType.CANONICAL, CrewType.NEW)
        assert "No clear advantage" in recommendation

    def test_error_handling(self):
        """Test error handling in analytics operations."""
        # Test with invalid execution ID
        result = self.analytics.update_execution("invalid_id", ExecutionStatus.RUNNING)
        assert not result.success

        result = self.analytics.complete_execution("invalid_id", 1, 0)
        assert not result.success

        result = self.analytics.fail_execution("invalid_id", "error")
        assert not result.success

    def test_concurrent_executions(self):
        """Test handling multiple concurrent executions."""
        execution_ids = []

        # Start multiple executions
        for i in range(5):
            execution_id = self.analytics.start_execution(CrewType.CANONICAL)
            execution_ids.append(execution_id)

        # Complete some executions
        for i in range(3):
            self.analytics.complete_execution(execution_ids[i], 2, 0, 100.0, 50.0)

        # Fail one execution
        self.analytics.fail_execution(execution_ids[3], "Test failure")

        # Check that all executions are tracked
        assert len(self.analytics.executions) == 5

        # Check metrics
        metrics = self.analytics.metrics[CrewType.CANONICAL]
        assert metrics.total_executions == 5
        assert metrics.successful_executions == 3
        assert metrics.failed_executions == 1

    def test_disabled_operations(self):
        """Test operations when analytics is disabled."""
        self.feature_flags.ENABLE_CREW_ANALYTICS = False
        analytics = CrewAnalytics(self.feature_flags)

        # All operations should fail when disabled
        result = analytics.update_execution("id", ExecutionStatus.RUNNING)
        assert not result.success

        result = analytics.complete_execution("id", 1, 0)
        assert not result.success

        result = analytics.get_crew_metrics(CrewType.CANONICAL)
        assert not result.success

        result = analytics.compare_crews(CrewType.CANONICAL, CrewType.NEW)
        assert not result.success

        result = analytics.get_dashboard_data()
        assert not result.success
