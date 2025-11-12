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

import contextlib
import logging
from contextlib import asynccontextmanager


# Early bootstrap to avoid stdlib/platform name clash
try:
    from ultimate_discord_intelligence_bot.core.bootstrap import ensure_platform_proxy  # type: ignore
except Exception:
    ensure_platform_proxy = None  # type: ignore
if callable(ensure_platform_proxy):  # type: ignore
    with contextlib.suppress(Exception):
        ensure_platform_proxy()  # type: ignore

from fastapi import FastAPI
# Skip middleware_shim for API server to avoid ASGI compatibility issues
# from server.middleware_shim import install_middleware_support
from ultimate_discord_intelligence_bot.obs.logfire_config import setup_logfire


# Only install middleware support for testing, not for production API server
# The middleware_shim breaks ASGI compatibility needed for uvicorn
# if __name__ == "__main__":  # Only when run directly (testing)
#     install_middleware_support()
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
from server.middleware import add_api_cache_middleware, add_cors_middleware, add_metrics_middleware
from server.rate_limit import add_rate_limit_middleware


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


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = Settings()

    app = FastAPI(title=settings.service_name)

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
