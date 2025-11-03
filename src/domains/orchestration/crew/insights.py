"""Insight generation helpers for crew execution.

This module consolidates insight generation logic from crew_insight_helpers.py
and provides utilities for extracting insights from crew execution results.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog


if TYPE_CHECKING:
    from domains.orchestration.crew.interfaces import CrewExecutionResult
logger = structlog.get_logger(__name__)


class CrewInsightGenerator:
    """Generates insights from crew execution results."""

    def __init__(self, tenant_id: str) -> None:
        """Initialize the insight generator.

        Args:
            tenant_id: Tenant identifier for logging
        """
        self.tenant_id = tenant_id

    def generate_insights(self, result: CrewExecutionResult) -> dict[str, Any]:
        """Generate insights from a crew execution result.

        Args:
            result: The execution result to analyze

        Returns:
            Dictionary containing generated insights
        """
        insights: dict[str, Any] = {
            "task_id": result.task_id,
            "success": result.step_result.success,
            "execution_time_seconds": result.execution_time_seconds,
            "performance": self._analyze_performance(result),
            "resource_usage": self._analyze_resource_usage(result),
            "recommendations": self._generate_recommendations(result),
        }
        logger.debug(
            "crew_insights_generated", tenant_id=self.tenant_id, task_id=result.task_id, insight_count=len(insights)
        )
        return insights

    def _analyze_performance(self, result: CrewExecutionResult) -> dict[str, Any]:
        """Analyze performance metrics from execution.

        Args:
            result: The execution result

        Returns:
            Performance analysis
        """
        if result.execution_time_seconds < 5:
            speed = "fast"
        elif result.execution_time_seconds < 30:
            speed = "normal"
        elif result.execution_time_seconds < 120:
            speed = "slow"
        else:
            speed = "very_slow"
        return {
            "speed_category": speed,
            "execution_time_seconds": result.execution_time_seconds,
            "cache_efficiency": result.cache_hits / (result.cache_hits + 1) if result.cache_hits > 0 else 0.0,
            "retry_rate": result.retry_count,
        }

    def _analyze_resource_usage(self, result: CrewExecutionResult) -> dict[str, Any]:
        """Analyze resource usage from execution.

        Args:
            result: The execution result

        Returns:
            Resource usage analysis
        """
        return {
            "agents_count": len(result.agents_used),
            "agents_used": result.agents_used,
            "tools_count": len(result.tools_used),
            "tools_used": result.tools_used,
            "cache_hits": result.cache_hits,
        }

    def _generate_recommendations(self, result: CrewExecutionResult) -> list[str]:
        """Generate recommendations based on execution results.

        Args:
            result: The execution result

        Returns:
            List of recommendations
        """
        recommendations: list[str] = []
        if result.execution_time_seconds > 120:
            recommendations.append("Consider breaking task into smaller sub-tasks for better performance")
        if result.cache_hits == 0 and result.execution_time_seconds > 10:
            recommendations.append("Enable caching to improve performance on repeated executions")
        if result.retry_count > 2:
            recommendations.append("High retry count detected - investigate root cause of failures")
        if len(result.agents_used) > 5:
            recommendations.append("Large number of agents used - consider simplifying workflow")
        return recommendations
