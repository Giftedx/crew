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

    def force_flush(self, timeout_millis: int = 30000) -> bool:  # pragma: no cover - simple
        return True

    def shutdown(self) -> None:  # pragma: no cover - simple stub
        with contextlib.suppress(Exception):
            shutdown = getattr(self.exporter, "shutdown", None)
            if callable(shutdown):
                shutdown()


class BatchSpanProcessor(SimpleSpanProcessor):
    """Batch span processor stub - accumulates spans until flushed."""

    def __init__(self, exporter: SpanExporter) -> None:
        super().__init__(exporter)
        self._pending: list[Any] = []

    def on_end(self, span: Any) -> None:
        self._pending.append(span)

    def _drain(self) -> bool:
        if not self._pending:
            return True

        spans = list(self._pending)
        self._pending.clear()
        try:
            result = self.exporter.export(spans)
        except Exception:
            # restore pending spans so a later flush still has data
            self._pending[:0] = spans
            return False

        if isinstance(result, SpanExportResult):
            return result.status != SpanExportResult.FAILURE
        return result is not False

    def force_flush(self, timeout_millis: int = 30000) -> bool:  # pragma: no cover - simple
        return self._drain()

    def shutdown(self) -> None:  # pragma: no cover - simple stub
        try:
            self._drain()
        finally:
            super().shutdown()


__all__ = [
    "BatchSpanProcessor",
    "ConsoleSpanExporter",
    "SimpleSpanProcessor",
    "SpanExportResult",
    "SpanExporter",
]
