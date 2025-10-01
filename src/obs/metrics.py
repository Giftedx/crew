"""Prometheus metrics helpers.

Design goals:
 - Optional dependency: if ``prometheus_client`` is absent provide inert no-op
     counters/histograms so core logic proceeds without guard clauses.
 - Test determinism: ``reset()`` reinitializes metric objects so unit tests can
     assert fresh series counts. For the real client we remove previous collectors
     from the global registry (using private internals guarded defensively).
 - Single source of truth: tools / services import *module attributes* (not
     individual counters) so rebinding inside ``reset`` is reflected everywhere.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from typing import Any, Protocol, cast, runtime_checkable


# Resolve current_tenant dynamically to work in both dev (tests import via 'src.*')
# and installed package contexts (imports via 'ultimate_discord_intelligence_bot.*').
def _resolve_current_tenant():
    try:
        import importlib

        for name in (
            # Prefer installed package path first to share the same thread-local with runtime/tests
            "ultimate_discord_intelligence_bot.tenancy.context",
            # Fallback to src path for direct execution contexts
            "src.ultimate_discord_intelligence_bot.tenancy.context",
        ):
            try:
                mod = importlib.import_module(name)
                ct = getattr(mod, "current_tenant", None)
                if callable(ct):
                    return ct
            except Exception:
                continue
    except Exception:
        pass

    def _none():  # pragma: no cover - trivial
        return None

    return _none


_current_tenant_fn = _resolve_current_tenant()

PROMETHEUS_AVAILABLE = False
REGISTRY: Any  # will be bound below
generate_latest: Callable[[Any], bytes]


@runtime_checkable
class MetricLike(Protocol):
    def labels(self, *args: Any, **kwargs: Any) -> MetricLike: ...
    def inc(self, *args: Any, **kwargs: Any) -> None: ...
    def observe(self, *args: Any, **kwargs: Any) -> None: ...
    def set(self, *args: Any, **kwargs: Any) -> None: ...


try:  # pragma: no cover - normal path
    from prometheus_client import REGISTRY as _PROM_REGISTRY
    from prometheus_client import Counter as _PromCounter
    from prometheus_client import Gauge as _PromGauge
    from prometheus_client import Histogram as _PromHistogram
    from prometheus_client import generate_latest as _prom_generate_latest

    PROMETHEUS_AVAILABLE = True
    REGISTRY = cast(Any, _PROM_REGISTRY)
    generate_latest = cast(Callable[[Any], bytes], _prom_generate_latest)
    CounterFactory: Callable[..., MetricLike] = _PromCounter  # type: ignore[assignment]
    HistogramFactory: Callable[..., MetricLike] = _PromHistogram  # type: ignore[assignment]
    GaugeFactory: Callable[..., MetricLike] = _PromGauge  # type: ignore[assignment]
except Exception:  # pragma: no cover - fallback path

    class _NoOpMetric:
        def labels(self, *args: Any, **kwargs: Any) -> _NoOpMetric:
            return self

        def inc(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - no-op
            return None

        def observe(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - no-op
            return None

        def set(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - no-op
            return None

    class _NoOpRegistry:
        _names_to_collectors: dict[str, _NoOpMetric] = {}

        def unregister(self, collector: Any) -> None:
            # No-op implementation
            pass

    REGISTRY = _NoOpRegistry()

    def _no_op_generate_latest(_registry: object = None) -> bytes:
        return b""

    def _no_op_counter(*_args: Any, **_kwargs: Any) -> _NoOpMetric:
        return _NoOpMetric()

    def _no_op_histogram(*_args: Any, **_kwargs: Any) -> _NoOpMetric:
        return _NoOpMetric()

    def _no_op_gauge(*_args: Any, **_kwargs: Any) -> _NoOpMetric:
        return _NoOpMetric()

    generate_latest = _no_op_generate_latest
    CounterFactory = _no_op_counter
    HistogramFactory = _no_op_histogram
    GaugeFactory = _no_op_gauge


# Public alias retained for backward compatibility (some code imports registry)
registry = REGISTRY

try:
    from .metric_specs import METRIC_SPECS as _SPEC_TUPLES  # type: ignore
except Exception:  # pragma: no cover - fallback if relative import fails
    from obs.metric_specs import METRIC_SPECS as _SPEC_TUPLES  # type: ignore

# Build runtime specs mapping underlying factories based on 'kind'.
_KIND_TO_FACTORY: dict[str, Callable[..., MetricLike]] = {
    "counter": cast(Callable[..., MetricLike], None),  # fill below
    "histogram": cast(Callable[..., MetricLike], None),
    "gauge": cast(Callable[..., MetricLike], None),
}
_KIND_TO_FACTORY["counter"] = cast(Callable[..., MetricLike], "CounterFactory")  # type: ignore[assignment]
_KIND_TO_FACTORY["histogram"] = cast(Callable[..., MetricLike], "HistogramFactory")  # type: ignore[assignment]
_KIND_TO_FACTORY["gauge"] = cast(Callable[..., MetricLike], "GaugeFactory")  # type: ignore[assignment]


def _resolve_factory(kind: str) -> Callable[..., MetricLike]:
    if kind == "counter":
        return cast(Callable[..., MetricLike], CounterFactory)
    if kind == "histogram":
        return cast(Callable[..., MetricLike], HistogramFactory)
    if kind == "gauge":
        return cast(Callable[..., MetricLike], GaugeFactory)
    raise ValueError(f"Unknown metric kind: {kind}")


def _purge_existing(metric_names: Sequence[str]) -> None:  # pragma: no cover - defensive
    """Remove any existing collectors whose names would collide.

    Needed when the module is reloaded mid-test (tests simulate missing
    prometheus_client then reload the real implementation). We have no
    handle to prior collector objects, so we inspect registry internals.
    """
    if not PROMETHEUS_AVAILABLE:  # no-op metrics do not register
        return
    names_map = getattr(registry, "_names_to_collectors", None)
    if not names_map:  # unexpected structure
        return
    seen: set[object] = set()
    for n, collector in list(names_map.items()):
        if (any(n.startswith(base.rstrip("_total")) or n == base for base in metric_names)) and (collector not in seen):
            try:
                registry.unregister(collector)
            except Exception as exc:
                logging.debug("metrics: purge unregister failed for %s: %s", n, exc)
            seen.add(collector)


def _instantiate_metrics() -> list[MetricLike]:
    objs: list[MetricLike] = []
    for kind, name, help_text, labels in _SPEC_TUPLES:
        ctor = _resolve_factory(kind)
        try:
            obj = ctor(name, help_text, labels, registry=registry)
        except ValueError as e:  # duplicate series: purge then retry once
            if "Duplicated timeseries" in str(e):
                _purge_existing([spec[1] for spec in _SPEC_TUPLES])
                obj = ctor(name, help_text, labels, registry=registry)
            else:
                raise
        objs.append(obj)
    return objs


# Create metrics initially
(
    ROUTER_DECISIONS,
    LLM_LATENCY,
    LLM_MODEL_SELECTED,
    LLM_BUDGET_REJECTIONS,
    LLM_ESTIMATED_COST,
    LLM_CACHE_HITS,
    LLM_CACHE_MISSES,
    STRUCTURED_LLM_REQUESTS,
    STRUCTURED_LLM_SUCCESS,
    STRUCTURED_LLM_ERRORS,
    STRUCTURED_LLM_PARSING_FAILURES,
    STRUCTURED_LLM_VALIDATION_FAILURES,
    STRUCTURED_LLM_INSTRUCTOR_USAGE,
    STRUCTURED_LLM_FALLBACK_USAGE,
    STRUCTURED_LLM_LATENCY,
    STRUCTURED_LLM_PARSING_LATENCY,
    STRUCTURED_LLM_STREAMING_REQUESTS,
    STRUCTURED_LLM_STREAMING_CHUNKS,
    STRUCTURED_LLM_STREAMING_LATENCY,
    STRUCTURED_LLM_STREAMING_PROGRESS,
    STRUCTURED_LLM_STREAMING_ERRORS,
    STRUCTURED_LLM_CACHE_HITS,
    STRUCTURED_LLM_CACHE_MISSES,
    HTTP_REQUEST_LATENCY,
    HTTP_REQUEST_COUNT,
    RATE_LIMIT_REJECTIONS,
    HTTP_RETRY_ATTEMPTS,
    HTTP_RETRY_GIVEUPS,
    TENANCY_FALLBACKS,
    PIPELINE_REQUESTS,
    PIPELINE_STEPS_COMPLETED,
    PIPELINE_STEPS_FAILED,
    PIPELINE_STEPS_SKIPPED,
    PIPELINE_DURATION,
    PIPELINE_STEP_DURATION,
    PIPELINE_TOTAL_DURATION,
    PIPELINE_INFLIGHT,
    CIRCUIT_BREAKER_REQUESTS,
    CIRCUIT_BREAKER_STATE,
    INGEST_TRANSCRIPT_FALLBACKS,
    INGEST_MISSING_ID_FALLBACKS,
    SCHEDULER_ENQUEUED,
    SCHEDULER_PROCESSED,
    SCHEDULER_ERRORS,
    SCHEDULER_QUEUE_BACKLOG,
    SYSTEM_HEALTH_SCORE,
    COST_PER_INTERACTION,
    CACHE_HITS,
    CACHE_MISSES,
    CACHE_PROMOTIONS,
    CACHE_DEMOTIONS,
    CACHE_EVICTIONS,
    CACHE_COMPRESSIONS,
    CACHE_DECOMPRESSIONS,
    CACHE_ERRORS,
    CACHE_SIZE_BYTES,
    CACHE_ENTRIES_COUNT,
    CACHE_HIT_RATE_RATIO,
    CACHE_MEMORY_USAGE_RATIO,
    CACHE_OPERATION_LATENCY,
    CACHE_COMPRESSION_RATIO,
    SEGMENT_CHUNK_SIZE_CHARS,
    SEGMENT_CHUNK_SIZE_TOKENS,
    SEGMENT_CHUNK_MERGES,
    EMBED_DEDUPLICATES_SKIPPED,
    DEGRADATION_EVENTS,
    DEGRADATION_IMPACT_LATENCY,
    RETRIEVAL_SELECTED_K,
    RETRIEVAL_LATENCY,
    PROMPT_COMPRESSION_RATIO,
    SEMANTIC_CACHE_SIMILARITY,
    SEMANTIC_CACHE_PREFETCH_ISSUED,
    SEMANTIC_CACHE_PREFETCH_USED,
    SEMANTIC_CACHE_SHADOW_HITS,
    SEMANTIC_CACHE_SHADOW_MISSES,
    SEMANTIC_CACHE_SHADOW_HIT_RATIO,
    RL_REWARD_LATENCY_GAP,
    ACTIVE_BANDIT_POLICY,
    EXPERIMENT_VARIANT_ALLOCATIONS,
    EXPERIMENT_REWARDS,
    EXPERIMENT_REWARD_VALUE,
    EXPERIMENT_REGRET,
    EXPERIMENT_PHASE_STATUS,
    TRAJECTORY_EVALUATIONS,
    ADVANCED_BANDIT_REWARD_MODEL_MSE,
    ADVANCED_BANDIT_TREE_DEPTH,
    ADVANCED_BANDIT_IMPORTANCE_WEIGHT,
    ADVANCED_BANDIT_CONFIDENCE_INTERVAL,
    PROMPT_COMPRESSION_TARGET_MET,
    PROMPT_EMERGENCY_TRUNCATIONS,
) = _instantiate_metrics()

_COLLECTORS: list[MetricLike] = [
    ROUTER_DECISIONS,
    LLM_LATENCY,
    LLM_MODEL_SELECTED,
    LLM_BUDGET_REJECTIONS,
    LLM_ESTIMATED_COST,
    LLM_CACHE_HITS,
    LLM_CACHE_MISSES,
    STRUCTURED_LLM_REQUESTS,
    STRUCTURED_LLM_SUCCESS,
    STRUCTURED_LLM_ERRORS,
    STRUCTURED_LLM_PARSING_FAILURES,
    STRUCTURED_LLM_VALIDATION_FAILURES,
    STRUCTURED_LLM_INSTRUCTOR_USAGE,
    STRUCTURED_LLM_FALLBACK_USAGE,
    STRUCTURED_LLM_LATENCY,
    STRUCTURED_LLM_PARSING_LATENCY,
    STRUCTURED_LLM_STREAMING_REQUESTS,
    STRUCTURED_LLM_STREAMING_CHUNKS,
    STRUCTURED_LLM_STREAMING_LATENCY,
    STRUCTURED_LLM_STREAMING_PROGRESS,
    STRUCTURED_LLM_STREAMING_ERRORS,
    STRUCTURED_LLM_CACHE_HITS,
    STRUCTURED_LLM_CACHE_MISSES,
    HTTP_REQUEST_LATENCY,
    HTTP_REQUEST_COUNT,
    RATE_LIMIT_REJECTIONS,
    HTTP_RETRY_ATTEMPTS,
    HTTP_RETRY_GIVEUPS,
    TENANCY_FALLBACKS,
    PIPELINE_REQUESTS,
    PIPELINE_STEPS_COMPLETED,
    PIPELINE_STEPS_FAILED,
    PIPELINE_STEPS_SKIPPED,
    PIPELINE_DURATION,
    PIPELINE_STEP_DURATION,
    PIPELINE_TOTAL_DURATION,
    PIPELINE_INFLIGHT,
    CIRCUIT_BREAKER_REQUESTS,
    CIRCUIT_BREAKER_STATE,
    INGEST_TRANSCRIPT_FALLBACKS,
    INGEST_MISSING_ID_FALLBACKS,
    SCHEDULER_ENQUEUED,
    SCHEDULER_PROCESSED,
    SCHEDULER_ERRORS,
    SCHEDULER_QUEUE_BACKLOG,
    SYSTEM_HEALTH_SCORE,
    COST_PER_INTERACTION,
    CACHE_HITS,
    CACHE_MISSES,
    CACHE_PROMOTIONS,
    CACHE_DEMOTIONS,
    CACHE_EVICTIONS,
    CACHE_COMPRESSIONS,
    CACHE_DECOMPRESSIONS,
    CACHE_ERRORS,
    CACHE_SIZE_BYTES,
    CACHE_ENTRIES_COUNT,
    CACHE_HIT_RATE_RATIO,
    CACHE_MEMORY_USAGE_RATIO,
    CACHE_OPERATION_LATENCY,
    CACHE_COMPRESSION_RATIO,
    SEGMENT_CHUNK_SIZE_CHARS,
    SEGMENT_CHUNK_SIZE_TOKENS,
    SEGMENT_CHUNK_MERGES,
    EMBED_DEDUPLICATES_SKIPPED,
    DEGRADATION_EVENTS,
    DEGRADATION_IMPACT_LATENCY,
    RETRIEVAL_SELECTED_K,
    RETRIEVAL_LATENCY,
    PROMPT_COMPRESSION_RATIO,
    SEMANTIC_CACHE_SIMILARITY,
    SEMANTIC_CACHE_PREFETCH_ISSUED,
    SEMANTIC_CACHE_PREFETCH_USED,
    SEMANTIC_CACHE_SHADOW_HITS,
    SEMANTIC_CACHE_SHADOW_MISSES,
    SEMANTIC_CACHE_SHADOW_HIT_RATIO,
    RL_REWARD_LATENCY_GAP,
    ACTIVE_BANDIT_POLICY,
    EXPERIMENT_VARIANT_ALLOCATIONS,
    EXPERIMENT_REWARDS,
    EXPERIMENT_REWARD_VALUE,
    EXPERIMENT_REGRET,
    EXPERIMENT_PHASE_STATUS,
    TRAJECTORY_EVALUATIONS,
    ADVANCED_BANDIT_REWARD_MODEL_MSE,
    ADVANCED_BANDIT_TREE_DEPTH,
    ADVANCED_BANDIT_IMPORTANCE_WEIGHT,
    ADVANCED_BANDIT_CONFIDENCE_INTERVAL,
    PROMPT_COMPRESSION_TARGET_MET,
    PROMPT_EMERGENCY_TRUNCATIONS,
]


def reset() -> None:
    """Reset metrics state for tests.

    For the real client we remove prior collectors from the global registry
    (touching a private mapping guarded by ``hasattr``); then we recreate
    metric objects bound to module globals. Downstream modules reference the
    *names*, so re-binding keeps them in sync.
    """
    global ROUTER_DECISIONS, LLM_LATENCY, LLM_MODEL_SELECTED, LLM_BUDGET_REJECTIONS, LLM_ESTIMATED_COST, LLM_CACHE_HITS, LLM_CACHE_MISSES  # noqa: PLW0603 - module level metric rebinding required for reset semantics in tests
    global STRUCTURED_LLM_REQUESTS, STRUCTURED_LLM_SUCCESS, STRUCTURED_LLM_ERRORS, STRUCTURED_LLM_PARSING_FAILURES, STRUCTURED_LLM_VALIDATION_FAILURES, STRUCTURED_LLM_INSTRUCTOR_USAGE, STRUCTURED_LLM_FALLBACK_USAGE, STRUCTURED_LLM_LATENCY, STRUCTURED_LLM_PARSING_LATENCY, STRUCTURED_LLM_STREAMING_REQUESTS, STRUCTURED_LLM_STREAMING_CHUNKS, STRUCTURED_LLM_STREAMING_LATENCY, STRUCTURED_LLM_STREAMING_PROGRESS, STRUCTURED_LLM_STREAMING_ERRORS, STRUCTURED_LLM_CACHE_HITS, STRUCTURED_LLM_CACHE_MISSES  # noqa: PLW0603
    global HTTP_REQUEST_LATENCY, HTTP_REQUEST_COUNT, RATE_LIMIT_REJECTIONS, HTTP_RETRY_ATTEMPTS, HTTP_RETRY_GIVEUPS, TENANCY_FALLBACKS  # noqa: PLW0603
    global PIPELINE_REQUESTS, PIPELINE_STEPS_COMPLETED, PIPELINE_STEPS_FAILED, PIPELINE_STEPS_SKIPPED, PIPELINE_DURATION, PIPELINE_STEP_DURATION, PIPELINE_TOTAL_DURATION, PIPELINE_INFLIGHT  # noqa: PLW0603
    global CIRCUIT_BREAKER_REQUESTS, CIRCUIT_BREAKER_STATE, INGEST_TRANSCRIPT_FALLBACKS, INGEST_MISSING_ID_FALLBACKS, SCHEDULER_ENQUEUED, SCHEDULER_PROCESSED, SCHEDULER_ERRORS, SCHEDULER_QUEUE_BACKLOG, SYSTEM_HEALTH_SCORE, COST_PER_INTERACTION  # noqa: PLW0603
    global CACHE_HITS, CACHE_MISSES, CACHE_PROMOTIONS, CACHE_DEMOTIONS, CACHE_EVICTIONS, CACHE_COMPRESSIONS, CACHE_DECOMPRESSIONS, CACHE_ERRORS, CACHE_SIZE_BYTES, CACHE_ENTRIES_COUNT, CACHE_HIT_RATE_RATIO, CACHE_MEMORY_USAGE_RATIO, CACHE_OPERATION_LATENCY, CACHE_COMPRESSION_RATIO, SEGMENT_CHUNK_SIZE_CHARS, SEGMENT_CHUNK_SIZE_TOKENS, SEGMENT_CHUNK_MERGES, EMBED_DEDUPLICATES_SKIPPED, DEGRADATION_EVENTS, DEGRADATION_IMPACT_LATENCY, _COLLECTORS  # noqa: PLW0603
    global RETRIEVAL_SELECTED_K, RETRIEVAL_LATENCY, PROMPT_COMPRESSION_RATIO, SEMANTIC_CACHE_SIMILARITY, SEMANTIC_CACHE_PREFETCH_ISSUED, SEMANTIC_CACHE_PREFETCH_USED, SEMANTIC_CACHE_SHADOW_HITS, SEMANTIC_CACHE_SHADOW_MISSES, SEMANTIC_CACHE_SHADOW_HIT_RATIO, RL_REWARD_LATENCY_GAP, ACTIVE_BANDIT_POLICY  # noqa: PLW0603
    global EXPERIMENT_VARIANT_ALLOCATIONS, EXPERIMENT_REWARDS, EXPERIMENT_REWARD_VALUE, EXPERIMENT_REGRET, EXPERIMENT_PHASE_STATUS, TRAJECTORY_EVALUATIONS, ADVANCED_BANDIT_REWARD_MODEL_MSE, ADVANCED_BANDIT_TREE_DEPTH, ADVANCED_BANDIT_IMPORTANCE_WEIGHT, ADVANCED_BANDIT_CONFIDENCE_INTERVAL  # noqa: PLW0603
    global PROMPT_COMPRESSION_TARGET_MET, PROMPT_EMERGENCY_TRUNCATIONS  # noqa: PLW0603
    if PROMETHEUS_AVAILABLE:
        # Attempt to unregister existing collectors; failures are logged but not fatal.
        to_unreg = list(_COLLECTORS)
        for c in to_unreg:
            if hasattr(registry, "unregister"):
                try:
                    registry.unregister(c)
                except Exception as exc:  # pragma: no cover - defensive
                    logging.debug("metrics: reset unregister failed: %s", exc)
    _purge_existing([spec[1] for spec in _SPEC_TUPLES])
    objs = _instantiate_metrics()
    (
        ROUTER_DECISIONS,
        LLM_LATENCY,
        LLM_MODEL_SELECTED,
        LLM_BUDGET_REJECTIONS,
        LLM_ESTIMATED_COST,
        LLM_CACHE_HITS,
        LLM_CACHE_MISSES,
        STRUCTURED_LLM_REQUESTS,
        STRUCTURED_LLM_SUCCESS,
        STRUCTURED_LLM_ERRORS,
        STRUCTURED_LLM_PARSING_FAILURES,
        STRUCTURED_LLM_VALIDATION_FAILURES,
        STRUCTURED_LLM_INSTRUCTOR_USAGE,
        STRUCTURED_LLM_FALLBACK_USAGE,
        STRUCTURED_LLM_LATENCY,
        STRUCTURED_LLM_PARSING_LATENCY,
        STRUCTURED_LLM_STREAMING_REQUESTS,
        STRUCTURED_LLM_STREAMING_CHUNKS,
        STRUCTURED_LLM_STREAMING_LATENCY,
        STRUCTURED_LLM_STREAMING_PROGRESS,
        STRUCTURED_LLM_STREAMING_ERRORS,
        STRUCTURED_LLM_CACHE_HITS,
        STRUCTURED_LLM_CACHE_MISSES,
        HTTP_REQUEST_LATENCY,
        HTTP_REQUEST_COUNT,
        RATE_LIMIT_REJECTIONS,
        HTTP_RETRY_ATTEMPTS,
        HTTP_RETRY_GIVEUPS,
        TENANCY_FALLBACKS,
        PIPELINE_REQUESTS,
        PIPELINE_STEPS_COMPLETED,
        PIPELINE_STEPS_FAILED,
        PIPELINE_STEPS_SKIPPED,
        PIPELINE_DURATION,
        PIPELINE_STEP_DURATION,
        PIPELINE_TOTAL_DURATION,
        PIPELINE_INFLIGHT,
        CIRCUIT_BREAKER_REQUESTS,
        CIRCUIT_BREAKER_STATE,
        INGEST_TRANSCRIPT_FALLBACKS,
        INGEST_MISSING_ID_FALLBACKS,
        SCHEDULER_ENQUEUED,
        SCHEDULER_PROCESSED,
        SCHEDULER_ERRORS,
        SCHEDULER_QUEUE_BACKLOG,
        SYSTEM_HEALTH_SCORE,
        COST_PER_INTERACTION,
        CACHE_HITS,
        CACHE_MISSES,
        CACHE_PROMOTIONS,
        CACHE_DEMOTIONS,
        CACHE_EVICTIONS,
        CACHE_COMPRESSIONS,
        CACHE_DECOMPRESSIONS,
        CACHE_ERRORS,
        CACHE_SIZE_BYTES,
        CACHE_ENTRIES_COUNT,
        CACHE_HIT_RATE_RATIO,
        CACHE_MEMORY_USAGE_RATIO,
        CACHE_OPERATION_LATENCY,
        CACHE_COMPRESSION_RATIO,
        SEGMENT_CHUNK_SIZE_CHARS,
        SEGMENT_CHUNK_SIZE_TOKENS,
        SEGMENT_CHUNK_MERGES,
        EMBED_DEDUPLICATES_SKIPPED,
        DEGRADATION_EVENTS,
        DEGRADATION_IMPACT_LATENCY,
        RETRIEVAL_SELECTED_K,
        RETRIEVAL_LATENCY,
        PROMPT_COMPRESSION_RATIO,
        SEMANTIC_CACHE_SIMILARITY,
        SEMANTIC_CACHE_PREFETCH_ISSUED,
        SEMANTIC_CACHE_PREFETCH_USED,
        SEMANTIC_CACHE_SHADOW_HITS,
        SEMANTIC_CACHE_SHADOW_MISSES,
        SEMANTIC_CACHE_SHADOW_HIT_RATIO,
        RL_REWARD_LATENCY_GAP,
        ACTIVE_BANDIT_POLICY,
        EXPERIMENT_VARIANT_ALLOCATIONS,
        EXPERIMENT_REWARDS,
        EXPERIMENT_REWARD_VALUE,
        EXPERIMENT_REGRET,
        EXPERIMENT_PHASE_STATUS,
        TRAJECTORY_EVALUATIONS,
        ADVANCED_BANDIT_REWARD_MODEL_MSE,
        ADVANCED_BANDIT_TREE_DEPTH,
        ADVANCED_BANDIT_IMPORTANCE_WEIGHT,
        ADVANCED_BANDIT_CONFIDENCE_INTERVAL,
        PROMPT_COMPRESSION_TARGET_MET,
        PROMPT_EMERGENCY_TRUNCATIONS,
    ) = objs
    _COLLECTORS = list(objs)


def label_ctx() -> dict[str, str]:
    ctx = _current_tenant_fn()
    if ctx:
        return {"tenant": ctx.tenant_id, "workspace": ctx.workspace_id}
    return {"tenant": "unknown", "workspace": "unknown"}


def render() -> bytes:
    """Return Prometheus exposition for current registry (global)."""
    if PROMETHEUS_AVAILABLE:
        data = generate_latest(REGISTRY)
        return data if isinstance(data, bytes) else bytes(str(data), "utf-8")
    else:
        return b""


__all__ = [
    "ROUTER_DECISIONS",
    "LLM_LATENCY",
    "LLM_MODEL_SELECTED",
    "LLM_BUDGET_REJECTIONS",
    "LLM_ESTIMATED_COST",
    "LLM_CACHE_HITS",
    "LLM_CACHE_MISSES",
    "STRUCTURED_LLM_REQUESTS",
    "STRUCTURED_LLM_SUCCESS",
    "STRUCTURED_LLM_ERRORS",
    "STRUCTURED_LLM_PARSING_FAILURES",
    "STRUCTURED_LLM_VALIDATION_FAILURES",
    "STRUCTURED_LLM_INSTRUCTOR_USAGE",
    "STRUCTURED_LLM_FALLBACK_USAGE",
    "STRUCTURED_LLM_LATENCY",
    "STRUCTURED_LLM_PARSING_LATENCY",
    "STRUCTURED_LLM_STREAMING_REQUESTS",
    "STRUCTURED_LLM_STREAMING_CHUNKS",
    "STRUCTURED_LLM_STREAMING_LATENCY",
    "STRUCTURED_LLM_STREAMING_PROGRESS",
    "STRUCTURED_LLM_STREAMING_ERRORS",
    "STRUCTURED_LLM_CACHE_HITS",
    "STRUCTURED_LLM_CACHE_MISSES",
    "HTTP_REQUEST_LATENCY",
    "HTTP_REQUEST_COUNT",
    "RATE_LIMIT_REJECTIONS",
    "HTTP_RETRY_ATTEMPTS",
    "HTTP_RETRY_GIVEUPS",
    "TENANCY_FALLBACKS",
    "PIPELINE_REQUESTS",
    "PIPELINE_STEPS_COMPLETED",
    "PIPELINE_STEPS_FAILED",
    "PIPELINE_STEPS_SKIPPED",
    "PIPELINE_DURATION",
    "PIPELINE_STEP_DURATION",
    "PIPELINE_TOTAL_DURATION",
    "PIPELINE_INFLIGHT",
    "CIRCUIT_BREAKER_REQUESTS",
    "CIRCUIT_BREAKER_STATE",
    "INGEST_TRANSCRIPT_FALLBACKS",
    "INGEST_MISSING_ID_FALLBACKS",
    "SCHEDULER_ENQUEUED",
    "SCHEDULER_PROCESSED",
    "SCHEDULER_ERRORS",
    "SCHEDULER_QUEUE_BACKLOG",
    "SYSTEM_HEALTH_SCORE",
    "COST_PER_INTERACTION",
    "CACHE_HITS",
    "CACHE_MISSES",
    "CACHE_PROMOTIONS",
    "CACHE_DEMOTIONS",
    "CACHE_EVICTIONS",
    "CACHE_COMPRESSIONS",
    "CACHE_DECOMPRESSIONS",
    "CACHE_ERRORS",
    "CACHE_SIZE_BYTES",
    "CACHE_ENTRIES_COUNT",
    "CACHE_HIT_RATE_RATIO",
    "CACHE_MEMORY_USAGE_RATIO",
    "CACHE_OPERATION_LATENCY",
    "CACHE_COMPRESSION_RATIO",
    "SEGMENT_CHUNK_SIZE_CHARS",
    "SEGMENT_CHUNK_SIZE_TOKENS",
    "SEGMENT_CHUNK_MERGES",
    "EMBED_DEDUPLICATES_SKIPPED",
    "DEGRADATION_EVENTS",
    "DEGRADATION_IMPACT_LATENCY",
    "RETRIEVAL_SELECTED_K",
    "RETRIEVAL_LATENCY",
    "PROMPT_COMPRESSION_RATIO",
    "SEMANTIC_CACHE_SIMILARITY",
    "SEMANTIC_CACHE_PREFETCH_ISSUED",
    "SEMANTIC_CACHE_PREFETCH_USED",
    "SEMANTIC_CACHE_SHADOW_HITS",
    "SEMANTIC_CACHE_SHADOW_MISSES",
    "SEMANTIC_CACHE_SHADOW_HIT_RATIO",
    "RL_REWARD_LATENCY_GAP",
    "ACTIVE_BANDIT_POLICY",
    "EXPERIMENT_VARIANT_ALLOCATIONS",
    "EXPERIMENT_REWARDS",
    "EXPERIMENT_REWARD_VALUE",
    "EXPERIMENT_REGRET",
    "EXPERIMENT_PHASE_STATUS",
    "TRAJECTORY_EVALUATIONS",
    "ADVANCED_BANDIT_REWARD_MODEL_MSE",
    "ADVANCED_BANDIT_TREE_DEPTH",
    "ADVANCED_BANDIT_IMPORTANCE_WEIGHT",
    "ADVANCED_BANDIT_CONFIDENCE_INTERVAL",
    "PROMPT_COMPRESSION_TARGET_MET",
    "PROMPT_EMERGENCY_TRUNCATIONS",
    "reset",
    "render",
    "registry",
    "label_ctx",
]
