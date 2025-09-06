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
from typing import Any, Protocol, runtime_checkable

from ultimate_discord_intelligence_bot.tenancy import current_tenant  # moved to top for E402 compliance

PROMETHEUS_AVAILABLE = False


@runtime_checkable
class MetricLike(Protocol):
    def labels(self, *args: Any, **kwargs: Any) -> MetricLike: ...
    def inc(self, *args: Any, **kwargs: Any) -> None: ...
    def observe(self, *args: Any, **kwargs: Any) -> None: ...
    def set(self, *args: Any, **kwargs: Any) -> None: ...


try:  # pragma: no cover - normal path
    from prometheus_client import REGISTRY, generate_latest
    from prometheus_client import Counter as _PromCounter
    from prometheus_client import Gauge as _PromGauge
    from prometheus_client import Histogram as _PromHistogram

    PROMETHEUS_AVAILABLE = True
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

_METRIC_SPECS: list[tuple[Callable[..., MetricLike], str, str, list[str]]] = [
    (CounterFactory, "router_decisions_total", "Number of routing decisions made", ["tenant", "workspace"]),
    (HistogramFactory, "llm_latency_ms", "Latency of LLM calls in milliseconds", ["tenant", "workspace"]),
    (
        CounterFactory,
        "llm_model_selected_total",
        "LLM model selections",
        ["tenant", "workspace", "task", "model", "provider"],
    ),
    (
        CounterFactory,
        "llm_budget_rejections_total",
        "LLM calls rejected due to budget",
        ["tenant", "workspace", "task", "provider"],
    ),
    (
        HistogramFactory,
        "llm_estimated_cost_usd",
        "Estimated cost (USD) of LLM calls",
        ["tenant", "workspace", "model", "provider"],
    ),
    (CounterFactory, "llm_cache_hits_total", "Total LLM cache hits", ["tenant", "workspace", "model", "provider"]),
    # Structured LLM metrics
    (
        CounterFactory,
        "structured_llm_requests_total",
        "Total structured LLM requests",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        CounterFactory,
        "structured_llm_success_total",
        "Total successful structured LLM responses",
        ["tenant", "workspace", "task", "method", "model"],
    ),
    (
        CounterFactory,
        "structured_llm_errors_total",
        "Total structured LLM errors by type",
        ["tenant", "workspace", "task", "method", "error_type"],
    ),
    (
        CounterFactory,
        "structured_llm_parsing_failures_total",
        "Total JSON parsing failures in structured responses",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        CounterFactory,
        "structured_llm_validation_failures_total",
        "Total Pydantic validation failures",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        CounterFactory,
        "structured_llm_instructor_usage_total",
        "Total usage of Instructor for structured outputs",
        ["tenant", "workspace", "task", "model"],
    ),
    (
        CounterFactory,
        "structured_llm_fallback_usage_total",
        "Total fallback to manual parsing",
        ["tenant", "workspace", "task", "model"],
    ),
    (
        HistogramFactory,
        "structured_llm_latency_ms",
        "Latency of structured LLM operations",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        HistogramFactory,
        "structured_llm_parsing_latency_ms",
        "Latency of JSON parsing operations",
        ["tenant", "workspace", "task"],
    ),
    # Streaming-specific metrics
    (
        CounterFactory,
        "structured_llm_streaming_requests_total",
        "Total streaming structured LLM requests",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        CounterFactory,
        "structured_llm_streaming_chunks_total",
        "Total streaming chunks processed",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        HistogramFactory,
        "structured_llm_streaming_latency_ms",
        "Latency of streaming structured LLM operations",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        HistogramFactory,
        "structured_llm_streaming_progress_ratio",
        "Progress ratio for streaming operations (0.0-1.0)",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        CounterFactory,
        "structured_llm_streaming_errors_total",
        "Total streaming structured LLM errors",
        ["tenant", "workspace", "task", "method", "error_type"],
    ),
    # Cache-specific metrics for structured LLM
    (
        CounterFactory,
        "structured_llm_cache_hits_total",
        "Total structured LLM cache hits",
        ["tenant", "workspace", "task", "method"],
    ),
    (
        CounterFactory,
        "structured_llm_cache_misses_total",
        "Total structured LLM cache misses",
        ["tenant", "workspace", "task", "method"],
    ),
    (HistogramFactory, "http_request_latency_ms", "Latency of inbound HTTP requests (FastAPI)", ["route", "method"]),
    (CounterFactory, "http_requests_total", "Total inbound HTTP requests", ["route", "method", "status"]),
    (
        CounterFactory,
        "rate_limit_rejections_total",
        "Total HTTP requests rejected due to rate limiting (429)",
        ["route", "method"],
    ),
    (
        CounterFactory,
        "http_retry_attempts_total",
        "Total HTTP retry attempts (excluding first attempt)",
        ["tenant", "workspace", "method", "host"],
    ),
    (
        CounterFactory,
        "http_retry_giveups_total",
        "Total HTTP operations that exhausted retries",
        ["tenant", "workspace", "method", "host"],
    ),
    # Pipeline-specific metrics
    (
        CounterFactory,
        "pipeline_requests_total",
        "Total pipeline processing requests",
        ["tenant", "workspace"],
    ),
    (
        CounterFactory,
        "pipeline_steps_completed_total",
        "Total pipeline steps completed successfully",
        ["tenant", "workspace", "step"],
    ),
    (
        CounterFactory,
        "pipeline_steps_failed_total",
        "Total pipeline steps that failed",
        ["tenant", "workspace", "step"],
    ),
    (
        CounterFactory,
        "pipeline_steps_skipped_total",
        "Total pipeline steps skipped",
        ["tenant", "workspace", "step"],
    ),
    (
        HistogramFactory,
        "pipeline_duration_seconds",
        "Duration of full pipeline processing",
        ["tenant", "workspace", "status"],
    ),
    (
        CounterFactory,
        "circuit_breaker_requests_total",
        "Circuit breaker outcomes",
        ["tenant", "workspace", "circuit", "result"],
    ),
    (
        GaugeFactory,
        "circuit_breaker_state",
        "Circuit breaker state (0=closed,0.5=half-open,1=open)",
        ["tenant", "workspace", "circuit"],
    ),
    # Ingest fallbacks (observability for resilience decisions)
    (
        CounterFactory,
        "ingest_transcript_fallbacks_total",
        "Count of transcript fallbacks to Whisper",
        ["tenant", "workspace", "source"],
    ),
    (
        CounterFactory,
        "ingest_missing_id_fallbacks_total",
        "Count of ingest runs missing episode_id (used URL-hash fallback)",
        ["tenant", "workspace", "source"],
    ),
    # Scheduler metrics
    (
        CounterFactory,
        "scheduler_enqueued_total",
        "Jobs enqueued by scheduler",
        ["tenant", "workspace", "source"],
    ),
    (
        CounterFactory,
        "scheduler_processed_total",
        "Jobs processed successfully by worker",
        ["tenant", "workspace", "source"],
    ),
    (
        CounterFactory,
        "scheduler_errors_total",
        "Worker errors while processing jobs",
        ["tenant", "workspace", "source"],
    ),
    (
        GaugeFactory,
        "scheduler_queue_backlog",
        "Current number of pending jobs in queue",
        ["tenant", "workspace"],
    ),
    (
        GaugeFactory,
        "system_health_score",
        "Overall system health score (0-100)",
        ["tenant", "workspace"],
    ),
    (
        GaugeFactory,
        "cost_per_interaction",
        "Average cost per user interaction in USD",
        ["tenant", "workspace"],
    ),
    # Cache performance metrics
    (
        CounterFactory,
        "cache_hits_total",
        "Total cache hits by cache and level",
        ["tenant", "workspace", "cache_name", "cache_level"],
    ),
    (
        CounterFactory,
        "cache_misses_total",
        "Total cache misses by cache and level",
        ["tenant", "workspace", "cache_name", "cache_level"],
    ),
    (
        CounterFactory,
        "cache_promotions_total",
        "Total entries promoted to higher cache level",
        ["tenant", "workspace", "cache_name"],
    ),
    (
        CounterFactory,
        "cache_demotions_total",
        "Total entries demoted to lower cache level",
        ["tenant", "workspace", "cache_name"],
    ),
    (
        CounterFactory,
        "cache_evictions_total",
        "Total entries evicted due to capacity limits",
        ["tenant", "workspace", "cache_name", "cache_level"],
    ),
    (
        CounterFactory,
        "cache_compressions_total",
        "Total entries compressed",
        ["tenant", "workspace", "cache_name"],
    ),
    (
        CounterFactory,
        "cache_decompressions_total",
        "Total entries decompressed",
        ["tenant", "workspace", "cache_name"],
    ),
    (
        CounterFactory,
        "cache_errors_total",
        "Total cache operation errors",
        ["tenant", "workspace", "cache_name", "operation", "error_type"],
    ),
    (
        GaugeFactory,
        "cache_size_bytes",
        "Current cache size in bytes",
        ["tenant", "workspace", "cache_name", "cache_level"],
    ),
    (
        GaugeFactory,
        "cache_entries_count",
        "Current number of entries in cache",
        ["tenant", "workspace", "cache_name", "cache_level"],
    ),
    (
        GaugeFactory,
        "cache_hit_rate_ratio",
        "Current cache hit rate (0.0-1.0)",
        ["tenant", "workspace", "cache_name", "cache_level"],
    ),
    (
        GaugeFactory,
        "cache_memory_usage_ratio",
        "Cache memory usage ratio (0.0-1.0)",
        ["tenant", "workspace", "cache_name", "cache_level"],
    ),
    (
        HistogramFactory,
        "cache_operation_latency_ms",
        "Latency of cache operations in milliseconds",
        ["tenant", "workspace", "cache_name", "operation"],
    ),
    (
        HistogramFactory,
        "cache_compression_ratio",
        "Compression effectiveness ratio (compressed/original)",
        ["tenant", "workspace", "cache_name"],
    ),
]


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
    for ctor, name, help_text, labels in _METRIC_SPECS:
        try:
            obj = ctor(name, help_text, labels, registry=registry)
        except ValueError as e:  # duplicate series: purge then retry once
            if "Duplicated timeseries" in str(e):
                _purge_existing([spec[1] for spec in _METRIC_SPECS])
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
    PIPELINE_REQUESTS,
    PIPELINE_STEPS_COMPLETED,
    PIPELINE_STEPS_FAILED,
    PIPELINE_STEPS_SKIPPED,
    PIPELINE_DURATION,
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
) = _instantiate_metrics()

