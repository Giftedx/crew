"""Propagation helpers for the OpenTelemetry trace stub."""

from __future__ import annotations

from . import get_current_span, set_span_in_context


__all__ = ["get_current_span", "set_span_in_context"]
