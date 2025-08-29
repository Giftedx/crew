"""OpenTelemetry tracing helpers (minimal, optional dependency).

If ``opentelemetry-sdk`` is not installed the public helpers degrade to no-ops
so the rest of the codebase does not need defensive import guards.
"""

from __future__ import annotations

import functools
import os
from collections.abc import Callable
from importlib import metadata

try:  # Optional dependency
    from opentelemetry import trace  # type: ignore
    from opentelemetry.sdk.resources import Resource  # type: ignore
    from opentelemetry.sdk.trace import TracerProvider  # type: ignore
    from opentelemetry.sdk.trace.export import (  # type: ignore
        ConsoleSpanExporter,
        SimpleSpanProcessor,
        SpanExporter,
    )
    try:  # OTLP exporter optional
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # type: ignore
            OTLPSpanExporter as _HttpOTLPSpanExporter,
        )
    except Exception:  # pragma: no cover
        _HttpOTLPSpanExporter = None  # type: ignore
    _OTEL_AVAILABLE = True
except Exception:  # pragma: no cover - fallback path
    _OTEL_AVAILABLE = False

    class _NoopSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def set_attribute(self, *_a, **_k):
            return None

    class _NoopTracer:
        def start_as_current_span(self, *_a, **_k):
            return _NoopSpan()

    class _API:
        def get_tracer_provider(self):
            return None

        def set_tracer_provider(self, _p):
            return None

        def get_tracer(self, _name):
            return _NoopTracer()

    trace = _API()  # type: ignore

    class SpanExporter:  # type: ignore
        pass

    class ConsoleSpanExporter(SpanExporter):  # type: ignore
        pass

    class SimpleSpanProcessor:  # type: ignore
        def __init__(self, *_a, **_k):
            pass

    class TracerProvider:  # type: ignore
        pass

    class Resource:  # type: ignore
        @staticmethod
        def create(_attrs):
            return None


def _auto_exporter() -> SpanExporter:
    if not _OTEL_AVAILABLE:
        return ConsoleSpanExporter()  # type: ignore
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return ConsoleSpanExporter()
    headers_env = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")
    header_dict = {}
    if headers_env:
        for part in headers_env.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                header_dict[k.strip()] = v.strip()
    if '_HttpOTLPSpanExporter' in globals() and globals().get('_HttpOTLPSpanExporter') is not None:  # type: ignore
        try:  # pragma: no cover
            return _HttpOTLPSpanExporter(endpoint=endpoint, headers=header_dict or None)  # type: ignore
        except Exception:
            return ConsoleSpanExporter()
    return ConsoleSpanExporter()


def init_tracing(service_name: str, exporter: SpanExporter | None = None) -> SpanExporter:
    """Initialise tracer provider if not already set.

    Returns the exporter in use (console or OTLP). Safe to call multiple times.
    """

    if not _OTEL_AVAILABLE:
        return ConsoleSpanExporter()  # type: ignore

    from opentelemetry.sdk.trace import TracerProvider as _TP  # type: ignore

    current = trace.get_tracer_provider()
    if isinstance(current, _TP):  # already configured
        if exporter is None:
            exporter = ConsoleSpanExporter()
        current.add_span_processor(SimpleSpanProcessor(exporter))
        return exporter

    if exporter is None:
        exporter = _auto_exporter()

    attrs = {"service.name": service_name}
    try:  # pragma: no cover
        attrs["service.version"] = metadata.version("ultimate_discord_intelligence_bot")
    except Exception:
        pass
    provider = TracerProvider(resource=Resource.create(attrs))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return exporter


def trace_call(span_name: str, **span_attrs: str) -> Callable:
    """Decorator to trace a function call (no-op if tracing unavailable)."""

    def decorator(func: Callable) -> Callable:
        tracer = trace.get_tracer(func.__module__)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:  # type: ignore[attr-defined]
                for k, v in span_attrs.items():
                    try:
                        span.set_attribute(k, v)  # type: ignore[attr-defined]
                    except Exception:
                        pass
                return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["init_tracing", "trace_call"]
