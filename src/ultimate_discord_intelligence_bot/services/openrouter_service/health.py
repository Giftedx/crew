"""Health check endpoints for OpenRouter service.

This module provides comprehensive health check functionality
for monitoring service status and dependencies.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from app.config.feature_flags import FeatureFlags


if TYPE_CHECKING:
    from .service import OpenRouterService
log = logging.getLogger(__name__)


class HealthChecker:
    """Provides health status for the OpenRouter service."""

    def __init__(self, service: OpenRouterService) -> None:
        """Initialize health checker.

        Args:
            service: The OpenRouter service instance
        """
        self._service = service
        self._feature_flags = FeatureFlags()
        self._last_health_check = 0.0
        self._health_check_interval = 30.0
        self._cached_health_status: dict[str, Any] | None = None

    async def check_health(self) -> dict[str, Any]:
        """Check comprehensive health status.

        Returns:
            Dictionary with health status information
        """
        current_time = time.time()
        if self._cached_health_status and current_time - self._last_health_check < self._health_check_interval:
            return self._cached_health_status
        try:
            health_status = {
                "status": "healthy",
                "timestamp": current_time,
                "service": "openrouter",
                "version": "1.0.0",
                "checks": {},
                "overall_healthy": True,
            }
            checks = await self._run_health_checks()
            health_status["checks"] = checks
            overall_healthy = all(check.get("healthy", False) for check in checks.values())
            health_status["overall_healthy"] = overall_healthy
            health_status["status"] = "healthy" if overall_healthy else "unhealthy"
            self._cached_health_status = health_status
            self._last_health_check = current_time
            return health_status
        except Exception as e:
            log.error("Health check failed: %s", e)
            return {
                "status": "error",
                "timestamp": current_time,
                "service": "openrouter",
                "error": str(e),
                "overall_healthy": False,
            }

    async def _run_health_checks(self) -> dict[str, dict[str, Any]]:
        """Run individual health checks.

        Returns:
            Dictionary with individual check results
        """
        checks = {}
        checks["configuration"] = await self._check_configuration()
        checks["api_connectivity"] = await self._check_api_connectivity()
        checks["cache"] = await self._check_cache()
        checks["memory"] = await self._check_memory()
        checks["feature_flags"] = await self._check_feature_flags()
        checks["circuit_breakers"] = await self._check_circuit_breakers()
        return checks

    async def _check_configuration(self) -> dict[str, Any]:
        """Check service configuration.

        Returns:
            Configuration check result
        """
        try:
            has_api_key = bool(self._service.api_key)
            has_models = bool(self._service.models_map)
            has_prompt_engine = bool(self._service.prompt_engine)
            has_token_meter = bool(self._service.token_meter)
            healthy = has_models and has_prompt_engine and has_token_meter
            return {
                "healthy": healthy,
                "details": {
                    "has_api_key": has_api_key,
                    "has_models": has_models,
                    "has_prompt_engine": has_prompt_engine,
                    "has_token_meter": has_token_meter,
                    "offline_mode": self._service.offline_mode,
                },
                "message": "Configuration check completed",
            }
        except Exception as e:
            return {"healthy": False, "error": str(e), "message": "Configuration check failed"}

    async def _check_api_connectivity(self) -> dict[str, Any]:
        """Check API connectivity.

        Returns:
            API connectivity check result
        """
        try:
            if self._service.offline_mode:
                return {
                    "healthy": True,
                    "details": {"mode": "offline", "message": "Service running in offline mode"},
                    "message": "Offline mode - no API connectivity required",
                }
            start_time = time.time()
            result = self._service.route("health check", task_type="general")
            latency = (time.time() - start_time) * 1000
            healthy = result.success
            message = "API connectivity check completed" if healthy else "API connectivity check failed"
            return {
                "healthy": healthy,
                "details": {
                    "latency_ms": round(latency, 2),
                    "response_status": result.data.get("status") if result.success else "error",
                    "error": result.error if not result.success else None,
                },
                "message": message,
            }
        except Exception as e:
            return {"healthy": False, "error": str(e), "message": "API connectivity check failed"}

    async def _check_cache(self) -> dict[str, Any]:
        """Check cache status.

        Returns:
            Cache check result
        """
        try:
            if not self._service.cache:
                return {
                    "healthy": True,
                    "details": {"cache_enabled": False, "message": "Cache not configured"},
                    "message": "No cache configured - not required",
                }
            test_key = "health_check_test"
            test_value = {"test": "data", "timestamp": time.time()}
            self._service.cache.set(test_key, test_value)
            retrieved = self._service.cache.get(test_key)
            import contextlib

            with contextlib.suppress(Exception):
                self._service.cache.delete(test_key)
            healthy = retrieved is not None and retrieved.get("test") == "data"
            return {
                "healthy": healthy,
                "details": {
                    "cache_enabled": True,
                    "set_operation": True,
                    "get_operation": healthy,
                    "cache_type": type(self._service.cache).__name__,
                },
                "message": "Cache check completed" if healthy else "Cache check failed",
            }
        except Exception as e:
            return {"healthy": False, "error": str(e), "message": "Cache check failed"}

    async def _check_memory(self) -> dict[str, Any]:
        """Check memory usage.

        Returns:
            Memory check result
        """
        try:
            import psutil

            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()
            memory_usage_percent = memory.percent
            process_memory_mb = process_memory.rss / 1024 / 1024
            healthy = memory_usage_percent < 90 and process_memory_mb < 1024
            return {
                "healthy": healthy,
                "details": {
                    "system_memory_percent": round(memory_usage_percent, 2),
                    "process_memory_mb": round(process_memory_mb, 2),
                    "available_memory_gb": round(memory.available / 1024 / 1024 / 1024, 2),
                    "total_memory_gb": round(memory.total / 1024 / 1024 / 1024, 2),
                },
                "message": "Memory check completed",
            }
        except ImportError:
            return {
                "healthy": True,
                "details": {"psutil_available": False, "message": "psutil not available for detailed memory check"},
                "message": "Memory check skipped - psutil not available",
            }
        except Exception as e:
            return {"healthy": False, "error": str(e), "message": "Memory check failed"}

    async def _check_feature_flags(self) -> dict[str, Any]:
        """Check feature flags status.

        Returns:
            Feature flags check result
        """
        try:
            flags_status = {
                "connection_pooling": self._feature_flags.ENABLE_OPENROUTER_CONNECTION_POOLING,
                "request_batching": self._feature_flags.ENABLE_OPENROUTER_REQUEST_BATCHING,
                "circuit_breaker": self._feature_flags.ENABLE_OPENROUTER_CIRCUIT_BREAKER,
                "advanced_caching": self._feature_flags.ENABLE_OPENROUTER_ADVANCED_CACHING,
                "async_routing": self._feature_flags.ENABLE_OPENROUTER_ASYNC_ROUTING,
                "object_pooling": self._feature_flags.ENABLE_OPENROUTER_OBJECT_POOLING,
                "metrics_collection": self._feature_flags.ENABLE_OPENROUTER_METRICS_COLLECTION,
                "health_checks": self._feature_flags.ENABLE_OPENROUTER_HEALTH_CHECKS,
            }
            enabled_count = sum(1 for enabled in flags_status.values() if enabled)
            total_count = len(flags_status)
            return {
                "healthy": True,
                "details": {
                    "enabled_features": enabled_count,
                    "total_features": total_count,
                    "feature_flags": flags_status,
                },
                "message": f"Feature flags check completed - {enabled_count}/{total_count} enabled",
            }
        except Exception as e:
            return {"healthy": False, "error": str(e), "message": "Feature flags check failed"}

    async def _check_circuit_breakers(self) -> dict[str, Any]:
        """Check circuit breaker status.

        Returns:
            Circuit breaker check result
        """
        try:
            if not self._feature_flags.ENABLE_OPENROUTER_CIRCUIT_BREAKER:
                return {
                    "healthy": True,
                    "details": {"circuit_breakers_enabled": False, "message": "Circuit breakers not enabled"},
                    "message": "Circuit breakers disabled - not required",
                }
            try:
                from .circuit_breaker import get_circuit_breaker_manager

                manager = get_circuit_breaker_manager()
                stats = manager.get_all_stats()
                open_breakers = [name for name, breaker_stats in stats.items() if breaker_stats.get("state") == "open"]
                healthy = len(open_breakers) == 0
                return {
                    "healthy": healthy,
                    "details": {
                        "circuit_breakers_enabled": True,
                        "total_breakers": len(stats),
                        "open_breakers": open_breakers,
                        "breaker_stats": stats,
                    },
                    "message": f"Circuit breaker check completed - {len(open_breakers)} open",
                }
            except ImportError:
                return {
                    "healthy": True,
                    "details": {"circuit_breakers_available": False, "message": "Circuit breaker module not available"},
                    "message": "Circuit breaker check skipped - module not available",
                }
        except Exception as e:
            return {"healthy": False, "error": str(e), "message": "Circuit breaker check failed"}

    def get_quick_health(self) -> dict[str, Any]:
        """Get quick health status without detailed checks.

        Returns:
            Quick health status
        """
        try:
            has_models = bool(self._service.models_map)
            has_prompt_engine = bool(self._service.prompt_engine)
            has_token_meter = bool(self._service.token_meter)
            healthy = has_models and has_prompt_engine and has_token_meter
            return {
                "status": "healthy" if healthy else "unhealthy",
                "timestamp": time.time(),
                "service": "openrouter",
                "basic_checks_passed": healthy,
                "details": {
                    "has_models": has_models,
                    "has_prompt_engine": has_prompt_engine,
                    "has_token_meter": has_token_meter,
                    "offline_mode": self._service.offline_mode,
                },
            }
        except Exception as e:
            return {"status": "error", "timestamp": time.time(), "service": "openrouter", "error": str(e)}

    def get_stats(self) -> dict[str, Any]:
        """Get health checker statistics.

        Returns:
            Dictionary with health checker statistics
        """
        return {
            "last_health_check": self._last_health_check,
            "health_check_interval": self._health_check_interval,
            "cached_status_available": self._cached_health_status is not None,
            "feature_flags": {"health_checks_enabled": self._feature_flags.ENABLE_OPENROUTER_HEALTH_CHECKS},
        }


class HealthEndpoint:
    """HTTP endpoint for health checks."""

    def __init__(self, service: OpenRouterService) -> None:
        """Initialize health endpoint.

        Args:
            service: The OpenRouter service instance
        """
        self._service = service
        self._health_checker = HealthChecker(service)
        self._feature_flags = FeatureFlags()

    async def health_check(self, detailed: bool = False) -> dict[str, Any]:
        """Perform health check.

        Args:
            detailed: Whether to perform detailed checks

        Returns:
            Health check result
        """
        if not self._feature_flags.ENABLE_OPENROUTER_HEALTH_CHECKS:
            return {
                "status": "disabled",
                "timestamp": time.time(),
                "service": "openrouter",
                "message": "Health checks are disabled",
            }
        if detailed:
            return await self._health_checker.check_health()
        else:
            return self._health_checker.get_quick_health()

    async def readiness_check(self) -> dict[str, Any]:
        """Perform readiness check.

        Returns:
            Readiness check result
        """
        try:
            quick_health = self._health_checker.get_quick_health()
            ready = quick_health.get("basic_checks_passed", False)
            return {
                "ready": ready,
                "timestamp": time.time(),
                "service": "openrouter",
                "message": "Service ready" if ready else "Service not ready",
            }
        except Exception as e:
            return {
                "ready": False,
                "timestamp": time.time(),
                "service": "openrouter",
                "error": str(e),
                "message": "Readiness check failed",
            }

    async def liveness_check(self) -> dict[str, Any]:
        """Perform liveness check.

        Returns:
            Liveness check result
        """
        try:
            return {
                "alive": True,
                "timestamp": time.time(),
                "service": "openrouter",
                "uptime_seconds": time.time() - self._health_checker._last_health_check,
                "message": "Service is alive",
            }
        except Exception as e:
            return {
                "alive": False,
                "timestamp": time.time(),
                "service": "openrouter",
                "error": str(e),
                "message": "Liveness check failed",
            }


_health_endpoint: HealthEndpoint | None = None


def get_health_endpoint(service: OpenRouterService) -> HealthEndpoint:
    """Get or create health endpoint for the service.

    Args:
        service: The OpenRouter service instance

    Returns:
        HealthEndpoint instance
    """
    global _health_endpoint
    if _health_endpoint is None:
        _health_endpoint = HealthEndpoint(service)
    return _health_endpoint


def close_health_endpoint() -> None:
    """Close the global health endpoint."""
    global _health_endpoint
    if _health_endpoint:
        _health_endpoint = None
