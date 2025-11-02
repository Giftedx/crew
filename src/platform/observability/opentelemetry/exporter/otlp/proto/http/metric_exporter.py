"""Stub for OpenTelemetry OTLP HTTP metric exporter."""


class OTLPMetricExporter:
    """No-op OTLP metric exporter stub."""

    def __init__(self, endpoint=None, headers=None, timeout=None, compression=None):
        """Initialize stub exporter."""

    def export(self, metrics_data):
        """No-op export."""
        return True

    def shutdown(self):
        """No-op shutdown."""

    def force_flush(self, timeout_millis=None):
        """No-op flush."""
        return True


__all__ = ["OTLPMetricExporter"]
