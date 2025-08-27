"""Prometheus metrics helpers.

The real `prometheus_client` package is optional for basic operation.  Tests
and local development in this repository should not require manually installing
the dependency; therefore this module falls back to lightweight no-op stubs
whenever the import is unavailable.  The public API (`Counter`, `Histogram`,
``generate_latest``) is preserved so downstream code does not need additional
guards.
"""

from __future__ import annotations

try:  # pragma: no cover - exercised via import in tests
    from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except Exception:  # pragma: no cover - missing optional dependency
    PROMETHEUS_AVAILABLE = False

    class _NoOpMetric:
        def labels(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            return self

        def inc(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            return None

        def observe(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            return None

    class _NoOpRegistry:  # pragma: no cover - simple container
        pass

    def Counter(*args, **kwargs):  # type: ignore[no-untyped-def]
        return _NoOpMetric()

    def Histogram(*args, **kwargs):  # type: ignore[no-untyped-def]
        return _NoOpMetric()

    def CollectorRegistry(*args, **kwargs):  # type: ignore[no-untyped-def]
        return _NoOpRegistry()

    def generate_latest(registry):  # type: ignore[no-untyped-def]
        return b""

from ultimate_discord_intelligence_bot.tenancy import current_tenant

registry = CollectorRegistry()

# Basic metrics used in tests and router instrumentation
ROUTER_DECISIONS = Counter(
    "router_decisions_total",
    "Number of routing decisions made",
    ["tenant", "workspace"],
    registry=registry,
)
LLM_LATENCY = Histogram(
    "llm_latency_ms",
    "Latency of LLM calls in milliseconds",
    ["tenant", "workspace"],
    registry=registry,
)


def reset() -> None:
    """Reset the metrics registry (for tests)."""
    global registry, ROUTER_DECISIONS, LLM_LATENCY
    registry = CollectorRegistry()
    ROUTER_DECISIONS = Counter(
        "router_decisions_total", "Number of routing decisions made", ["tenant", "workspace"], registry=registry
    )
    LLM_LATENCY = Histogram(
        "llm_latency_ms", "Latency of LLM calls in milliseconds", ["tenant", "workspace"], registry=registry
    )


def label_ctx():
    ctx = current_tenant()
    if ctx:
        return {"tenant": ctx.tenant_id, "workspace": ctx.workspace_id}
    return {"tenant": "unknown", "workspace": "unknown"}


def render() -> bytes:
    """Return the current metrics exposition in Prometheus text format."""
    return generate_latest(registry)


__all__ = ["ROUTER_DECISIONS", "LLM_LATENCY", "reset", "render", "registry", "label_ctx"]
