"""Stub OTLP HTTP log exporter."""

from __future__ import annotations

from typing import Any


class OTLPLogExporter:
    """No-op log exporter matching the OTLP interface."""

    def __init__(self, endpoint: str | None = None, headers: dict[str, str] | None = None, timeout: int | None = None):
        self.endpoint = endpoint
        self.headers = headers or {}
        self.timeout = timeout

    def export(self, batch: Any) -> bool:  # pragma: no cover - stub behaviour
        return True

    def shutdown(self) -> None:  # pragma: no cover - stub behaviour
        pass

    def force_flush(self, timeout_millis: int | None = None) -> bool:  # pragma: no cover - stub behaviour
        return True


__all__ = ["OTLPLogExporter"]
