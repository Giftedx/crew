"""Health endpoints for production deployments.

Provides standardized health check endpoints:
- GET /health - Legacy simple health check (backward compatibility)
- GET /healthz - Fast liveness probe (<10ms target)
- GET /readyz - Comprehensive dependency readiness validation
- GET /livez - Core service availability checks
- GET /activities/health - Discord Activities lightweight check

Designed for Kubernetes, Docker Compose, and load balancer health probes.
Follows Kubernetes health check conventions:
- /healthz: Returns 200 if process alive (no dependency checks)
- /readyz: Returns 200 if all critical dependencies healthy, 503 otherwise
- /livez: Returns 200 if core services loaded, 503 otherwise
"""

from __future__ import annotations

from platform.http.health import get_health_checker
from typing import TYPE_CHECKING, Any

from fastapi import Response, status


if TYPE_CHECKING:
    from fastapi import FastAPI


def register_health_routes(app: FastAPI) -> None:
    """Register all health check endpoints."""

    health_checker = get_health_checker()

    @app.get("/health")
    def _health() -> dict[str, str]:
        """Legacy simple health check for backward compatibility."""
        return {"status": "ok"}

    @app.get("/activities/health")
    def _activities_health() -> dict[str, str]:
        """Lightweight health endpoint for Discord Activities local dev."""
        return {"status": "ok", "component": "activities"}

    @app.get("/healthz")
    def _healthz() -> dict[str, Any]:
        """Fast liveness probe - returns healthy if process alive.

        Target: <10ms response time
        Use: Kubernetes liveness probe, fast health checks
        Returns: 200 OK with uptime metadata
        """
        result = health_checker.liveness_check()
        return result.data or {"status": "ok"}

    @app.get("/readyz")
    async def _readyz(response: Response) -> dict[str, Any]:
        """Comprehensive dependency readiness check.

        Validates:
        - Qdrant vector database connectivity
        - Redis cache availability (optional, degrades gracefully)
        - Neo4j graph database (if ENABLE_GRAPH_MEMORY=true)
        - Configuration completeness

        Returns:
            200 OK if all critical dependencies healthy
            503 Service Unavailable if any critical dependency fails
        """
        result = await health_checker.readiness_check()

        if not result.success:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return result.data or {"status": "unavailable", "error": result.error}

        return result.data or {"status": "ready"}

    @app.get("/livez")
    async def _livez(response: Response) -> dict[str, Any]:
        """Core service availability check.

        Validates:
        - LLM router initialized
        - Tool registry loaded
        - Memory providers configured

        Returns:
            200 OK if all core services available
            503 Service Unavailable if any core service missing
        """
        result = await health_checker.service_check()

        if not result.success:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return result.data or {"status": "unavailable", "error": result.error}

        return result.data or {"status": "live"}


__all__ = ["register_health_routes"]
