# Type stubs for opentelemetry.exporter.otlp
from typing import Any

class OTLPSpanExporter:
    """OTLP span exporter."""
    def __init__(
        self,
        endpoint: str | None = None,
        credentials: Any | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
        compression: str | None = None,
    ) -> None: ...
    def export(self, spans: Any) -> Any: ...
    def shutdown(self) -> None: ...

__all__ = ["OTLPSpanExporter"]
