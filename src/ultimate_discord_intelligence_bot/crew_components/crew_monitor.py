"""Crew monitor for modular crew organization."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.step_result import StepResult


class CrewMonitor:
    """Monitor for tracking crew performance and execution."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.execution_history: list[dict[str, Any]] = []
        self.performance_metrics: dict[str, Any] = {}
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    def start_execution(self, inputs: dict[str, Any]) -> None:
        """Start monitoring crew execution."""
        self.start_time = time.time()
        self.logger.info(f"Starting crew execution with inputs: {inputs}")
        execution_record = {"start_time": datetime.now(UTC).isoformat(), "inputs": inputs, "status": "running"}
        self.execution_history.append(execution_record)

    def end_execution(self, result: Any, success: bool = True) -> None:
        """End monitoring crew execution."""
        self.end_time = time.time()
        execution_time = self.end_time - self.start_time
        self.logger.info(f"Crew execution completed in {execution_time:.2f}s with success: {success}")
        if self.execution_history:
            self.execution_history[-1].update(
                {
                    "end_time": datetime.now(UTC).isoformat(),
                    "execution_time": execution_time,
                    "success": success,
                    "status": "completed" if success else "failed",
                    "result": str(result) if result else None,
                }
            )
        self.performance_metrics.update(
            {
                "last_execution_time": execution_time,
                "total_executions": len(self.execution_history),
                "success_rate": self._calculate_success_rate(),
                "average_execution_time": self._calculate_average_execution_time(),
            }
        )

    def log_step(self, step_name: str, step_result: StepResult) -> None:
        """Log a crew execution step."""
        self.logger.info(f"Step '{step_name}' completed with success: {step_result.success}")
        if not step_result.success:
            self.logger.warning(f"Step '{step_name}' failed: {step_result.error}")

    def get_execution_summary(self) -> dict[str, Any]:
        """Get a summary of crew execution history."""
        if not self.execution_history:
            return {"message": "No executions recorded"}
        recent_executions = self.execution_history[-10:]
        return {
            "total_executions": len(self.execution_history),
            "recent_executions": recent_executions,
            "performance_metrics": self.performance_metrics,
            "current_status": self.execution_history[-1]["status"] if self.execution_history else "idle",
        }

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get current performance metrics."""
        return self.performance_metrics.copy()

    def reset_metrics(self) -> None:
        """Reset all monitoring metrics."""
        self.execution_history.clear()
        self.performance_metrics.clear()
        self.start_time = 0.0
        self.end_time = 0.0
        self.logger.info("Crew monitoring metrics reset")

    def _calculate_success_rate(self) -> float:
        """Calculate the success rate of executions."""
        if not self.execution_history:
            return 0.0
        successful_executions = sum(1 for record in self.execution_history if record.get("success", False))
        return successful_executions / len(self.execution_history)

    def _calculate_average_execution_time(self) -> float:
        """Calculate the average execution time."""
        if not self.execution_history:
            return 0.0
        execution_times = [
            record.get("execution_time", 0) for record in self.execution_history if "execution_time" in record
        ]
        return sum(execution_times) / len(execution_times) if execution_times else 0.0

    def get_health_status(self) -> dict[str, Any]:
        """Get the health status of the crew system."""
        time.time()
        recent_failures = [record for record in self.execution_history[-5:] if not record.get("success", True)]
        recent_times = [
            record.get("execution_time", 0) for record in self.execution_history[-5:] if "execution_time" in record
        ]
        avg_recent_time = sum(recent_times) / len(recent_times) if recent_times else 0.0
        return {
            "status": "healthy" if len(recent_failures) < 2 else "degraded",
            "recent_failures": len(recent_failures),
            "average_execution_time": avg_recent_time,
            "total_executions": len(self.execution_history),
            "last_execution": self.execution_history[-1] if self.execution_history else None,
        }
