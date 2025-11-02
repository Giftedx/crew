from __future__ import annotations

import contextlib
import random
import time
from dataclasses import dataclass, field
from typing import Any

from .. import context as context_api


_GLOBAL_PROVIDER: TracerProvider | None = None
_CURRENT_SPAN_KEY = "otel.current_span"


class StatusCode:
    """Status codes for spans."""

    UNSET = 0
    OK = 1
    ERROR = 2


@dataclass
class Status:
    """Span status container."""

    status_code: int
    description: str = ""


class SpanKind:
    """Enumeration of span kinds."""

    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class TraceFlags(int):
    """Trace flag bitmask helper."""

    SAMPLED = 0x01

    def __new__(cls, value: int = 0) -> TraceFlags:  # type: ignore[override]
        return int.__new__(cls, value & 0xFF)

    def __or__(self, other: int) -> TraceFlags:  # pragma: no cover - simple helper
        return TraceFlags(int(self) | int(other))

    def __and__(self, other: int) -> TraceFlags:  # pragma: no cover - simple helper
        return TraceFlags(int(self) & int(other))


@dataclass
class Event:
    """Represents a timestamped event attached to a span."""

    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    timestamp: int | None = None


@dataclass
class SpanContext:
    """Span context values used for propagation."""

    trace_id: int = field(default_factory=lambda: random.getrandbits(128))
    span_id: int = field(default_factory=lambda: random.getrandbits(64))
    is_remote: bool = False
    trace_flags: int = 0
    trace_state: dict[str, Any] | None = None

    @property
    def is_valid(self) -> bool:
        return bool(self.trace_id and self.span_id)


@dataclass
class Link:
    """Link to another span context."""

    context: SpanContext
    attributes: dict[str, Any] | None = None


class ReadableSpan:
    """Read-only view of a span used by processors and exporters."""

    def __init__(
        self,
        name: str,
        *,
        context: SpanContext,
        parent: SpanContext | None = None,
        resource: Any | None = None,
        attributes: dict[str, Any] | None = None,
        events: list[Event] | None = None,
        links: list[Link] | None = None,
        status: Status | None = None,
        kind: str = SpanKind.INTERNAL,
        start_time: int | None = None,
        end_time: int | None = None,
        instrumentation_scope: Any | None = None,
    ) -> None:
        self.name = name
        self.context = context
        self.parent = parent
        self.resource = resource
        self.attributes = dict(attributes or {})
        self.events = list(events or [])
        self.links = list(links or [])
        self.status = status or Status(StatusCode.UNSET)
        self.kind = kind
        self.start_time = start_time
        self.end_time = end_time
        self.instrumentation_scope = instrumentation_scope

    def get_span_context(self) -> SpanContext:
        return self.context

    def is_recording(self) -> bool:  # pragma: no cover - default behaviour for snapshots
        return False

    def to_dict(self) -> dict[str, Any]:  # pragma: no cover - convenience helper
        return {
            "name": self.name,
            "context": self.context,
            "parent": self.parent,
            "resource": self.resource,
            "attributes": dict(self.attributes),
            "events": list(self.events),
            "links": list(self.links),
            "status": self.status,
            "kind": self.kind,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "instrumentation_scope": self.instrumentation_scope,
        }


class Span(ReadableSpan):
    """Basic span implementation for tests."""

    def __init__(
        self,
        name: str,
        *,
        context: SpanContext | None = None,
        parent: Span | SpanContext | None = None,
        kind: str = SpanKind.INTERNAL,
        resource: Any | None = None,
        instrumentation_scope: Any | None = None,
        processors: tuple[Any, ...] | None = None,
    ) -> None:
        context_obj = context or SpanContext()
        if isinstance(parent, Span):
            parent_context: SpanContext | None = parent.get_span_context()
        elif isinstance(parent, SpanContext):
            parent_context = parent
        else:
            parent_context = None

        super().__init__(
            name,
            context=context_obj,
            parent=parent_context,
            resource=resource,
            attributes={},
            events=None,
            links=None,
            status=Status(StatusCode.UNSET),
            kind=kind,
            start_time=time.time_ns(),
            end_time=None,
            instrumentation_scope=instrumentation_scope,
        )
        self._parent_span = parent if isinstance(parent, Span) else None
        self._processors: tuple[Any, ...] | None = tuple(processors) if processors is not None else None

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def set_attributes(self, attributes: dict[str, Any]) -> None:
        self.attributes.update(dict(attributes))

    def add_event(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        timestamp: int | None = None,
    ) -> None:
        event = Event(name=name, attributes=dict(attributes or {}), timestamp=timestamp or time.time_ns())
        self.events.append(event)

    def add_link(self, context: SpanContext, attributes: dict[str, Any] | None = None) -> None:
        self.links.append(Link(context=context, attributes=attributes))

    def update_name(self, name: str) -> None:
        self.name = name

    def set_status(self, status: Status | int, description: str | None = None) -> None:
        if isinstance(status, Status):
            self.status = status
        else:
            self.status = Status(status, description or "")

    def end(self, end_time: int | None = None) -> None:
        self.end_time = end_time if end_time is not None else time.time_ns()
        processors: tuple[Any, ...]
        if self._processors is not None:
            processors = self._processors
        else:
            prov = get_tracer_provider()
            processors = tuple(prov._processors) if isinstance(prov, TracerProvider) else ()

        for proc in processors:
            with contextlib.suppress(Exception):
                proc.on_end(self)

    def is_recording(self) -> bool:
        return self.end_time is None

    def record_exception(self, exc: Exception) -> None:  # pragma: no cover - stub
        self.add_event("exception", {"type": type(exc).__name__, "message": str(exc)})

    def get_span_context(self) -> SpanContext:
        return self.context


