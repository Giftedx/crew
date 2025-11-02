"""Tracing utilities with graceful degradation when `obs.tracing` is unavailable."""
from __future__ import annotations
from typing import Any
try:
    from platform.observability import tracing as _obs_tracing
    TRACING_AVAILABLE = True
    tracing_module: Any = _obs_tracing
except Exception:
    TRACING_AVAILABLE = False

    class _NoOpSpan:

        def __enter__(self) -> _NoOpSpan:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def set_attribute(self, _key: str, _value: object) -> None:
            return None

    class _NoOpTracing:

        def start_span(self, _name: str) -> _NoOpSpan:
            return _NoOpSpan()
    tracing_module = _NoOpTracing()
__all__ = ['TRACING_AVAILABLE', 'tracing_module']