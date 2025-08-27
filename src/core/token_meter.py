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
from typing import Dict

# Rough per-token costs in USD for demonstration purposes.
MODEL_PRICES: Dict[str, float] = {
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


budget = BudgetManager()


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
