"""Legacy metrics constants facade.

Tests and example scripts import metric families from `obs.metrics` and then use
Prometheus-like calls such as `FOO_COUNT.labels(...).inc()` or
`FOO_LATENCY.labels(...).observe(value)`.

This module provides lightweight shims backed by the project's metrics facade
(`ultimate_discord_intelligence_bot.obs.metrics.get_metrics`). The shims are
safe no-ops if the underlying exporter is not configured.
"""

from __future__ import annotations

from typing import Any

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics as _get_metrics


class _LabeledMetric:
    def __init__(self, name: str, kind: str, labels: dict[str, Any]) -> None:
        self._name = name
        self._kind = kind  # "counter" | "histogram" | "gauge"
        self._labels = labels

    # Prometheus Counter-like
    def inc(self, amount: float = 1.0) -> None:
        if self._kind == "counter" or self._kind == "gauge":
            # Use counter/gauge facade which already returns a labeled metric
            if self._kind == "counter":
                _get_metrics().counter(self._name, labels=self._labels).inc(amount)
            else:
                _get_metrics().gauge(self._name, labels=self._labels).add(amount)
        else:
            # Histograms don't support inc; ignore
            return None

    # Prometheus Gauge-like convenience
    def set(self, value: float) -> None:
        _get_metrics().gauge(self._name, labels=self._labels).set(value)

    # Prometheus Histogram-like
    def observe(self, value: float) -> None:
        if self._kind == "histogram":
            _get_metrics().histogram(self._name, value, labels=self._labels)
        else:
            # Non-histograms ignore observe
            return None


class _MetricFamily:
    def __init__(self, name: str, kind: str, label_names: tuple[str, ...] | None = None) -> None:
        self._name = name
        self._kind = kind
        self._label_names = tuple(label_names or ())

    def labels(self, *args: Any, **kwargs: Any) -> _LabeledMetric:
        if args and kwargs:
            # Mixed usage is ambiguous; prefer kwargs and append the rest as _n
            for idx, v in enumerate(args):
                kwargs[f"_{idx}"] = v
        elif args and not kwargs:
            kwargs = dict(zip(self._label_names, args, strict=False))
        # Pass through as-is (facade validates downstream)
        return _LabeledMetric(self._name, self._kind, dict(kwargs))


# Define metric families used across tests/scripts
# Heuristic: *_LATENCY are histograms, *_COUNT and *_ERROR_COUNT are counters

# Content ingestion
CONTENT_INGESTION_COUNT = _MetricFamily(
    "content_ingestion_count", kind="counter", label_names=("platform", "content_type")
)
CONTENT_INGESTION_ERROR_COUNT = _MetricFamily(
    "content_ingestion_error_count", kind="counter", label_names=("platform", "content_type")
)
CONTENT_INGESTION_LATENCY = _MetricFamily(
    "content_ingestion_latency_seconds", kind="histogram", label_names=("platform", "content_type")
)

# Content analysis
CONTENT_ANALYSIS_COUNT = _MetricFamily("content_analysis_count", kind="counter", label_names=("analysis_type",))
CONTENT_ANALYSIS_ERROR_COUNT = _MetricFamily(
    "content_analysis_error_count", kind="counter", label_names=("analysis_type",)
)
CONTENT_ANALYSIS_LATENCY = _MetricFamily(
    "content_analysis_latency_seconds", kind="histogram", label_names=("analysis_type",)
)

# Discord messaging
DISCORD_MESSAGE_COUNT = _MetricFamily("discord_message_count", kind="counter", label_names=("message_type",))
DISCORD_MESSAGE_ERROR_COUNT = _MetricFamily(
    "discord_message_error_count", kind="counter", label_names=("message_type",)
)
DISCORD_MESSAGE_LATENCY = _MetricFamily(
    "discord_message_latency_seconds", kind="histogram", label_names=("message_type",)
)

# Model routing
MODEL_ROUTING_COUNT = _MetricFamily("model_routing_count", kind="counter", label_names=("model",))
MODEL_ROUTING_LATENCY = _MetricFamily("model_routing_latency_seconds", kind="histogram", label_names=("model",))

# Generic request metrics
REQUEST_COUNT = _MetricFamily("http_request_total", kind="counter", label_names=("method", "endpoint"))
REQUEST_LATENCY = _MetricFamily("http_request_latency_seconds", kind="histogram", label_names=("method", "endpoint"))
ERROR_COUNT = _MetricFamily(
    "http_request_errors_total", kind="counter", label_names=("method", "endpoint", "error_type")
)

# Memory operations
MEMORY_STORE_COUNT = _MetricFamily("memory_store_count", kind="counter", label_names=("store_type",))
MEMORY_RETRIEVAL_COUNT = _MetricFamily("memory_retrieval_count", kind="counter", label_names=("store_type",))
MEMORY_STORE_LATENCY = _MetricFamily("memory_store_latency_seconds", kind="histogram", label_names=("store_type",))
MEMORY_RETRIEVAL_LATENCY = _MetricFamily(
    "memory_retrieval_latency_seconds", kind="histogram", label_names=("store_type",)
)

# MCP tool calls
MCP_TOOL_CALL_COUNT = _MetricFamily("mcp_tool_call_count", kind="counter", label_names=("tool_name",))
MCP_TOOL_CALL_ERROR_COUNT = _MetricFamily("mcp_tool_call_error_count", kind="counter", label_names=("tool_name",))
MCP_TOOL_CALL_LATENCY = _MetricFamily("mcp_tool_call_latency_seconds", kind="histogram", label_names=("tool_name",))

__all__ = [
    "CONTENT_ANALYSIS_COUNT",
    "CONTENT_ANALYSIS_ERROR_COUNT",
    "CONTENT_ANALYSIS_LATENCY",
    "CONTENT_INGESTION_COUNT",
    "CONTENT_INGESTION_ERROR_COUNT",
    "CONTENT_INGESTION_LATENCY",
    "DISCORD_MESSAGE_COUNT",
    "DISCORD_MESSAGE_ERROR_COUNT",
    "DISCORD_MESSAGE_LATENCY",
    "ERROR_COUNT",
    "MCP_TOOL_CALL_COUNT",
    "MCP_TOOL_CALL_ERROR_COUNT",
    "MCP_TOOL_CALL_LATENCY",
    "MEMORY_RETRIEVAL_COUNT",
    "MEMORY_RETRIEVAL_LATENCY",
    "MEMORY_STORE_COUNT",
    "MEMORY_STORE_LATENCY",
    "MODEL_ROUTING_COUNT",
    "MODEL_ROUTING_LATENCY",
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
]
