"""Rate limiting middleware (fixed 1s window) for FastAPI shim.

Provides a very small fixed-window limiter primarily to satisfy tests. The
implementation is intentionally minimal and avoids pulling in heavier third
party primitives.

Behaviour:
    * Disabled unless the environment variable ENABLE_RATE_LIMITING is truthy.
    * Fixed one‑second window with a simple counter that resets every second.
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
from obs import metrics

from server import middleware_shim

## Optional Starlette integration ---------------------------------------------------
# We attempted to hide imports behind TYPE_CHECKING previously which caused the
# runtime to fall back to a dummy object even when Starlette WAS available.
# That broke FastAPI's `add_middleware` because the created instance was not an
# ASGI callable (no `__call__`). We now import at runtime and only provide a
# lightweight fallback when Starlette truly is absent.
try:  # pragma: no cover - starlette is present in normal test/runtime envs
    from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
    from starlette.requests import Request as StarletteRequest
except Exception:  # pragma: no cover - minimal environments without starlette

    class BaseHTTPMiddleware:  # type: ignore[no-redef]
        """Minimal stand‑in implementing Starlette's interface enough for tests.

        Provides an ASGI callable that wraps a `dispatch` coroutine method.
        """

        def __init__(self, app: Any) -> None:  # noqa: D401
            self.app = app

        async def __call__(self, scope: dict, receive: Callable, send: Callable):
            if scope.get("type") != "http":  # pass through non-http
                await self.app(scope, receive, send)
                return
            request = Request(scope, receive=receive)

            async def call_next(req: Request) -> Response:  # noqa: D401
                responder = await self.app(scope, receive, send)
                return responder

            response = await self.dispatch(request, call_next)
            # If dispatch returned a Response we need to send it (Starlette would handle this)
            if isinstance(response, Response):
                await response(scope, receive, send)

        async def dispatch(self, request: Request, call_next: Callable):  # pragma: no cover - overridden
            return await call_next(request)

    StarletteRequest = Request  # type: ignore
    RequestResponseEndpoint = Callable[[Request], Awaitable[Response]]  # type: ignore


class FixedWindowRateLimiter(BaseHTTPMiddleware):  # noqa: D401 - Starlette middleware signature
    """Simple fixed-window rate limiter middleware.

    Works with real Starlette (subclassing its BaseHTTPMiddleware) or with the
    lightweight dummy base when Starlette is absent (tests / shim mode).
    """

    def __init__(self, app: Any, burst: int) -> None:  # noqa: D401 - Starlette middleware signature
        # Always attempt super(); fallback already ensures compat
        try:  # pragma: no cover - defensive
            super().__init__(app)
        except Exception:  # pragma: no cover
            self.app = app
        self._burst = max(1, burst)
        self._remaining = self._burst
        self._reset = time.monotonic() + 1.0

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Any:
        now = time.monotonic()
        scope_path = request.scope.get("path", "/")
        raw_path = str(scope_path)
        # Some environments (observed under BaseHTTPMiddleware) surfaced a scope path
        # of '/' for every request, while request.url.path retained the real path.
        # Fallback to request.url.path when scope path is root to preserve exclusion logic.
        try:  # pragma: no cover - defensive; url should always exist
            url_path = request.url.path
            if raw_path == "/" and url_path != "/":
                raw_path = url_path
        except Exception:  # pragma: no cover - never expected
            pass
        # Determine metrics path: environment override or app state annotation
        _app = getattr(request, "app", None)
        _state = getattr(_app, "state", None) if _app else None
        metrics_path = (
            os.getenv("PROMETHEUS_ENDPOINT_PATH")
            or (getattr(_state, "metrics_path", None) if _state else None)
            or "/metrics"
        )
        # Exclusions (exact or prefix for metrics)
        mp_norm = metrics_path.rstrip("/") or "/metrics"
        rp_norm = raw_path.rstrip("/") or raw_path
        if (
            request.scope.get("_skip_rate_limit")
            or rp_norm == mp_norm
            or rp_norm == "/health"
            or rp_norm.startswith(mp_norm + "/")
        ):
            return await call_next(request)
        # Window reset
        if now >= self._reset:
            self._remaining = self._burst
            self._reset = now + 1.0
        # Enforce
        if self._remaining <= 0:
            try:
                metrics.RATE_LIMIT_REJECTIONS.labels(rp_norm, getattr(request, "method", "?")).inc()  # noqa: E203
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
    app_any.add_middleware(FixedWindowRateLimiter, burst=burst)


__all__ = ["add_rate_limit_middleware"]
