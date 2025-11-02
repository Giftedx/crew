"""Route components for OpenRouter service refactoring.

This module extracts the complex route method into focused, composable components
to improve maintainability, testability, and performance.
"""

from __future__ import annotations

import copy
import logging
import os as _os
import time
from dataclasses import dataclass
from platform.http.http_utils import REQUEST_TIMEOUT_SECONDS, http_request_with_retry, is_retry_enabled, resilient_post
from platform.observability import metrics
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.tenancy.context import TenantContext


if TYPE_CHECKING:
    from core.learning_engine import LearningEngine
    from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry
log = logging.getLogger(__name__)


@dataclass
class RouteContext:
    """Context for route execution containing all necessary state."""

    prompt: str
    task_type: str
    model: str | None
    provider_opts: dict[str, Any] | None
    tenant_context: TenantContext | None
    effective_models: dict[str, list[str]]
    provider: dict[str, Any]
    provider_family: str
    tokens_in: int
    projected_cost: float
    effective_max: float
    cache_key: str | None
    namespace: str | None


@dataclass
class RouteResult:
    """Result of route execution."""

    status: str
    model: str
    response: str | None = None
    tokens: int = 0
    provider: dict[str, Any] | None = None
    error: str | None = None
    cached: bool = False
    cache_type: str | None = None


