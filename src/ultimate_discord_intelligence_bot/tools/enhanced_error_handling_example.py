"""Example tool demonstrating enhanced error handling with StepResult.

This serves as a reference for how to use the enhanced StepResult features
in tool implementations.
"""

from __future__ import annotations

import time
from typing import Any

from ultimate_discord_intelligence_bot.step_result import (
    ErrorCategory,
    StepResult,
)

from ._base import BaseTool


class EnhancedErrorHandlingExample(BaseTool[StepResult]):
    """Example tool showing comprehensive error handling patterns."""

    name: str = "Enhanced Error Handling Example"
    description: str = "Demonstrates comprehensive error handling with enhanced StepResult"

    def _run(self, operation: str, **kwargs: Any) -> StepResult:
        """Execute operation with comprehensive error handling."""
        try:
            # Input validation
            if not operation:
                return StepResult.bad_request("Operation cannot be empty")

            if operation not in ["process", "validate", "transform"]:
                return StepResult.bad_request(f"Unknown operation: {operation}")

            # Simulate different error scenarios
            if operation == "process":
                return self._simulate_processing_error()
            elif operation == "validate":
                return self._simulate_validation_error()
            elif operation == "transform":
                return self._simulate_success_with_warnings()

        except Exception as e:
            # Catch-all for unexpected errors
            return StepResult.fail(
                f"Unexpected error in {operation}: {str(e)}",
                error_category=ErrorCategory.SYSTEM,
                retryable=False,
                metadata={"operation": operation, "timestamp": time.time()},
            )

    def _simulate_processing_error(self) -> StepResult:
        """Simulate a processing error."""
        # Simulate a timeout scenario
        return StepResult.timeout_error(
            "Processing operation timed out after 30 seconds",
            metadata={"operation": "processing", "timeout_seconds": 30, "attempted_at": time.time()},
        )

    def _simulate_validation_error(self) -> StepResult:
        """Simulate a validation error."""
        return StepResult.bad_request(
            "Invalid data format: missing required field 'content'",
            metadata={
                "missing_fields": ["content"],
                "provided_fields": ["title"],
                "validation_rules": "content_required",
            },
        )

    def _simulate_success_with_warnings(self) -> StepResult:
        """Simulate a successful operation with warnings."""
        return StepResult.success_with_warnings(
            ["Partial data available due to API rate limits", "Some metadata fields were missing from source"],
            data={
                "transformed_content": "Successfully transformed content",
                "confidence_score": 0.85,
                "partial_data": True,
            },
            metadata={"processing_time": 2.5, "api_calls_made": 3, "rate_limit_hits": 1},
        )

    def _run_with_network_simulation(self, url: str) -> StepResult:
        """Example of network error handling."""
        try:
            # Simulate network issues
            if "unavailable" in url:
                return StepResult.service_unavailable(
                    "External service is temporarily unavailable", metadata={"service_url": url, "attempt": 1}
                )
            elif "rate-limit" in url:
                return StepResult.rate_limited(
                    "Rate limit exceeded for API endpoint", metadata={"endpoint": url, "retry_after": 60}
                )
            else:
                return StepResult.ok(
                    data={"content": "Successfully retrieved content"},
                    metadata={"source_url": url, "response_time": 0.5},
                )
        except Exception as e:
            return StepResult.network_error(
                f"Network error accessing {url}: {str(e)}",
                retryable=True,
                metadata={"url": url, "error_type": type(e).__name__},
            )
