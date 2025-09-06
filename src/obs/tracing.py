"""OpenTelemetry tracing helpers (minimal, optional dependency).

If ``opentelemetry-sdk`` is not installed the public helpers degrade to no-ops
so the rest of the codebase does not need defensive import guards.
"""

from __future__ import annotations

import functools
import logging
import os
from collections.abc import Callable
from importlib import metadata
from typing import Any, ParamSpec, Protocol, TypeVar, cast, runtime_checkable


@runtime_checkable
class _SpanLike(Protocol):
    def __enter__(self) -> _SpanLike: ...
    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool: ...
    def set_attribute(self, key: str, value: Any) -> Any: ...


@runtime_checkable
class _TracerLike(Protocol):
    def start_as_current_span(self, name: str) -> _SpanLike: ...


@runtime_checkable
class _TraceAPI(Protocol):
    def get_tracer_provider(self) -> Any: ...
    def set_tracer_provider(self, provider: Any) -> Any: ...
    def get_tracer(self, name: str) -> _TracerLike: ...


_OTEL_AVAILABLE = False
try:  # Optional dependency (runtime)
    from opentelemetry import trace as _otel_trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        ConsoleSpanExporter,
        SimpleSpanProcessor,
        SpanExporter,
    )

    try:  # OTLP exporter optional
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter as _HttpOTLPSpanExporter,
        )
    except Exception:  # pragma: no cover
        _HttpOTLPSpanExporter = None
    _OTEL_AVAILABLE = True
except Exception:  # pragma: no cover - dependency missing
    _otel_trace = None  # type: ignore[assignment]
    _HttpOTLPSpanExporter = None

    class _FallbackSpanExporter:  # fallback minimal stubs
        pass

    class _FallbackConsoleSpanExporter(_FallbackSpanExporter):
        pass

    class _FallbackSimpleSpanProcessor:  # noqa: D401 - minimal
        def __init__(self, *_a, **_k):
            pass

    class _FallbackTracerProvider:  # noqa: D401 - minimal
        pass

    class _FallbackResource:  # noqa: D401 - minimal
        @staticmethod
        def create(_attrs: dict[str, Any]):
            return None

    # Map public names to fallbacks for downstream references
    SpanExporter = _FallbackSpanExporter  # type: ignore
    ConsoleSpanExporter = _FallbackConsoleSpanExporter  # type: ignore
    SimpleSpanProcessor = _FallbackSimpleSpanProcessor  # type: ignore
    TracerProvider = _FallbackTracerProvider  # type: ignore
    Resource = _FallbackResource  # type: ignore


class _NoopSpan:
    def __enter__(self) -> _NoopSpan:  # pragma: no cover - trivial
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:  # pragma: no cover
        # Returning None is equivalent to False (do not suppress exceptions)
        return None

    def set_attribute(self, *_a: Any, **_k: Any) -> None:  # noqa: D401 - simple noop
        return None


class _NoopTracer:
    def start_as_current_span(self, *_a: Any, **_k: Any) -> _NoopSpan:  # noqa: D401 - simple noop
        return _NoopSpan()


class _NoopTraceAPI:
    def get_tracer_provider(self) -> None:  # noqa: D401 - simple noop
        return None

    def set_tracer_provider(self, _p: object) -> None:  # noqa: D401 - simple noop
        return None

    def get_tracer(self, _name: str) -> _NoopTracer:  # noqa: D401 - simple noop
        return _NoopTracer()


trace: _TraceAPI | _NoopTraceAPI = (
    cast(_TraceAPI, _otel_trace) if _OTEL_AVAILABLE and _otel_trace is not None else _NoopTraceAPI()
)


def _auto_exporter() -> Any:
    if not _OTEL_AVAILABLE:
        return ConsoleSpanExporter()
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
    if (
        "_HttpOTLPSpanExporter" in globals()
        and globals().get("_HttpOTLPSpanExporter") is not None
        and callable(globals().get("_HttpOTLPSpanExporter"))
    ):
        try:  # pragma: no cover
            return globals()["_HttpOTLPSpanExporter"](endpoint=endpoint, headers=header_dict or None)
        except Exception:  # pragma: no cover
            return ConsoleSpanExporter()
    return ConsoleSpanExporter()


def init_tracing(service_name: str, exporter: Any | None = None) -> Any:
    """Initialise tracer provider if not already set.

    Returns the exporter in use (console or OTLP). Safe to call multiple times.
    """

    if not _OTEL_AVAILABLE:
        return ConsoleSpanExporter()

    current = trace.get_tracer_provider()
    if _OTEL_AVAILABLE and isinstance(current, TracerProvider):  # already configured
        if exporter is None:
            exporter = ConsoleSpanExporter()
        try:
            current.add_span_processor(SimpleSpanProcessor(exporter))  # pragma: no cover - depends on otel
        except Exception:  # pragma: no cover
            return exporter
        return exporter

    if exporter is None:
        exporter = _auto_exporter()

    attrs = {"service.name": service_name}
    try:  # pragma: no cover
        attrs["service.version"] = metadata.version("ultimate_discord_intelligence_bot")
    except Exception as exc:  # pragma: no cover
        logging.debug("version lookup failed: %s", exc)
    provider = TracerProvider(resource=Resource.create(attrs))
    try:  # pragma: no cover
        provider.add_span_processor(SimpleSpanProcessor(exporter))  # pragma: no cover
    except Exception as exc:  # pragma: no cover
        logging.debug("add_span_processor failed: %s", exc)
    try:  # pragma: no cover
        trace.set_tracer_provider(provider)  # pragma: no cover
    except Exception as exc:  # pragma: no cover
        logging.debug("set_tracer_provider failed: %s", exc)
    return exporter


P = ParamSpec("P")
R = TypeVar("R")


def trace_call(span_name: str, **span_attrs: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to trace a function call (no-op if tracing unavailable)."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        tracer = trace.get_tracer(func.__module__)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with tracer.start_as_current_span(span_name) as span:
                # Attribute setting separated to avoid try/except in the hot loop; validate first.
                if hasattr(span, "set_attribute"):
                    for k, v in span_attrs.items():
                        span.set_attribute(k, v)
                result = func(*args, **kwargs)
            return result

        return wrapper

    return decorator


__all__ = ["init_tracing", "trace_call"]


def start_span(name: str) -> _SpanLike:  # pragma: no cover - thin helper for tests
    """Compatibility helper used in tests: return an active span context manager.

    This mirrors the prior interface expected by call sites that do:
        with tracing.start_span("span_name") as span:
            ...
    """
    tracer = trace.get_tracer(__name__)
    return tracer.start_as_current_span(name)  # type: ignore[return-value]
