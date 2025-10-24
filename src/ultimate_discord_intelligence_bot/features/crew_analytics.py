"""Crew performance analytics and monitoring system.

This module provides analytics for crew execution patterns, performance
comparison, and monitoring across different crew implementations.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class CrewType(Enum):
    """Types of crew implementations."""

    CANONICAL = "canonical"
    NEW = "new"
    MODULAR = "modular"
    REFACTORED = "refactored"
    LEGACY = "legacy"


class ExecutionStatus(Enum):
    """Execution status for crew operations."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class CrewExecution:
    """Represents a crew execution with metrics."""

    execution_id: str
    crew_type: CrewType
    start_time: float
    end_time: float | None = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    task_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_execution_time: float = 0.0
    memory_usage_peak: float = 0.0
    cpu_usage_peak: float = 0.0
    error_messages: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CrewMetrics:
    """Aggregated metrics for a crew type."""

    crew_type: CrewType
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0.0
    average_memory_usage: float = 0.0
    average_cpu_usage: float = 0.0
    success_rate: float = 0.0
    error_rate: float = 0.0
    last_execution: float | None = None
    performance_score: float = 0.0


@dataclass
class CrewComparison:
    """Comparison results between crew implementations."""

    baseline_crew: CrewType
    comparison_crew: CrewType
    performance_improvement: float = 0.0
    memory_efficiency: float = 0.0
    reliability_score: float = 0.0
    recommendation: str = ""
    detailed_metrics: dict[str, Any] = field(default_factory=dict)


