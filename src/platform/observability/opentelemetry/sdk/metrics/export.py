"""Stub for OpenTelemetry SDK metrics export."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


class AggregationTemporality:
    """Enumeration placeholder for aggregation temporality."""

    UNSPECIFIED = "unspecified"
    DELTA = "delta"
    CUMULATIVE = "cumulative"


class MetricExportResult:
    """Simple export result enumeration."""

    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class MetricsData:
    """Container object representing exported metrics."""

    resource_metrics: list[Any] = field(default_factory=list)

    def to_json(self) -> str:  # pragma: no cover - helper for tests
        return json.dumps({"resource_metrics": self.resource_metrics})


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


class MetricReader:
    """Base metric reader stub."""

    def __init__(self, exporter: MetricExporter | None = None):
        self.exporter = exporter
        self._metrics: list[MetricsData] = []

    def shutdown(self, timeout_millis=30000):  # pragma: no cover - stub behaviour
        return True

    def force_flush(self, timeout_millis=30000):  # pragma: no cover - stub behaviour
        return True

    def _store(self, metrics_data: MetricsData) -> None:
        self._metrics.append(metrics_data)


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


class InMemoryMetricReader(MetricReader):
    """Metric reader that retains metric data in memory for inspection."""

    def __init__(self, preferred_temporality: dict[str, Any] | None = None):
        super().__init__(exporter=None)
        self.preferred_temporality = preferred_temporality or {}

    def get_metrics_data(self) -> MetricsData | None:
        return self._metrics[-1] if self._metrics else None

    def clear(self) -> None:
        self._metrics.clear()

    def consume(self, metrics_data: MetricsData) -> None:
        self._store(metrics_data)


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
    "AggregationTemporality",
    "ConsoleMetricExporter",
    "InMemoryMetricExporter",
    "InMemoryMetricReader",
    "MetricExportResult",
    "MetricExporter",
    "MetricReader",
    "MetricsData",
    "PeriodicExportingMetricReader",
]
