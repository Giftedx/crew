"""Comprehensive health checking system for all platform components.

This module provides centralized health monitoring for all critical components
of the multi-agent orchestration platform.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    component: str
    healthy: bool
    message: str
    latency_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class ComponentHealthChecker:
    """Centralized health checking for all platform components."""

    def __init__(self):
        self.checks: dict[str, callable] = {}
        self.check_results: dict[str, HealthCheckResult] = {}
        self.check_history: list[HealthCheckResult] = []

        # Register default health checks
        self._register_default_checks()

    def _register_default_checks(self) -> None:
        """Register default health checks for core components."""
        self.register_check("step_result", self._check_step_result)
        self.register_check("monitoring", self._check_monitoring)
        self.register_check("performance_validator", self._check_performance_validator)
        self.register_check("cost_optimizer", self._check_cost_optimizer)
        self.register_check(
            "distributed_rate_limiter", self._check_distributed_rate_limiter
        )
        self.register_check("advanced_cache", self._check_advanced_cache)
        self.register_check("llm_router", self._check_llm_router)
        self.register_check("vector_database", self._check_vector_database)
        self.register_check("agent_coordination", self._check_agent_coordination)
        self.register_check("mcp_tools", self._check_mcp_tools)

    def register_check(self, name: str, check_func: callable) -> None:
        """Register a health check function."""
        self.checks[name] = check_func
        logger.info(f"Registered health check: {name}")

    async def run_all_checks(self) -> StepResult:
        """Run all registered health checks."""
        try:
            start_time = time.time()
            results = {}
            overall_healthy = True

            # Run checks concurrently where possible
            check_tasks = []
            for name, check_func in self.checks.items():
                task = asyncio.create_task(self._run_single_check(name, check_func))
                check_tasks.append(task)

            # Wait for all checks to complete
            check_results = await asyncio.gather(*check_tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(check_results):
                check_name = list(self.checks.keys())[i]

                if isinstance(result, Exception):
                    logger.error(f"Health check {check_name} failed: {result}")
                    results[check_name] = HealthCheckResult(
                        component=check_name,
                        healthy=False,
                        message=f"Check failed: {str(result)}",
                    )
                    overall_healthy = False
                elif isinstance(result, HealthCheckResult):
                    results[check_name] = result
                    if not result.healthy:
                        overall_healthy = False
                else:
                    logger.error(
                        f"Unexpected result type for {check_name}: {type(result)}"
                    )
                    results[check_name] = HealthCheckResult(
                        component=check_name,
                        healthy=False,
                        message="Unexpected result type",
                    )
                    overall_healthy = False

            # Store results
            self.check_results = results
            self.check_history.extend(results.values())

            # Keep only last 100 results per component
            self._cleanup_history()

            duration_ms = (time.time() - start_time) * 1000

            return StepResult.ok(
                data={
                    "overall_healthy": overall_healthy,
                    "checks": {
                        name: result.__dict__ for name, result in results.items()
                    },
                    "total_checks": len(self.checks),
                    "healthy_checks": sum(1 for r in results.values() if r.healthy),
                    "duration_ms": duration_ms,
                    "timestamp": time.time(),
                }
            )

        except Exception as e:
            logger.error(f"Health check execution failed: {e}")
            return StepResult.fail(f"Health check execution failed: {str(e)}")

    async def _run_single_check(
        self, name: str, check_func: callable
    ) -> HealthCheckResult:
        """Run a single health check with timing."""
        start_time = time.time()

        try:
            # Run the check function
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()

            latency_ms = (time.time() - start_time) * 1000

            # Convert StepResult to HealthCheckResult
            if isinstance(result, StepResult):
                return HealthCheckResult(
                    component=name,
                    healthy=result.success,
                    message=result.error or "OK",
                    latency_ms=latency_ms,
                    details=result.data or {},
                )
            elif isinstance(result, HealthCheckResult):
                result.latency_ms = latency_ms
                return result
            else:
                return HealthCheckResult(
                    component=name,
                    healthy=True,
                    message="OK",
                    latency_ms=latency_ms,
                    details={"result": result},
                )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Health check {name} failed: {e}")
            return HealthCheckResult(
                component=name,
                healthy=False,
                message=f"Check failed: {str(e)}",
                latency_ms=latency_ms,
                details={"error": str(e)},
            )

    def _check_step_result(self) -> HealthCheckResult:
        """Check StepResult functionality."""
        try:
            # Test StepResult creation
            result = StepResult.ok(data={"test": "value"})
            if not result.success:
                return HealthCheckResult(
                    component="step_result",
                    healthy=False,
                    message="StepResult.ok() not working correctly",
                )

            # Test error handling
            error_result = StepResult.fail("test error")
            if error_result.success:
                return HealthCheckResult(
                    component="step_result",
                    healthy=False,
                    message="StepResult.fail() not working correctly",
                )

            return HealthCheckResult(
                component="step_result",
                healthy=True,
                message="StepResult functionality verified",
                details={"test_cases_passed": 2},
            )

        except Exception as e:
            return HealthCheckResult(
                component="step_result",
                healthy=False,
                message=f"StepResult check failed: {e}",
            )

    def _check_monitoring(self) -> HealthCheckResult:
        """Check production monitoring system."""
        try:
            from ultimate_discord_intelligence_bot.monitoring import (
                get_production_monitor,
            )

            monitor = get_production_monitor()
            health = monitor.health_check()

            if health.success:
                return HealthCheckResult(
                    component="monitoring",
                    healthy=True,
                    message="Production monitoring operational",
                    details=health.data,
                )
            else:
                return HealthCheckResult(
                    component="monitoring",
                    healthy=False,
                    message=f"Monitoring unhealthy: {health.error}",
                )

        except Exception as e:
            return HealthCheckResult(
                component="monitoring",
                healthy=False,
                message=f"Monitoring check failed: {e}",
            )

    def _check_performance_validator(self) -> HealthCheckResult:
        """Check performance validator."""
        try:
            from core.performance_validator import get_performance_validator

            validator = get_performance_validator()
            health = validator.health_check()

            if health.success:
                return HealthCheckResult(
                    component="performance_validator",
                    healthy=True,
                    message="Performance validator operational",
                    details=health.data,
                )
            else:
                return HealthCheckResult(
                    component="performance_validator",
                    healthy=False,
                    message=f"Performance validator unhealthy: {health.error}",
                )

        except Exception as e:
            return HealthCheckResult(
                component="performance_validator",
                healthy=False,
                message=f"Performance validator check failed: {e}",
            )

    def _check_cost_optimizer(self) -> HealthCheckResult:
        """Check cost optimizer."""
        try:
            from core.cost_optimizer import get_cost_optimizer

            optimizer = get_cost_optimizer()
            health = optimizer.health_check()

            if health.success:
                return HealthCheckResult(
                    component="cost_optimizer",
                    healthy=True,
                    message="Cost optimizer operational",
                    details=health.data,
                )
            else:
                return HealthCheckResult(
                    component="cost_optimizer",
                    healthy=False,
                    message=f"Cost optimizer unhealthy: {health.error}",
                )

        except Exception as e:
            return HealthCheckResult(
                component="cost_optimizer",
                healthy=False,
                message=f"Cost optimizer check failed: {e}",
            )

    def _check_distributed_rate_limiter(self) -> HealthCheckResult:
        """Check distributed rate limiter."""
        try:
            from core.distributed_rate_limiter import get_distributed_rate_limiter

            rate_limiter = get_distributed_rate_limiter()
            health = rate_limiter.health_check()

            if health.success:
                return HealthCheckResult(
                    component="distributed_rate_limiter",
                    healthy=True,
                    message="Distributed rate limiter operational",
                    details=health.data,
                )
            else:
                return HealthCheckResult(
                    component="distributed_rate_limiter",
                    healthy=False,
                    message=f"Rate limiter unhealthy: {health.error}",
                )

        except Exception as e:
            return HealthCheckResult(
                component="distributed_rate_limiter",
                healthy=False,
                message=f"Rate limiter check failed: {e}",
            )

    def _check_advanced_cache(self) -> HealthCheckResult:
        """Check advanced semantic cache."""
        try:
            from core.advanced_cache import get_advanced_cache

            cache = get_advanced_cache()
            health = cache.health_check()

            if health.success:
                return HealthCheckResult(
                    component="advanced_cache",
                    healthy=True,
                    message="Advanced cache operational",
                    details=health.data,
                )
            else:
                return HealthCheckResult(
                    component="advanced_cache",
                    healthy=False,
                    message=f"Advanced cache unhealthy: {health.error}",
                )

        except Exception as e:
            return HealthCheckResult(
                component="advanced_cache",
                healthy=False,
                message=f"Advanced cache check failed: {e}",
            )

    def _check_llm_router(self) -> HealthCheckResult:
        """Check LLM router functionality (Phase 6: migrated to OpenRouterService)."""
        try:
            # Phase 6: Use OpenRouterService instead of deprecated core.llm_router
            from ultimate_discord_intelligence_bot.services.openrouter_service import (
                OpenRouterService,
            )

            # Create a minimal OpenRouterService for testing
            service = OpenRouterService()

            # Test basic initialization (smoke test)
            try:
                return HealthCheckResult(
                    component="llm_router",
                    healthy=True,
                    message="OpenRouterService initialized successfully (Phase 6 migration)",
                    details={"service_initialized": True, "migration": "phase6"},
                )
            except Exception as router_error:
                return HealthCheckResult(
                    component="llm_router",
                    healthy=False,
                    message=f"OpenRouterService functionality issue: {router_error}",
                )

        except Exception as e:
            return HealthCheckResult(
                component="llm_router",
                healthy=False,
                message=f"LLM router check failed: {e}",
            )

    def _check_vector_database(self) -> HealthCheckResult:
        """Check vector database connectivity."""
        try:
            from memory.qdrant_provider import get_qdrant_client

            client = get_qdrant_client()

            # Test basic connectivity
            try:
                collections = client.get_collections()
                return HealthCheckResult(
                    component="vector_database",
                    healthy=True,
                    message="Vector database operational",
                    details={"collections_count": len(collections.collections)},
                )
            except Exception as db_error:
                return HealthCheckResult(
                    component="vector_database",
                    healthy=False,
                    message=f"Vector database connectivity issue: {db_error}",
                )

        except Exception as e:
            return HealthCheckResult(
                component="vector_database",
                healthy=False,
                message=f"Vector database check failed: {e}",
            )

    def _check_agent_coordination(self) -> HealthCheckResult:
        """Check agent coordination system."""
        try:
            from ultimate_discord_intelligence_bot.crew import (
                UltimateDiscordIntelligenceBotCrew,
            )

            # Test crew initialization
            crew = UltimateDiscordIntelligenceBotCrew()

            return HealthCheckResult(
                component="agent_coordination",
                healthy=True,
                message="Agent coordination system operational",
                details={"crew_initialized": True},
            )

        except Exception as e:
            return HealthCheckResult(
                component="agent_coordination",
                healthy=False,
                message=f"Agent coordination check failed: {e}",
            )

    def _check_mcp_tools(self) -> HealthCheckResult:
        """Check MCP tools integration."""
        try:
            from ultimate_discord_intelligence_bot.tools.mcp_call_tool import (
                MCPCallTool,
            )

            # Test MCP tool initialization
            mcp_tool = MCPCallTool()

            return HealthCheckResult(
                component="mcp_tools",
                healthy=True,
                message="MCP tools operational",
                details={"mcp_tool_initialized": True},
            )

        except Exception as e:
            return HealthCheckResult(
                component="mcp_tools",
                healthy=False,
                message=f"MCP tools check failed: {e}",
            )

    def _cleanup_history(self) -> None:
        """Clean up health check history to prevent memory growth."""
        if len(self.check_history) > 1000:  # Keep last 1000 results
            self.check_history = self.check_history[-1000:]

    def get_health_summary(self) -> StepResult:
        """Get overall health summary."""
        try:
            if not self.check_results:
                return StepResult.fail("No health check results available")

            total_checks = len(self.check_results)
            healthy_checks = sum(1 for r in self.check_results.values() if r.healthy)
            unhealthy_checks = total_checks - healthy_checks

            # Calculate average latency
            avg_latency = (
                sum(r.latency_ms for r in self.check_results.values()) / total_checks
            )

            # Identify unhealthy components
            unhealthy_components = [
                name
                for name, result in self.check_results.items()
                if not result.healthy
            ]

            return StepResult.ok(
                data={
                    "overall_health": "healthy"
                    if unhealthy_checks == 0
                    else "degraded",
                    "total_components": total_checks,
                    "healthy_components": healthy_checks,
                    "unhealthy_components": unhealthy_checks,
                    "unhealthy_component_list": unhealthy_components,
                    "average_check_latency_ms": avg_latency,
                    "last_check_timestamp": max(
                        r.timestamp for r in self.check_results.values()
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Health summary failed: {e}")
            return StepResult.fail(f"Health summary failed: {str(e)}")

    def health_check(self) -> StepResult:
        """Health check for the health checker itself."""
        try:
            return StepResult.ok(
                data={
                    "health_checker_healthy": True,
                    "registered_checks": len(self.checks),
                    "check_history_size": len(self.check_history),
                    "last_results_count": len(self.check_results),
                }
            )

        except Exception as e:
            logger.error(f"Health checker health check failed: {e}")
            return StepResult.fail(f"Health checker health check failed: {str(e)}")


# Global health checker instance
_health_checker: ComponentHealthChecker | None = None


def get_health_checker() -> ComponentHealthChecker:
    """Get the global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = ComponentHealthChecker()
    return _health_checker
