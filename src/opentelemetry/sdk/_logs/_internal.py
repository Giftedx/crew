"""Internal helpers for OpenTelemetry log processors."""

from __future__ import annotations

from . import LogData, LogRecordProcessor


class SynchronousMultiLogRecordProcessor(LogRecordProcessor):
    """Fan-out processor that forwards records to multiple processors."""

    def __init__(self, processors: list[LogRecordProcessor] | None = None):
        self._processors: list[LogRecordProcessor] = list(processors or [])

    def add_log_record_processor(self, processor: LogRecordProcessor) -> None:
        self._processors.append(processor)

    def on_emit(self, log_data: LogData) -> None:  # pragma: no cover - stub behaviour
        for processor in self._processors:
            processor.on_emit(log_data)

    def shutdown(self) -> None:  # pragma: no cover - stub behaviour
        for processor in self._processors:
            processor.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:  # pragma: no cover - stub behaviour
        return all(processor.force_flush(timeout_millis) for processor in self._processors)


__all__ = ["SynchronousMultiLogRecordProcessor"]
