"""Stub for OpenTelemetry SDK metrics."""


class MeterProvider:
    """No-op meter provider stub."""

    def __init__(self, resource=None, metric_readers=None, views=None):
        """Initialize stub meter provider."""

    def get_meter(self, name, version="", schema_url=""):
        """Return a no-op meter."""
        from opentelemetry import metrics

        return metrics.get_meter(name, version, schema_url)

    def shutdown(self, timeout_millis=30000):
        """No-op shutdown."""
        return True

    def force_flush(self, timeout_millis=30000):
        """No-op flush."""
        return True


class Counter:
    """No-op counter stub."""

    def add(self, amount, attributes=None):
        """No-op add."""


class UpDownCounter:
    """No-op up/down counter stub."""

    def add(self, amount, attributes=None):
        """No-op add."""


class Histogram:
    """No-op histogram stub."""

    def record(self, amount, attributes=None):
        """No-op record."""


class ObservableCounter:
    """No-op observable counter stub."""


class ObservableUpDownCounter:
    """No-op observable up/down counter stub."""


class ObservableGauge:
    """No-op observable gauge stub."""


__all__ = [
    "Counter",
    "Histogram",
    "MeterProvider",
    "ObservableCounter",
    "ObservableGauge",
    "ObservableUpDownCounter",
    "UpDownCounter",
]
