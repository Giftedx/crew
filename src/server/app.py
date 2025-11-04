"""FastAPI application factory.

This project ships an optional API service. In containerized setups (docker-compose,
Kubernetes) the API runs when the service is started. Feature exposure (metrics,
tracing, rate limiting, Prometheus endpoint) is controlled by environment flags
in settings. The factory wires:

* Settings injection
* Tracing initialisation (OTLP or console)
* Metrics middleware (histogram + counter) - guarded by flag
* Prometheus exposition endpoint (``/metrics`` by default) - guarded by flag
* Existing archive router
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

# Early bootstrap to avoid stdlib/platform name clash
try:
    from ultimate_discord_intelligence_bot.core.bootstrap import ensure_platform_proxy  # type: ignore
except Exception:
    ensure_platform_proxy = None  # type: ignore
if callable(ensure_platform_proxy):  # type: ignore
    try:
        ensure_platform_proxy()  # type: ignore
    except Exception:
        pass

from platform.observability.logfire_config import setup_logfire

from fastapi import FastAPI
from server.middleware_shim import install_middleware_support


install_middleware_support()
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
    from platform.config.settings import Settings
except Exception:

    class Settings:
        service_name: str = "service"
        enable_http_metrics: bool = False
        enable_rate_limiting: bool = False
        enable_tracing: bool = False
        enable_prometheus_endpoint: bool = False
        prometheus_endpoint_path: str = "/metrics"
        rate_limit_redis_url: str | None = None
        rate_limit_rps: int = 10
        rate_limit_burst: int = 10
        enable_cors: bool = False
        cors_allow_origins: list[str] | None = None


from platform.observability.enhanced_monitoring import start_monitoring_system, stop_monitoring_system
from platform.observability.tracing import init_tracing

from domains.memory.vector.qdrant import get_qdrant_client
from server.rate_limit import add_rate_limit_middleware

from .middleware import add_api_cache_middleware, add_cors_middleware, add_metrics_middleware


@asynccontextmanager
async def _lifespan(app: FastAPI):
    settings = Settings()
    if settings.enable_tracing:
        init_tracing(settings.service_name)
    try:
        await start_monitoring_system()
        logging.info("Enhanced monitoring system started")
    except Exception as exc:
        logging.warning(f"Failed to start enhanced monitoring system: {exc}")
    try:
        setup_logfire(app)
    except Exception as exc:
        logging.debug(f"Logfire setup skipped: {exc}")
    try:
        get_qdrant_client()
    except Exception as exc:
        logging.debug(f"qdrant pre-init failed (will retry lazily): {exc}")
    yield
    try:
        await stop_monitoring_system()
        logging.info("Enhanced monitoring system stopped")
    except Exception as exc:
        logging.warning(f"Failed to stop enhanced monitoring system: {exc}")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title=settings.service_name, lifespan=_lifespan)
    register_archive_routes(app)
    register_alert_routes(app)
    register_a2a_router(app, settings)
    register_pipeline_routes(app, settings)
    register_autointel_routes(app, settings)
    register_performance_dashboard(app)
    add_cors_middleware(app, settings)
    add_metrics_middleware(app, settings)
    add_api_cache_middleware(app, settings)
    register_metrics_endpoint(app, settings)
    add_rate_limit_middleware(app)
    register_pilot_route(app, settings)
    register_health_routes(app)
    register_activities_echo(app, settings)
    return app


__all__ = ["create_app"]
