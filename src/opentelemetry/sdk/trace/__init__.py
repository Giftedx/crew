from __future__ import annotations

from ...trace import TracerProvider as BaseTracerProvider
from ..resources import Resource


class TracerProvider(BaseTracerProvider):
    """Enhanced TracerProvider stub for SDK compatibility."""

    def __init__(self, resource: Resource | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource = resource or Resource.create({})

    def get_tracer(self, name: str, version: str | None = None, schema_url: str | None = None):
        from ...trace import get_tracer

        return get_tracer(name, version, schema_url)


class Tracer:
    """Stub Tracer class."""

    def start_span(self, name: str, **kwargs):
        from ...trace import Span

        return Span()

    def start_as_current_span(self, name: str, **kwargs):
        from ...trace import Span

        return Span()


__all__ = ["Resource", "Tracer", "TracerProvider"]
