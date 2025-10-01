"""A2A adapter metrics helpers.

Provides small wrappers around obs.metrics to record counters and histograms
without importing the whole metrics surface into the router module.
"""

from __future__ import annotations

try:
    from obs.metrics import get_metrics  # type: ignore

    _M = get_metrics()
except Exception:  # pragma: no cover - optional dependency
    _M = None


def observe_tool_latency(tool: str, seconds: float, outcome: str) -> None:
    if _M is None:
        return
    try:
        _M.get_histogram("a2a_tool_latency_seconds", ["tool", "outcome"]).labels(tool, outcome).observe(seconds)
    except Exception:
        pass


def inc_tool_runs(tool: str, outcome: str) -> None:
    if _M is None:
        return
    try:
        _M.get_counter("a2a_tool_runs_total", ["tool", "outcome"]).labels(tool, outcome).inc()
    except Exception:
        pass


def observe_batch_size(n: int) -> None:
    if _M is None:
        return
    try:
        _M.get_histogram("a2a_jsonrpc_batch_size").observe(n)
    except Exception:
        pass


def observe_request_latency(mode: str, seconds: float) -> None:
    if _M is None:
        return
    try:
        _M.get_histogram("a2a_jsonrpc_request_latency_seconds", ["mode"]).labels(mode).observe(seconds)
    except Exception:
        pass


__all__ = [
    "observe_tool_latency",
    "inc_tool_runs",
    "observe_batch_size",
    "observe_request_latency",
]
