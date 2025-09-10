"""Lightweight OpenTelemetry stub to support tests without external deps.

Provides minimal interfaces used by our code/tests:
- ``from opentelemetry import trace``
- ``from opentelemetry.sdk.resources import Resource``
- ``from opentelemetry.sdk.trace import TracerProvider``
- ``from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor, SpanExporter``
- ``from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter``
"""

from . import trace  # re-export submodule for ``from opentelemetry import trace``

__all__ = ["trace"]
