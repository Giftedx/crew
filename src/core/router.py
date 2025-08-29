"""Model and provider router using the learning engine."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from obs import metrics, tracing
from ultimate_discord_intelligence_bot.tenancy import current_tenant
from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry

from . import token_meter
from .learning_engine import LearningEngine


class Router:
    """Selects a model/provider combination for a request."""

    def __init__(self, engine: LearningEngine, registry: TenantRegistry | None = None) -> None:
        self.engine = engine
        self.registry = registry
        try:
            self.engine.registry.get("routing")
        except KeyError:
            self.engine.register_domain("routing")

    @tracing.trace_call("router.preflight")
    def preflight(self, prompt: str, candidates: Sequence[str], expected_output_tokens: int) -> str:
        """Select a model that fits within the cost guard.

        Iterates through ``candidates`` and picks the first model whose
        estimated cost does not exceed the configured per-request budget.
        Raises ``BudgetError`` if none are affordable.
        """

        tokens_in = token_meter.estimate_tokens(prompt)
        for model in candidates:
            cost = token_meter.estimate(tokens_in, expected_output_tokens, model)
            try:
                token_meter.budget.preflight(cost)
                return model
            except token_meter.BudgetError:
                continue
        raise token_meter.BudgetError("budget_exceeded")

    def _filter_candidates(self, candidates: Sequence[str]) -> Sequence[str]:
        ctx = current_tenant()
        if not ctx or not self.registry:
            return candidates
        allowed = self.registry.get_allowed_models(ctx)
        if allowed:
            filtered = [c for c in candidates if c in allowed]
            return filtered
        return candidates

    @tracing.trace_call("router.route")
    def route(self, task: str, candidates: Sequence[str], context: dict[str, Any]) -> str:
        """Return the model name selected for ``task``."""

        candidates = list(self._filter_candidates(candidates))
        if not candidates:
            raise ValueError("no allowed models for tenant")

        try:
            model = self.engine.recommend("routing", context, candidates)
        except Exception:
            model = candidates[0]
        metrics.ROUTER_DECISIONS.labels(**metrics.label_ctx()).inc()

        try:
            token_meter.budget.preflight(context.get("estimated_cost_usd", 0.0))
        except token_meter.BudgetError:
            # downshift to cheapest candidate that fits
            model = self.preflight(
                context.get("prompt", ""),
                candidates,
                context.get("expected_output_tokens", 0),
            )
        return model


__all__ = ["Router"]
