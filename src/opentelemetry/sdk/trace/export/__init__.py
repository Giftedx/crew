from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Iterable


class SpanExportResult:
    """Stub for SpanExportResult."""

    SUCCESS = 0
    FAILURE = 1

    def __init__(self, status: int = 0):
        self.status = status


class SpanExporter:
    def export(self, spans: Iterable[Any]) -> None:  # pragma: no cover - base stub
        pass


class ConsoleSpanExporter(SpanExporter):  # pragma: no cover - simple stub
    def export(self, spans: Iterable[Any]) -> None:
        # No-op; could print if needed
        return None


class SimpleSpanProcessor:
    def __init__(self, exporter: SpanExporter) -> None:
        self.exporter = exporter

    # Our stubbed TracerProvider calls on_end on processors
    def on_end(self, span: Any) -> None:
        with contextlib.suppress(Exception):
            self.exporter.export([span])


class BatchSpanProcessor(SimpleSpanProcessor):
    """Batch span processor stub - same as SimpleSpanProcessor for testing"""


__all__ = [
    "BatchSpanProcessor",
    "ConsoleSpanExporter",
    "SimpleSpanProcessor",
    "SpanExportResult",
    "SpanExporter",
]
