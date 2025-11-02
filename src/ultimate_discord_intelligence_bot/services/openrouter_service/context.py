"""Preparation helpers for OpenRouter routing."""

from __future__ import annotations
import contextlib
import copy
import logging
import os as _os
from typing import TYPE_CHECKING, Any
from platform.observability import metrics
from ..request_budget import current_request_tracker as _crt
from .state import RouteState

log = logging.getLogger(__name__)
if TYPE_CHECKING:
    from .service import OpenRouterService


def prepare_route_state(
    service: OpenRouterService, prompt: str, task_type: str, model: str | None, provider_opts: dict[str, Any] | None
) -> RouteState:
    """Assemble initial routing state (tenant context, model selection, provider preferences)."""
    ctx_effective = service._ctx_or_fallback("openrouter_service")

    def _labels() -> dict[str, str]:
        if ctx_effective is not None:
            return {
                "tenant": getattr(ctx_effective, "tenant_id", "unknown"),
                "workspace": getattr(ctx_effective, "workspace_id", "unknown"),
            }
        return metrics.label_ctx()

    labels_initial = _labels()
    effective_models = copy.deepcopy(service.models_map)
    if service.tenant_registry:
        ctx = ctx_effective
        if ctx:
            overrides = service.tenant_registry.get_model_overrides(ctx)
            if overrides:
                default_override = overrides.get("default")
                if default_override:
                    effective_models.setdefault("general", [default_override])
                    if "analysis" not in overrides:
                        effective_models["analysis"] = [default_override]
                for key, value in overrides.items():
                    if key != "default":
                        effective_models[key] = [value]
    candidate_models = list(dict.fromkeys(effective_models.get(task_type, effective_models.get("general", []))))
    fallback_choice = service._choose_model_from_map(task_type, effective_models)
    if not service.api_key and (not service.offline_mode):
        env_key = _os.getenv("OPENROUTER_API_KEY")
        if env_key:
            service.api_key = env_key
            service.offline_mode = False
    effective_offline = service.offline_mode or not service.api_key
    chosen = model or fallback_choice
    adaptive_trial_index: int | None = None
    adaptive_suggested_model: str | None = None
    adaptive_candidates: list[str] | None = candidate_models or None
    rl_router_selection: dict[str, Any] | None = None
    rl_router = getattr(service, "rl_router", None)
    if rl_router is not None and model is None and bool(candidate_models):
        try:
            context_features = {
                "task_type": task_type,
                "tenant": labels_initial.get("tenant", "unknown"),
                "workspace": labels_initial.get("workspace", "unknown"),
                "offline_mode": bool(effective_offline),
                "candidate_count": len(candidate_models),
                "default_model": fallback_choice,
            }
            rl_selection = rl_router.route_request(context_features, candidate_models)
            if rl_selection:
                rl_router_selection = rl_selection
                chosen = rl_selection.get("model", fallback_choice)
                log.debug(f"RL Router selected model: {chosen}")
        except Exception as rl_exc:
            log.warning(f"RL Router selection failed, falling back to standard routing: {rl_exc}")
    manager = getattr(service, "adaptive_routing", None)
    adaptive_enabled = (
        model is None
        and manager is not None
        and getattr(manager, "enabled", False)
        and bool(candidate_models)
        and (rl_router_selection is None)
    )
    if adaptive_enabled:
        context_payload = {
            "tenant": labels_initial.get("tenant", "unknown"),
            "workspace": labels_initial.get("workspace", "unknown"),
            "requested_model": model,
            "default_model": fallback_choice,
            "candidate_count": len(candidate_models),
            "offline_mode": bool(effective_offline),
        }
        trial = manager.suggest(task_type, candidate_models, context_payload)
        if trial is not None:
            adaptive_trial_index, suggested_model = trial
            adaptive_suggested_model = suggested_model
            chosen = suggested_model
    if manager is not None and getattr(manager, "enabled", False):
        with contextlib.suppress(Exception):
            metrics.ACTIVE_BANDIT_POLICY.labels(
                tenant=labels_initial.get("tenant", "unknown"),
                workspace=labels_initial.get("workspace", "unknown"),
                domain=task_type,
                policy="ax_adaptive",
            ).set(1.0 if adaptive_trial_index is not None else 0.0)
    provider: dict[str, Any] = {}
    if service.tenant_registry:
        ctx = ctx_effective
        if ctx:
            prefs = service.tenant_registry.get_provider_preferences(ctx)
            if prefs:
                provider = {"order": prefs}
    if service.provider_opts:
        provider = service._deep_merge(provider, copy.deepcopy(service.provider_opts))
    if provider_opts:
        provider = service._deep_merge(provider, provider_opts)
    provider_family = "unknown"
    try:
        order = provider.get("order") if isinstance(provider, dict) else None
        if isinstance(order, list) and order:
            provider_family = str(order[0])
    except Exception:
        provider_family = "unknown"
    optimised_prompt, compression_meta = service.prompt_engine.optimise_with_metadata(prompt, model=chosen)
    prompt = optimised_prompt
    tokens_in = int(compression_meta.get("final_tokens", service.prompt_engine.count_tokens(prompt, chosen)))
    effective_prices = dict(service.token_meter.model_prices)
    if service.tenant_registry:
        ctx = ctx_effective
        if ctx:
            effective_prices.update(service.tenant_registry.get_pricing_map(ctx))
    projected_cost = service.token_meter.estimate_cost(tokens_in, chosen, prices=effective_prices)
    affordable = service.token_meter.affordable_model(
        tokens_in, effective_models.get(task_type, effective_models.get("general", [])), prices=effective_prices
    )
    tracker = _crt()
    return RouteState(
        prompt=prompt,
        task_type=task_type,
        requested_model=model,
        chosen_model=chosen,
        ctx_effective=ctx_effective,
        labels_factory=_labels,
        effective_models=effective_models,
        provider=provider,
        provider_family=provider_family,
        tokens_in=tokens_in,
        projected_cost=projected_cost,
        affordable_alternative=affordable,
        effective_prices=effective_prices,
        tracker=tracker,
        offline_mode=effective_offline,
        provider_overrides=provider_opts,
        compression_metadata=compression_meta,
        adaptive_trial_index=adaptive_trial_index,
        adaptive_suggested_model=adaptive_suggested_model,
        adaptive_candidates=adaptive_candidates,
        rl_router_selection=rl_router_selection,
    )
