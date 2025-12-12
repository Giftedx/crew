"""Health check utilities for production deployments.

Provides standardized health check implementations for:
- /healthz: Fast liveness probe (<10ms target)
- /readyz: Dependency readiness validation
- /livez: Core service availability checks

Designed for Kubernetes, Docker Compose, and load balancer health probes.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from platform.core.step_result import ErrorCategory, StepResult
from typing import Any


logger = logging.getLogger(__name__)


def _emit_health_metrics(check_type: str, status: str, latency_ms: float, component: str | None = None) -> None:
    """Emit health check metrics for observability.

    Metrics emitted:
    - health_check_duration_seconds{endpoint,status,component}
    - health_check_total{endpoint,status,component}
    """
    try:
        from ultimate_discord_intelligence_bot.obs.metrics import get_metrics

        metrics = get_metrics()

        labels = {
            "endpoint": check_type,
            "status": status,
        }
        if component:
            labels["component"] = component

        # Emit duration histogram
        metrics.histogram(
            "health_check_duration_seconds",
            latency_ms / 1000.0,  # Convert ms to seconds
            labels=labels,
        )

        # Emit counter
        metrics.counter("health_check_total", labels=labels)

    except Exception as e:
        logger.debug(f"Failed to emit health metrics: {e}")


class HealthStatus(str, Enum):
    """Health check status enumeration."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a single health check."""

    component: str
    status: HealthStatus
    latency_ms: float
    message: str | None = None
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "component": self.component,
            "status": self.status.value,
            "latency_ms": round(self.latency_ms, 2),
        }
        if self.message:
            result["message"] = self.message
        if self.details:
            result["details"] = self.details
        return result


