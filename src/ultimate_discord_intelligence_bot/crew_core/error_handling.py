"""Consolidated error handling for crew execution.

This module consolidates error handling logic from crew_error_handler.py
and provides standardized error handling utilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from ultimate_discord_intelligence_bot.step_result import ErrorCategory, StepResult


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.crew_core.interfaces import CrewTask

logger = structlog.get_logger(__name__)


class CrewErrorHandler:
    """Handles errors during crew execution with standardized recovery strategies."""

    def __init__(self, tenant_id: str) -> None:
        """Initialize the error handler.

        Args:
            tenant_id: Tenant identifier for logging
        """
        self.tenant_id = tenant_id

    async def handle_execution_error(
        self,
        task: CrewTask,
        error: Exception,
        attempt: int,
    ) -> StepResult:
        """Handle an execution error with appropriate recovery strategy.

        Args:
            task: The task that failed
            error: The exception that occurred
            attempt: The attempt number (0-indexed)

        Returns:
            StepResult indicating how to proceed
        """
        error_type = type(error).__name__

        logger.error(
            "crew_execution_error",
            tenant_id=self.tenant_id,
            task_id=task.task_id,
            task_type=task.task_type,
            error=str(error),
            error_type=error_type,
            attempt=attempt,
        )

        # Categorize the error
        category = self._categorize_error(error)

        # Determine if retryable
        retryable = category in {
            ErrorCategory.TIMEOUT,
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.NETWORK,
        }

        return StepResult.fail(
            f"Task execution failed: {error!s}",
            error_category=category,
            retryable=retryable,
            metadata={
                "error_type": error_type,
                "error_message": str(error),
                "attempt": attempt,
                "task_id": task.task_id,
            },
        )

    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize an error into an ErrorCategory.

        Args:
            error: The exception to categorize

        Returns:
            The appropriate ErrorCategory
        """
        error_type = type(error).__name__

        # Timeout errors
        if "timeout" in error_type.lower() or "timeout" in str(error).lower():
            return ErrorCategory.TIMEOUT

        # Rate limit errors
        if "rate" in error_type.lower() or "429" in str(error):
            return ErrorCategory.RATE_LIMIT

        # Network errors
        if any(keyword in error_type.lower() for keyword in ["connection", "network", "socket"]):
            return ErrorCategory.NETWORK

        # Validation errors
        if "validation" in error_type.lower() or "invalid" in str(error).lower():
            return ErrorCategory.VALIDATION

        # Authentication errors
        if any(keyword in error_type.lower() for keyword in ["auth", "permission", "unauthorized", "forbidden"]):
            return ErrorCategory.AUTHENTICATION

        # Default to processing error
        return ErrorCategory.PROCESSING
