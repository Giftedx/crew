from __future__ import annotations
import logging
import time
from typing import TYPE_CHECKING
from platform.cache.api_cache_middleware import APICacheMiddleware
from fastapi import FastAPI, Request, Response
from platform.observability import metrics
if TYPE_CHECKING:
    from collections.abc import Callable

def add_metrics_middleware(app: FastAPI, settings) -> None:
    if not getattr(settings, 'enable_http_metrics', False):
        return

    @app.middleware('http')
    async def _metrics_mw(request: Request, call_next: Callable):
        start = time.perf_counter()
        response: Response = await call_next(request)
        route = request.url.path
        if route == getattr(settings, 'prometheus_endpoint_path', '/metrics'):
            return response
        method = request.method
        dur_ms = (time.perf_counter() - start) * 1000
        try:
            metrics.HTTP_REQUEST_LATENCY.labels(route, method).observe(dur_ms)
            metrics.HTTP_REQUEST_COUNT.labels(route, method, str(response.status_code)).inc()
            if int(getattr(response, 'status_code', 0)) == 429:
                metrics.RATE_LIMIT_REJECTIONS.labels(route, method).inc()
        except Exception as exc:
            logging.debug('metrics middleware swallow error: %s', exc)
        return response

def add_api_cache_middleware(app: FastAPI, settings) -> None:
    """Add API response caching middleware."""
    if not getattr(settings, 'enable_advanced_cache', False):
        return
    try:
        ttl_api = getattr(settings, 'cache_ttl_api', None)
        if not isinstance(ttl_api, int) or ttl_api <= 0:
            from platform.cache.unified_config import get_unified_cache_config
            ttl_api = int(get_unified_cache_config().get_ttl_for_domain('tool'))
    except Exception:
        ttl_api = getattr(settings, 'cache_ttl_api', 300) if isinstance(getattr(settings, 'cache_ttl_api', None), int) else 300
    middleware_instance = APICacheMiddleware(cache_ttl=ttl_api, exclude_paths={'/health', '/metrics', '/pilot/run', '/activities/', '/activities/health', '/activities/echo'}, exclude_methods={'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'}, include_headers=['Authorization', 'X-API-Key'])

    @app.middleware('http')
    async def api_cache_middleware(request: Request, call_next):
        return await middleware_instance(request, call_next)

def add_cors_middleware(app: FastAPI, settings) -> None:
    """Minimal CORS support without external middleware dependencies."""
    try:
        import os as _os
        enable_cors = getattr(settings, 'enable_cors', False)
        if not enable_cors:
            enable_cors = _os.getenv('ENABLE_CORS', '0').lower() in {'1', 'true', 'yes', 'on'}
        if not enable_cors:
            return
        cfg_origins = getattr(settings, 'cors_allow_origins', None)
        origins: list[str] = []
        if isinstance(cfg_origins, list) and cfg_origins:
            origins = [str(o) for o in cfg_origins]
        else:
            raw = _os.getenv('CORS_ALLOW_ORIGINS', '')
            if raw:
                origins = [o.strip() for o in raw.split(',') if o.strip()]
        if not origins:
            origins = ['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:5174', 'http://127.0.0.1:5174']
        allowed = set(origins)

        @app.middleware('http')
        async def _cors_middleware(request: Request, call_next):
            origin = request.headers.get('origin')
            req_method = request.method
            if req_method == 'OPTIONS' and origin and (origin in allowed):
                acrm = request.headers.get('access-control-request-method', 'GET')
                headers = {'access-control-allow-origin': origin, 'access-control-allow-methods': acrm, 'access-control-allow-headers': request.headers.get('access-control-request-headers', '*'), 'access-control-allow-credentials': 'true'}
                return Response(status_code=200, headers=headers)
            response: Response = await call_next(request)
            if origin and origin in allowed:
                response.headers['access-control-allow-origin'] = origin
                response.headers['access-control-allow-credentials'] = 'true'
            return response

        @app.options('/{full_path:path}')
        def _cors_preflight(request: Request) -> Response:
            origin = request.headers.get('origin')
            if not origin or origin not in allowed:
                return Response(status_code=404)
            acrm = request.headers.get('access-control-request-method', 'GET')
            headers = {'access-control-allow-origin': origin, 'access-control-allow-methods': acrm, 'access-control-allow-headers': request.headers.get('access-control-request-headers', '*'), 'access-control-allow-credentials': 'true'}
            return Response(status_code=200, headers=headers)
    except Exception as exc:
        logging.debug('inline CORS middleware skipped: %s', exc)
__all__ = ['add_api_cache_middleware', 'add_cors_middleware', 'add_metrics_middleware']