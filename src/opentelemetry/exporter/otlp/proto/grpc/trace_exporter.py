"""OpenTelemetry OTLP gRPC trace exporter stub."""

from typing import Any


class OTLPSpanExporter:
    """Stub OTLP span exporter for testing."""

    def __init__(self, *args, **kwargs):
        pass

    def export(self, spans: Any) -> Any:
        """No-op export method."""
        return None

    def shutdown(self) -> None:
        """No-op shutdown method."""
        pass


__all__ = ["OTLPSpanExporter"]
