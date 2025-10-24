from __future__ import annotations

import contextlib
from typing import Any


_GLOBAL_PROVIDER: TracerProvider | None = None


class Status:
    """Status for spans."""

    def __init__(self, status_code: StatusCode, description: str = ""):
        self.status_code = status_code
        self.description = description


class StatusCode:
    """Status codes for spans."""

    UNSET = 0
    OK = 1
    ERROR = 2


class Span:
    def __init__(self, name: str) -> None:
        self.name = name
        self.attributes: dict[str, Any] = {}

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def set_status(self, status: Status) -> None:
        self.status = status


class _SpanContext:
    def __init__(self, tracer: Tracer, span: Span) -> None:
        self._tracer = tracer
        self._span = span

    def __enter__(self) -> Span:
        return self._span

    def __exit__(self, exc_type, exc, tb) -> None:
        # Notify provider that the span ended
        prov = get_tracer_provider()
        if isinstance(prov, TracerProvider):
            for proc in prov._processors:
                with contextlib.suppress(Exception):
                    proc.on_end(self._span)


class Tracer:
    def __init__(self, name: str) -> None:
        self.name = name

    def start_as_current_span(self, name: str) -> _SpanContext:
        return _SpanContext(self, Span(name))


class TracerProvider:
    def __init__(self, resource: Any | None = None) -> None:
        self._resource = resource
        self._processors: list[Any] = []

    def add_span_processor(self, processor: Any) -> None:
        self._processors.append(processor)


def get_tracer_provider() -> TracerProvider | None:
    return _GLOBAL_PROVIDER


def set_tracer_provider(provider: TracerProvider) -> None:
    global _GLOBAL_PROVIDER
    _GLOBAL_PROVIDER = provider


def get_tracer(name: str) -> Tracer:
    return Tracer(name)
