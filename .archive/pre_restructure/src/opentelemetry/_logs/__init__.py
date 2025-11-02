"""Public logging API stubs for OpenTelemetry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any


class SeverityNumber(IntEnum):
    """Subset of OpenTelemetry severity numbers used by Logfire."""

    SEVERITY_NUMBER_UNSPECIFIED = 0
    SEVERITY_NUMBER_TRACE = 1
    SEVERITY_NUMBER_TRACE2 = 2
    SEVERITY_NUMBER_TRACE3 = 3
    SEVERITY_NUMBER_TRACE4 = 4
    SEVERITY_NUMBER_DEBUG = 5
    SEVERITY_NUMBER_DEBUG2 = 6
    SEVERITY_NUMBER_DEBUG3 = 7
    SEVERITY_NUMBER_DEBUG4 = 8
    SEVERITY_NUMBER_INFO = 9
    SEVERITY_NUMBER_INFO2 = 10
    SEVERITY_NUMBER_INFO3 = 11
    SEVERITY_NUMBER_INFO4 = 12
    SEVERITY_NUMBER_WARN = 13
    SEVERITY_NUMBER_WARN2 = 14
    SEVERITY_NUMBER_WARN3 = 15
    SEVERITY_NUMBER_WARN4 = 16
    SEVERITY_NUMBER_ERROR = 17
    SEVERITY_NUMBER_ERROR2 = 18
    SEVERITY_NUMBER_ERROR3 = 19
    SEVERITY_NUMBER_ERROR4 = 20
    SEVERITY_NUMBER_FATAL = 21
    SEVERITY_NUMBER_FATAL2 = 22
    SEVERITY_NUMBER_FATAL3 = 23
    SEVERITY_NUMBER_FATAL4 = 24


@dataclass
class LogRecord:
    """Represents a log record captured by OpenTelemetry."""

    body: Any | None = None
    attributes: dict[str, Any] | None = None
    severity_number: SeverityNumber | int | None = None
    severity_text: str | None = None
    timestamp: int | None = None
    observed_timestamp: int | None = None
    trace_id: int | None = None
    span_id: int | None = None
    trace_flags: int | None = None
    resource: Any | None = None
    instrumentation_scope: Any | None = None

    def __post_init__(self) -> None:  # pragma: no cover - simple coercion
        if isinstance(self.severity_number, int):
            try:
                self.severity_number = SeverityNumber(self.severity_number)
            except ValueError:
                self.severity_number = None


class Logger:
    """Interface for loggers able to emit :class:`LogRecord` objects."""

    def emit(self, record: LogRecord) -> None:  # pragma: no cover - interface stub
        raise NotImplementedError


class LoggerProvider:
    """Interface for accessing :class:`Logger` instances."""

    def get_logger(
        self,
        name: str,
        version: str | None = None,
        schema_url: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Logger:  # pragma: no cover - interface stub
        raise NotImplementedError

    def shutdown(self) -> None:  # pragma: no cover - interface stub
        return None

    def force_flush(self, timeout_millis: int = 30000) -> bool:  # pragma: no cover - interface stub
        return True


class NoOpLogger(Logger):
    """Logger implementation that discards all log records."""

    def emit(self, record: LogRecord) -> None:  # pragma: no cover - stub behaviour
        return None


class NoOpLoggerProvider(LoggerProvider):
    """Default provider used when logging is disabled."""

    def get_logger(
        self,
        name: str,
        version: str | None = None,
        schema_url: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Logger:
        return NoOpLogger()


_LOGGER_PROVIDER: LoggerProvider = NoOpLoggerProvider()


def get_logger_provider() -> LoggerProvider:
    """Return the globally configured logger provider."""

    return _LOGGER_PROVIDER


def set_logger_provider(provider: LoggerProvider) -> None:
    """Set the global logger provider."""

    global _LOGGER_PROVIDER
    _LOGGER_PROVIDER = provider


__all__ = [
    "LogRecord",
    "Logger",
    "LoggerProvider",
    "NoOpLogger",
    "NoOpLoggerProvider",
    "SeverityNumber",
    "get_logger_provider",
    "set_logger_provider",
]
