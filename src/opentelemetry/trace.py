from __future__ import annotations

from typing import Any

_GLOBAL_PROVIDER: TracerProvider | None = None


class Span:
    def __init__(self, name: str) -> None:
        self.name = name
        self.attributes: dict[str, Any] = {}

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value


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
                try:
                    proc.on_end(self._span)
                except Exception:
                    pass


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
