"""Rate limiting middleware (fixed 1s window) for FastAPI shim.

Provides a very small fixed-window limiter primarily to satisfy tests.
If ENABLE_RATE_LIMITING is not set, no middleware is registered.
Environment variables:
  RATE_LIMIT_BURST / RATE_LIMIT_RPS determine per-second allowance.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request, Response
from obs import metrics
from server import middleware_shim

# Detect real Starlette middleware base to integrate with FastAPI's stack when
# available. Falls back to shim-style class used by middleware_shim during tests.
try:  # pragma: no cover - environment dependent
    from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
    from starlette.requests import Request as StarletteRequest

    STARLETTE_AVAILABLE = True
except Exception:  # pragma: no cover - shim-only path
    BaseHTTPMiddleware = object  # type: ignore[assignment]
    RequestResponseEndpoint = Callable  # type: ignore[assignment]
    StarletteRequest = Request  # type: ignore[assignment]
    STARLETTE_AVAILABLE = False


if STARLETTE_AVAILABLE:

    class _FixedWindowRateLimiter(BaseHTTPMiddleware):  # type: ignore[misc]
        def __init__(self, app: Any, burst: int) -> None:  # noqa: D401 - Starlette middleware signature
            super().__init__(app)
            self._burst = max(1, burst)
            self._remaining = self._burst
            self._reset = time.monotonic() + 1.0

        async def dispatch(self, request: StarletteRequest, call_next: RequestResponseEndpoint):  # type: ignore[override]
            now = time.monotonic()
            path = getattr(request.scope.get("route"), "path", getattr(request.url, "path", "/"))
            if path in {"/metrics", "/health"}:
                return await call_next(request)
            if now >= self._reset:
                self._remaining = self._burst
                self._reset = now + 1.0
            if self._remaining <= 0:
                try:
                    route = getattr(request.scope.get("route"), "path", getattr(request.url, "path", "/"))
                    metrics.RATE_LIMIT_REJECTIONS.labels(route, request.method).inc()
                except Exception as exc:  # pragma: no cover - defensive
                    logging.debug("rate limit metrics error: %s", exc)
                return Response(status_code=429, content="Rate limit exceeded")
            self._remaining -= 1
            return await call_next(request)
else:

    class _FixedWindowRateLimiter:
        def __init__(self, app: Any, burst: int) -> None:
            self.app = app
            self._burst = max(1, burst)
            self._remaining = self._burst
            self._reset = time.monotonic() + 1.0

        async def dispatch(self, request: Request, call_next: Callable[[Request], Any]):
            now = time.monotonic()
            # Never rate limit metrics endpoint or health for observability stability
            path = getattr(request.scope.get("route"), "path", getattr(request.url, "path", "/"))
            if path in {"/metrics", "/health"}:
                return await call_next(request)
            if now >= self._reset:
                self._remaining = self._burst
                self._reset = now + 1.0
            if self._remaining <= 0:
                try:
                    route = getattr(request.scope.get("route"), "path", getattr(request.url, "path", "/"))
                    metrics.RATE_LIMIT_REJECTIONS.labels(route, request.method).inc()
                except Exception as exc:  # pragma: no cover - defensive
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
    # Ensure add_middleware exists on shim FastAPI
    middleware_shim.install_middleware_support()
    from typing import cast as _cast

    app_any = _cast(Any, app)
    app_any.add_middleware(_FixedWindowRateLimiter, burst=burst)


__all__ = ["add_rate_limit_middleware"]
