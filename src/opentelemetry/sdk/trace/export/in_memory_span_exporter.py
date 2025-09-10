from __future__ import annotations

from typing import Any

from . import SpanExporter


class InMemorySpanExporter(SpanExporter):
    def __init__(self) -> None:
        self._spans: list[Any] = []

    def export(self, spans):
        try:
            self._spans.extend(list(spans))
        except Exception:
            pass

    def get_finished_spans(self) -> list[Any]:
        return list(self._spans)

    def clear(self) -> None:
        self._spans.clear()


__all__ = ["InMemorySpanExporter"]