class CrewAnalytics:
    """Analytics system for crew performance monitoring and comparison."""

    def __init__(self, feature_flags: FeatureFlags):
        """Initialize crew analytics system.

        Args:
            feature_flags: Feature flags configuration
        """
        self.feature_flags = feature_flags
        self.executions: dict[str, CrewExecution] = {}
        self.metrics: dict[CrewType, CrewMetrics] = {}
        self.comparisons: list[CrewComparison] = []

        # Initialize metrics for all crew types
        for crew_type in CrewType:
            self.metrics[crew_type] = CrewMetrics(crew_type=crew_type)

    def is_enabled(self) -> bool:
        """Check if crew analytics is enabled."""
        return self.feature_flags.ENABLE_CREW_ANALYTICS

    def start_execution(self, crew_type: CrewType, task_count: int = 0, metadata: dict[str, Any] | None = None) -> str:
        """Start tracking a crew execution.

        Args:
            crew_type: Type of crew being executed
            task_count: Number of tasks in the execution
            metadata: Optional metadata for the execution

        Returns:
            str: Execution ID for tracking
        """
        if not self.is_enabled():
            return ""

        execution_id = str(uuid4())
        execution = CrewExecution(
            execution_id=execution_id,
            crew_type=crew_type,
            start_time=time.time(),
            task_count=task_count,
            metadata=metadata or {},
        )

        self.executions[execution_id] = execution
        logger.info(f"Started tracking execution {execution_id} for crew {crew_type.value}")

        return execution_id

    def update_execution(
        self,
        execution_id: str,
        status: ExecutionStatus,
        success_count: int = 0,
        failure_count: int = 0,
        memory_usage: float = 0.0,
        cpu_usage: float = 0.0,
        error_messages: list[str] | None = None,
    ) -> StepResult:
        """Update execution metrics during runtime.

        Args:
            execution_id: ID of the execution to update
            status: Current execution status
            success_count: Number of successful tasks
            failure_count: Number of failed tasks
            memory_usage: Current memory usage
            cpu_usage: Current CPU usage
            error_messages: List of error messages

        Returns:
            StepResult: Result of the update operation
        """
        if not self.is_enabled():
            return StepResult.fail("Crew analytics disabled")

        if execution_id not in self.executions:
            return StepResult.fail("Execution not found")

        try:
            execution = self.executions[execution_id]
            execution.status = status
            execution.success_count = success_count
            execution.failure_count = failure_count

            # Update peak usage metrics
            if memory_usage > execution.memory_usage_peak:
                execution.memory_usage_peak = memory_usage
            if cpu_usage > execution.cpu_usage_peak:
                execution.cpu_usage_peak = cpu_usage

            if error_messages:
                execution.error_messages.extend(error_messages)

            return StepResult.ok(data={"execution_id": execution_id, "status": status.value, "updated_at": time.time()})

        except Exception as e:
            logger.error(f"Failed to update execution {execution_id}: {e}")
            return StepResult.fail(f"Update failed: {e}")

    def complete_execution(
        self,
        execution_id: str,
        success_count: int,
        failure_count: int,
        final_memory_usage: float = 0.0,
        final_cpu_usage: float = 0.0,
    ) -> StepResult:
        """Complete execution tracking and update metrics.

        Args:
            execution_id: ID of the execution to complete
            success_count: Final success count
            failure_count: Final failure count
            final_memory_usage: Final memory usage
            final_cpu_usage: Final CPU usage

        Returns:
            StepResult: Result of the completion operation
        """
        if not self.is_enabled():
            return StepResult.fail("Crew analytics disabled")

        if execution_id not in self.executions:
            return StepResult.fail("Execution not found")

        try:
            execution = self.executions[execution_id]
            execution.end_time = time.time()
            execution.status = ExecutionStatus.COMPLETED
            execution.success_count = success_count
            execution.failure_count = failure_count
            execution.total_execution_time = execution.end_time - execution.start_time

            # Update peak usage
            if final_memory_usage > execution.memory_usage_peak:
                execution.memory_usage_peak = final_memory_usage
            if final_cpu_usage > execution.cpu_usage_peak:
                execution.cpu_usage_peak = final_cpu_usage

            # Update aggregated metrics
            self._update_crew_metrics(execution)

            logger.info(f"Completed tracking execution {execution_id} for crew {execution.crew_type.value}")

            return StepResult.ok(
                data={
                    "execution_id": execution_id,
                    "total_time": execution.total_execution_time,
                    "success_rate": success_count / (success_count + failure_count)
                    if (success_count + failure_count) > 0
                    else 0,
                }
            )

        except Exception as e:
            logger.error(f"Failed to complete execution {execution_id}: {e}")
            return StepResult.fail(f"Completion failed: {e}")

    def fail_execution(self, execution_id: str, error_message: str, failure_count: int = 0) -> StepResult:
        """Mark execution as failed.

        Args:
            execution_id: ID of the failed execution
            error_message: Error message describing the failure
            failure_count: Number of failed tasks

        Returns:
            StepResult: Result of the failure operation
        """
        if not self.is_enabled():
            return StepResult.fail("Crew analytics disabled")

        if execution_id not in self.executions:
            return StepResult.fail("Execution not found")

        try:
            execution = self.executions[execution_id]
            execution.end_time = time.time()
            execution.status = ExecutionStatus.FAILED
            execution.failure_count = failure_count
            execution.total_execution_time = execution.end_time - execution.start_time
            execution.error_messages.append(error_message)

            # Update aggregated metrics
            self._update_crew_metrics(execution)

            logger.warning(f"Execution {execution_id} failed for crew {execution.crew_type.value}: {error_message}")

            return StepResult.ok(data={"execution_id": execution_id, "status": "failed", "error": error_message})

        except Exception as e:
            logger.error(f"Failed to mark execution {execution_id} as failed: {e}")
            return StepResult.fail(f"Failure tracking failed: {e}")

    def get_crew_metrics(self, crew_type: CrewType) -> StepResult:
        """Get metrics for a specific crew type.

        Args:
            crew_type: Type of crew to get metrics for

        Returns:
            StepResult: Result containing crew metrics
        """
        if not self.is_enabled():
            return StepResult.fail("Crew analytics disabled")

        try:
            metrics = self.metrics.get(crew_type)
            if not metrics:
                return StepResult.fail(f"No metrics found for crew type {crew_type.value}")

            return StepResult.ok(
                data={
                    "crew_type": crew_type.value,
                    "total_executions": metrics.total_executions,
                    "successful_executions": metrics.successful_executions,
                    "failed_executions": metrics.failed_executions,
                    "success_rate": metrics.success_rate,
                    "error_rate": metrics.error_rate,
                    "average_execution_time": metrics.average_execution_time,
                    "average_memory_usage": metrics.average_memory_usage,
                    "average_cpu_usage": metrics.average_cpu_usage,
                    "performance_score": metrics.performance_score,
                    "last_execution": metrics.last_execution,
                }
            )

        except Exception as e:
            logger.error(f"Failed to get metrics for crew {crew_type.value}: {e}")
            return StepResult.fail(f"Metrics retrieval failed: {e}")

    def compare_crews(self, crew_a: CrewType, crew_b: CrewType) -> StepResult:
        """Compare two crew implementations.

        Args:
            crew_a: First crew to compare
            crew_b: Second crew to compare

        Returns:
            StepResult: Result containing comparison data
        """
        if not self.is_enabled():
            return StepResult.fail("Crew analytics disabled")

        try:
            metrics_a = self.metrics.get(crew_a)
            metrics_b = self.metrics.get(crew_b)

            if not metrics_a or not metrics_b:
                return StepResult.fail("Insufficient metrics for comparison")

            # Calculate performance improvement
            if metrics_a.average_execution_time > 0:
                performance_improvement = (
                    (metrics_a.average_execution_time - metrics_b.average_execution_time)
                    / metrics_a.average_execution_time
                ) * 100
            else:
                performance_improvement = 0.0

            # Calculate memory efficiency
            if metrics_a.average_memory_usage > 0:
                memory_efficiency = (
                    (metrics_a.average_memory_usage - metrics_b.average_memory_usage) / metrics_a.average_memory_usage
                ) * 100
            else:
                memory_efficiency = 0.0

            # Calculate reliability score
            reliability_score = (metrics_b.success_rate - metrics_a.success_rate) * 100

            # Generate recommendation
            recommendation = self._generate_recommendation(
                performance_improvement, memory_efficiency, reliability_score, crew_a, crew_b
            )

            comparison = CrewComparison(
                baseline_crew=crew_a,
                comparison_crew=crew_b,
                performance_improvement=performance_improvement,
                memory_efficiency=memory_efficiency,
                reliability_score=reliability_score,
                recommendation=recommendation,
                detailed_metrics={
                    "crew_a": {
                        "execution_time": metrics_a.average_execution_time,
                        "memory_usage": metrics_a.average_memory_usage,
                        "success_rate": metrics_a.success_rate,
                    },
                    "crew_b": {
                        "execution_time": metrics_b.average_execution_time,
                        "memory_usage": metrics_b.average_memory_usage,
                        "success_rate": metrics_b.success_rate,
                    },
                },
            )

            self.comparisons.append(comparison)

            return StepResult.ok(
                data={
                    "baseline_crew": crew_a.value,
                    "comparison_crew": crew_b.value,
                    "performance_improvement": performance_improvement,
                    "memory_efficiency": memory_efficiency,
                    "reliability_score": reliability_score,
                    "recommendation": recommendation,
                    "detailed_metrics": comparison.detailed_metrics,
                }
            )

        except Exception as e:
            logger.error(f"Failed to compare crews {crew_a.value} and {crew_b.value}: {e}")
            return StepResult.fail(f"Comparison failed: {e}")

    def get_dashboard_data(self) -> StepResult:
        """Get comprehensive dashboard data for all crews.

        Returns:
            StepResult: Result containing dashboard data
        """
        if not self.is_enabled():
            return StepResult.fail("Crew analytics disabled")

        try:
            dashboard_data = {
                "crews": {},
                "comparisons": [],
                "summary": {
                    "total_executions": 0,
                    "active_executions": 0,
                    "best_performing_crew": None,
                    "most_reliable_crew": None,
                },
            }

            # Collect metrics for all crews
            best_performance = 0.0
            best_reliability = 0.0
            best_performing_crew = None
            most_reliable_crew = None

            for crew_type, metrics in self.metrics.items():
                dashboard_data["crews"][crew_type.value] = {
                    "total_executions": metrics.total_executions,
                    "success_rate": metrics.success_rate,
                    "average_execution_time": metrics.average_execution_time,
                    "average_memory_usage": metrics.average_memory_usage,
                    "performance_score": metrics.performance_score,
                }

                dashboard_data["summary"]["total_executions"] += metrics.total_executions

                # Track best performers
                if metrics.performance_score > best_performance:
                    best_performance = metrics.performance_score
                    best_performing_crew = crew_type.value

                if metrics.success_rate > best_reliability:
                    best_reliability = metrics.success_rate
                    most_reliable_crew = crew_type.value

            # Count active executions
            active_count = sum(
                1
                for exec in self.executions.values()
                if exec.status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]
            )
            dashboard_data["summary"]["active_executions"] = active_count
            dashboard_data["summary"]["best_performing_crew"] = best_performing_crew
            dashboard_data["summary"]["most_reliable_crew"] = most_reliable_crew

            # Add recent comparisons
            for comparison in self.comparisons[-10:]:  # Last 10 comparisons
                dashboard_data["comparisons"].append(
                    {
                        "baseline": comparison.baseline_crew.value,
                        "comparison": comparison.comparison_crew.value,
                        "performance_improvement": comparison.performance_improvement,
                        "recommendation": comparison.recommendation,
                    }
                )

            return StepResult.ok(data=dashboard_data)

        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return StepResult.fail(f"Dashboard data retrieval failed: {e}")

    def _update_crew_metrics(self, execution: CrewExecution) -> None:
        """Update aggregated metrics for a crew type.

        Args:
            execution: Completed execution to process
        """
        try:
            metrics = self.metrics[execution.crew_type]

            # Update execution counts
            metrics.total_executions += 1
            if execution.status == ExecutionStatus.COMPLETED:
                metrics.successful_executions += 1
            else:
                metrics.failed_executions += 1

            # Update success/error rates
            if metrics.total_executions > 0:
                metrics.success_rate = metrics.successful_executions / metrics.total_executions
                metrics.error_rate = metrics.failed_executions / metrics.total_executions

            # Update average execution time
            if execution.total_execution_time > 0:
                if metrics.average_execution_time == 0:
                    metrics.average_execution_time = execution.total_execution_time
                else:
                    metrics.average_execution_time = (
                        metrics.average_execution_time * (metrics.total_executions - 1) + execution.total_execution_time
                    ) / metrics.total_executions

            # Update average memory usage
            if execution.memory_usage_peak > 0:
                if metrics.average_memory_usage == 0:
                    metrics.average_memory_usage = execution.memory_usage_peak
                else:
                    metrics.average_memory_usage = (
                        metrics.average_memory_usage * (metrics.total_executions - 1) + execution.memory_usage_peak
                    ) / metrics.total_executions

            # Update average CPU usage
            if execution.cpu_usage_peak > 0:
                if metrics.average_cpu_usage == 0:
                    metrics.average_cpu_usage = execution.cpu_usage_peak
                else:
                    metrics.average_cpu_usage = (
                        metrics.average_cpu_usage * (metrics.total_executions - 1) + execution.cpu_usage_peak
                    ) / metrics.total_executions

            # Calculate performance score (weighted combination of metrics)
            metrics.performance_score = (
                metrics.success_rate * 0.4  # 40% weight on success rate
                + (1.0 / max(metrics.average_execution_time, 0.1)) * 0.3  # 30% weight on speed
                + (1.0 / max(metrics.average_memory_usage, 0.1)) * 0.3  # 30% weight on memory efficiency
            )

            metrics.last_execution = execution.end_time or time.time()

        except Exception as e:
            logger.error(f"Failed to update metrics for crew {execution.crew_type.value}: {e}")

    def _generate_recommendation(
        self,
        performance_improvement: float,
        memory_efficiency: float,
        reliability_score: float,
        crew_a: CrewType,
        crew_b: CrewType,
    ) -> str:
        """Generate recommendation based on comparison metrics.

        Args:
            performance_improvement: Performance improvement percentage
            memory_efficiency: Memory efficiency improvement percentage
            reliability_score: Reliability score difference
            crew_a: Baseline crew
            crew_b: Comparison crew

        Returns:
            str: Recommendation text
        """
        if performance_improvement > 20 and memory_efficiency > 10 and reliability_score > 0:
            return f"Strongly recommend {crew_b.value} over {crew_a.value} - significant improvements in all metrics"
        elif performance_improvement > 10 and reliability_score > 0:
            return f"Recommend {crew_b.value} over {crew_a.value} - good performance and reliability improvements"
        elif memory_efficiency > 15:
            return f"Consider {crew_b.value} for memory-constrained environments"
        elif performance_improvement > 5:
            return f"Slight preference for {crew_b.value} based on performance"
        elif reliability_score > 0:
            return f"Slight preference for {crew_b.value} based on reliability"
        else:
            return f"No clear advantage between {crew_a.value} and {crew_b.value} - consider other factors"
