"""Simple token and cost estimator.

The estimator uses a rough heuristic of four characters per token when the
specific tokenizer for a provider is unavailable. Costs are derived from
provider-specific per-token pricing so that downstream reinforcement learning
can reason about expenses.
"""

from __future__ import annotations

import math
import os
from contextlib import contextmanager
from dataclasses import dataclass

from ultimate_discord_intelligence_bot.tenancy import TenantContext, current_tenant
from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry

# Rough per-token costs in USD for demonstration purposes.
MODEL_PRICES: dict[str, float] = {
    "gpt-3.5": 0.002 / 1000,
    "gpt-4": 0.03 / 1000,
}


class BudgetError(RuntimeError):
    """Raised when a request would exceed the configured budget."""


@dataclass
class BudgetManager:
    """Tracks spend against simple in-memory budgets."""

    max_per_request: float = float(os.getenv("COST_MAX_PER_REQUEST", "1.0"))
    daily_budget: float = float(os.getenv("COST_BUDGET_DAILY", "100.0"))
    spent_today: float = 0.0

    def preflight(self, cost_usd: float) -> None:
        if cost_usd > self.max_per_request or self.spent_today + cost_usd > self.daily_budget:
            raise BudgetError("budget_exceeded")

    def charge(self, cost_usd: float) -> None:
        self.spent_today += cost_usd


class BudgetStore:
    """Per-tenant budgets resolved via :class:`TenantRegistry`."""

    def __init__(self, registry: TenantRegistry | None = None) -> None:
        self.registry = registry
        self._budgets: dict[str, BudgetManager] = {}

    def _get(self) -> BudgetManager:
        ctx = current_tenant() or TenantContext("default", "main")
        key = ctx.tenant_id
        if key not in self._budgets:
            max_req = float(os.getenv("COST_MAX_PER_REQUEST", "1.0"))
            daily = float(os.getenv("COST_BUDGET_DAILY", "100.0"))
            if self.registry:
                cfg = self.registry.get_budget_config(key)
                if cfg:
                    max_req = float(cfg.get("max_per_request", max_req))
                    daily = float(cfg.get("daily_cap_usd", daily))
            self._budgets[key] = BudgetManager(max_per_request=max_req, daily_budget=daily)
        return self._budgets[key]

    def preflight(self, cost_usd: float) -> None:
        self._get().preflight(cost_usd)

    def charge(self, cost_usd: float) -> None:
        self._get().charge(cost_usd)

    # expose attributes for tests
    @property
    def max_per_request(self) -> float:
        return self._get().max_per_request

    @max_per_request.setter
    def max_per_request(self, value: float) -> None:
        self._get().max_per_request = value

    @property
    def daily_budget(self) -> float:
        return self._get().daily_budget

    @daily_budget.setter
    def daily_budget(self, value: float) -> None:
        self._get().daily_budget = value


budget = BudgetStore()


def estimate_tokens(text: str) -> int:
    """Estimate token count using a simple character heuristic."""
    return math.ceil(len(text) / 4)


@dataclass
class TokenCost:
    tokens: int
    cost_usd: float


def measure(text: str, model: str) -> TokenCost:
    """Return token and cost estimates for ``text`` under ``model``."""
    tokens = estimate_tokens(text)
    price = MODEL_PRICES.get(model, 0.0)
    return TokenCost(tokens=tokens, cost_usd=tokens * price)


def estimate(tokens_in: int, tokens_out: int, model: str) -> float:
    """Estimate USD cost for a call with ``tokens_in`` and ``tokens_out``."""
    price = MODEL_PRICES.get(model, 0.0)
    return (tokens_in + tokens_out) * price


@contextmanager
def cost_guard(tokens_in: int, tokens_out: int, model: str):
    """Context manager enforcing request and daily budgets."""

    cost = estimate(tokens_in, tokens_out, model)
    budget.preflight(cost)
    try:
        yield cost
    finally:
        budget.charge(cost)


__all__ = [
    "TokenCost",
    "measure",
    "estimate_tokens",
    "estimate",
    "cost_guard",
    "BudgetError",
    "budget",
]
