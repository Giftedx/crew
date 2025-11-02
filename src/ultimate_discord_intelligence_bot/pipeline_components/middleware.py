"""Pipeline step middleware primitives."""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol
from .tracing import tracing_module

if TYPE_CHECKING:
    from platform.core.step_result import StepResult


@dataclass(slots=True)
class StepContext:
    """State shared with step middleware callbacks."""

    step: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    pipeline: Any
    start_time: float = field(default_factory=time.monotonic)
    result: StepResult | None = None
    exception: Exception | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class PipelineStepMiddleware(Protocol):
    """Hook interface for observing pipeline step execution."""

    async def before_step(self, context: StepContext) -> None: ...

    async def after_step(self, context: StepContext) -> None: ...

    async def on_error(self, context: StepContext) -> None: ...


class BasePipelineStepMiddleware:
    """Convenience base with optional async hooks."""

    async def before_step(self, context: StepContext) -> None:
        return None

    async def after_step(self, context: StepContext) -> None:
        return None

    async def on_error(self, context: StepContext) -> None:
        return None


class TracingStepMiddleware(BasePipelineStepMiddleware):
    """Adds tracing spans around pipeline steps."""

    _SPAN_KEY = "tracing_span"
    _SPAN_CM_KEY = "tracing_span_cm"

    def __init__(self, *, span_prefix: str = "pipeline.step") -> None:
        self._span_prefix = span_prefix

    async def before_step(self, context: StepContext) -> None:
        span_cm = tracing_module.start_span(f"{self._span_prefix}.{context.step}")
        span = span_cm.__enter__()
        self._store_span(context, span_cm, span)
        span.set_attribute("step.name", context.step)
        orchestrator = getattr(context.pipeline, "_orchestrator", None)
        if orchestrator:
            span.set_attribute("pipeline.orchestrator", orchestrator)

    async def after_step(self, context: StepContext) -> None:
        span_cm, span = self._pop_span(context)
        if not span_cm:
            return
        result = context.result
        if result is not None:
            span.set_attribute("step.success", result.success)
            if result.custom_status is not None:
                span.set_attribute("step.custom_status", result.custom_status)
            if result.error:
                span.set_attribute("step.error_flag", True)
            else:
                span.set_attribute("step.error_flag", False)
        self._finalize_span(span_cm, span, context, None)

    async def on_error(self, context: StepContext) -> None:
        span_cm, span = self._pop_span(context)
        if not span_cm:
            return
        exc = context.exception
        if exc is not None:
            span.set_attribute("step.error_flag", True)
            span.set_attribute("step.error.type", exc.__class__.__name__)
        self._finalize_span(span_cm, span, context, exc)

    def _store_span(self, context: StepContext, span_cm: Any, span: Any) -> None:
        context.metadata[self._SPAN_CM_KEY] = span_cm
        context.metadata[self._SPAN_KEY] = span

    def _pop_span(self, context: StepContext) -> tuple[Any | None, Any | None]:
        span_cm = context.metadata.pop(self._SPAN_CM_KEY, None)
        span = context.metadata.pop(self._SPAN_KEY, None)
        return (span_cm, span)

    def _finalize_span(self, span_cm: Any, span: Any, context: StepContext, exc: Exception | None) -> None:
        duration_ms = (time.monotonic() - context.start_time) * 1000.0
        span.set_attribute("step.duration_ms", duration_ms)
        span_cm.__exit__(exc.__class__ if exc else None, exc, None)


__all__ = ["BasePipelineStepMiddleware", "PipelineStepMiddleware", "StepContext", "TracingStepMiddleware"]
