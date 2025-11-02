"""Unified service facade for OpenRouter operations.

This module provides a simplified interface for all OpenRouter service operations,
coordinating caching, budgeting, metrics, and routing through a single facade.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any
from platform.core.step_result import StepResult

if TYPE_CHECKING:
    from .service import OpenRouterService
log = logging.getLogger(__name__)


class FacadeCacheManager:
    """Manages caching operations for the OpenRouter service."""

    def __init__(self, service: OpenRouterService) -> None:
        """Initialize cache manager with service reference."""
        self._service = service

    def get_cached_response(self, prompt: str, model: str, **kwargs: Any) -> dict[str, Any] | None:
        """Retrieve cached response if available."""
        try:
            if self._service.cache:
                cache_key = self._service.cache.make_key(prompt, model)
                return self._service.cache.get(cache_key)
            return None
        except Exception as e:
            log.debug("Cache retrieval failed: %s", e)
            return None

    def set_cached_response(self, prompt: str, model: str, response: dict[str, Any], **kwargs: Any) -> None:
        """Store response in cache."""
        try:
            if self._service.cache:
                cache_key = self._service.cache.make_key(prompt, model)
                self._service.cache.set(cache_key, response)
        except Exception as e:
            log.debug("Cache storage failed: %s", e)


class FacadeBudgetManager:
    """Manages budget enforcement for OpenRouter requests."""

    def __init__(self, service: OpenRouterService) -> None:
        """Initialize budget manager with service reference."""
        self._service = service

    def check_budget_limits(self, prompt: str, model: str, task_type: str) -> StepResult | None:
        """Check if request is within budget limits."""
        try:
            tokens_in = self._service.prompt_engine.count_tokens(prompt, model)
            projected_cost = self._service.token_meter.estimate_cost(tokens_in, model)
            if (
                hasattr(self._service, "request_tracker")
                and self._service.request_tracker
                and (not self._service.request_tracker.can_charge(projected_cost, task_type))
            ):
                return StepResult.fail("Cumulative cost exceeds limit")
            if hasattr(self._service.token_meter, "max_cost_per_request"):
                max_cost = self._service.token_meter.max_cost_per_request
                if max_cost and projected_cost > max_cost:
                    return StepResult.fail("Projected cost exceeds per-request limit")
            return None
        except Exception as e:
            log.debug("Budget check failed: %s", e)
            return StepResult.fail(f"Budget check failed: {e!s}")

    def charge_budget(self, cost: float, task_type: str) -> None:
        """Charge the budget for a completed request."""
        try:
            if hasattr(self._service, "request_tracker") and self._service.request_tracker:
                self._service.request_tracker.charge(cost, task_type)
        except Exception as e:
            log.debug("Budget charge failed: %s", e)


class FacadeMetricsCollector:
    """Collects and reports metrics for OpenRouter operations."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self._request_count = 0
        self._total_latency = 0.0
        self._total_tokens = 0

    def record_request(self, latency_ms: float, tokens: int, success: bool) -> None:
        """Record metrics for a completed request."""
        self._request_count += 1
        self._total_latency += latency_ms
        self._total_tokens += tokens
        log.debug(
            "Request metrics: count=%d, latency=%.2fms, tokens=%d, success=%s",
            self._request_count,
            latency_ms,
            tokens,
            success,
        )

    def get_stats(self) -> dict[str, Any]:
        """Get current metrics statistics."""
        avg_latency = self._total_latency / max(self._request_count, 1)
        return {
            "request_count": self._request_count,
            "total_latency_ms": self._total_latency,
            "average_latency_ms": avg_latency,
            "total_tokens": self._total_tokens,
        }


class OpenRouterServiceFacade:
    """Unified interface for all OpenRouter operations.

    This facade provides a simplified interface that coordinates caching,
    budgeting, metrics collection, and routing through the underlying
    OpenRouterService while maintaining backward compatibility.
    """

    def __init__(self, service: OpenRouterService) -> None:
        """Initialize facade with OpenRouter service.

        Args:
            service: The underlying OpenRouterService instance
        """
        self._service = service
        self._cache_manager = FacadeCacheManager(service)
        self._budget_manager = FacadeBudgetManager(service)
        self._metrics_collector = FacadeMetricsCollector()

    def route(
        self,
        prompt: str,
        task_type: str = "general",
        model: str | None = None,
        provider_opts: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> StepResult:
        """Route a prompt with unified caching, budgeting, and metrics.

        Args:
            prompt: The prompt to route
            task_type: Type of task (general, analysis, etc.)
            model: Specific model to use (optional)
            provider_opts: Provider-specific options
            **kwargs: Additional routing options

        Returns:
            StepResult with routing response or error
        """
        import time

        start_time = time.perf_counter()
        try:
            cached_response = self._cache_manager.get_cached_response(prompt, model or "default", task_type=task_type)
            if cached_response:
                log.debug("Cache hit for prompt routing")
                return StepResult.ok(data=cached_response)
            budget_error = self._budget_manager.check_budget_limits(prompt, model or "default", task_type)
            if budget_error:
                return budget_error
            result = self._service.route(
                prompt=prompt, task_type=task_type, model=model, provider_opts=provider_opts, **kwargs
            )
            latency_ms = (time.perf_counter() - start_time) * 1000
            tokens = result.data.get("tokens", 0) if result.success else 0
            self._metrics_collector.record_request(latency_ms, tokens, result.success)
            if result.success and result.data:
                self._cache_manager.set_cached_response(prompt, model or "default", result.data, task_type=task_type)
            return result
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._metrics_collector.record_request(latency_ms, 0, False)
            log.error("Facade routing failed: %s", e)
            return StepResult.fail(f"Routing failed: {e!s}")

    def get_metrics(self) -> dict[str, Any]:
        """Get current service metrics.

        Returns:
            Dictionary containing service performance metrics
        """
        return self._metrics_collector.get_stats()

    def health_check(self) -> StepResult:
        """Perform health check on the service.

        Returns:
            StepResult indicating service health status
        """
        try:
            test_result = self._service.route("health check", task_type="general")
            if test_result.success:
                return StepResult.ok(data={"status": "healthy", "service": "openrouter"})
            else:
                return StepResult.fail("Service health check failed")
        except Exception as e:
            return StepResult.fail(f"Health check error: {e!s}")

    @property
    def service(self) -> OpenRouterService:
        """Get the underlying OpenRouter service instance."""
        return self._service

    @property
    def cache_manager(self) -> FacadeCacheManager:
        """Get the cache manager instance."""
        return self._cache_manager

    @property
    def budget_manager(self) -> FacadeBudgetManager:
        """Get the budget manager instance."""
        return self._budget_manager

    @property
    def metrics_collector(self) -> FacadeMetricsCollector:
        """Get the metrics collector instance."""
        return self._metrics_collector
