# Type stubs for opentelemetry.exporter
from typing import Any

class SpanExporter:
    """Base span exporter interface."""
    def export(self, spans: Any) -> Any: ...
    def shutdown(self) -> None: ...

__all__ = ["SpanExporter"]
