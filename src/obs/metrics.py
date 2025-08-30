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

try:  # pragma: no cover - normal path
    from prometheus_client import REGISTRY, generate_latest
    from prometheus_client import Counter as _PromCounter
    from prometheus_client import Histogram as _PromHistogram
    PROMETHEUS_AVAILABLE = True
    CounterFactory: Callable[..., MetricLike] = _PromCounter  # type: ignore[assignment]
    HistogramFactory: Callable[..., MetricLike] = _PromHistogram  # type: ignore[assignment]
except Exception:  # pragma: no cover - fallback path
    class _NoOpMetric:
        def labels(self, *args: Any, **kwargs: Any) -> _NoOpMetric:
            return self
        def inc(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - no-op
            return None
        def observe(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - no-op
            return None

    class _NoOpRegistry:
        _names_to_collectors: dict[str, _NoOpMetric] = {}

    REGISTRY = _NoOpRegistry()  # type: ignore[assignment]

    def _no_op_generate_latest(_registry: object = None) -> bytes:
        return b""

    def _no_op_counter(*_args: Any, **_kwargs: Any) -> _NoOpMetric:
        return _NoOpMetric()

    def _no_op_histogram(*_args: Any, **_kwargs: Any) -> _NoOpMetric:
        return _NoOpMetric()

    generate_latest = _no_op_generate_latest  # type: ignore[assignment]
    CounterFactory = _no_op_counter
    HistogramFactory = _no_op_histogram


# Public alias retained for backward compatibility (some code imports registry)
registry = REGISTRY

_METRIC_SPECS: list[tuple[Callable[..., MetricLike], str, str, list[str]]] = [
    (CounterFactory, "router_decisions_total", "Number of routing decisions made", ["tenant", "workspace"]),
    (HistogramFactory, "llm_latency_ms", "Latency of LLM calls in milliseconds", ["tenant", "workspace"]),
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
        ["tenant", "workspace", "method"],
    ),
    (
    CounterFactory,
        "http_retry_giveups_total",
        "Total HTTP operations that exhausted retries",
        ["tenant", "workspace", "method"],
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
    HTTP_REQUEST_LATENCY,
    HTTP_REQUEST_COUNT,
    RATE_LIMIT_REJECTIONS,
    HTTP_RETRY_ATTEMPTS,
    HTTP_RETRY_GIVEUPS,
) = _instantiate_metrics()

_COLLECTORS: list[MetricLike] = [
    ROUTER_DECISIONS,
    LLM_LATENCY,
    HTTP_REQUEST_LATENCY,
    HTTP_REQUEST_COUNT,
    RATE_LIMIT_REJECTIONS,
    HTTP_RETRY_ATTEMPTS,
    HTTP_RETRY_GIVEUPS,
]


def reset() -> None:
    """Reset metrics state for tests.

    For the real client we remove prior collectors from the global registry
    (touching a private mapping guarded by ``hasattr``); then we recreate
    metric objects bound to module globals. Downstream modules reference the
    *names*, so re-binding keeps them in sync.
    """
    global ROUTER_DECISIONS, LLM_LATENCY, HTTP_RETRY_ATTEMPTS, HTTP_RETRY_GIVEUPS  # noqa: PLW0603 - module level metric rebinding required for reset semantics in tests
    global HTTP_REQUEST_LATENCY, HTTP_REQUEST_COUNT, RATE_LIMIT_REJECTIONS, _COLLECTORS  # noqa: PLW0603
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
        HTTP_REQUEST_LATENCY,
        HTTP_REQUEST_COUNT,
        RATE_LIMIT_REJECTIONS,
        HTTP_RETRY_ATTEMPTS,
        HTTP_RETRY_GIVEUPS,
    ) = objs
    _COLLECTORS = list(objs)


def label_ctx() -> dict[str, str]:
    ctx = current_tenant()
    if ctx:
        return {"tenant": ctx.tenant_id, "workspace": ctx.workspace_id}
    return {"tenant": "unknown", "workspace": "unknown"}


def render() -> bytes:
    """Return Prometheus exposition for current registry (global)."""
    data = generate_latest(REGISTRY)
    return data if isinstance(data, bytes) else bytes(str(data), "utf-8")


__all__ = [
    "ROUTER_DECISIONS",
    "LLM_LATENCY",
    "HTTP_RETRY_ATTEMPTS",
    "HTTP_RETRY_GIVEUPS",
    "reset",
    "render",
    "registry",
    "label_ctx",
    "HTTP_REQUEST_LATENCY",
    "HTTP_REQUEST_COUNT",
    "RATE_LIMIT_REJECTIONS",
]
