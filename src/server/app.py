"""FastAPI application factory.

The API is optional and only enabled when ``ENABLE_API=1`` (or any truthy
value) is set.  The factory wires:

* Settings injection
* Tracing initialisation (OTLP or console)
* Metrics middleware (histogram + counter) – guarded by flag
* Prometheus exposition endpoint (``/metrics`` by default) – guarded by flag
* Existing archive router
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response

from archive.discord_store.api import api_router
from core.settings import get_settings, Settings
from memory.qdrant_provider import get_qdrant_client
from obs import metrics
from obs.tracing import init_tracing
from security.rate_limit import TokenBucket


def _add_metrics_middleware(app: FastAPI, settings: Settings) -> None:
    if not settings.enable_http_metrics:
        return

    @app.middleware("http")
    async def _metrics_mw(request: Request, call_next: Callable):  # type: ignore[no-untyped-def]
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
        except Exception:  # pragma: no cover - defensive; metrics optional
            pass
        return response


def _add_rate_limit_middleware(app: FastAPI, settings: Settings) -> None:
    if not settings.enable_rate_limiting:
        return

    bucket = TokenBucket(rate=float(max(1, settings.rate_limit_rps)), capacity=max(settings.rate_limit_rps, settings.rate_limit_burst))

    @app.middleware("http")
    async def _rate_limit(request: Request, call_next: Callable):  # type: ignore[no-untyped-def]
        route = getattr(request.scope.get("route"), "path", request.url.path)
        # Allow scraping endpoint to bypass rate limiting so metrics remain observable
        if route == settings.prometheus_endpoint_path:
            return await call_next(request)
        key = request.client.host if request.client else "unknown"
        if not bucket.allow(key):
            # Attempt to record rejection metric if metrics enabled
            if settings.enable_http_metrics:
                try:  # pragma: no cover - defensive
                    metrics.RATE_LIMIT_REJECTIONS.labels(route, request.method).inc()
                except Exception:
                    pass
            return Response(status_code=429, content="Rate limit exceeded")
        return await call_next(request)


@asynccontextmanager
async def _lifespan(app: FastAPI):  # pragma: no cover - integration tested indirectly
    # Use fresh Settings to reflect any environment changes at process start.
    settings = Settings()
    if settings.enable_tracing:
        init_tracing(settings.service_name)
    # Force Qdrant client instantiation early to surface config errors
    try:
        get_qdrant_client()
    except Exception:
        pass  # optional; errors will surface when used
    yield
    # QdrantClient has no explicit close for http/grpc; rely on GC


def create_app(settings: Settings | None = None) -> FastAPI:
    # Construct fresh Settings unless caller supplies one so tests that mutate
    # os.environ after an earlier cached instance still see new values.
    settings = settings or Settings()
    app = FastAPI(title=settings.service_name, lifespan=_lifespan)

    # Routers
    app.include_router(api_router)

    # Metrics & tracing
    _add_metrics_middleware(app, settings)
    _add_rate_limit_middleware(app, settings)

    if settings.enable_prometheus_endpoint:

        @app.get(settings.prometheus_endpoint_path)
        def _metrics():  # type: ignore[no-untyped-def]
            return Response(
                content=metrics.render(), media_type="text/plain; version=0.0.4"
            )

    return app


__all__ = ["create_app"]
