"""Backpressure middleware for FastAPI.

Rejects HTTP requests when system backpressure is active, preventing
cascading failures and allowing the system to recover from overload conditions.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


if TYPE_CHECKING:
    from collections.abc import Callable

    from starlette.requests import Request
    from starlette.responses import Response

    from fastapi import FastAPI

logger = logging.getLogger(__name__)


class BackpressureMiddleware(BaseHTTPMiddleware):
    """Middleware that rejects requests when system backpressure is active.

    When the backpressure coordinator detects system overload (≥2 circuit breakers
    open OR system load >80%), this middleware rejects incoming HTTP requests with
    503 Service Unavailable status and a Retry-After header.

    Excluded paths (always allowed):
    - /health
    - /metrics
    - /readiness
    - /liveness
    """

    EXCLUDED_PATHS: ClassVar[set[str]] = {"/health", "/metrics", "/readiness", "/liveness"}

    def __init__(self, app: FastAPI) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._coordinator = None  # Lazy init to avoid import cycles

    def _get_coordinator(self):
        """Lazy initialization of backpressure coordinator."""
        if self._coordinator is None:
            try:
                from core.resilience.backpressure_coordinator import get_backpressure_coordinator

                self._coordinator = get_backpressure_coordinator()
            except Exception as e:
                logger.warning(f"Failed to initialize backpressure coordinator: {e}")

                # Return a dummy object that always reports no backpressure
                class DummyCoordinator:
                    def is_backpressure_active(self) -> bool:
                        return False

                    def get_backpressure_level(self):
                        class Level:
                            name = "NORMAL"

                        return Level()

                    def record_request_rejected(self) -> None:
                        pass

                self._coordinator = DummyCoordinator()
        return self._coordinator

    async def dispatch(self, request: Request, call_next: Callable) -> Response:  # type: ignore[override]
        """Process request and check for backpressure before forwarding.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            Response: Either 503 rejection or forwarded response
        """
        # Always allow health/metrics endpoints
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        coordinator = self._get_coordinator()

        # Check if backpressure is active
        if coordinator.is_backpressure_active():
            level = coordinator.get_backpressure_level()
            coordinator.record_request_rejected()

            logger.warning(
                f"Request rejected due to backpressure (level={level.name}): {request.method} {request.url.path}"
            )

            # Return 503 Service Unavailable with Retry-After header
            return JSONResponse(  # type: ignore[return-value]
                status_code=503,
                headers={
                    "Retry-After": "30",  # Suggest retry after 30 seconds
                    "X-Backpressure-Level": level.name,
                },
                content={
                    "error": "service_unavailable",
                    "message": "System is currently overloaded. Please retry after the suggested delay.",
                    "backpressure_level": level.name,
                    "retry_after_seconds": 30,
                },
            )

        # No backpressure - forward request normally
        return await call_next(request)


def add_backpressure_middleware(app: FastAPI) -> None:
    """Add backpressure middleware to FastAPI application.

    This middleware should be added EARLY in the middleware stack so it can
    reject requests before they consume resources in downstream middleware
    or route handlers.

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(BackpressureMiddleware)  # type: ignore[attr-defined]
    logger.info("Backpressure middleware installed")
