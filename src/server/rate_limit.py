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

from fastapi import FastAPI, Request, Response  # type: ignore
from obs import metrics  # type: ignore


class _FixedWindowRateLimiter:
    def __init__(self, app: Any, burst: int) -> None:
        self.app = app
        self._burst = max(1, burst)
        self._remaining = self._burst
        self._reset = time.monotonic() + 1.0

    async def dispatch(self, request: Request, call_next: Callable):  # type: ignore[override]
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
                route = getattr(request.scope.get("route"), "path", request.url.path)
                metrics.RATE_LIMIT_REJECTIONS.labels(route, request.method).inc()
            except Exception as exc:  # pragma: no cover - defensive
                logging.debug("rate limit metrics error: %s", exc)
            return Response(status_code=429, content="Rate limit exceeded")
        self._remaining -= 1
        return await call_next(request)


def add_rate_limit_middleware(app: FastAPI) -> None:  # type: ignore[override]
    enable = os.getenv("ENABLE_RATE_LIMITING", "0").lower() in ("1", "true", "yes", "on")
    if not enable:
        return
    try:
        burst = int(os.getenv("RATE_LIMIT_BURST", os.getenv("RATE_LIMIT_RPS", "10")))
    except Exception:
        burst = 10
    # Provided by middleware_shim when real FastAPI absent
    app.add_middleware(_FixedWindowRateLimiter, burst=burst)  # type: ignore[attr-defined]


__all__ = ["add_rate_limit_middleware"]
