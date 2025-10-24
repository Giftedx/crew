"""Stub for OpenTelemetry SDK metrics export."""


class MetricExporter:
    """Base no-op metric exporter stub."""

    def export(self, metrics_data):
        """No-op export."""
        return True

    def shutdown(self, timeout_millis=30000):
        """No-op shutdown."""

    def force_flush(self, timeout_millis=30000):
        """No-op flush."""
        return True


class ConsoleMetricExporter(MetricExporter):
    """No-op console metric exporter stub."""


class InMemoryMetricExporter(MetricExporter):
    """No-op in-memory metric exporter stub."""

    def __init__(self):
        """Initialize with empty storage."""
        self.metrics_data = []

    def export(self, metrics_data):
        """Store metrics data."""
        self.metrics_data.append(metrics_data)
        return True

    def get_finished_metrics(self):
        """Return collected metrics."""
        return self.metrics_data

    def clear(self):
        """Clear collected metrics."""
        self.metrics_data = []


class PeriodicExportingMetricReader:
    """No-op periodic exporting metric reader stub."""

    def __init__(
        self,
        exporter,
        export_interval_millis=60000,
        export_timeout_millis=30000,
    ):
        """Initialize stub reader."""
        self.exporter = exporter

    def shutdown(self, timeout_millis=30000):
        """No-op shutdown."""
        return True

    def force_flush(self, timeout_millis=30000):
        """No-op flush."""
        return True


__all__ = [
    "ConsoleMetricExporter",
    "InMemoryMetricExporter",
    "MetricExporter",
    "PeriodicExportingMetricReader",
]
