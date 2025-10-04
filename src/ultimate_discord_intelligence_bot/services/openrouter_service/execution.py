"""Execution paths for OpenRouter routing."""

from __future__ import annotations

import logging
import os as _os
import sys
import time
from typing import TYPE_CHECKING, Any

from core.http_utils import (
    REQUEST_TIMEOUT_SECONDS,
    http_request_with_retry,
    is_retry_enabled,
)
from core.http_utils import (
    resilient_post as _default_resilient_post,
)
from obs import metrics

from .service import get_settings
from .state import RouteState

try:
    from obs.enhanced_langsmith_integration import trace_llm_call as _trace_llm_call

    def trace_llm_call(*args: Any, **kwargs: Any) -> None:
        _trace_llm_call(*args, **kwargs)

except Exception:  # pragma: no cover

    def trace_llm_call(*_args: Any, **_kwargs: Any) -> None:
        return None


try:  # pragma: no cover - optional local vLLM adapter
    from core.vllm_service import is_vllm_available as _is_vllm_available
    from core.vllm_service import vLLMOpenRouterAdapter as _VLLMAdapterCtor
except Exception:  # pragma: no cover
    _is_vllm_available = None
    _VLLMAdapterCtor = None

vllm_adapter_ctor: Any | None = _VLLMAdapterCtor

log = logging.getLogger(__name__)

_MODULE_NAMES = (
    "ultimate_discord_intelligence_bot.services.openrouter_service",
    "src.ultimate_discord_intelligence_bot.services.openrouter_service",
)


def _call_resilient_post(*args: Any, **kwargs: Any) -> Any:
    module = None
    for name in _MODULE_NAMES:
        module = sys.modules.get(name)
        if module is not None:
            break
    if module is not None and hasattr(module, "resilient_post"):
        return module.resilient_post(*args, **kwargs)
    return _default_resilient_post(*args, **kwargs)


def execute_offline(service: OpenRouterService, state: RouteState) -> dict[str, Any]:
    prompt = state.prompt
    chosen = state.chosen_model
    provider = state.provider
    provider_family = state.provider_family
    labels = state.labels()

    response = prompt.upper()
    latency_ms = (time.perf_counter() - state.start_time) * 1000
    tokens_out = service.prompt_engine.count_tokens(response, chosen)

    reward = _compute_reward(service, state, latency_ms)
    service.learning.update(state.task_type, chosen, reward=reward)
    service._adaptive_record_outcome(
        state,
        reward=reward,
        status="success",
        metadata={
            "latency_ms": latency_ms,
            "tokens_out": tokens_out,
            "execution_mode": "offline",
            "cache_hit": False,
        },
    )
    metrics.LLM_MODEL_SELECTED.labels(**labels, task=state.task_type, model=chosen, provider=provider_family).inc()
    metrics.LLM_ESTIMATED_COST.labels(**labels, model=chosen, provider=provider_family).observe(state.projected_cost)
    metrics.LLM_LATENCY.labels(**labels).observe(latency_ms)
    if service.logger:
        service.logger.log_llm_call(
            state.task_type,
            chosen,
            str(provider),
            state.tokens_in,
            tokens_out,
            float(state.projected_cost),
            latency_ms,
            None,
            True,
            None,
        )
    result = {
        "status": "success",
        "model": chosen,
        "response": response,
        "tokens": state.tokens_in,
        "provider": provider,
    }
    if state.cache_metadata:
        result.setdefault("cache_info", state.cache_metadata)
    if state.compression_metadata:
        result.setdefault("compression_info", state.compression_metadata)
    trace_llm_call(
        name=f"openrouter_{state.task_type}",
        prompt=prompt,
        response=response,
        model=chosen,
        metadata={"provider": provider, "task_type": state.task_type, "offline": True},
        latency_ms=latency_ms,
        token_usage={
            "input_tokens": state.tokens_in,
            "output_tokens": tokens_out,
            "total_tokens": state.tokens_in + tokens_out,
        },
        cost=state.projected_cost,
    )
    _persist_caches(service, state, result)
    _charge_tracker(state)
    result["cached"] = False
    state.result = result
    return result


