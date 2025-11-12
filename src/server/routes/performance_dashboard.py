"""Performance Dashboard route registration for Week 4 Phase 2 Week 3."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.responses import FileResponse

from server.routers.performance_dashboard import router as performance_router


if TYPE_CHECKING:
    from fastapi import FastAPI


def register_performance_dashboard(app: FastAPI) -> None:
    """
    Register performance dashboard routes and static files.

    This includes:
    - REST API endpoints at /api/performance/
    - Static dashboard HTML at /dashboard

    Args:
        app: FastAPI application instance
    """
    app.include_router(performance_router)

    @app.get("/dashboard")
    async def dashboard_page():
        """Serve the performance dashboard HTML page."""
        return FileResponse("src/server/static/performance_dashboard.html")


__all__ = ["register_performance_dashboard"]
