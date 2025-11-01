from __future__ import annotations

from typing import Any

from ... import trace as trace_api
from ...trace import (
    Event,
    ReadableSpan,
    Span,
    SpanContext,
)
from ...trace import (
    Tracer as BaseTracer,
)
from ...trace import (
    TracerProvider as BaseTracerProvider,
)
from ..resources import Resource
from ..util.instrumentation import InstrumentationScope


class TracerProvider(BaseTracerProvider):
    """Enhanced TracerProvider stub for SDK compatibility."""

    def __init__(self, resource: Resource | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._resource = resource or Resource.create({})

    @property
    def resource(self) -> Resource:
        return self._resource

    def get_tracer(self, name: str, version: str | None = None, schema_url: str | None = None) -> Tracer:
        scope = InstrumentationScope(name, version, schema_url)
        tracer = Tracer(name, resource=self._resource, instrumentation_scope=scope)
        return tracer


class Tracer(BaseTracer):
    """SDK tracer that enriches spans with resource and instrumentation scope."""

    def __init__(
        self,
        name: str,
        *,
        resource: Resource | None = None,
        instrumentation_scope: InstrumentationScope | None = None,
    ) -> None:
        super().__init__(name, resource=resource, instrumentation_scope=instrumentation_scope)

    def start_span(
        self,
        name: str,
        *,
        context: SpanContext | None = None,
        parent: Span | None = None,
        kind: str = trace_api.SpanKind.INTERNAL,
    ) -> Span:
        span = super().start_span(name, context=context, parent=parent, kind=kind)
        # Ensure spans inherit the latest resource and instrumentation scope assignments.
        if getattr(self, "_resource", None) is not None and getattr(span, "resource", None) is None:
            span.resource = self._resource
        if getattr(self, "_instrumentation_scope", None) is not None:
            span.instrumentation_scope = self._instrumentation_scope
        return span


class SpanProcessor:
    """Minimal span processor stub."""

    def on_start(self, span: Span, parent_context=None) -> None:  # pragma: no cover - stub
        pass

    def on_end(self, span: Span) -> None:  # pragma: no cover - stub
        pass

    def shutdown(self) -> None:  # pragma: no cover - stub
        pass

    def force_flush(self, timeout_millis: int | None = None) -> None:  # pragma: no cover - stub
        pass


class SynchronousMultiSpanProcessor(SpanProcessor):
    """Fan-out span processor that invokes multiple processors synchronously."""

    def __init__(self, processors: list[SpanProcessor]):
        self._processors = list(processors)

    def on_start(self, span: Span, parent_context=None) -> None:  # pragma: no cover - stub behaviour
        for processor in self._processors:
            processor.on_start(span, parent_context)

    def on_end(self, span: Span) -> None:  # pragma: no cover - stub behaviour
        for processor in self._processors:
            processor.on_end(span)

    def shutdown(self) -> None:  # pragma: no cover - stub behaviour
        for processor in self._processors:
            processor.shutdown()

    def force_flush(self, timeout_millis: int | None = None) -> None:  # pragma: no cover - stub behaviour
        for processor in self._processors:
            processor.force_flush(timeout_millis)


__all__ = [
    "Event",
    "ReadableSpan",
    "Resource",
    "Span",
    "SpanProcessor",
    "SynchronousMultiSpanProcessor",
    "Tracer",
    "TracerProvider",
]
