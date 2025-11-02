"""Circuit breaker pattern for OpenRouter service resilience.

This module provides circuit breaker functionality to prevent cascading
failures and improve service reliability.
"""

from __future__ import annotations
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any
from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags
from platform.core.step_result import StepResult

if TYPE_CHECKING:
    from collections.abc import Callable
    from .service import OpenRouterService
log = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    recovery_timeout: int = 60
    success_threshold: int = 3
    timeout: int = 30
    enable_circuit_breaker: bool = True


class CircuitBreaker:
    """Circuit breaker implementation for OpenRouter service."""

    def __init__(self, name: str, config: CircuitBreakerConfig | None = None) -> None:
        """Initialize circuit breaker.

        Args:
            name: Name of the circuit breaker
            config: Circuit breaker configuration
        """
        self._name = name
        self._config = config or CircuitBreakerConfig()
        self._feature_flags = FeatureFlags()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._last_success_time: float | None = None
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "circuit_opens": 0,
            "circuit_closes": 0,
            "requests_blocked": 0,
            "half_open_attempts": 0,
        }

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset.

        Returns:
            True if reset should be attempted
        """
        if self._last_failure_time is None:
            return False
        return time.time() - self._last_failure_time >= self._config.recovery_timeout

    def _can_execute(self) -> bool:
        """Check if request can be executed based on circuit state.

        Returns:
            True if request can be executed
        """
        if not self._feature_flags.ENABLE_OPENROUTER_CIRCUIT_BREAKER or not self._config.enable_circuit_breaker:
            return True
        if self._state == CircuitState.CLOSED:
            return True
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
                self._stats["half_open_attempts"] += 1
                log.info("Circuit breaker %s transitioning to HALF_OPEN", self._name)
                return True
            else:
                self._stats["requests_blocked"] += 1
                return False
        return self._state == CircuitState.HALF_OPEN

    def _on_success(self) -> None:
        """Handle successful request."""
        self._last_success_time = time.time()
        self._success_count += 1
        self._stats["successful_requests"] += 1
        if self._state == CircuitState.HALF_OPEN and self._success_count >= self._config.success_threshold:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._stats["circuit_closes"] += 1
            log.info("Circuit breaker %s closed after successful recovery", self._name)

    def _on_failure(self) -> None:
        """Handle failed request."""
        self._last_failure_time = time.time()
        self._failure_count += 1
        self._stats["failed_requests"] += 1
        if self._state == CircuitState.CLOSED:
            if self._failure_count >= self._config.failure_threshold:
                self._state = CircuitState.OPEN
                self._stats["circuit_opens"] += 1
                log.warning("Circuit breaker %s opened after %d failures", self._name, self._failure_count)
        elif self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            self._stats["circuit_opens"] += 1
            log.warning("Circuit breaker %s opened due to failure in HALF_OPEN state", self._name)

    def execute(self, func: Callable[[], Any]) -> Any:
        """Execute function with circuit breaker protection.

        Args:
            func: Function to execute

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenException: If circuit is open
        """
        self._stats["total_requests"] += 1
        if not self._can_execute():
            raise CircuitBreakerOpenException(
                f"Circuit breaker {self._name} is OPEN. Last failure: {self._last_failure_time}, Recovery timeout: {self._config.recovery_timeout}s"
            )
        try:
            result = func()
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    async def execute_async(self, func: Callable[[], Any]) -> Any:
        """Execute async function with circuit breaker protection.

        Args:
            func: Async function to execute

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenException: If circuit is open
        """
        self._stats["total_requests"] += 1
        if not self._can_execute():
            raise CircuitBreakerOpenException(
                f"Circuit breaker {self._name} is OPEN. Last failure: {self._last_failure_time}, Recovery timeout: {self._config.recovery_timeout}s"
            )
        try:
            result = await func()
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def get_state(self) -> CircuitState:
        """Get current circuit breaker state.

        Returns:
            Current circuit state
        """
        return self._state

    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics.

        Returns:
            Dictionary with circuit breaker statistics
        """
        total_requests = self._stats["total_requests"]
        success_rate = self._stats["successful_requests"] / total_requests * 100 if total_requests > 0 else 0
        return {
            **self._stats,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "success_rate_percent": round(success_rate, 2),
            "last_failure_time": self._last_failure_time,
            "last_success_time": self._last_success_time,
            "config": {
                "failure_threshold": self._config.failure_threshold,
                "recovery_timeout": self._config.recovery_timeout,
                "success_threshold": self._config.success_threshold,
                "timeout": self._config.timeout,
                "enable_circuit_breaker": self._config.enable_circuit_breaker,
            },
        }

    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._last_success_time = None
        log.info("Circuit breaker %s manually reset", self._name)

    def force_open(self) -> None:
        """Force circuit breaker to open state."""
        self._state = CircuitState.OPEN
        self._last_failure_time = time.time()
        self._stats["circuit_opens"] += 1
        log.warning("Circuit breaker %s manually forced open", self._name)


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""


