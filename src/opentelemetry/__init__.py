"""Lightweight OpenTelemetry stub to support tests without external deps.

Provides minimal interfaces used by our code/tests:
- ``from opentelemetry import trace``
- ``from opentelemetry import metrics``
- ``from opentelemetry.sdk.resources import Resource``
- ``from opentelemetry.sdk.trace import TracerProvider``
- ``from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor, SpanExporter``
- ``from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter``
"""

from . import context, propagate, trace  # re-export submodules for compatibility


class _BaggageStub:
    """Stub for OpenTelemetry baggage."""

    @staticmethod
    def set_baggage(key: str, value: str) -> None:
        pass

    @staticmethod
    def get_baggage(key: str) -> str | None:
        return None

    @staticmethod
    def get_all_baggage() -> dict:
        return {}

    @staticmethod
    def get_all() -> dict:
        return {}


class _MetricsStub:
    """Stub for OpenTelemetry metrics."""

    @staticmethod
    def get_meter_provider():
        """Return a no-op meter provider."""
        return _MeterProviderStub()

    @staticmethod
    def set_meter_provider(provider):
        """No-op set meter provider."""

    @staticmethod
    def get_meter(name: str, version: str = "", schema_url: str = ""):
        """Return a no-op meter."""
        return _MeterStub()


class _MeterProviderStub:
    """Stub for meter provider."""

    def get_meter(self, name: str, version: str = "", schema_url: str = ""):
        """Return a no-op meter."""
        return _MeterStub()


class _MeterStub:
    """Stub for meter."""

    def create_counter(self, name: str, unit: str = "", description: str = ""):
        """Return a no-op counter."""
        return _InstrumentStub()

    def create_up_down_counter(self, name: str, unit: str = "", description: str = ""):
        """Return a no-op up/down counter."""
        return _InstrumentStub()

    def create_histogram(self, name: str, unit: str = "", description: str = ""):
        """Return a no-op histogram."""
        return _InstrumentStub()

    def create_observable_counter(self, name: str, callbacks=None, unit: str = "", description: str = ""):
        """Return a no-op observable counter."""
        return _InstrumentStub()

    def create_observable_up_down_counter(self, name: str, callbacks=None, unit: str = "", description: str = ""):
        """Return a no-op observable up/down counter."""
        return _InstrumentStub()

    def create_observable_gauge(self, name: str, callbacks=None, unit: str = "", description: str = ""):
        """Return a no-op observable gauge."""
        return _InstrumentStub()


class _InstrumentStub:
    """Stub for metric instruments."""

    def add(self, amount, attributes=None):
        """No-op add."""

    def record(self, amount, attributes=None):
        """No-op record."""


# Create instances
baggage = _BaggageStub()
metrics = _MetricsStub()

__all__ = ["baggage", "context", "metrics", "propagate", "trace"]
