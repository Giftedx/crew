"""Minimal log SDK stubs for OpenTelemetry compatibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from opentelemetry._logs import Logger as _APILogger
from opentelemetry._logs import LoggerProvider as _APILoggerProvider
from opentelemetry._logs import LogRecord

from ..util.instrumentation import InstrumentationScope


@dataclass
class LogData:
    """Container bundling a log record with resource and scope metadata."""

    log_record: LogRecord
    resource: Any | None = None
    instrumentation_scope: InstrumentationScope | None = None


class LogRecordProcessor:
    """Base processor interface stub."""

    def on_emit(self, log_data: LogData) -> None:  # pragma: no cover - stub
        return None

    def shutdown(self) -> None:  # pragma: no cover - stub
        return None

    def force_flush(self, timeout_millis: int = 30000) -> bool:  # pragma: no cover - stub
        return True


class Logger(_APILogger):
    """Logger implementation that forwards records to registered processors."""

    def __init__(
        self,
        processors: list[LogRecordProcessor],
        resource: Any | None,
        instrumentation_scope: InstrumentationScope | None,
    ) -> None:
        self._processors = list(processors)
        self.resource = resource
        self.instrumentation_scope = instrumentation_scope

    def emit(self, record: LogRecord) -> None:  # pragma: no cover - stub behaviour
        resource = record.resource or self.resource
        if resource is not None:
            record.resource = resource

        scope = record.instrumentation_scope or self.instrumentation_scope
        if scope is not None:
            record.instrumentation_scope = scope

        log_data = LogData(
            log_record=record,
            resource=resource,
            instrumentation_scope=scope,
        )

        for processor in self._processors:
            processor.on_emit(log_data)


class LoggerProvider(_APILoggerProvider):
    """Minimal logger provider compatible with Logfire expectations."""

    def __init__(self, resource: Any | None = None):
        self._resource = resource
        self._processors: list[LogRecordProcessor] = []

    def get_logger(
        self,
        name: str,
        version: str | None = None,
        schema_url: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Logger:
        scope = InstrumentationScope(name, version, schema_url)
        logger = Logger(self._processors, self._resource, scope)
        if attributes:
            logger.attributes = dict(attributes)
        return logger

    def add_log_record_processor(self, processor: LogRecordProcessor) -> None:
        self._processors.append(processor)

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return all(processor.force_flush(timeout_millis) for processor in self._processors)

    def shutdown(self) -> None:
        for processor in self._processors:
            processor.shutdown()


__all__ = ["LogData", "LogRecord", "LogRecordProcessor", "Logger", "LoggerProvider"]
