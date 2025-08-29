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
    from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest

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

# HTTP request instrumentation (added when enable_http_metrics flag is on)
HTTP_REQUEST_LATENCY = Histogram(
    "http_request_latency_ms",
    "Latency of inbound HTTP requests (FastAPI)",
    ["route", "method"],
    registry=registry,
)
HTTP_REQUEST_COUNT = Counter(
    "http_requests_total", "Total inbound HTTP requests", ["route", "method", "status"], registry=registry
)

# Rate limit rejections (429) – only incremented if rate limiting enabled
RATE_LIMIT_REJECTIONS = Counter(
    "rate_limit_rejections_total",
    "Total HTTP requests rejected due to rate limiting (429)",
    ["route", "method"],
    registry=registry,
)

# HTTP retry metrics (populated only when retry flag enabled)
HTTP_RETRY_ATTEMPTS = Counter(
    "http_retry_attempts_total",
    "Total HTTP retry attempts (excluding first attempt)",
    ["tenant", "workspace", "method"],
    registry=registry,
)
HTTP_RETRY_GIVEUPS = Counter(
    "http_retry_giveups_total",
    "Total HTTP operations that exhausted retries",
    ["tenant", "workspace", "method"],
    registry=registry,
)


def reset() -> None:
    """Reset the metrics registry (for tests)."""
    global registry, ROUTER_DECISIONS, LLM_LATENCY, HTTP_RETRY_ATTEMPTS, HTTP_RETRY_GIVEUPS, HTTP_REQUEST_LATENCY, HTTP_REQUEST_COUNT, RATE_LIMIT_REJECTIONS
    registry = CollectorRegistry()
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
    HTTP_REQUEST_LATENCY = Histogram(
        "http_request_latency_ms",
        "Latency of inbound HTTP requests (FastAPI)",
        ["route", "method"],
        registry=registry,
    )
    HTTP_REQUEST_COUNT = Counter(
        "http_requests_total",
        "Total inbound HTTP requests",
        ["route", "method", "status"],
        registry=registry,
    )
    RATE_LIMIT_REJECTIONS = Counter(
        "rate_limit_rejections_total",
        "Total HTTP requests rejected due to rate limiting (429)",
        ["route", "method"],
        registry=registry,
    )
    HTTP_RETRY_ATTEMPTS = Counter(
        "http_retry_attempts_total",
        "Total HTTP retry attempts (excluding first attempt)",
        ["tenant", "workspace", "method"],
        registry=registry,
    )
    HTTP_RETRY_GIVEUPS = Counter(
        "http_retry_giveups_total",
        "Total HTTP operations that exhausted retries",
        ["tenant", "workspace", "method"],
        registry=registry,
    )


def label_ctx():
    ctx = current_tenant()
    if ctx:
        return {"tenant": ctx.tenant_id, "workspace": ctx.workspace_id}
    return {"tenant": "unknown", "workspace": "unknown"}


def render() -> bytes:
    """Return the current metrics exposition in Prometheus text format."""
    return generate_latest(registry)


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
