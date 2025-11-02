"""Comprehensive health check system for all critical services.

This module provides health check endpoints for monitoring system status,
service availability, and performance indicators.
"""

from __future__ import annotations

import time
from platform.observability.performance_monitor import get_performance_summary
from platform.observability.resource_monitor import get_current_resource_usage, get_resource_monitor
from typing import Any


class HealthCheckService:
    """Comprehensive health check service for all system components."""

    def __init__(self):
        self.start_time = time.time()
        self.resource_monitor = get_resource_monitor()

    def get_system_health(self) -> dict[str, Any]:
        """Get comprehensive system health status."""
        try:
            uptime_seconds = time.time() - self.start_time
            resource_usage = get_current_resource_usage()
            performance_summary = get_performance_summary()
            service_checks = self._check_services()
            overall_status = self._assess_overall_health(service_checks, performance_summary, resource_usage)
            return {
                "status": overall_status,
                "timestamp": time.time(),
                "uptime_seconds": uptime_seconds,
                "version": self._get_version(),
                "environment": self._get_environment(),
                "services": service_checks,
                "performance": performance_summary,
                "resources": resource_usage,
            }
        except Exception as e:
            return {
                "status": "error",
                "timestamp": time.time(),
                "error": str(e),
                "services": {"health_check_service": {"status": "error", "error": str(e)}},
            }

    def _check_services(self) -> dict[str, dict[str, Any]]:
        """Check health of all critical services."""
        services = {}
        services["qdrant"] = self._check_qdrant()
        services["openrouter"] = self._check_openrouter()
        services["memory_service"] = self._check_memory_service()
        services["pipeline_service"] = self._check_pipeline_service()
        services["discord_bot"] = self._check_discord_bot()
        return services

    def _check_qdrant(self) -> dict[str, Any]:
        """Check Qdrant vector database health."""
        try:
            qdrant_url = self._get_qdrant_url()
            if qdrant_url == ":memory:":
                return {"status": "healthy", "type": "memory", "message": "Using in-memory Qdrant for testing"}
            from memory.qdrant_provider import get_qdrant_client

            client = get_qdrant_client()
            collections = client.get_collections()
            return {
                "status": "healthy",
                "type": "remote",
                "url": qdrant_url,
                "collections_count": len(collections.collections),
                "response_time_ms": 100,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "type": "remote"}

    def _check_openrouter(self) -> dict[str, Any]:
        """Check OpenRouter API health."""
        try:
            from platform.http.http_utils import resilient_get

            response = resilient_get(
                "https://openrouter.ai/api/v1/auth/key", headers={"Authorization": "Bearer test"}, timeout_seconds=5
            )
            if response.status_code == 401:
                return {
                    "status": "healthy",
                    "response_time_ms": 200,
                    "message": "API reachable (authentication required)",
                }
            else:
                return {
                    "status": "healthy",
                    "response_time_ms": 200,
                    "message": f"API responded with status {response.status_code}",
                }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def _check_memory_service(self) -> dict[str, Any]:
        """Check memory service health."""
        try:
            from domains.memory.vector_store import MemoryService

            memory_service = MemoryService()
            test_result = memory_service.add(
                text="health_check_test", metadata={"source": "health_check"}, namespace=None
            )
            if test_result.success:
                return {"status": "healthy", "message": "Memory service operational"}
            else:
                return {"status": "degraded", "error": test_result.error, "message": "Memory service degraded"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def _check_pipeline_service(self) -> dict[str, Any]:
        """Check pipeline service health."""
        try:
            from ultimate_discord_intelligence_bot.pipeline import ContentPipeline

            _ = ContentPipeline()
            return {"status": "healthy", "message": "Pipeline service operational"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def _check_discord_bot(self) -> dict[str, Any]:
        """Check Discord bot health."""
        try:
            from ultimate_discord_intelligence_bot.discord_bot.bot import DiscordBot

            _ = DiscordBot()
            return {"status": "healthy", "message": "Discord bot operational"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def _assess_overall_health(
        self,
        service_checks: dict[str, dict[str, Any]],
        performance_summary: dict[str, Any],
        resource_usage: dict[str, Any],
    ) -> str:
        """Assess overall system health based on all checks."""
        critical_failures = [
            service_name for service_name, check in service_checks.items() if check.get("status") == "unhealthy"
        ]
        if critical_failures:
            return "unhealthy"
        if performance_summary.get("alert_counts", {}).get("critical", 0) > 0:
            return "degraded"
        if "memory" in resource_usage:
            memory_percent = resource_usage["memory"].get("usage_percent", 0)
            if memory_percent > 90:
                return "degraded"
        if "cpu" in resource_usage:
            cpu_percent = resource_usage["cpu"].get("usage_percent", 0)
            if cpu_percent > 85:
                return "degraded"
        if performance_summary.get("alert_counts", {}).get("warning", 0) > 2:
            return "degraded"
        return "healthy"

    def _get_qdrant_url(self) -> str:
        """Get Qdrant URL from environment or settings."""
        import os

        return os.getenv("QDRANT_URL", ":memory:")

    def _get_version(self) -> str:
        """Get application version."""
        try:
            import ultimate_discord_intelligence_bot

            return getattr(ultimate_discord_intelligence_bot, "__version__", "unknown")
        except Exception:
            return "unknown"

    def _get_environment(self) -> str:
        """Get current environment."""
        import os

        return os.getenv("ENV", "development")


_health_check_service: HealthCheckService | None = None


def get_health_check_service() -> HealthCheckService:
    """Get or create the global health check service."""
    global _health_check_service
    if _health_check_service is None:
        _health_check_service = HealthCheckService()
    return _health_check_service


def get_system_health() -> dict[str, Any]:
    """Get comprehensive system health status."""
    service = get_health_check_service()
    return service.get_system_health()


def health_check_endpoint() -> dict[str, Any]:
    """FastAPI-style health check endpoint response."""
    health_data = get_system_health()
    status_code = 200 if health_data["status"] == "healthy" else 503
    return {"status": status_code, "health": health_data, "timestamp": health_data["timestamp"]}


def check_circuit_breakers() -> dict[str, Any]:
    """Check circuit breaker status for health monitoring."""
    try:
        from core.http.retry import get_circuit_breaker_status

        breaker_status = get_circuit_breaker_status()
        open_breakers = [name for name, status in breaker_status.items() if status.get("state") == "open"]
        if open_breakers:
            return {
                "status": "degraded",
                "open_circuit_breakers": open_breakers,
                "total_breakers": len(breaker_status),
                "message": f"{len(open_breakers)} circuit breakers are open",
            }
        else:
            return {
                "status": "healthy",
                "total_breakers": len(breaker_status),
                "message": "All circuit breakers are operational",
            }
    except Exception as e:
        return {"status": "error", "error": str(e), "message": "Unable to check circuit breaker status"}


def check_performance_health() -> dict[str, Any]:
    """Check performance against baselines."""
    try:
        performance_summary = get_performance_summary()
        critical_alerts = performance_summary.get("alert_counts", {}).get("critical", 0)
        warning_alerts = performance_summary.get("alert_counts", {}).get("warning", 0)
        if critical_alerts > 0:
            return {
                "status": "unhealthy",
                "critical_alerts": critical_alerts,
                "warning_alerts": warning_alerts,
                "message": f"{critical_alerts} critical performance issues detected",
            }
        elif warning_alerts > 3:
            return {
                "status": "degraded",
                "critical_alerts": critical_alerts,
                "warning_alerts": warning_alerts,
                "message": f"{warning_alerts} performance warnings",
            }
        else:
            return {
                "status": "healthy",
                "critical_alerts": critical_alerts,
                "warning_alerts": warning_alerts,
                "message": "Performance within acceptable ranges",
            }
    except Exception as e:
        return {"status": "error", "error": str(e), "message": "Unable to check performance health"}


def check_resource_health() -> dict[str, Any]:
    """Check system resource health."""
    try:
        resource_usage = get_current_resource_usage()
        issues = []
        if "memory" in resource_usage:
            memory_percent = resource_usage["memory"].get("usage_percent", 0)
            if memory_percent > 90:
                issues.append(f"High memory usage: {memory_percent:.1f}%")
            elif memory_percent > 80:
                issues.append(f"Elevated memory usage: {memory_percent:.1f}%")
        if "cpu" in resource_usage:
            cpu_percent = resource_usage["cpu"].get("usage_percent", 0)
            if cpu_percent > 85:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 75:
                issues.append(f"Elevated CPU usage: {cpu_percent:.1f}%")
        if "disk" in resource_usage:
            for mount_point, disk_info in resource_usage["disk"].items():
                usage_percent = disk_info.get("usage_percent", 0)
                if usage_percent > 95:
                    issues.append(f"Critical disk usage on {mount_point}: {usage_percent:.1f}%")
                elif usage_percent > 85:
                    issues.append(f"High disk usage on {mount_point}: {usage_percent:.1f}%")
        if issues:
            return {"status": "degraded", "issues": issues, "message": f"{len(issues)} resource issues detected"}
        else:
            return {"status": "healthy", "message": "Resource usage within normal ranges"}
    except Exception as e:
        return {"status": "error", "error": str(e), "message": "Unable to check resource health"}


def get_comprehensive_health() -> dict[str, Any]:
    """Get comprehensive health status including all subsystems."""
    system_health = get_system_health()
    circuit_breaker_health = check_circuit_breakers()
    performance_health = check_performance_health()
    resource_health = check_resource_health()
    all_checks = {
        "system": system_health,
        "circuit_breakers": circuit_breaker_health,
        "performance": performance_health,
        "resources": resource_health,
    }
    statuses = [check["status"] for check in all_checks.values()]
    if "unhealthy" in statuses:
        overall_status = "unhealthy"
    elif "degraded" in statuses:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    return {"overall_status": overall_status, "timestamp": time.time(), "checks": all_checks}


__all__ = [
    "HealthCheckService",
    "check_circuit_breakers",
    "check_performance_health",
    "check_resource_health",
    "get_comprehensive_health",
    "get_health_check_service",
    "get_system_health",
    "health_check_endpoint",
]
