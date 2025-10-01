from __future__ import annotations

from fastapi import FastAPI

"""Health endpoints for service and Activities.

Routes:
- GET /health
- GET /activities/health
"""


def register_health_routes(app: FastAPI) -> None:
    @app.get("/health")
    def _health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/activities/health")
    def _activities_health() -> dict[str, str]:
        """Lightweight health endpoint for Discord Activities local dev."""
        return {"status": "ok", "component": "activities"}


__all__ = ["register_health_routes"]
