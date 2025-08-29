"""Estimate token usage costs and enforce simple budgeting."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class TokenMeter:
    """Token and cost estimation helper.

    The meter stores per-model pricing (USD per 1K tokens) and exposes helpers
    to estimate request costs.  It also enforces a per-request cost ceiling to
    guard against accidental overspend.
    """

    model_prices: dict[str, float] = field(default_factory=dict)
    max_cost_per_request: float | None = None

    def __post_init__(self) -> None:
        if self.max_cost_per_request is None:
            env_val = os.getenv("COST_MAX_PER_REQUEST")
            self.max_cost_per_request = float(env_val) if env_val else float("inf")

    # ------------------------------------------------------------------
    def estimate_cost(self, tokens: int, model: str) -> float:
        """Return the projected cost for ``tokens`` on ``model``.

        Pricing is expressed as USD per 1K tokens.  Unknown models default to
        zero cost which effectively bypasses budgeting.
        """

        price = self.model_prices.get(model, 0.0)
        return price * (tokens / 1000)

    # ------------------------------------------------------------------
    def affordable_model(self, tokens: int, candidates: list[str]) -> str | None:
        """Return the cheapest candidate fitting within the request budget.

        Models are sorted by price; the first whose estimated cost is below the
        configured per-request ceiling is returned.  ``None`` indicates no
        candidate satisfies the constraint.
        """

        max_cost = self.max_cost_per_request or float("inf")
        for model in sorted(candidates, key=lambda m: self.model_prices.get(m, 0.0)):
            if self.estimate_cost(tokens, model) <= max_cost:
                return model
        return None
