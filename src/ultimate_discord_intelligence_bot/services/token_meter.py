"""Estimate token usage costs and enforce simple budgeting."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from platform.config.configuration import get_config

if TYPE_CHECKING:
    from platform.core.step_result import StepResult


@dataclass
class TokenMeter:
    """Token and cost estimation helper.

    The meter stores per-model pricing (USD per 1K tokens) and exposes helpers
    to estimate request costs.  It also enforces a per-request cost ceiling to
    guard against accidental overspend.
    """

    model_prices: dict[str, float] = field(default_factory=dict)
    max_cost_per_request: float | None = None

    def __post_init__(self) -> StepResult:
        if self.max_cost_per_request is None:
            config = get_config()
            self.max_cost_per_request = config.cost_max_per_request

    def estimate_cost(self, tokens: int, model: str, prices: dict[str, float] | None = None) -> StepResult:
        """Return the projected cost for ``tokens`` on ``model``.

        Pricing is expressed as USD per 1K tokens.  Unknown models default to
        zero cost which effectively bypasses budgeting.
        """
        price_map = prices or self.model_prices
        price = price_map.get(model, 0.0)
        return price * (tokens / 1000)

    def affordable_model(
        self, tokens: int, candidates: list[str], prices: dict[str, float] | None = None
    ) -> StepResult:
        """Return the cheapest candidate fitting within the request budget.

        Models are sorted by price; the first whose estimated cost is below the
        configured per-request ceiling is returned.  ``None`` indicates no
        candidate satisfies the constraint.
        """
        max_cost = self.max_cost_per_request or float("inf")
        price_map = prices or self.model_prices
        for model in sorted(candidates, key=lambda m: price_map.get(m, 0.0)):
            if self.estimate_cost(tokens, model, prices=price_map) <= max_cost:
                return model
        return None
