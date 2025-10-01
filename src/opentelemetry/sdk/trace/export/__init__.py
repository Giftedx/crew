from __future__ import annotations

from collections.abc import Iterable
from typing import Any


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
        try:
            self.exporter.export([span])
        except Exception:
            pass


class BatchSpanProcessor(SimpleSpanProcessor):
    """Batch span processor stub - same as SimpleSpanProcessor for testing"""

    pass


__all__ = ["SpanExporter", "ConsoleSpanExporter", "SimpleSpanProcessor", "BatchSpanProcessor", "SpanExportResult"]