class HealthChecker:
    """Centralized health check orchestrator.

    Provides standardized health checks for all service dependencies:
    - Qdrant vector database
    - Redis cache
    - Neo4j graph database
    - LLM providers (via router)

    Design Principles:
    - Fast liveness checks (<10ms) for /healthz
    - Comprehensive dependency checks for /readyz
    - Non-blocking async checks with timeouts
    - Structured metrics emission for observability
    """

    def __init__(self):
        """Initialize health checker with lazy dependency loading."""
        self._initialized = False
        self._startup_time = time.time()

    def liveness_check(self) -> StepResult:
        """Fast liveness probe - always returns healthy if process alive.

        Target: <10ms response time
        Use: Kubernetes liveness probe, fast health checks

        Returns:
            StepResult with status and uptime metadata
        """
        start_time = time.perf_counter()
        uptime_seconds = time.time() - self._startup_time

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Emit metrics
        _emit_health_metrics("liveness", HealthStatus.HEALTHY.value, latency_ms, component="api_server")

        return StepResult.ok(
            status=HealthStatus.HEALTHY.value,
            uptime_seconds=round(uptime_seconds, 2),
            latency_ms=round(latency_ms, 2),
            metadata={
                "check_type": "liveness",
                "component": "api_server",
                "latency_ms": latency_ms,
            },
        )

    async def readiness_check(self) -> StepResult:
        """Comprehensive dependency health checks.

        Validates:
        - Qdrant vector database connectivity
        - Redis cache availability
        - Neo4j graph database (if enabled)
        - Configuration completeness

        Returns 503 if any critical dependency fails.

        Returns:
            StepResult with per-dependency status and latency
        """
        start_time = time.perf_counter()
        checks: list[HealthCheckResult] = []

        # Check Qdrant (critical dependency)
        qdrant_result = await self._check_qdrant()
        checks.append(qdrant_result)

        # Check Redis (optional, degrades gracefully)
        redis_result = await self._check_redis()
        checks.append(redis_result)

        # Check Neo4j (optional, feature-flagged)
        if os.getenv("ENABLE_GRAPH_MEMORY", "false").lower() == "true":
            neo4j_result = await self._check_neo4j()
            checks.append(neo4j_result)

        # Check configuration
        config_result = self._check_configuration()
        checks.append(config_result)

        # Aggregate status
        overall_status = self._aggregate_status(checks)
        total_latency_ms = (time.perf_counter() - start_time) * 1000

        # Emit aggregated metrics
        _emit_health_metrics("readiness", overall_status.value, total_latency_ms)

        # Emit per-component metrics
        for check in checks:
            _emit_health_metrics("readiness", check.status.value, check.latency_ms, component=check.component)

        # Return failure if any critical dependency unhealthy
        if overall_status == HealthStatus.UNHEALTHY:
            return StepResult.fail(
                error=f"Service not ready: {self._format_failures(checks)}",
                error_category=ErrorCategory.DEPENDENCY,
                retryable=True,
                status=overall_status.value,
                checks=[check.to_dict() for check in checks],
                latency_ms=round(total_latency_ms, 2),
                metadata={"check_type": "readiness", "failed_components": self._get_failed_components(checks)},
            )

        return StepResult.ok(
            status=overall_status.value,
            checks=[check.to_dict() for check in checks],
            latency_ms=round(total_latency_ms, 2),
            metadata={"check_type": "readiness", "total_latency_ms": total_latency_ms},
        )

    async def service_check(self) -> StepResult:
        """Core service availability checks.

        Validates:
        - LLM router initialized
        - CrewAI executor loaded
        - Tool registry available
        - Memory providers configured

        Returns:
            StepResult with service status
        """
        start_time = time.perf_counter()
        checks: list[HealthCheckResult] = []

        # Check LLM router
        router_result = self._check_llm_router()
        checks.append(router_result)

        # Check tool registry
        tools_result = self._check_tool_registry()
        checks.append(tools_result)

        # Check memory providers
        memory_result = self._check_memory_providers()
        checks.append(memory_result)

        overall_status = self._aggregate_status(checks)
        total_latency_ms = (time.perf_counter() - start_time) * 1000

        # Emit aggregated metrics
        _emit_health_metrics("service", overall_status.value, total_latency_ms)

        # Emit per-component metrics
        for check in checks:
            _emit_health_metrics("service", check.status.value, check.latency_ms, component=check.component)

        if overall_status == HealthStatus.UNHEALTHY:
            return StepResult.fail(
                error=f"Core services unavailable: {self._format_failures(checks)}",
                error_category=ErrorCategory.DEPENDENCY,
                retryable=False,
                status=overall_status.value,
                checks=[check.to_dict() for check in checks],
                latency_ms=round(total_latency_ms, 2),
                metadata={"check_type": "service", "failed_components": self._get_failed_components(checks)},
            )

        return StepResult.ok(
            status=overall_status.value,
            checks=[check.to_dict() for check in checks],
            latency_ms=round(total_latency_ms, 2),
            metadata={"check_type": "service", "total_latency_ms": total_latency_ms},
        )

    async def _check_qdrant(self) -> HealthCheckResult:
        """Check Qdrant vector database connectivity."""
        start_time = time.perf_counter()

        try:
            from domains.memory.vector.client_factory import get_qdrant_client

            client = get_qdrant_client()
            if client is None:
                return HealthCheckResult(
                    component="qdrant",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    message="Qdrant client not initialized",
                )

            # Attempt lightweight health check
            try:
                # get_collections is a fast health check operation
                await asyncio.wait_for(asyncio.to_thread(client.get_collections), timeout=2.0)
                latency_ms = (time.perf_counter() - start_time) * 1000

                return HealthCheckResult(
                    component="qdrant",
                    status=HealthStatus.HEALTHY,
                    latency_ms=latency_ms,
                    message="Connected",
                )
            except asyncio.TimeoutError:
                return HealthCheckResult(
                    component="qdrant",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    message="Connection timeout (>2s)",
                )
            except Exception as e:
                return HealthCheckResult(
                    component="qdrant",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    message=f"Connection failed: {e!s}",
                )

        except Exception as e:
            return HealthCheckResult(
                component="qdrant",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.perf_counter() - start_time) * 1000,
                message=f"Import error: {e!s}",
            )

    async def _check_redis(self) -> HealthCheckResult:
        """Check Redis cache availability."""
        start_time = time.perf_counter()

        try:
            # Redis is optional, graceful degradation if not available
            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                return HealthCheckResult(
                    component="redis",
                    status=HealthStatus.DEGRADED,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    message="Redis not configured (optional)",
                )

            # Attempt ping
            try:
                import redis.asyncio as redis

                client = await redis.from_url(redis_url)
                await asyncio.wait_for(client.ping(), timeout=1.0)
                await client.aclose()

                return HealthCheckResult(
                    component="redis",
                    status=HealthStatus.HEALTHY,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    message="Connected",
                )
            except asyncio.TimeoutError:
                return HealthCheckResult(
                    component="redis",
                    status=HealthStatus.DEGRADED,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    message="Timeout (>1s), cache disabled",
                )
            except Exception as e:
                return HealthCheckResult(
                    component="redis",
                    status=HealthStatus.DEGRADED,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    message=f"Unavailable: {e!s}, cache disabled",
                )

        except Exception as e:
            return HealthCheckResult(
                component="redis",
                status=HealthStatus.DEGRADED,
                latency_ms=(time.perf_counter() - start_time) * 1000,
                message=f"Import error: {e!s}",
            )

    async def _check_neo4j(self) -> HealthCheckResult:
        """Check Neo4j graph database connectivity."""
        start_time = time.perf_counter()

        try:
            neo4j_uri = os.getenv("NEO4J_URI")
            if not neo4j_uri:
                return HealthCheckResult(
                    component="neo4j",
                    status=HealthStatus.DEGRADED,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    message="Neo4j not configured",
                )

            # Attempt driver ping
            try:
                try:
                    from neo4j import AsyncGraphDatabase  # type: ignore
                except ImportError:
                    return HealthCheckResult(
                        component="neo4j",
                        status=HealthStatus.DEGRADED,
                        latency_ms=(time.perf_counter() - start_time) * 1000,
                        message="Neo4j driver not installed",
                    )

                driver = AsyncGraphDatabase.driver(
                    neo4j_uri, auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", ""))
                )

                await asyncio.wait_for(driver.verify_connectivity(), timeout=2.0)
                await driver.close()

                return HealthCheckResult(
                    component="neo4j",
                    status=HealthStatus.HEALTHY,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    message="Connected",
                )
            except asyncio.TimeoutError:
                return HealthCheckResult(
                    component="neo4j",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    message="Connection timeout (>2s)",
                )
            except Exception as e:
                return HealthCheckResult(
                    component="neo4j",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    message=f"Connection failed: {e!s}",
                )

        except Exception as e:
            return HealthCheckResult(
                component="neo4j",
                status=HealthStatus.DEGRADED,
                latency_ms=(time.perf_counter() - start_time) * 1000,
                message=f"Import error: {e!s}",
            )

    def _check_configuration(self) -> HealthCheckResult:
        """Check critical configuration completeness."""
        start_time = time.perf_counter()

        missing_critical = []
        required_vars = []

        # Check OpenAI or OpenRouter key
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("OPENROUTER_API_KEY"):
            missing_critical.append("LLM API key (OPENAI_API_KEY or OPENROUTER_API_KEY)")

        # Check Discord token if running bot mode
        if os.getenv("RUN_MODE", "api") == "discord" and not os.getenv("DISCORD_BOT_TOKEN"):
            missing_critical.append("DISCORD_BOT_TOKEN")

        # Check Qdrant URL
        if not os.getenv("QDRANT_URL"):
            required_vars.append("QDRANT_URL")

        if missing_critical or required_vars:
            return HealthCheckResult(
                component="configuration",
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.perf_counter() - start_time) * 1000,
                message=f"Missing config: {', '.join(missing_critical + required_vars)}",
                details={"missing_critical": missing_critical, "missing_optional": required_vars},
            )

        return HealthCheckResult(
            component="configuration",
            status=HealthStatus.HEALTHY,
            latency_ms=(time.perf_counter() - start_time) * 1000,
            message="Configuration complete",
        )

    def _check_llm_router(self) -> HealthCheckResult:
        """Check LLM router initialization."""
        start_time = time.perf_counter()

        try:
            from platform.llm.llm_router import get_router

            router = get_router()
            if router is None:
                return HealthCheckResult(
                    component="llm_router",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    message="Router not initialized",
                )

            # Check if router has clients
            available_models = getattr(router, "_clients", {})
            if not available_models:
                return HealthCheckResult(
                    component="llm_router",
                    status=HealthStatus.DEGRADED,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    message="No LLM clients configured",
                )

            return HealthCheckResult(
                component="llm_router",
                status=HealthStatus.HEALTHY,
                latency_ms=(time.perf_counter() - start_time) * 1000,
                message=f"Router active with {len(available_models)} clients",
                details={"client_count": len(available_models)},
            )

        except Exception as e:
            return HealthCheckResult(
                component="llm_router",
                status=HealthStatus.DEGRADED,
                latency_ms=(time.perf_counter() - start_time) * 1000,
                message=f"Router check failed: {e!s}",
            )

    def _check_tool_registry(self) -> HealthCheckResult:
        """Check tool registry availability."""
        start_time = time.perf_counter()

        try:
            # Import tool registry
            from ultimate_discord_intelligence_bot.tools import MAPPING as tool_mapping

            if not tool_mapping:
                return HealthCheckResult(
                    component="tool_registry",
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    message="Tool registry empty",
                )

            return HealthCheckResult(
                component="tool_registry",
                status=HealthStatus.HEALTHY,
                latency_ms=(time.perf_counter() - start_time) * 1000,
                message=f"{len(tool_mapping)} tools registered",
                details={"tool_count": len(tool_mapping)},
            )

        except Exception as e:
            return HealthCheckResult(
                component="tool_registry",
                status=HealthStatus.DEGRADED,
                latency_ms=(time.perf_counter() - start_time) * 1000,
                message=f"Registry check failed: {e!s}",
            )

    def _check_memory_providers(self) -> HealthCheckResult:
        """Check memory provider configuration."""
        start_time = time.perf_counter()

        try:
            # Check if memory providers are configured
            providers = []
            if os.getenv("ENABLE_GRAPH_MEMORY", "false").lower() == "true":
                providers.append("graph")
            if os.getenv("QDRANT_URL"):
                providers.append("vector")

            if not providers:
                return HealthCheckResult(
                    component="memory_providers",
                    status=HealthStatus.DEGRADED,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    message="No memory providers configured",
                )

            return HealthCheckResult(
                component="memory_providers",
                status=HealthStatus.HEALTHY,
                latency_ms=(time.perf_counter() - start_time) * 1000,
                message=f"Providers active: {', '.join(providers)}",
                details={"providers": providers},
            )

        except Exception as e:
            return HealthCheckResult(
                component="memory_providers",
                status=HealthStatus.DEGRADED,
                latency_ms=(time.perf_counter() - start_time) * 1000,
                message=f"Provider check failed: {e!s}",
            )

    def _aggregate_status(self, checks: list[HealthCheckResult]) -> HealthStatus:
        """Aggregate individual check statuses into overall status.

        Rules:
        - Any UNHEALTHY -> overall UNHEALTHY
        - All HEALTHY -> overall HEALTHY
        - Mix of HEALTHY/DEGRADED -> overall DEGRADED
        """
        statuses = {check.status for check in checks}

        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        if HealthStatus.UNKNOWN in statuses:
            return HealthStatus.UNKNOWN

        return HealthStatus.HEALTHY

    def _format_failures(self, checks: list[HealthCheckResult]) -> str:
        """Format failed checks into error message."""
        failed = [check for check in checks if check.status == HealthStatus.UNHEALTHY]
        if not failed:
            return "No critical failures"
        return ", ".join(f"{check.component}: {check.message}" for check in failed)

    def _get_failed_components(self, checks: list[HealthCheckResult]) -> list[str]:
        """Extract names of failed components."""
        return [check.component for check in checks if check.status == HealthStatus.UNHEALTHY]


# Singleton instance
_health_checker: HealthChecker | None = None


def get_health_checker() -> HealthChecker:
    """Get singleton health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


__all__ = ["HealthCheckResult", "HealthChecker", "HealthStatus", "get_health_checker"]
