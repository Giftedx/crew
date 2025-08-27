"""OpenTelemetry tracing helpers."""
from __future__ import annotations

from typing import Callable, Optional
import functools

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
)


def init_tracing(service_name: str, exporter: Optional[SpanExporter] = None) -> SpanExporter:
    """Initialize a basic tracer provider.

    Parameters
    ----------
    service_name:
        Name reported in the ``service.name`` resource attribute.
    exporter:
        Optional ``SpanExporter``. If omitted, spans are printed to stdout via
        :class:`~opentelemetry.sdk.trace.export.ConsoleSpanExporter`.
    """

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    if exporter is None:
        exporter = ConsoleSpanExporter()
    processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    return exporter


def trace_call(span_name: str, **span_attrs: str) -> Callable:
    """Decorator to trace a function call.

    Examples
    --------
    >>> @trace_call("demo")
    ... def fn():
    ...     return "hi"
    >>> fn()
    'hi'
    """

    def decorator(func: Callable) -> Callable:
        tracer = trace.get_tracer(func.__module__)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                for k, v in span_attrs.items():
                    span.set_attribute(k, v)
                return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["init_tracing", "trace_call"]