def execute_online(service: OpenRouterService, state: RouteState) -> dict[str, Any]:
    prompt = state.prompt
    chosen = state.chosen_model
    provider = state.provider
    provider_family = state.provider_family
    payload: dict[str, Any] = {"model": chosen, "messages": [{"role": "user", "content": prompt}]}
    if provider:
        payload["provider"] = provider
    settings = get_settings()

    if (
        chosen.startswith("local/")
        and vllm_adapter_ctor is not None
        and _has_vllm()
        and getattr(settings, "enable_vllm_local", False)
    ):
        try:  # pragma: no cover - only when local inference available
            AdapterType: Any = vllm_adapter_ctor
            adapter = AdapterType()
            vllm_result = adapter.route_to_local_model(prompt, chosen, state.task_type)
            if vllm_result.get("status") == "success":
                latency_ms = (time.perf_counter() - state.start_time) * 1000
                trace_llm_call(
                    name=f"vllm_{state.task_type}",
                    prompt=prompt,
                    response=vllm_result["response"],
                    model=chosen,
                    metadata={"provider": "vllm", "task_type": state.task_type, "local_inference": True},
                    latency_ms=latency_ms,
                    token_usage={
                        "input_tokens": state.tokens_in,
                        "output_tokens": vllm_result.get("tokens", 0),
                        "total_tokens": state.tokens_in + vllm_result.get("tokens", 0),
                    },
                    cost=state.projected_cost,
                )
                _charge_tracker(state)
                state.result = vllm_result
                return vllm_result
        except Exception as exc:  # pragma: no cover
            log.warning("vLLM local inference failed: %s, falling back to HTTP", exc)

    if getattr(settings, "local_llm_url", None):
        local_model = chosen.split("/", 1)[1] if "/" in chosen else chosen
        local_payload = {"model": local_model, "messages": payload["messages"]}
        local_url = str(getattr(settings, "local_llm_url", "")).rstrip("/") + "/v1/chat/completions"
        resp = _call_resilient_post(local_url, json_payload=local_payload, timeout_seconds=REQUEST_TIMEOUT_SECONDS)
        if resp is not None and getattr(resp, "status_code", 200) < 400:  # noqa: PLR2004
            data = resp.json()
            message = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            latency_ms = (time.perf_counter() - state.start_time) * 1000
            tokens_out = service.prompt_engine.count_tokens(message, local_model)
            result_local = {
                "status": "success",
                "model": chosen,
                "response": message,
                "tokens": state.tokens_in,
                "provider": {"order": ["local"]},
            }
            _post_success(service, state, result_local, tokens_out, latency_ms, provider_family, offline=False)
            return result_local

    url = "https://openrouter.ai/api/v1/chat/completions"
    api_key = service.api_key or ""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    ref = getattr(settings, "openrouter_referer", None) or _os.getenv("OPENROUTER_REFERER")
    if ref:
        ref = str(ref)
        headers["Referer"] = ref
        headers["HTTP-Referer"] = ref
    title = getattr(settings, "openrouter_title", None) or _os.getenv("OPENROUTER_TITLE")
    if title:
        headers["X-Title"] = str(title)

    resp = None
    if is_retry_enabled():
        try:
            resp = http_request_with_retry(
                "POST",
                url,
                request_callable=lambda u, **_: _call_resilient_post(
                    u, headers=headers, json_payload=payload, timeout_seconds=REQUEST_TIMEOUT_SECONDS
                ),
                max_attempts=3,
            )
        except Exception as retry_exc:
            latency_ms = (time.perf_counter() - state.start_time) * 1000
            if service.logger:
                try:
                    service.logger.log_llm_call(
                        state.task_type,
                        chosen,
                        str(provider),
                        state.tokens_in,
                        0,
                        float(state.projected_cost),
                        latency_ms,
                        None,
                        False,
                        str(retry_exc),
                    )
                except Exception as log_exc:  # pragma: no cover
                    log.debug("logger failure in retry give-up: %s", log_exc)
            error = {
                "status": "error",
                "error": str(retry_exc),
                "model": chosen,
                "tokens": state.tokens_in,
                "provider": provider,
            }
            state.error = error
            service._adaptive_record_outcome(
                state,
                reward=0.0,
                status="error",
                metadata={
                    "stage": "http_retry",
                    "error": str(retry_exc),
                    "latency_ms": latency_ms,
                },
            )
            return error
    else:
        resp = _call_resilient_post(url, headers=headers, json_payload=payload, timeout_seconds=REQUEST_TIMEOUT_SECONDS)

    if resp is None or getattr(resp, "status_code", 200) >= 400:  # noqa: PLR2004
        code = getattr(resp, "status_code", "unknown")
        raise RuntimeError(f"openrouter_error status={code}")
    data = resp.json() if resp is not None else {}
    message = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    latency_ms = (time.perf_counter() - state.start_time) * 1000
    tokens_out = service.prompt_engine.count_tokens(message, chosen)

    result = {
        "status": "success",
        "model": chosen,
        "response": message,
        "tokens": state.tokens_in,
        "provider": provider,
    }
    if state.cache_metadata:
        result.setdefault("cache_info", state.cache_metadata)
    _post_success(service, state, result, tokens_out, latency_ms, provider_family, offline=False)
    return result


def handle_failure(service: OpenRouterService, state: RouteState, exc: Exception) -> dict[str, Any]:
    latency_ms = (time.perf_counter() - state.start_time) * 1000
    if service.logger:
        service.logger.log_llm_call(
            state.task_type,
            state.chosen_model,
            str(state.provider),
            state.tokens_in,
            0,
            0.0,
            latency_ms,
            None,
            False,
            None,
        )
    log.error(
        "OpenRouterService route failed task=%s model=%s provider=%s err=%s",
        state.task_type,
        state.chosen_model,
        state.provider_family,
        exc,
        exc_info=True,
    )
    error = {
        "status": "error",
        "error": str(exc),
        "model": state.chosen_model,
        "tokens": state.tokens_in,
        "provider": state.provider,
    }
    state.error = error
    service._adaptive_record_outcome(
        state,
        reward=0.0,
        status="exception",
        metadata={"error": str(exc), "latency_ms": latency_ms},
    )
    return error


