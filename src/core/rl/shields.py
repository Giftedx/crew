"""Safety and budget constraint checks."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass
class ShieldResult:
    """Result of a shield evaluation."""

    allowed: bool
    reason: str | None = None


def check(proposal: Mapping[str, float], constraints: Mapping[str, float]) -> ShieldResult:
    """Check basic budget and latency constraints for a proposal."""
    budget = constraints.get("budget", float("inf"))
    if proposal.get("cost_usd", 0.0) > budget:
        return ShieldResult(False, "budget_exceeded")
    latency_slo = constraints.get("latency_ms", float("inf"))
    if proposal.get("latency_ms", 0.0) > latency_slo:
        return ShieldResult(False, "latency_exceeded")
    return ShieldResult(True)