_COLLECTORS: list[MetricLike] = [
    ROUTER_DECISIONS,
    LLM_LATENCY,
    LLM_MODEL_SELECTED,
    LLM_BUDGET_REJECTIONS,
    LLM_ESTIMATED_COST,
    LLM_CACHE_HITS,
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
    PIPELINE_REQUESTS,
    PIPELINE_STEPS_COMPLETED,
    PIPELINE_STEPS_FAILED,
    PIPELINE_STEPS_SKIPPED,
    PIPELINE_DURATION,
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
]


def reset() -> None:
    """Reset metrics state for tests.

    For the real client we remove prior collectors from the global registry
    (touching a private mapping guarded by ``hasattr``); then we recreate
    metric objects bound to module globals. Downstream modules reference the
    *names*, so re-binding keeps them in sync.
    """
    global ROUTER_DECISIONS, LLM_LATENCY, LLM_MODEL_SELECTED, LLM_BUDGET_REJECTIONS, LLM_ESTIMATED_COST, LLM_CACHE_HITS  # noqa: PLW0603 - module level metric rebinding required for reset semantics in tests
    global STRUCTURED_LLM_REQUESTS, STRUCTURED_LLM_SUCCESS, STRUCTURED_LLM_ERRORS, STRUCTURED_LLM_PARSING_FAILURES, STRUCTURED_LLM_VALIDATION_FAILURES, STRUCTURED_LLM_INSTRUCTOR_USAGE, STRUCTURED_LLM_FALLBACK_USAGE, STRUCTURED_LLM_LATENCY, STRUCTURED_LLM_PARSING_LATENCY, STRUCTURED_LLM_STREAMING_REQUESTS, STRUCTURED_LLM_STREAMING_CHUNKS, STRUCTURED_LLM_STREAMING_LATENCY, STRUCTURED_LLM_STREAMING_PROGRESS, STRUCTURED_LLM_STREAMING_ERRORS, STRUCTURED_LLM_CACHE_HITS, STRUCTURED_LLM_CACHE_MISSES  # noqa: PLW0603
    global HTTP_REQUEST_LATENCY, HTTP_REQUEST_COUNT, RATE_LIMIT_REJECTIONS, HTTP_RETRY_ATTEMPTS, HTTP_RETRY_GIVEUPS  # noqa: PLW0603
    global PIPELINE_REQUESTS, PIPELINE_STEPS_COMPLETED, PIPELINE_STEPS_FAILED, PIPELINE_STEPS_SKIPPED, PIPELINE_DURATION  # noqa: PLW0603
    global CIRCUIT_BREAKER_REQUESTS, CIRCUIT_BREAKER_STATE, INGEST_TRANSCRIPT_FALLBACKS, INGEST_MISSING_ID_FALLBACKS, SCHEDULER_ENQUEUED, SCHEDULER_PROCESSED, SCHEDULER_ERRORS, SCHEDULER_QUEUE_BACKLOG, SYSTEM_HEALTH_SCORE, COST_PER_INTERACTION  # noqa: PLW0603
    global CACHE_HITS, CACHE_MISSES, CACHE_PROMOTIONS, CACHE_DEMOTIONS, CACHE_EVICTIONS, CACHE_COMPRESSIONS, CACHE_DECOMPRESSIONS, CACHE_ERRORS, CACHE_SIZE_BYTES, CACHE_ENTRIES_COUNT, CACHE_HIT_RATE_RATIO, CACHE_MEMORY_USAGE_RATIO, CACHE_OPERATION_LATENCY, CACHE_COMPRESSION_RATIO, _COLLECTORS  # noqa: PLW0603
    if PROMETHEUS_AVAILABLE:
        # Attempt to unregister existing collectors; failures are logged but not fatal.
        to_unreg = list(_COLLECTORS)
        for c in to_unreg:
            if hasattr(registry, "unregister"):
                try:
                    registry.unregister(c)  # type: ignore[arg-type]
                except Exception as exc:  # pragma: no cover - defensive
                    logging.debug("metrics: reset unregister failed: %s", exc)
        _purge_existing([spec[1] for spec in _METRIC_SPECS])
    objs = _instantiate_metrics()
    (
        ROUTER_DECISIONS,
        LLM_LATENCY,
        LLM_MODEL_SELECTED,
        LLM_BUDGET_REJECTIONS,
        LLM_ESTIMATED_COST,
        LLM_CACHE_HITS,
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
        PIPELINE_REQUESTS,
        PIPELINE_STEPS_COMPLETED,
        PIPELINE_STEPS_FAILED,
        PIPELINE_STEPS_SKIPPED,
        PIPELINE_DURATION,
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
    ) = objs
    _COLLECTORS = list(objs)


def label_ctx() -> dict[str, str]:
    ctx = current_tenant()
    if ctx:
        return {"tenant": ctx.tenant_id, "workspace": ctx.workspace_id}
    return {"tenant": "unknown", "workspace": "unknown"}


def render() -> bytes:
    """Return Prometheus exposition for current registry (global)."""
    if PROMETHEUS_AVAILABLE:
        data = generate_latest(REGISTRY)  # type: ignore[arg-type]
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
    "PIPELINE_REQUESTS",
    "PIPELINE_STEPS_COMPLETED",
    "PIPELINE_STEPS_FAILED",
    "PIPELINE_STEPS_SKIPPED",
    "PIPELINE_DURATION",
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
    "reset",
    "render",
    "registry",
    "label_ctx",
]
