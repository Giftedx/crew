"""Compatibility shim for obs.tracing imports.

Re-exports from platform.observability.tracing for backward compatibility.
"""

from platform.observability.tracing import init_tracing, trace_call


__all__ = ["init_tracing", "trace_call"]
