from __future__ import annotations

import os

from langfuse import Langfuse
from langfuse.model import CreateSpan, CreateTrace, UpdateSpan

from ultimate_discord_intelligence_bot.step_result import StepResult


class LangfuseService:
    """A service for integrating with Langfuse for observability."""

    def __init__(self):
        """Initializes the LangfuseService."""
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")

        if not public_key or not secret_key:
            raise ValueError("LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set.")

        self.langfuse = Langfuse(public_key, secret_key)

    def create_trace(self, name: str, user_id: str, metadata: dict | None = None) -> StepResult:
        """
        Creates a new trace in Langfuse.

        Args:
            name: The name of the trace.
            user_id: The ID of the user associated with this trace.
            metadata: Optional metadata for the trace.

        Returns:
            A StepResult containing the created trace object.
        """
        try:
            trace = self.langfuse.trace(CreateTrace(name=name, user_id=user_id, metadata=metadata or {}))
            return StepResult.ok(data=trace)
        except Exception as e:
            return StepResult.fail(f"Langfuse create trace failed: {e}")

    def create_span(self, trace, name: str, input_data: dict, metadata: dict | None = None) -> StepResult:
        """
        Creates a new span within a trace.

        Args:
            trace: The Langfuse trace object to add the span to.
            name: The name of the span.
            input_data: The input data for this span.
            metadata: Optional metadata for the span.

        Returns:
            A StepResult containing the created span object.
        """
        try:
            span = trace.span(CreateSpan(name=name, input=input_data, metadata=metadata or {}))
            return StepResult.ok(data=span)
        except Exception as e:
            return StepResult.fail(f"Langfuse create span failed: {e}")

    def update_span(self, span, output_data: dict, error: str | None = None) -> StepResult:
        """
        Updates an existing span with output data or an error.

        Args:
            span: The Langfuse span object to update.
            output_data: The output data from the span's execution.
            error: An optional error message if the span failed.

        Returns:
            A StepResult indicating success or failure.
        """
        try:
            span.update(
                UpdateSpan(
                    output=output_data,
                    level="ERROR" if error else "DEFAULT",
                    status_message=error,
                )
            )
            self.langfuse.flush()  # Ensure data is sent
            return StepResult.ok()
        except Exception as e:
            return StepResult.fail(f"Langfuse update span failed: {e}")
