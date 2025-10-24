"""Simple SLO evaluation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass
class SLO:
    """Represents a single service level objective."""

    metric: str
    threshold: float


class SLOEvaluator:
    """Evaluate metrics against SLO thresholds."""

    def __init__(self, slos: Iterable[SLO]) -> None:
        self.slos: list[SLO] = list(slos)

    def evaluate(self, values: dict[str, float]) -> dict[str, bool]:
        """Return a mapping of metric -> whether it met the SLO."""
        result: dict[str, bool] = {}
        for slo in self.slos:
            val = values.get(slo.metric, 0.0)
            result[slo.metric] = val <= slo.threshold
        return result


__all__ = ["SLO", "SLOEvaluator"]