def _post_success(
    service: OpenRouterService,
    state: RouteState,
    result: dict[str, Any],
    tokens_out: int,
    latency_ms: float,
    provider_family: str,
    *,
    offline: bool,
) -> None:
    reward = _compute_reward(service, state, latency_ms)
    service.learning.update(state.task_type, state.chosen_model, reward=reward)
    cache_meta = state.cache_metadata or {}
    cache_hit = any(isinstance(meta, dict) and meta.get("status") == "hit" for meta in cache_meta.values())
    service._adaptive_record_outcome(
        state,
        reward=reward,
        status="success",
        metadata={
            "latency_ms": latency_ms,
            "tokens_out": tokens_out,
            "execution_mode": "offline" if offline else "online",
            "cache_hit": cache_hit,
        },
    )
    labels = state.labels()
    metrics.LLM_MODEL_SELECTED.labels(
        **labels, task=state.task_type, model=state.chosen_model, provider=provider_family
    ).inc()
    metrics.LLM_ESTIMATED_COST.labels(**labels, model=state.chosen_model, provider=provider_family).observe(
        state.projected_cost
    )
    metrics.LLM_LATENCY.labels(**labels).observe(latency_ms)
    if service.logger:
        service.logger.log_llm_call(
            state.task_type,
            state.chosen_model,
            str(state.provider),
            state.tokens_in,
            tokens_out,
            float(state.projected_cost),
            latency_ms,
            None,
            True,
            None,
        )
    metadata = {
        "provider": state.provider,
        "task_type": state.task_type,
        "offline": offline,
    }
    if not offline:
        metadata["api_endpoint"] = "openrouter"
    if state.cache_metadata:
        result.setdefault("cache_info", state.cache_metadata)
    if state.compression_metadata:
        result.setdefault("compression_info", state.compression_metadata)
    trace_llm_call(
        name=f"openrouter_{state.task_type}",
        prompt=state.prompt,
        response=result.get("response"),
        model=state.chosen_model,
        metadata=metadata,
        latency_ms=latency_ms,
        token_usage={
            "input_tokens": state.tokens_in,
            "output_tokens": tokens_out,
            "total_tokens": state.tokens_in + tokens_out,
        },
        cost=state.projected_cost,
    )
    _persist_caches(service, state, result)
    _charge_tracker(state)
    result["cached"] = False
    state.result = result


def _persist_caches(service: OpenRouterService, state: RouteState, result: dict[str, Any]) -> None:
    if service.semantic_cache is not None:
        try:
            sc = service.semantic_cache
            # Call cache.set() directly - no longer async
            if sc is not None:
                sc.set(state.prompt, state.chosen_model, result, namespace=state.namespace)
            log.debug("semantic_cache_set completed for model=%s ns=%s", state.chosen_model, state.namespace)
        except Exception:
            pass
    if service.cache and state.cache_key:
        service.cache.set(state.cache_key, result)


def _charge_tracker(state: RouteState) -> None:
    tracker = state.tracker
    if tracker:
        try:
            tracker.charge(state.projected_cost, state.task_type)
        except Exception as charge_exc:  # pragma: no cover
            log.debug(
                "request budget charge failed task=%s model=%s err=%s",
                state.task_type,
                state.chosen_model,
                charge_exc,
            )


def _compute_reward(service: OpenRouterService, state: RouteState, latency_ms: float) -> float:
    settings = get_settings()
    rl: dict[str, Any] = {}
    if service.tenant_registry:
        ctx_t = state.ctx_effective
        rl = service.tenant_registry.get_rl_overrides(ctx_t) if ctx_t else {}
    w_cost = float(rl.get("reward_cost_weight", getattr(settings, "reward_cost_weight", 0.5) or 0.5))
    w_lat = float(rl.get("reward_latency_weight", getattr(settings, "reward_latency_weight", 0.5) or 0.5))
    if w_cost == 0.0 and w_lat == 0.0:
        w_cost = w_lat = 0.5
    norm = w_cost + w_lat
    w_cost /= norm
    w_lat /= norm
    cost_norm = 0.0
    if state.projected_cost > 0:
        if rl.get("reward_cost_weight") is not None or rl.get("reward_latency_weight") is not None:
            denom = state.projected_cost
        else:
            denom = (
                state.effective_max
                if state.effective_max and state.effective_max != float("inf")
                else state.projected_cost
            )
        cost_norm = min(1.0, state.projected_cost / max(denom, 1e-9))
    lat_window = float(rl.get("reward_latency_ms_window", getattr(settings, "reward_latency_ms_window", 2000) or 2000))
    lat_window = max(1.0, lat_window)
    lat_norm = min(1.0, latency_ms / lat_window)
    return max(0.0, 1.0 - w_cost * cost_norm - w_lat * lat_norm)


def _has_vllm() -> bool:
    try:
        if _is_vllm_available is None:
            return False
        return bool(_is_vllm_available())
    except Exception:
        return False


if TYPE_CHECKING:  # pragma: no cover
    from .service import OpenRouterService