class CircuitBreakerManager:
    """Manages circuit breakers for different services and endpoints."""

    def __init__(self) -> None:
        """Initialize circuit breaker manager."""
        self._breakers: dict[str, CircuitBreaker] = {}
        self._feature_flags = FeatureFlags()

    def get_breaker(self, name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
        """Get or create a circuit breaker.

        Args:
            name: Name of the circuit breaker
            config: Circuit breaker configuration

        Returns:
            CircuitBreaker instance
        """
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, config)
            log.debug("Created circuit breaker: %s", name)
        return self._breakers[name]

    def get_openrouter_breaker(self) -> CircuitBreaker:
        """Get circuit breaker for OpenRouter API.

        Returns:
            CircuitBreaker for OpenRouter API
        """
        config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60,
            success_threshold=3,
            timeout=30,
            enable_circuit_breaker=self._feature_flags.ENABLE_OPENROUTER_CIRCUIT_BREAKER,
        )
        return self.get_breaker("openrouter_api", config)

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all circuit breakers.

        Returns:
            Dictionary mapping breaker names to their statistics
        """
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset()
        log.info("Reset all circuit breakers")

    def force_open_all(self) -> None:
        """Force all circuit breakers to open state."""
        for breaker in self._breakers.values():
            breaker.force_open()
        log.warning("Forced all circuit breakers open")


class OpenRouterCircuitBreaker:
    """Circuit breaker wrapper for OpenRouter service operations."""

    def __init__(self, service: OpenRouterService) -> None:
        """Initialize OpenRouter circuit breaker.

        Args:
            service: The OpenRouter service instance
        """
        self._service = service
        self._manager = CircuitBreakerManager()
        self._api_breaker = self._manager.get_openrouter_breaker()
        self._feature_flags = FeatureFlags()

    def route_with_circuit_breaker(
        self,
        prompt: str,
        task_type: str = "general",
        model: str | None = None,
        provider_opts: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> StepResult:
        """Route a prompt with circuit breaker protection.

        Args:
            prompt: The prompt to route
            task_type: Type of task
            model: Specific model to use
            provider_opts: Provider-specific options
            **kwargs: Additional routing options

        Returns:
            StepResult with routing response or error
        """
        if not self._feature_flags.ENABLE_OPENROUTER_CIRCUIT_BREAKER:
            return self._service.route(prompt, task_type, model, provider_opts, **kwargs)
        try:

            def route_func() -> StepResult:
                return self._service.route(prompt, task_type, model, provider_opts, **kwargs)

            result = self._api_breaker.execute(route_func)
            return result
        except CircuitBreakerOpenException as e:
            log.warning("Circuit breaker blocked request: %s", e)
            return StepResult.fail(f"Service temporarily unavailable: {e!s}")
        except Exception as e:
            log.error("Routing failed: %s", e)
            return StepResult.fail(f"Routing failed: {e!s}")

    async def route_async_with_circuit_breaker(
        self,
        prompt: str,
        task_type: str = "general",
        model: str | None = None,
        provider_opts: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Route a prompt asynchronously with circuit breaker protection.

        Args:
            prompt: The prompt to route
            task_type: Type of task
            model: Specific model to use
            provider_opts: Provider-specific options
            **kwargs: Additional routing options

        Returns:
            Response dictionary
        """
        if not self._feature_flags.ENABLE_OPENROUTER_CIRCUIT_BREAKER:
            result = self._service.route(prompt, task_type, model, provider_opts, **kwargs)
            return result.data if result.success else {"status": "error", "error": result.error}
        try:

            async def route_func() -> dict[str, Any]:
                result = self._service.route(prompt, task_type, model, provider_opts, **kwargs)
                return result.data if result.success else {"status": "error", "error": result.error}

            return await self._api_breaker.execute_async(route_func)
        except CircuitBreakerOpenException as e:
            log.warning("Circuit breaker blocked async request: %s", e)
            return {
                "status": "error",
                "error": f"Service temporarily unavailable: {e!s}",
                "model": model or "unknown",
                "tokens": 0,
                "provider": provider_opts or {},
            }
        except Exception as e:
            log.error("Async routing failed: %s", e)
            return {
                "status": "error",
                "error": f"Routing failed: {e!s}",
                "model": model or "unknown",
                "tokens": 0,
                "provider": provider_opts or {},
            }

    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics.

        Returns:
            Dictionary with circuit breaker statistics
        """
        return self._manager.get_all_stats()

    def reset_circuit_breakers(self) -> None:
        """Reset all circuit breakers."""
        self._manager.reset_all()

    def force_open_circuit_breakers(self) -> None:
        """Force all circuit breakers to open state."""
        self._manager.force_open_all()


_circuit_breaker_manager: CircuitBreakerManager | None = None


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get or create global circuit breaker manager.

    Returns:
        CircuitBreakerManager instance
    """
    global _circuit_breaker_manager
    if _circuit_breaker_manager is None:
        _circuit_breaker_manager = CircuitBreakerManager()
    return _circuit_breaker_manager


def get_openrouter_circuit_breaker(service: OpenRouterService) -> OpenRouterCircuitBreaker:
    """Get or create OpenRouter circuit breaker for the service.

    Args:
        service: The OpenRouter service instance

    Returns:
        OpenRouterCircuitBreaker instance
    """
    return OpenRouterCircuitBreaker(service)
