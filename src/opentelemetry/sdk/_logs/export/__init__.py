"""Minimal log exporter stubs for OpenTelemetry."""

from __future__ import annotations

from .. import LogData, LogRecordProcessor


class LogExportResult:
    """Simple enumeration for log export outcomes."""

    SUCCESS = "success"
    FAILURE = "failure"


class LogExporter:
    """Base log exporter stub."""

    def export(self, batch: list[LogData]):  # pragma: no cover - stub
        return LogExportResult.SUCCESS

    def shutdown(self) -> None:  # pragma: no cover - stub
        return None


class InMemoryLogExporter(LogExporter):
    """Exporter that retains log data for inspection in tests."""

    def __init__(self) -> None:
        self._storage: list[LogData] = []

    def export(self, batch: list[LogData]):  # pragma: no cover - simple storage
        self._storage.extend(batch)
        return LogExportResult.SUCCESS

    def get_finished_logs(self) -> list[LogData]:  # pragma: no cover - helper
        return list(self._storage)

    def clear(self) -> None:  # pragma: no cover - helper
        self._storage.clear()

    def shutdown(self) -> None:  # pragma: no cover - stub behaviour
        self.clear()


class SimpleLogRecordProcessor(LogRecordProcessor):
    """Processor that immediately forwards records to an exporter."""

    def __init__(self, exporter: LogExporter):
        self._exporter = exporter

    def on_emit(self, log_data: LogData) -> None:  # pragma: no cover - stub behaviour
        self._exporter.export([log_data])

    def shutdown(self) -> None:  # pragma: no cover - stub behaviour
        self._exporter.shutdown()


class BatchLogRecordProcessor(LogRecordProcessor):
    """Simplified batch processor that exports each record individually."""

    def __init__(self, exporter: LogExporter):
        self._exporter = exporter

    def on_emit(self, log_data: LogData) -> None:  # pragma: no cover - stub behaviour
        self._exporter.export([log_data])

    def shutdown(self) -> None:  # pragma: no cover - stub behaviour
        self._exporter.shutdown()


__all__ = [
    "BatchLogRecordProcessor",
    "InMemoryLogExporter",
    "LogExportResult",
    "LogExporter",
    "SimpleLogRecordProcessor",
]
