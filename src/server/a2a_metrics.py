"""A2A adapter metrics helpers.

Provides small wrappers around obs.metrics to record counters and histograms
without importing the whole metrics surface into the router module.
"""

from __future__ import annotations

import contextlib


try:
    from ultimate_discord_intelligence_bot.obs.metrics import get_metrics

    _M = get_metrics()
except Exception:
    _M = None


def observe_tool_latency(tool: str, seconds: float, outcome: str) -> None:
    if _M is None:
        return
    with contextlib.suppress(Exception):
        _M.get_histogram("a2a_tool_latency_seconds", ["tool", "outcome"]).labels(tool, outcome).observe(seconds)


def inc_tool_runs(tool: str, outcome: str) -> None:
    if _M is None:
        return
    with contextlib.suppress(Exception):
        _M.get_counter("a2a_tool_runs_total", ["tool", "outcome"]).labels(tool, outcome).inc()


def observe_batch_size(n: int) -> None:
    if _M is None:
        return
    with contextlib.suppress(Exception):
        _M.get_histogram("a2a_jsonrpc_batch_size").observe(n)


def observe_request_latency(mode: str, seconds: float) -> None:
    if _M is None:
        return
    with contextlib.suppress(Exception):
        _M.get_histogram("a2a_jsonrpc_request_latency_seconds", ["mode"]).labels(mode).observe(seconds)


__all__ = ["inc_tool_runs", "observe_batch_size", "observe_request_latency", "observe_tool_latency"]
