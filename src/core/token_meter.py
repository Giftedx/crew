"""Simple token and cost estimator.

The estimator uses a rough heuristic of four characters per token when the
specific tokenizer for a provider is unavailable. Costs are derived from
provider-specific per-token pricing so that downstream reinforcement learning
can reason about expenses.
"""

from __future__ import annotations

import math
from contextlib import contextmanager
from dataclasses import dataclass

from ultimate_discord_intelligence_bot.tenancy import TenantContext, current_tenant
from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry

# Comprehensive per-token costs in USD (input/output averaged for simplicity).
# Updated pricing as of 2024 - reflects current market rates for major providers.
MODEL_PRICES: dict[str, float] = {
    # OpenAI Models
    "gpt-4": 0.045 / 1000,  # Average of input (0.03) and output (0.06)
    "gpt-4-turbo": 0.02 / 1000,  # Average of input (0.01) and output (0.03)
    "gpt-3.5-turbo": 0.0015 / 1000,  # Average of input (0.001) and output (0.002)
    "gpt-3.5": 0.0015 / 1000,  # Alias for gpt-3.5-turbo for backward compatibility
    # Anthropic Claude Models
    "claude-3-opus": 0.045 / 1000,  # Average of input (0.015) and output (0.075)
    "claude-3-sonnet": 0.009 / 1000,  # Average of input (0.003) and output (0.015)
    "claude-3-haiku": 0.000625 / 1000,  # Average of input (0.00025) and output (0.00125)
    # Google Gemini Models (estimated - add when available)
    "gemini-pro": 0.0015 / 1000,  # Estimated based on competitive pricing
    "gemini-pro-vision": 0.002 / 1000,  # Estimated for vision capabilities
    # Meta Llama Models (estimated)
    "llama-2-70b": 0.0008 / 1000,  # Estimated
    "llama-3-70b": 0.001 / 1000,  # Estimated
    # Fallback for unknown models
    "default": 0.002 / 1000,  # Conservative fallback rate
}


class BudgetError(RuntimeError):
    """Raised when a request would exceed the configured budget."""


def _get_cost_settings() -> tuple[float, float]:
    """Get cost settings with fallback to avoid circular imports."""
    try:
        from .secure_config import get_config

        config = get_config()
        return config.cost_max_per_request, config.cost_budget_daily
    except ImportError:
        return 1.0, 100.0  # Remove os.getenv fallback as config handles it


@dataclass
class BudgetManager:
    """Tracks spend against simple in-memory budgets.

    Values are injected by ``BudgetStore`` which already resolves global + per-tenant
    overrides; we intentionally do NOT mutate them in ``__post_init__`` to avoid
    clobbering tenant-specific configuration (previous behaviour caused tests to fail
    because overrides were replaced with global defaults)."""

    max_per_request: float = 1.0
    daily_budget: float = 100.0
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
            max_req, daily = _get_cost_settings()
            if self.registry:
                cfg = self.registry.get_budget_config(key)
                if cfg:
                    # Backward-compatible flat keys
                    if "max_per_request" in cfg:
                        try:
                            max_req = float(cfg.get("max_per_request", max_req))
                        except Exception:
                            pass
                    if "daily_cap_usd" in cfg:
                        try:
                            daily = float(cfg.get("daily_cap_usd", daily))
                        except Exception:
                            pass
                    # Optional nested schema: limits.{max_per_request,daily_limit}
                    limits = cfg.get("limits") if isinstance(cfg, dict) else None
                    if isinstance(limits, dict):
                        if "max_per_request" in limits:
                            try:
                                max_req = float(limits.get("max_per_request", max_req))
                            except Exception:
                                pass
                        if "daily_limit" in limits:
                            try:
                                daily = float(limits.get("daily_limit", daily))
                            except Exception:
                                pass
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
    # Use detailed pricing if available, otherwise fall back to averaged pricing
    try:
        from .cost_optimizer import get_cost_optimizer

        optimizer = get_cost_optimizer()
        if model in optimizer.model_pricing:
            pricing = optimizer.model_pricing[model]
            input_cost = tokens_in * pricing["input"]
            output_cost = tokens_out * pricing["output"]
            return input_cost + output_cost
    except Exception:
        pass

    # Fallback to averaged pricing
    price = MODEL_PRICES.get(model, MODEL_PRICES.get("default", 0.002 / 1000))
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
