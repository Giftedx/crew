"""Rate limiting middleware (fixed 1s window) for FastAPI shim.

Provides a very small fixed-window limiter primarily to satisfy tests. The
implementation is intentionally minimal and avoids pulling in heavier third
party primitives.

Behaviour:
    * Disabled unless the environment variable ENABLE_RATE_LIMITING is truthy.
    * Fixed one-second window with a simple counter that resets every second.
    * Excludes /metrics and /health endpoints from limiting for observability.

Configuration:
    * RATE_LIMIT_BURST or RATE_LIMIT_RPS: integer burst per second (default 10).

Typing & Optional Dependency Notes:
    The code can run without Starlette installed (tests using a FastAPI shim).
    We therefore provide a tiny dummy ``BaseHTTPMiddleware`` replacement when
    Starlette is absent. This keeps the public surface identical while avoiding
    ``type: ignore`` assignments to imported symbols.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request, Response


try:
    from server import middleware_shim
except ImportError:
    middleware_shim = None
from ultimate_discord_intelligence_bot.obs import metrics


try:
    from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
    from starlette.requests import Request as StarletteRequest
except Exception:

    class BaseHTTPMiddleware:
        """Minimal stand-in implementing Starlette's interface enough for tests.

        Provides an ASGI callable that wraps a `dispatch` coroutine method.
        """

        def __init__(self, app: Any) -> None:
            self.app = app

        async def __call__(self, scope: dict, receive: Callable, send: Callable):
            if scope.get("type") != "http":
                await self.app(scope, receive, send)
                return
            request = Request(scope, receive=receive)

            async def call_next(req: Request) -> Response:
                new_scope = dict(scope)
                req_scope = getattr(req, "scope", {})
                if isinstance(req_scope, dict):
                    new_scope.update({k: v for k, v in req_scope.items() if k in {"path", "raw_path", "query_string"}})
                    if "method" in req_scope:
                        new_scope["method"] = req_scope["method"]
                responder = await self.app(new_scope, receive, send)
                return responder

            response = await self.dispatch(request, call_next)
            if isinstance(response, Response):
                await response(scope, receive, send)

        async def dispatch(self, request: Request, call_next: Callable):
            return await call_next(request)

    StarletteRequest = Request
    RequestResponseEndpoint = Callable[[Request], Awaitable[Response]]


class FixedWindowRateLimiter(BaseHTTPMiddleware):
    """Simple fixed-window rate limiter middleware.

    Works with real Starlette (subclassing its BaseHTTPMiddleware) or with the
    lightweight dummy base when Starlette is absent (tests / shim mode).
    """

    def __init__(self, app: Any, burst: int) -> None:
        try:
            super().__init__(app)
        except Exception:
            self.app = app
        self._burst = max(1, burst)
        self._remaining = self._burst
        self._reset = time.monotonic() + 1.0

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Any:
        now = time.monotonic()
        raw_path = request.url.path
        _app = getattr(request, "app", None)
        _state = getattr(_app, "state", None) if _app else None
        metrics_path = None
        try:
            metrics_path = getattr(_state, "metrics_path", None) if _state else None
        except Exception:
            metrics_path = None
        if not metrics_path:
            metrics_path = os.getenv("PROMETHEUS_ENDPOINT_PATH") or "/metrics"
        mp_norm = str(metrics_path).rstrip("/") or "/metrics"
        rp_norm = raw_path.rstrip("/") or raw_path
        if (
            request.scope.get("_skip_rate_limit")
            or rp_norm == mp_norm
            or rp_norm == "/health"
            or rp_norm.startswith(mp_norm + "/")
        ):
            return await call_next(request)
        if now >= self._reset:
            self._remaining = self._burst
            self._reset = now + 1.0
        if self._remaining <= 0:
            try:
                _metrics = metrics.get_metrics()
                meth = getattr(request, "method", "GET")
                _metrics.RATE_LIMIT_REJECTIONS.labels(rp_norm, str(meth).upper()).inc()
            except Exception as exc:
                logging.debug("rate limit metrics error: %s", exc)
            return Response(status_code=429, content="Rate limit exceeded")
        self._remaining -= 1
        return await call_next(request)


def add_rate_limit_middleware(app: FastAPI) -> None:
    enable = os.getenv("ENABLE_RATE_LIMITING", "0").lower() in ("1", "true", "yes", "on")
    if not enable:
        return
    try:
        burst = int(os.getenv("RATE_LIMIT_BURST", os.getenv("RATE_LIMIT_RPS", "10")))
    except Exception:
        burst = 10
    if middleware_shim is not None:
        middleware_shim.install_middleware_support()
    from typing import cast as _cast

    app_any = _cast("Any", app)
    app_any.add_middleware(FixedWindowRateLimiter, burst=burst)


__all__ = ["add_rate_limit_middleware"]
