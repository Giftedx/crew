# Type stubs for opentelemetry
# This provides type hints for the OpenTelemetry library
# to reduce MyPy errors related to missing type information

from typing import Any

class Tracer:
    def start_as_current_span(self, name: str, **kwargs: Any) -> Any: ...

class TracerProvider:
    def get_tracer(self, name: str, version: str | None = None) -> Tracer: ...

def get_tracer_provider() -> TracerProvider: ...
def set_tracer_provider(provider: TracerProvider) -> None: ...

__all__ = ["Tracer", "TracerProvider", "get_tracer_provider", "set_tracer_provider"]
