"""FastAPI application factory.

This project ships an optional API service. In containerized setups (docker-compose,
Kubernetes) the API runs when the service is started. Feature exposure (metrics,
tracing, rate limiting, Prometheus endpoint) is controlled by environment flags
in settings. The factory wires:

* Settings injection
* Tracing initialisation (OTLP or console)
* Metrics middleware (histogram + counter) – guarded by flag
* Prometheus exposition endpoint (``/metrics`` by default) – guarded by flag
* Existing archive router
"""

from __future__ import annotations

# ruff: noqa: E402
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from obs.logfire_config import setup_logfire
from server.middleware_shim import install_middleware_support


# Ensure middleware support available for local FastAPI shim
install_middleware_support()

# Route registrars (modularized)
from server.routes import (
    register_a2a_router,
    register_activities_echo,
    register_alert_routes,
    register_archive_routes,
    register_autointel_routes,
    register_health_routes,
    register_metrics_endpoint,
    register_performance_dashboard,
    register_pilot_route,
    register_pipeline_routes,
)


try:
    from core.settings import Settings  # type: ignore
except Exception:  # pragma: no cover - fallback when pydantic unavailable

    class Settings:  # type: ignore[no-redef]
        service_name: str = "service"
        enable_http_metrics: bool = False
        enable_rate_limiting: bool = False
        enable_tracing: bool = False
        enable_prometheus_endpoint: bool = False
        prometheus_endpoint_path: str = "/metrics"
        rate_limit_redis_url: str | None = None
        rate_limit_rps: int = 10
        rate_limit_burst: int = 10
        # Optional CORS support
        enable_cors: bool = False
        cors_allow_origins: list[str] | None = None


from memory.qdrant_provider import get_qdrant_client
from obs.enhanced_monitoring import (
    start_monitoring_system,
    stop_monitoring_system,
)
from obs.tracing import init_tracing
from server.rate_limit import add_rate_limit_middleware

from .middleware import (
    add_api_cache_middleware,
    add_cors_middleware,
    add_metrics_middleware,
)


# moved to server/middleware.py: add_metrics_middleware


# from server.rate_limit import add_rate_limit_middleware  # legacy middleware unused after inline limiter


@asynccontextmanager
async def _lifespan(app: FastAPI):  # pragma: no cover - integration tested indirectly
    # Use fresh Settings to reflect any environment changes at process start.
    settings = Settings()
    if settings.enable_tracing:
        init_tracing(settings.service_name)

        # Start enhanced monitoring system
    try:
        await start_monitoring_system()
        logging.info("Enhanced monitoring system started")
    except Exception as exc:
        logging.warning(f"Failed to start enhanced monitoring system: {exc}")

    # Initialize Logfire observability if enabled (safe no-op otherwise)
    try:
        setup_logfire(app)
    except Exception as exc:
        logging.debug(f"Logfire setup skipped: {exc}")

    # Force Qdrant client instantiation early to surface config errors
    try:
        get_qdrant_client()
    except Exception as exc:
        logging.debug(f"qdrant pre-init failed (will retry lazily): {exc}")

    yield

    # Shutdown monitoring system
    try:
        await stop_monitoring_system()
        logging.info("Enhanced monitoring system stopped")
    except Exception as exc:
        logging.warning(f"Failed to stop enhanced monitoring system: {exc}")

    # QdrantClient has no explicit close for http/grpc; rely on GC


# moved to server/middleware.py: add_api_cache_middleware


# moved to server/middleware.py: add_cors_middleware


def create_app(settings: Settings | None = None) -> FastAPI:
    # Construct fresh Settings unless caller supplies one so tests that mutate
    # os.environ after an earlier cached instance still see new values.
    settings = settings or Settings()
    app = FastAPI(title=settings.service_name, lifespan=_lifespan)

    # Routers
    register_archive_routes(app)
    register_alert_routes(app)
    register_a2a_router(app, settings)
    register_pipeline_routes(app, settings)
    register_autointel_routes(app, settings)
    register_performance_dashboard(app)

    # Optional: CORS for local Activities or web clients (inline middleware)
    # Register CORS EARLY so preflight (OPTIONS) can be intercepted reliably before other middlewares
    add_cors_middleware(app, settings)

    # Metrics & tracing (ensure metrics route can be registered before rate limiting so it is always observable)
    add_metrics_middleware(app, settings)
    add_api_cache_middleware(app, settings)
    # Prometheus endpoint registration with environment fallback
    register_metrics_endpoint(app, settings)

    # Install rate limit middleware after metrics route so it can still exclude it based on path.
    add_rate_limit_middleware(app)

    # Optional: LangGraph pilot API endpoint for quick orchestration demo
    register_pilot_route(app, settings)

    # Health routes
    register_health_routes(app)

    # Optional debug echo endpoint for Activities/web clients
    # Optional debug echo endpoint for Activities/web clients
    register_activities_echo(app, settings)

    # Removed experimental catch-all; middleware now consistently handles 404s.

    return app


__all__ = ["create_app"]
