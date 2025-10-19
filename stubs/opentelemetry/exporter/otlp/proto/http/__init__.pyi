# Type stubs for opentelemetry.exporter.otlp.proto.http
from typing import Any

def export_to_http(
    data: Any,
    endpoint: str,
    headers: dict[str, str] | None = None,
    timeout: int | None = None,
) -> Any: ...

__all__ = ["export_to_http"]
