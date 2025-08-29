"""Feature extraction and simple sliding window statistics."""

from __future__ import annotations

from collections import deque
from statistics import mean
from typing import Any

FeatureVector = dict[str, float]

# Keep short sliding windows of recent outcomes to expose running averages.
_cost_usd_history: deque[float] = deque(maxlen=100)
_latency_history: deque[float] = deque(maxlen=100)


def featurize(call_ctx: dict[str, Any]) -> FeatureVector:
    """Convert a call context dictionary into a numeric feature vector.

    Parameters
    ----------
    call_ctx:
        Mapping containing metadata about the current call.

    Returns
    -------
    FeatureVector
        Numeric features for policy consumption.
    """
    features: FeatureVector = {
        "input_tokens": float(call_ctx.get("input_tokens", 0)),
        "output_tokens": float(call_ctx.get("output_tokens", 0)),
        "avg_cost_usd": mean(_cost_usd_history) if _cost_usd_history else 0.0,
        "avg_latency_ms": mean(_latency_history) if _latency_history else 0.0,
    }
    return features


def update_stats(outcome: dict[str, Any]) -> None:
    """Update sliding window statistics from a call outcome."""
    _cost_usd_history.append(float(outcome.get("cost_usd", 0.0)))
    _latency_history.append(float(outcome.get("latency_ms", 0.0)))