class NonRecordingSpan(Span):
    """Span placeholder that does not record data."""

    def __init__(self, context: SpanContext | None = None) -> None:
        super().__init__("non-recording", context=context or SpanContext())

    def is_recording(self) -> bool:
        return False


class _SpanContextManager:
    def __init__(self, span: Span) -> None:
        self._span = span
        self._token: Any | None = None

    def __enter__(self) -> Span:
        self._token = context_api.attach(set_span_in_context(self._span))
        return self._span

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._token is not None:
            context_api.detach(self._token)
            self._token = None
        self._span.end()


class Tracer:
    def __init__(
        self,
        name: str,
        *,
        resource: Any | None = None,
        instrumentation_scope: Any | None = None,
        provider: TracerProvider | None = None,
    ) -> None:
        self.name = name
        self._resource = resource
        self._instrumentation_scope = instrumentation_scope
        self._provider = provider

    def start_span(
        self,
        name: str,
        *,
        context: SpanContext | None = None,
        parent: Span | None = None,
        kind: str = SpanKind.INTERNAL,
    ) -> Span:
        provider = self._provider or get_tracer_provider()
        processors: tuple[Any, ...] | None = None
        if isinstance(provider, TracerProvider):
            processors = tuple(provider._processors)

        span = Span(
            name,
            context=context,
            parent=parent,
            kind=kind,
            resource=self._resource,
            instrumentation_scope=self._instrumentation_scope,
            processors=processors,
        )
        if isinstance(provider, TracerProvider):
            for proc in provider._processors:
                with contextlib.suppress(Exception):
                    proc.on_start(span, None)
        return span

    def start_as_current_span(self, name: str, **kwargs: Any) -> _SpanContextManager:
        span = self.start_span(name, **kwargs)
        return _SpanContextManager(span)


class TracerProvider:
    def __init__(self, resource: Any | None = None) -> None:
        self._resource = resource
        self._processors: list[Any] = []

    def add_span_processor(self, processor: Any) -> None:
        self._processors.append(processor)

    def get_tracer(self, name: str, version: str | None = None, schema_url: str | None = None) -> Tracer:
        return Tracer(name, resource=self._resource, provider=self)

    def shutdown(self) -> None:  # pragma: no cover - stub
        for proc in self._processors:
            with contextlib.suppress(Exception):
                proc.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:  # pragma: no cover - stub
        ok = True
        for proc in self._processors:
            method = getattr(proc, "force_flush", None)
            if method is None:
                continue
            try:
                result = method(timeout_millis)
            except Exception:
                ok = False
                continue
            if result is False:
                ok = False
        return ok


class _NoOpSpanContextManager:
    def __init__(self, span: Span) -> None:
        self._span = span

    def __enter__(self) -> Span:
        return self._span

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _NoOpTracer(Tracer):
    def __init__(self) -> None:
        super().__init__("noop")

    def start_span(
        self,
        name: str,
        *,
        context: SpanContext | None = None,
        parent: Span | None = None,
        kind: str = SpanKind.INTERNAL,
    ) -> Span:
        return NonRecordingSpan(context=context or SpanContext())

    def start_as_current_span(self, name: str, **kwargs: Any) -> _NoOpSpanContextManager:
        return _NoOpSpanContextManager(self.start_span(name, **kwargs))


class NoOpTracerProvider:
    """Tracer provider that produces non-recording spans."""

    def get_tracer(self, name: str, version: str | None = None, schema_url: str | None = None) -> Tracer:
        return _NoOpTracer()

    def shutdown(self) -> None:  # pragma: no cover - stub
        return None

    def force_flush(self, timeout_millis: int = 30000) -> bool:  # pragma: no cover - stub
        return True


def get_tracer_provider() -> TracerProvider | None:
    return _GLOBAL_PROVIDER


def set_tracer_provider(provider: TracerProvider) -> None:
    global _GLOBAL_PROVIDER
    _GLOBAL_PROVIDER = provider


def get_tracer(name: str, version: str | None = None, schema_url: str | None = None) -> Tracer:
    provider = get_tracer_provider()
    if isinstance(provider, TracerProvider):
        return provider.get_tracer(name, version, schema_url)
    return Tracer(name)


def set_span_in_context(span: Span, context: context_api.Context | None = None) -> context_api.Context:
    return context_api.set_value(_CURRENT_SPAN_KEY, span, context)


def get_current_span(context: context_api.Context | None = None) -> Span:
    value = context_api.get_value(_CURRENT_SPAN_KEY, context)
    if isinstance(value, Span):
        return value
    return NonRecordingSpan()


def format_span_id(span_id: int) -> str:
    """Return the canonical hex representation of a span identifier."""

    return f"{span_id:016x}"


def format_trace_id(trace_id: int) -> str:
    """Return the canonical hex representation of a trace identifier."""

    return f"{trace_id:032x}"


__all__ = [
    "Event",
    "Link",
    "NoOpTracerProvider",
    "NonRecordingSpan",
    "ReadableSpan",
    "Span",
    "SpanContext",
    "SpanKind",
    "Status",
    "StatusCode",
    "TraceFlags",
    "Tracer",
    "TracerProvider",
    "format_span_id",
    "format_trace_id",
    "get_current_span",
    "get_tracer",
    "get_tracer_provider",
    "set_span_in_context",
    "set_tracer_provider",
]
