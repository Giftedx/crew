"""Budget enforcement utilities for OpenRouter routing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from obs import metrics


if TYPE_CHECKING:  # pragma: no cover
    from .service import OpenRouterService
    from .state import RouteState


def enforce_budget_limits(service: OpenRouterService, state: RouteState) -> dict[str, Any] | None:
    """Apply cumulative and per-request budget constraints.

    Returns an error response dict when limits are exceeded, otherwise mutates
    ``state`` with potentially adjusted model choice and projected cost.
    """

    labels = state.labels()
    provider_family = state.provider_family
    provider = state.provider
    chosen = state.chosen_model
    tokens_in = state.tokens_in
    projected_cost = state.projected_cost
    affordable = state.affordable_alternative
    tracker = state.tracker
    task_type = state.task_type

    def _record_rejection(reason: str, err: dict[str, Any]) -> dict[str, Any]:
        state.chosen_model = chosen
        state.tokens_in = tokens_in
        state.projected_cost = projected_cost
        state.error = err
        service._adaptive_record_outcome(
            state,
            reward=0.0,
            status="budget_rejection",
            metadata={"reason": reason},
        )
        return err

    if tracker and not tracker.can_charge(projected_cost, task_type):
        if affordable and affordable != chosen:
            alt_tokens = service.prompt_engine.count_tokens(state.prompt, affordable)
            alt_cost = service.token_meter.estimate_cost(alt_tokens, affordable, prices=state.effective_prices)
            if tracker.can_charge(alt_cost, task_type):
                chosen = affordable
                tokens_in = alt_tokens
                projected_cost = alt_cost
            else:
                metrics.LLM_BUDGET_REJECTIONS.labels(**labels, task=task_type, provider=provider_family).inc()
                error = {
                    "status": "error",
                    "error": "cumulative cost exceeds limit",
                    "model": chosen,
                    "tokens": tokens_in,
                    "provider": provider,
                }
                return _record_rejection("tracker_limit", error)
        else:
            metrics.LLM_BUDGET_REJECTIONS.labels(**labels, task=task_type, provider=provider_family).inc()
            error = {
                "status": "error",
                "error": "cumulative cost exceeds limit",
                "model": chosen,
                "tokens": tokens_in,
                "provider": provider,
            }
            return _record_rejection("tracker_limit", error)

    tenant_max: float | None = None
    if service.tenant_registry:
        ctx = state.ctx_effective
        if ctx:
            per_task_limit = service.tenant_registry.get_per_request_limit(ctx, task_type)
            if per_task_limit is not None:
                tenant_max = per_task_limit
            else:
                bcfg = service.tenant_registry.get_budget_config(ctx.tenant_id)
                if isinstance(bcfg, dict):
                    limits = bcfg.get("limits") if isinstance(bcfg.get("limits"), dict) else None
                    if limits and "max_per_request" in limits:
                        try:
                            tenant_max = float(limits["max_per_request"])
                        except Exception:
                            tenant_max = None
                    if tenant_max is None and "max_per_request" in bcfg:
                        try:
                            raw_val = bcfg.get("max_per_request")
                            tenant_max = float(raw_val) if raw_val is not None else None
                        except Exception:
                            tenant_max = None

    effective_max = (
        service.token_meter.max_cost_per_request
        if service.token_meter.max_cost_per_request is not None
        else float("inf")
    )
    if tenant_max is not None:
        effective_max = min(effective_max, tenant_max)

    if projected_cost > effective_max:
        if affordable and affordable != chosen:
            alt_tokens = service.prompt_engine.count_tokens(state.prompt, affordable)
            alt_cost = service.token_meter.estimate_cost(alt_tokens, affordable, prices=state.effective_prices)
            if alt_cost <= effective_max:
                chosen = affordable
                tokens_in = alt_tokens
                projected_cost = alt_cost
            else:
                metrics.LLM_BUDGET_REJECTIONS.labels(**labels, task=task_type, provider=provider_family).inc()
                error = {
                    "status": "error",
                    "error": "projected cost exceeds limit",
                    "model": chosen,
                    "tokens": tokens_in,
                    "provider": provider,
                }
                return _record_rejection("per_request_limit", error)
        else:
            metrics.LLM_BUDGET_REJECTIONS.labels(**labels, task=task_type, provider=provider_family).inc()
            error = {
                "status": "error",
                "error": "projected cost exceeds limit",
                "model": chosen,
                "tokens": tokens_in,
                "provider": provider,
            }
            return _record_rejection("per_request_limit", error)

    state.chosen_model = chosen
    state.tokens_in = tokens_in
    state.projected_cost = projected_cost
    state.effective_max = effective_max

    return None
