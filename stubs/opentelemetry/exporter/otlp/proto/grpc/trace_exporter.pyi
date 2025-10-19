# Type stubs for opentelemetry.exporter.otlp.proto.grpc.trace_exporter
from typing import Any

def export_spans(
    spans: Any,
    endpoint: str | None = None,
    credentials: Any | None = None,
    headers: dict[str, str] | None = None,
    timeout: int | None = None,
) -> Any: ...

__all__ = ["export_spans"]
