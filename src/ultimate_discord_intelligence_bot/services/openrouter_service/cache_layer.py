"""Cache helpers for the OpenRouter routing workflow."""

from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.obs import metrics

from ...cache import combine_keys, generate_key_from_params


log = logging.getLogger(__name__)
if TYPE_CHECKING:
    from .service import OpenRouterService
    from .state import RouteState


def check_caches(service: OpenRouterService, state: RouteState) -> dict[str, Any] | None:
    """Return cached response if semantic or Redis cache hits occur."""
    labels = state.labels()
    chosen = state.chosen_model
    provider_family = state.provider_family
    provider = state.provider
    prompt = state.prompt
    ctx_effective = state.ctx_effective
    task_type = state.task_type
    task_type_normalized = str(task_type).strip().lower()
    ns: str | None = None
    if ctx_effective:
        try:
            tenant_id = getattr(ctx_effective, "tenant_id", "unknown")
            workspace_id = getattr(ctx_effective, "workspace_id", "unknown")
            ns = f"{tenant_id}:{workspace_id}"
        except Exception:
            ns = None
    state.namespace = ns
    cache_meta: dict[str, Any] = {"namespace": ns, "task_type": task_type}
    state.cache_metadata = cache_meta
    shadow_mode = bool(getattr(service, "semantic_cache_shadow_mode", False))
    shadow_tasks = getattr(service, "semantic_cache_shadow_task_types", None)
    normalized_shadow_tasks: set[str] | None = None
    if shadow_tasks:
        try:
            normalized_shadow_tasks = {str(t).strip().lower() for t in shadow_tasks if str(t).strip()}
        except Exception:
            normalized_shadow_tasks = None
        if normalized_shadow_tasks:
            try:
                if task_type_normalized in normalized_shadow_tasks:
                    shadow_mode = True
            except Exception:
                pass
    if service.semantic_cache is not None:
        cache_meta_sem = cache_meta.setdefault("semantic", {"status": "pending"})
        cache_meta_sem.setdefault("mode", "shadow" if shadow_mode else "active")
        try:
            log.debug(
                "semantic_cache_get attempting (ns=%s, model=%s, type=%s)", ns, chosen, type(service.semantic_cache)
            )
            sc = service.semantic_cache
            sem_res = sc.get(prompt, chosen, namespace=ns) if sc is not None else None
            if sem_res is not None:
                log.debug("semantic_cache_get HIT for model=%s ns=%s", chosen, ns)
                try:
                    cache_meta_sem.update(
                        {
                            "status": "hit",
                            "cache_type": "semantic",
                            "similarity": float(sem_res.get("similarity", 0.0) if isinstance(sem_res, dict) else 0.0),
                        }
                    )
                except Exception:
                    cache_meta_sem["status"] = "hit"
                if shadow_mode:
                    try:
                        metrics.SEMANTIC_CACHE_SHADOW_HITS.labels(**labels, model=chosen).inc()
                        service._update_shadow_hit_ratio(labels, is_hit=True)
                    except Exception:
                        pass
                    try:
                        sim_val = float(sem_res.get("similarity", 0.0)) if isinstance(sem_res, dict) else 0.0
                    except Exception:
                        sim_val = 0.0
                    promote = bool(getattr(service, "semantic_cache_promotion_enabled", False)) and sim_val >= float(
                        getattr(service, "semantic_cache_promotion_threshold", 0.9)
                    )
                    if promote:
                        result = dict(sem_res) if isinstance(sem_res, dict) else {"response": str(sem_res)}
                        result["cached"] = True
                        result["cache_type"] = "semantic"
                        result["cache_info"] = cache_meta
                        _record_similarity(labels, chosen, sim_val)
                        _record_cache_hit(labels, chosen, provider_family, shadow_promoted=True)
                        service._adaptive_record_outcome(
                            state,
                            reward=0.0,
                            status="cache_hit",
                            metadata={
                                "cache_type": "semantic_shadow",
                                "similarity": sim_val,
                                "cache_info": cache_meta,
                                "promotion": True,
                            },
                        )
                        state.result = result
                        return result
                    log.debug(
                        "semantic_cache SHADOW HIT (no promotion) tracked for model=%s ns=%s sim=%.3f",
                        chosen,
                        ns,
                        sim_val,
                    )
                else:
                    result = dict(sem_res)
                    result["cached"] = True
                    result["cache_type"] = "semantic"
                    result["cache_info"] = cache_meta
                    _record_similarity(labels, chosen, float(result.get("similarity", 0.0)))
                    with contextlib.suppress(Exception):
                        metrics.SEMANTIC_CACHE_PREFETCH_USED.labels(**labels).inc()
                    metrics.LLM_CACHE_HITS.labels(**labels, model=chosen, provider=provider_family).inc()
                    try:
                        similarity_val = float(result.get("similarity", 0.0))
                    except Exception:
                        similarity_val = 0.0
                    service._adaptive_record_outcome(
                        state,
                        reward=0.0,
                        status="cache_hit",
                        metadata={"cache_type": "semantic", "similarity": similarity_val, "cache_info": cache_meta},
                    )
                    state.result = result
                    return result
            else:
                log.debug("semantic_cache_get MISS for model=%s ns=%s", chosen, ns)
                if shadow_mode:
                    try:
                        metrics.SEMANTIC_CACHE_SHADOW_MISSES.labels(**labels, model=chosen).inc()
                        service._update_shadow_hit_ratio(labels, is_hit=False)
                    except Exception:
                        pass
                    cache_meta_sem["status"] = "miss"
                else:
                    with contextlib.suppress(Exception):
                        metrics.LLM_CACHE_MISSES.labels(**labels, model=chosen, provider=provider_family).inc()
                    with contextlib.suppress(Exception):
                        metrics.SEMANTIC_CACHE_PREFETCH_ISSUED.labels(**labels).inc()
                    cache_meta_sem["status"] = "miss"
        except Exception:
            cache_meta_sem["status"] = "error"
    else:
        cache_meta.setdefault("semantic", {"status": "disabled"})
    if service.cache:
        norm_prompt = prompt

        def _sig(obj: Any) -> str:
            if isinstance(obj, dict):
                return "{" + ",".join(f"{key}:{_sig(obj[key])}" for key in sorted(obj)) + "}"
            if isinstance(obj, list):
                return "[" + ",".join(_sig(item) for item in obj) + "]"
            return str(obj)

        provider_sig = _sig(provider) if provider else "{}"
        cache_key = combine_keys(
            generate_key_from_params(
                task_type=task_type,
                prompt=norm_prompt,
                provider=provider_sig,
                namespace=state.namespace or "default:main",
            ),
            generate_key_from_params(system_prompt=getattr(service, "system_prompt", "") or ""),
        )
        state.cache_key = cache_key
        cached = service.cache.get(cache_key)
        cache_meta_redis = cache_meta.setdefault("redis", {"status": "pending"})
        if cached:
            result = dict(cached)
            result["cached"] = True
            metrics.LLM_CACHE_HITS.labels(**labels, model=result.get("model", chosen), provider=provider_family).inc()
            result.setdefault("cache_info", cache_meta)
            cache_meta_redis.update({"status": "hit", "cache_type": "redis"})
            service._adaptive_record_outcome(
                state, reward=0.0, status="cache_hit", metadata={"cache_type": "redis", "cache_info": cache_meta}
            )
            state.result = result
            return result
        cache_meta_redis["status"] = "miss"
    else:
        state.cache_key = None
        cache_meta.setdefault("redis", {"status": "disabled"})
    return None


def _record_similarity(labels: dict[str, str], _model: str, similarity: float) -> None:
    with contextlib.suppress(Exception):
        if similarity >= 0.9:
            bucket = ">=0.9"
        elif similarity >= 0.75:
            bucket = "0.75-0.9"
        else:
            bucket = "<0.75"
        metrics.SEMANTIC_CACHE_SIMILARITY.labels(**labels, bucket=bucket).observe(similarity)


def _record_cache_hit(
    labels: dict[str, str], model: str, provider_family: str, *, shadow_promoted: bool = False
) -> None:
    try:
        if shadow_promoted:
            metrics.CACHE_PROMOTIONS.labels(**labels, cache_name="semantic").inc()
            metrics.SEMANTIC_CACHE_PREFETCH_USED.labels(**labels).inc()
        metrics.LLM_CACHE_HITS.labels(**labels, model=model, provider=provider_family).inc()
    except Exception:
        pass
