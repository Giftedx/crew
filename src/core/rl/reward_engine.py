"""Reward computation utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, MutableMapping, Optional


@dataclass
class RewardBreakdown:
    """Container for the components of the reward signal with weights."""

    quality: float = 0.0
    groundedness: float = 0.0
    cost: float = 0.0
    latency: float = 0.0
    safety: float = 0.0
    privacy: float = 0.0

    # Weights for each component. Defaults match the composite reward
    # formulation ``Quality + Groundedness - Cost - Latency - Safety - Privacy``.
    w_q: float = 1.0
    w_g: float = 1.0
    w_c: float = 1.0
    w_l: float = 1.0
    w_s: float = 1.0
    w_p: float = 1.0

    @property
    def total(self) -> float:
        """Return the weighted composite scalar reward."""
        return (
            self.w_q * self.quality
            + self.w_g * self.groundedness
            - self.w_c * self.cost
            - self.w_l * self.latency
            - self.w_s * self.safety
            - self.w_p * self.privacy
        )


def compute_reward(
    outcome: Mapping[str, Any],
    signals: Mapping[str, Any],
    weights: Optional[MutableMapping[str, float]] = None,
) -> RewardBreakdown:
    """Compute reward components from logged signals.

    Parameters
    ----------
    outcome:
        Mapping of system metrics such as cost and latency.
    signals:
        Quality and safety related measurements.
    weights:
        Optional mapping of weight overrides keyed by component name
        (``quality``, ``groundedness``, ``cost``, ``latency``, ``safety``,
        ``privacy``).
    """

    w = {
        "quality": 1.0,
        "groundedness": 1.0,
        "cost": 1.0,
        "latency": 1.0,
        "safety": 1.0,
        "privacy": 1.0,
    }
    if weights:
        w.update(weights)

    return RewardBreakdown(
        quality=float(signals.get("quality", 0.0)),
        groundedness=float(signals.get("groundedness", 0.0)),
        cost=float(outcome.get("cost_usd", 0.0)),
        latency=float(outcome.get("latency_ms", 0.0)),
        safety=float(signals.get("safety_penalty", 0.0)),
        privacy=float(signals.get("privacy_penalty", 0.0)),
        w_q=float(w["quality"]),
        w_g=float(w["groundedness"]),
        w_c=float(w["cost"]),
        w_l=float(w["latency"]),
        w_s=float(w["safety"]),
        w_p=float(w["privacy"]),
    )


def attribute_reward(decisions: Mapping[str, Any], breakdown: RewardBreakdown) -> Dict[str, float]:
    """Naively attribute the total reward equally across decisions."""
    if not decisions:
        return {}
    share = breakdown.total / len(decisions)
    return {action_id: share for action_id in decisions}
