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
        exclude_paths={"/health", "/metrics", "/pilot/run"},
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

    # Optional: A2A JSON-RPC adapter (disabled by default; enable via env)
    try:
        import os as _os

        if _os.getenv("ENABLE_A2A_API", "0").lower() in ("1", "true", "yes", "on"):
            try:
                from server.a2a_router import router as a2a_router  # type: ignore

                app.include_router(a2a_router)
            except Exception as exc:  # pragma: no cover - optional path
                logging.debug("a2a router wiring skipped: %s", exc)
    except Exception:  # pragma: no cover - environment access issues
        pass

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

    # Optional: LangGraph pilot API endpoint for quick orchestration demo
    try:
        import os as _os

        if _os.getenv("ENABLE_LANGGRAPH_PILOT_API", "0").lower() in ("1", "true", "yes", "on"):
            try:
                from graphs.langgraph_pilot import run_ingest_analysis_pilot  # type: ignore

                @app.get("/pilot/run")
                def _pilot_run(request: Request) -> dict:
                    """Trigger the pilot with minimal stub functions.

                    Query params 'tenant' and 'workspace' are optional and default
                    to 'default'/'main' when not supplied.
                    """

                    def _ingest(job: dict) -> dict:
                        """Simulate ingest step returning logical vector namespace.

                        Uses VectorStore.namespace for consistency with memory layer so that
                        downstream components (if wired later) can rely on identical formatting.
                        """
                        t = job.get("tenant", "default")
                        w = job.get("workspace", "main")
                        # Defensive: legacy/test shim may have injected a Request object if
                        # handler signature misaligned; coerce non-string values to defaults.
                        if not isinstance(t, str):
                            t = "default"
                        if not isinstance(w, str):
                            w = "main"
                        try:
                            from memory.vector_store import (
                                VectorStore,  # local import to avoid heavy deps at import time
                            )

                            ns = VectorStore.namespace(t, w, "pilot")
                        except Exception:  # pragma: no cover - fallback if import fails
                            ns = f"{t}:{w}:pilot"
                        return {"chunks": 2, "namespace": ns}

                    def _analyze(ctx: dict) -> dict:
                        n = int(ctx.get("chunks", 0))
                        return {"insights": n * 2}

                    def _segment(ctx: dict) -> dict:
                        # Derive a fake chunks detail to simulate segmentation
                        n = int(ctx.get("chunks", 0))
                        return {"segments": n * 4}

                    def _embed(ctx: dict) -> dict:
                        # Simulate embedding count derived from segments if present
                        segs = int(ctx.get("segments", 0))
                        return {"embeddings": max(segs, 1)}

                    # Extract tenant/workspace from query params since the lightweight test shim
                    # does not inject query arguments as named function parameters.
                    q = getattr(request, "query_params", {}) if request is not None else {}
                    tenant_val = q.get("tenant", "default") if isinstance(q, dict) else "default"
                    workspace_val = q.get("workspace", "main") if isinstance(q, dict) else "main"
                    # Optional feature toggles derived from query for demo purposes
                    enable_segment = (
                        q.get("enable_segment") in ("1", "true", "yes", "on") if isinstance(q, dict) else False
                    )
                    enable_embed = q.get("enable_embed") in ("1", "true", "yes", "on") if isinstance(q, dict) else False
                    if not isinstance(tenant_val, str):  # defensive
                        tenant_val = "default"
                    if not isinstance(workspace_val, str):
                        workspace_val = "main"
                    job = {"tenant": tenant_val, "workspace": workspace_val}
                    seg_fn = _segment if enable_segment else None
                    emb_fn = _embed if enable_embed else None
                    t0 = time.perf_counter()
                    out = run_ingest_analysis_pilot(job, _ingest, _analyze, segment_fn=seg_fn, embed_fn=emb_fn)
                    try:
                        out["duration_seconds"] = max(0.0, time.perf_counter() - t0)
                    except Exception:
                        pass
                    return out
            except Exception as exc:  # pragma: no cover - optional path
                logging.debug("pilot api wiring skipped: %s", exc)
    except Exception:  # pragma: no cover - environment access issues
        pass

    @app.get("/health")
    def _health() -> dict[str, str]:
        return {"status": "ok"}

    # Removed experimental catch-all; middleware now consistently handles 404s.

    return app


__all__ = ["create_app"]
