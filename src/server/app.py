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

import logging
import time
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from server.middleware_shim import install_middleware_support

# Ensure middleware support available for local FastAPI shim
install_middleware_support()

try:
    from archive.discord_store.api import api_router  # type: ignore
except Exception:  # pragma: no cover - optional dependency path
    api_router = None  # type: ignore
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


from core.cache.api_cache_middleware import APICacheMiddleware
from memory.qdrant_provider import get_qdrant_client
from obs import metrics
from obs.enhanced_monitoring import start_monitoring_system, stop_monitoring_system
from obs.tracing import init_tracing

from ops.alert_adapter import alert_router
from server.rate_limit import add_rate_limit_middleware


def _add_metrics_middleware(app: FastAPI, settings: Settings) -> None:
    if not settings.enable_http_metrics:
        return

    @app.middleware("http")
    async def _metrics_mw(request: Request, call_next: Callable):
        start = time.perf_counter()
        response: Response = await call_next(request)
        route = getattr(request.scope.get("route"), "path", request.url.path)
        if route == settings.prometheus_endpoint_path:
            return response  # avoid self instrumentation to keep metrics stable
        method = request.method
        dur_ms = (time.perf_counter() - start) * 1000
        try:
            metrics.HTTP_REQUEST_LATENCY.labels(route, method).observe(dur_ms)
            metrics.HTTP_REQUEST_COUNT.labels(route, method, str(response.status_code)).inc()
        except Exception as exc:  # pragma: no cover - defensive; metrics optional
            logging.debug("metrics middleware swallow error: %s", exc)
        return response


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

    # Force Qdrant client instantiation early to surface config errors
    try:
        get_qdrant_client()
    except Exception:
        logging.debug("qdrant pre-init failed (will retry lazily): {exc}")

    yield

    # Shutdown monitoring system
    try:
        await stop_monitoring_system()
        logging.info("Enhanced monitoring system stopped")
    except Exception as exc:
        logging.warning(f"Failed to stop enhanced monitoring system: {exc}")

    # QdrantClient has no explicit close for http/grpc; rely on GC


def _add_api_cache_middleware(app: FastAPI, settings: Settings) -> None:
    """Add API response caching middleware."""
    if not getattr(settings, "enable_advanced_cache", False):
        return

    # Create middleware instance
    middleware_instance = APICacheMiddleware(
        cache_ttl=getattr(settings, "cache_ttl_api", 300),
        exclude_paths={"/health", "/metrics"},
        exclude_methods={"POST", "PUT", "DELETE", "PATCH"},
        include_headers=["Authorization", "X-API-Key"],
    )

    # Add as FastAPI middleware using decorator pattern
    @app.middleware("http")
    async def api_cache_middleware(request: Request, call_next):
        return await middleware_instance(request, call_next)


def create_app(settings: Settings | None = None) -> FastAPI:
    # Construct fresh Settings unless caller supplies one so tests that mutate
    # os.environ after an earlier cached instance still see new values.
    settings = settings or Settings()
    app = FastAPI(title=settings.service_name, lifespan=_lifespan)

    # Routers (archive API optional in minimal test environments)
    if api_router is not None:
        try:
            app.include_router(api_router)
        except Exception as exc:
            logging.debug(f"Failed to include archive API router: {exc}")
    app.include_router(alert_router)

    # Metrics & tracing (ensure metrics route can be registered before rate limiting so it is always observable)
    _add_metrics_middleware(app, settings)
    _add_api_cache_middleware(app, settings)

    # Prometheus endpoint registration with environment fallback (shim settings may not load env)
    enable_prom = getattr(settings, "enable_prometheus_endpoint", False)
    if not enable_prom:
        import os as _os

        enable_prom = _os.getenv("ENABLE_PROMETHEUS_ENDPOINT", "0").lower() in ("1", "true", "yes", "on")
    if enable_prom:
        path = getattr(settings, "prometheus_endpoint_path", "/metrics")
        # Pydantic FieldInfo may leak through if Settings not fully instantiated; coerce to str
        try:
            from pydantic.fields import FieldInfo  # type: ignore

            if isinstance(path, FieldInfo):  # type: ignore
                path = getattr(path, "default", "/metrics")  # type: ignore
        except Exception:  # pragma: no cover - pydantic absent
            pass

        @app.get(str(path))
        def _metrics():  # noqa: D401
            data = metrics.render()
            return Response(data, status_code=200, media_type="text/plain; version=0.0.4")

        # Persist metrics path to application state so middleware without reliable path
        # information can still exclude it.
        try:  # pragma: no cover - defensive
            app.state.metrics_path = str(path)  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover
            setattr(app, "_metrics_path", str(path))

        # Bypass middleware no longer required: shim now propagates real path in scope.

    # Install rate limit middleware after metrics route so it can still exclude it based on path.
    add_rate_limit_middleware(app)

    @app.get("/health")
    def _health() -> dict[str, str]:
        return {"status": "ok"}

    # Removed experimental catch-all; middleware now consistently handles 404s.

    return app


__all__ = ["create_app"]
