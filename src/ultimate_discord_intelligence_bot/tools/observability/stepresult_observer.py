"""StepResult observer for monitoring tool execution.

This module provides observability capabilities for tracking StepResult objects
and tool execution metrics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.step_result import StepResult


class StepResultObserver:
    """Observer for tracking StepResult objects and tool execution."""

    def __init__(self) -> None:
        self.execution_times: list[float] = []
        self.error_counts: dict[str, int] = {}
        self.success_count = 0
        self.total_count = 0

    def observe_result(self, result: StepResult, execution_time: float) -> None:
        """Observe a StepResult and track metrics.

        Args:
            result: The StepResult to observe
            execution_time: Time taken to execute the tool in seconds
        """
        self.total_count += 1
        self.execution_times.append(execution_time)

        if result.success:
            self.success_count += 1
        else:
            error_category = result.error_category.value if result.error_category else "unknown"
            self.error_counts[error_category] = self.error_counts.get(error_category, 0) + 1

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics.

        Returns:
            Dictionary containing current metrics
        """
        avg_execution_time = sum(self.execution_times) / len(self.execution_times) if self.execution_times else 0
        success_rate = self.success_count / self.total_count if self.total_count > 0 else 0

        return {
            "total_executions": self.total_count,
            "success_count": self.success_count,
            "success_rate": success_rate,
            "average_execution_time": avg_execution_time,
            "error_counts": self.error_counts,
            "total_errors": sum(self.error_counts.values()),
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.execution_times.clear()
        self.error_counts.clear()
        self.success_count = 0
        self.total_count = 0


# Global observer instance
_global_observer = StepResultObserver()


def get_global_observer() -> StepResultObserver:
    """Get the global StepResult observer instance."""
    return _global_observer


def observe_tool_execution(result: StepResult, execution_time: float) -> None:
    """Observe a tool execution result.

    Args:
        result: The StepResult from the tool execution
        execution_time: Time taken to execute the tool
    """
    _global_observer.observe_result(result, execution_time)


def get_execution_metrics() -> dict[str, Any]:
    """Get current execution metrics."""
    return _global_observer.get_metrics()


def reset_execution_metrics() -> None:
    """Reset execution metrics."""
    _global_observer.reset()
