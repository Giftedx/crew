"""Route registrar utilities for the FastAPI app factory.

Each function registers a set of related endpoints on a provided FastAPI app,
keeping `server.app.create_app` small and focused.
"""

from .a2a import register_a2a_router
from .activities import register_activities_echo
from .alerts import register_alert_routes
from .archive import register_archive_routes
from .autointel import register_autointel_routes
from .health import register_health_routes
from .metrics import register_metrics_endpoint
from .performance_dashboard import register_performance_dashboard
from .pilot import register_pilot_route
from .pipeline_api import register_pipeline_routes

__all__ = [
    "register_metrics_endpoint",
    "register_health_routes",
    "register_activities_echo",
    "register_a2a_router",
    "register_pilot_route",
    "register_archive_routes",
    "register_alert_routes",
    "register_pipeline_routes",
    "register_autointel_routes",
    "register_performance_dashboard",
]