class TenantResolver:
    """Handles tenant context resolution and model overrides."""

    def __init__(self, tenant_registry: TenantRegistry | None = None):
        self.tenant_registry = tenant_registry

    def resolve_context(self, component: str) -> TenantContext | None:
        """Resolve tenant context with fallback logic."""
        try:
            from ultimate_discord_intelligence_bot.tenancy.context import current_tenant

            ctx = current_tenant()
            if ctx is not None:
                return ctx
            from core.flags import enabled

            if enabled("ENABLE_TENANCY_STRICT", False):
                raise RuntimeError(f"TenantContext required for {component} but not set (strict mode)")
            return TenantContext("default", "main")
        except Exception:
            return None

    def get_effective_models(
        self, models_map: dict[str, list[str]], tenant_context: TenantContext | None
    ) -> dict[str, list[str]]:
        """Get effective model map with tenant overrides."""
        effective_models = copy.deepcopy(models_map)
        if self.tenant_registry and tenant_context:
            overrides = self.tenant_registry.get_model_overrides(tenant_context)
            if overrides:
                default_override = overrides.get("default")
                if default_override:
                    effective_models.setdefault("general", [default_override])
                    if "analysis" not in overrides:
                        effective_models["analysis"] = [default_override]
                for k, v in overrides.items():
                    if k != "default":
                        effective_models[k] = [v]
        return effective_models

    def get_provider_preferences(self, tenant_context: TenantContext | None) -> dict[str, Any]:
        """Get provider preferences for tenant."""
        if self.tenant_registry and tenant_context:
            prefs = self.tenant_registry.get_provider_preferences(tenant_context)
            if prefs:
                return {"order": prefs}
        return {}

    def _deep_merge(self, base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries."""
        result = copy.deepcopy(base)
        for key, value in overrides.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        return result


class CostCalculator:
    """Handles cost estimation and budget enforcement."""

    def __init__(self, token_meter, tenant_registry: TenantRegistry | None = None):
        self.token_meter = token_meter
        self.tenant_registry = tenant_registry

    def calculate_costs(
        self,
        prompt: str,
        chosen_model: str,
        effective_models: dict[str, list[str]],
        task_type: str,
        tenant_context: TenantContext | None,
    ) -> tuple[int, float, str | None]:
        """Calculate token count, projected cost, and affordable model."""
        tokens_in = self.token_meter.count_tokens(prompt, chosen_model)
        effective_prices = dict(self.token_meter.model_prices)
        if self.tenant_registry and tenant_context:
            effective_prices.update(self.tenant_registry.get_pricing_map(tenant_context))
        projected_cost = self.token_meter.estimate_cost(tokens_in, chosen_model, prices=effective_prices)
        affordable = self.token_meter.affordable_model(
            tokens_in, effective_models.get(task_type, effective_models.get("general", [])), prices=effective_prices
        )
        return (tokens_in, projected_cost, affordable)

    def enforce_budget_limits(
        self,
        projected_cost: float,
        task_type: str,
        chosen_model: str,
        affordable: str | None,
        tokens_in: int,
        effective_max: float,
        tenant_context: TenantContext | None,
    ) -> tuple[bool, str | None, str | None]:
        """Enforce budget limits and return (can_proceed, error_message, fallback_model)."""
        try:
            from .request_budget import current_request_tracker as _crt
        except ImportError:

            def _crt() -> None:
                return None

        tracker = _crt()
        if tracker and (not tracker.can_charge(projected_cost, task_type)):
            if affordable and affordable != chosen_model:
                alt_tokens = self.token_meter.count_tokens("", affordable)
                alt_cost = self.token_meter.estimate_cost(alt_tokens, affordable)
                if tracker.can_charge(alt_cost, task_type):
                    return (True, None, affordable)
            return (False, "cumulative cost exceeds limit", None)
        if projected_cost > effective_max:
            if affordable and affordable != chosen_model:
                return (True, None, affordable)
            return (False, "projected cost exceeds limit", None)
        return (True, None, None)


class CacheManager:
    """Handles all caching operations (semantic and traditional)."""

    def __init__(self, semantic_cache, traditional_cache):
        self.semantic_cache = semantic_cache
        self.traditional_cache = traditional_cache

    def get_semantic_cache_result(
        self,
        prompt: str,
        chosen_model: str,
        namespace: str | None,
        shadow_mode: bool,
        promotion_enabled: bool,
        promotion_threshold: float,
    ) -> RouteResult | None:
        """Get result from semantic cache if available."""
        if self.semantic_cache is None:
            return None
        try:
            import asyncio as _asyncio
            import threading as _threading

            _holder: dict[str, Any] = {}
            sc = self.semantic_cache

            def _runner() -> None:
                try:
                    if sc is not None:
                        _holder["result"] = _asyncio.run(sc.get(prompt, chosen_model, namespace=namespace))
                except Exception as e:
                    _holder["error"] = e

            t = _threading.Thread(target=_runner, daemon=True)
            t.start()
            t.join()
            if "error" not in _holder:
                sem_res = _holder.get("result")
                if sem_res is not None:
                    return self._process_semantic_cache_result(
                        sem_res, chosen_model, shadow_mode, promotion_enabled, promotion_threshold
                    )
        except Exception:
            pass
        return None

    def _process_semantic_cache_result(
        self,
        sem_res: dict[str, Any],
        chosen_model: str,
        shadow_mode: bool,
        promotion_enabled: bool,
        promotion_threshold: float,
    ) -> RouteResult | None:
        """Process semantic cache result and determine if it should be used."""
        if shadow_mode:
            sim_val = float(sem_res.get("similarity", 0.0))
            if promotion_enabled and sim_val >= promotion_threshold:
                result = dict(sem_res)
                result["cached"] = True
                result["cache_type"] = "semantic"
                return RouteResult(
                    status="success",
                    model=chosen_model,
                    response=result.get("response", ""),
                    cached=True,
                    cache_type="semantic",
                )
            return None
        else:
            result = dict(sem_res)
            result["cached"] = True
            result["cache_type"] = "semantic"
            return RouteResult(
                status="success",
                model=chosen_model,
                response=result.get("response", ""),
                cached=True,
                cache_type="semantic",
            )

    def get_traditional_cache_result(self, cache_key: str, chosen_model: str) -> RouteResult | None:
        """Get result from traditional cache if available."""
        if not self.traditional_cache or not cache_key:
            return None
        cached = self.traditional_cache.get(cache_key)
        if cached:
            result = dict(cached)
            result["cached"] = True
            return RouteResult(
                status="success",
                model=result.get("model", chosen_model),
                response=result.get("response", ""),
                cached=True,
                cache_type="traditional",
            )
        return None

    def set_cache_results(
        self, prompt: str, chosen_model: str, result: dict[str, Any], namespace: str | None, cache_key: str | None
    ) -> None:
        """Set results in both caches."""
        if self.semantic_cache is not None:
            try:
                import asyncio as _asyncio
                import threading as _threading

                sc = self.semantic_cache

                def _runner_set() -> None:
                    try:
                        if sc is not None:
                            _asyncio.run(sc.set(prompt, chosen_model, result, namespace=namespace))
                    except Exception:
                        pass

                t_set = _threading.Thread(target=_runner_set, daemon=True)
                t_set.start()
                t_set.join()
            except Exception:
                pass
        if self.traditional_cache and cache_key:
            self.traditional_cache.set(cache_key, result)


class RewardCalculator:
    """Handles reward calculation for reinforcement learning."""

    def __init__(self, tenant_registry: TenantRegistry | None = None):
        self.tenant_registry = tenant_registry

    def calculate_reward(
        self,
        projected_cost: float,
        latency_ms: float,
        effective_max: float,
        task_type: str,
        tenant_context: TenantContext | None,
    ) -> float:
        """Calculate reward for reinforcement learning."""
        try:
            from platform.core.settings import get_settings
        except Exception:
            try:
                from ultimate_discord_intelligence_bot.settings import Settings

                def get_settings():
                    return Settings()
            except Exception:

                class _S:
                    reward_cost_weight = 0.5
                    reward_latency_weight = 0.5
                    reward_latency_ms_window = 2000

                def get_settings() -> _S:
                    return _S()

        settings = get_settings()
        rl: dict[str, float] = {}
        if self.tenant_registry and tenant_context:
            rl = self.tenant_registry.get_rl_overrides(tenant_context)
        w_cost = float(rl.get("reward_cost_weight", getattr(settings, "reward_cost_weight", 0.5) or 0.5))
        w_lat = float(rl.get("reward_latency_weight", getattr(settings, "reward_latency_weight", 0.5) or 0.5))
        if w_cost == 0.0 and w_lat == 0.0:
            w_cost = w_lat = 0.5
        norm = w_cost + w_lat
        w_cost /= norm
        w_lat /= norm
        cost_norm = 0.0
        if projected_cost > 0:
            if rl.get("reward_cost_weight") is not None or rl.get("reward_latency_weight") is not None:
                denom = projected_cost
            else:
                denom = effective_max if effective_max and effective_max != float("inf") else projected_cost
            cost_norm = min(1.0, projected_cost / max(denom, 1e-09))
        lat_window = float(
            rl.get("reward_latency_ms_window", getattr(settings, "reward_latency_ms_window", 2000) or 2000)
        )
        lat_window = max(1.0, lat_window)
        lat_norm = min(1.0, latency_ms / lat_window)
        return max(0.0, 1.0 - w_cost * cost_norm - w_lat * lat_norm)


class MetricsRecorder:
    """Handles metrics recording for route execution."""

    def __init__(self, tenant_context: TenantContext | None = None):
        self.tenant_context = tenant_context

    def get_labels(self) -> dict[str, str]:
        """Get metric labels for current context."""
        if self.tenant_context is not None:
            return {
                "tenant": getattr(self.tenant_context, "tenant_id", "unknown"),
                "workspace": getattr(self.tenant_context, "workspace_id", "unknown"),
            }
        try:
            if hasattr(metrics, "label_ctx"):
                return metrics.label_ctx()
            else:
                return {"tenant": "unknown", "workspace": "unknown"}
        except Exception:
            return {"tenant": "unknown", "workspace": "unknown"}

    def record_model_selection(self, task_type: str, model: str, provider_family: str) -> None:
        """Record model selection metrics."""
        try:
            metric = getattr(metrics, "LLM_MODEL_SELECTED", None)
            if metric:
                metric.labels(**self.get_labels(), task=task_type, model=model, provider=provider_family).inc()
        except Exception:
            pass

    def record_cost_metrics(self, model: str, provider_family: str, projected_cost: float) -> None:
        """Record cost-related metrics."""
        try:
            metric = getattr(metrics, "LLM_ESTIMATED_COST", None)
            if metric:
                metric.labels(**self.get_labels(), model=model, provider=provider_family).observe(projected_cost)
        except Exception:
            pass

    def record_latency_metrics(self, latency_ms: float) -> None:
        """Record latency metrics."""
        try:
            metric = getattr(metrics, "LLM_LATENCY", None)
            if metric:
                metric.labels(**self.get_labels()).observe(latency_ms)
        except Exception:
            pass

    def record_cache_hit(self, model: str, provider_family: str) -> None:
        """Record cache hit metrics."""
        try:
            metric = getattr(metrics, "LLM_CACHE_HITS", None)
            if metric:
                metric.labels(**self.get_labels(), model=model, provider=provider_family).inc()
        except Exception:
            pass

    def record_budget_rejection(self, task_type: str, provider_family: str) -> None:
        """Record budget rejection metrics."""
        try:
            metric = getattr(metrics, "LLM_BUDGET_REJECTIONS", None)
            if metric:
                metric.labels(**self.get_labels(), task=task_type, provider=provider_family).inc()
        except Exception:
            pass


class OfflineExecutor:
    """Handles offline execution path."""

    def __init__(
        self,
        prompt_engine,
        learning_engine: LearningEngine,
        reward_calculator: RewardCalculator,
        metrics_recorder: MetricsRecorder,
    ):
        self.prompt_engine = prompt_engine
        self.learning_engine = learning_engine
        self.reward_calculator = reward_calculator
        self.metrics_recorder = metrics_recorder

    def execute(
        self, context: RouteContext, projected_cost: float, effective_max: float, tenant_context: TenantContext | None
    ) -> RouteResult:
        """Execute offline path."""
        start = time.perf_counter()
        response = context.prompt.upper()
        latency_ms = (time.perf_counter() - start) * 1000
        reward = self.reward_calculator.calculate_reward(
            projected_cost, latency_ms, effective_max, context.task_type, tenant_context
        )
        if context.model:
            self.learning_engine.update(context.task_type, context.model, reward=reward)
        if context.model:
            self.metrics_recorder.record_model_selection(context.task_type, context.model, context.provider_family)
            self.metrics_recorder.record_cost_metrics(context.model, context.provider_family, projected_cost)
        self.metrics_recorder.record_latency_metrics(latency_ms)
        return RouteResult(
            status="success",
            model=context.model or "unknown",
            response=response,
            tokens=context.tokens_in,
            provider=context.provider,
            cached=False,
        )


class NetworkExecutor:
    """Handles network execution path."""

    def __init__(
        self,
        api_key: str,
        prompt_engine,
        learning_engine: LearningEngine,
        reward_calculator: RewardCalculator,
        metrics_recorder: MetricsRecorder,
    ):
        self.api_key = api_key
        self.prompt_engine = prompt_engine
        self.learning_engine = learning_engine
        self.reward_calculator = reward_calculator
        self.metrics_recorder = metrics_recorder

    def execute(
        self, context: RouteContext, projected_cost: float, effective_max: float, tenant_context: TenantContext | None
    ) -> RouteResult:
        """Execute network path."""
        start = time.perf_counter()
        try:
            payload: dict[str, Any] = {
                "model": context.model,
                "messages": [{"role": "user", "content": context.prompt}],
            }
            if context.provider:
                payload["provider"] = context.provider
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            try:
                from platform.core.settings import get_settings
            except Exception:
                try:
                    pass
                except Exception:

                    def get_settings():
                        return type("Settings", (), {})()

            settings = get_settings()
            ref = getattr(settings, "openrouter_referer", None) or _os.getenv("OPENROUTER_REFERER")
            if ref:
                headers["Referer"] = str(ref)
                headers["HTTP-Referer"] = str(ref)
            title = getattr(settings, "openrouter_title", None) or _os.getenv("OPENROUTER_TITLE")
            if title:
                headers["X-Title"] = str(title)
            resp = None
            if is_retry_enabled():
                try:
                    resp = http_request_with_retry(
                        "POST",
                        url,
                        request_callable=lambda u, **_: resilient_post(
                            u, headers=headers, json_payload=payload, timeout_seconds=REQUEST_TIMEOUT_SECONDS
                        ),
                        max_attempts=3,
                    )
                except Exception as retry_exc:
                    latency_ms = (time.perf_counter() - start) * 1000
                    return RouteResult(
                        status="error",
                        model=context.model or "unknown",
                        error=str(retry_exc),
                        tokens=context.tokens_in,
                        provider=context.provider,
                    )
            else:
                resp = resilient_post(
                    url, headers=headers, json_payload=payload, timeout_seconds=REQUEST_TIMEOUT_SECONDS
                )
            if resp is None or getattr(resp, "status_code", 200) >= 400:
                code = getattr(resp, "status_code", "unknown")
                raise RuntimeError(f"openrouter_error status={code}")
            data = resp.json() if resp is not None else {}
            message = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            latency_ms = (time.perf_counter() - start) * 1000
            reward = self.reward_calculator.calculate_reward(
                projected_cost, latency_ms, effective_max, context.task_type, tenant_context
            )
            if context.model:
                self.learning_engine.update(context.task_type, context.model, reward=reward)
            if context.model:
                self.metrics_recorder.record_model_selection(context.task_type, context.model, context.provider_family)
                self.metrics_recorder.record_cost_metrics(context.model, context.provider_family, projected_cost)
            self.metrics_recorder.record_latency_metrics(latency_ms)
            return RouteResult(
                status="success",
                model=context.model or "unknown",
                response=message,
                tokens=context.tokens_in,
                provider=context.provider,
                cached=False,
            )
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            return RouteResult(
                status="error",
                model=context.model or "unknown",
                error=str(exc),
                tokens=context.tokens_in,
                provider=context.provider,
            )
