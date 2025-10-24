"""Enhanced retry strategies for OpenRouter service.

This module provides advanced retry mechanisms with exponential backoff,
jitter, and configurable retry policies.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags
from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from .service import OpenRouterService


log = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry strategy."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_range: float = 0.1
    retryable_status_codes: set[int] = None
    retryable_exceptions: tuple[type, ...] = None
    enable_retry: bool = True

    def __post_init__(self) -> None:
        """Initialize default values after dataclass creation."""
        if self.retryable_status_codes is None:
            self.retryable_status_codes = {500, 502, 503, 504, 429}

        if self.retryable_exceptions is None:
            self.retryable_exceptions = (
                ConnectionError,
                TimeoutError,
                asyncio.TimeoutError,
            )


class RetryStrategy:
    """Enhanced retry strategy with exponential backoff and jitter."""

    def __init__(self, config: RetryConfig | None = None) -> None:
        """Initialize retry strategy.

        Args:
            config: Retry configuration
        """
        self._config = config or RetryConfig()
        self._feature_flags = FeatureFlags()
        self._stats = {
            "total_attempts": 0,
            "successful_attempts": 0,
            "failed_attempts": 0,
            "retries_performed": 0,
            "total_retry_delay": 0.0,
        }

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = self._config.base_delay * (self._config.exponential_base**attempt)

        # Apply maximum delay limit
        delay = min(delay, self._config.max_delay)

        # Add jitter if enabled
        if self._config.jitter:
            jitter_amount = delay * self._config.jitter_range
            jitter = random.uniform(-jitter_amount, jitter_amount)
            delay += jitter

        # Ensure delay is positive
        return max(0.0, delay)

    def _should_retry(self, exception: Exception | None, status_code: int | None = None) -> bool:
        """Determine if the operation should be retried.

        Args:
            exception: Exception that occurred
            status_code: HTTP status code (if applicable)

        Returns:
            True if operation should be retried
        """
        if not self._config.enable_retry:
            return False

        # Check status code
        if status_code is not None:
            if status_code in self._config.retryable_status_codes:
                return True

        # Check exception type
        if exception is not None:
            if isinstance(exception, self._config.retryable_exceptions):
                return True

        return False

    def execute_with_retry(
        self,
        func: Callable[[], Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries failed
        """
        last_exception = None
        status_code = None

        for attempt in range(self._config.max_retries + 1):
            self._stats["total_attempts"] += 1

            try:
                result = func(*args, **kwargs)
                self._stats["successful_attempts"] += 1

                if attempt > 0:
                    self._stats["retries_performed"] += 1
                    log.info("Operation succeeded after %d retries", attempt)

                return result

            except Exception as e:
                last_exception = e
                self._stats["failed_attempts"] += 1

                # Extract status code if it's an HTTP exception
                if hasattr(e, "response") and hasattr(e.response, "status_code"):
                    status_code = e.response.status_code
                elif hasattr(e, "status_code"):
                    status_code = e.status_code

                # Check if we should retry
                if attempt < self._config.max_retries and self._should_retry(e, status_code):
                    delay = self._calculate_delay(attempt)
                    self._stats["total_retry_delay"] += delay

                    log.warning("Attempt %d failed, retrying in %.2fs: %s", attempt + 1, delay, str(e))

                    time.sleep(delay)
                else:
                    # No more retries or not retryable
                    if attempt >= self._config.max_retries:
                        log.error("All %d retry attempts failed", self._config.max_retries)
                    else:
                        log.error("Non-retryable error: %s", str(e))
                    break

        # All retries failed
        raise last_exception

    async def execute_async_with_retry(
        self,
        func: Callable[[], Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute async function with retry logic.

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries failed
        """
        last_exception = None
        status_code = None

        for attempt in range(self._config.max_retries + 1):
            self._stats["total_attempts"] += 1

            try:
                result = await func(*args, **kwargs)
                self._stats["successful_attempts"] += 1

                if attempt > 0:
                    self._stats["retries_performed"] += 1
                    log.info("Async operation succeeded after %d retries", attempt)

                return result

            except Exception as e:
                last_exception = e
                self._stats["failed_attempts"] += 1

                # Extract status code if it's an HTTP exception
                if hasattr(e, "response") and hasattr(e.response, "status_code"):
                    status_code = e.response.status_code
                elif hasattr(e, "status_code"):
                    status_code = e.status_code

                # Check if we should retry
                if attempt < self._config.max_retries and self._should_retry(e, status_code):
                    delay = self._calculate_delay(attempt)
                    self._stats["total_retry_delay"] += delay

                    log.warning("Async attempt %d failed, retrying in %.2fs: %s", attempt + 1, delay, str(e))

                    await asyncio.sleep(delay)
                else:
                    # No more retries or not retryable
                    if attempt >= self._config.max_retries:
                        log.error("All %d async retry attempts failed", self._config.max_retries)
                    else:
                        log.error("Non-retryable async error: %s", str(e))
                    break

        # All retries failed
        raise last_exception

    def get_stats(self) -> dict[str, Any]:
        """Get retry strategy statistics.

        Returns:
            Dictionary with retry statistics
        """
        total_attempts = self._stats["total_attempts"]
        success_rate = self._stats["successful_attempts"] / total_attempts * 100 if total_attempts > 0 else 0

        avg_retry_delay = (
            self._stats["total_retry_delay"] / max(self._stats["retries_performed"], 1)
            if self._stats["retries_performed"] > 0
            else 0
        )

        return {
            **self._stats,
            "success_rate_percent": round(success_rate, 2),
            "average_retry_delay": round(avg_retry_delay, 2),
            "config": {
                "max_retries": self._config.max_retries,
                "base_delay": self._config.base_delay,
                "max_delay": self._config.max_delay,
                "exponential_base": self._config.exponential_base,
                "jitter": self._config.jitter,
                "enable_retry": self._config.enable_retry,
            },
        }

    def reset_stats(self) -> None:
        """Reset retry statistics."""
        self._stats = {
            "total_attempts": 0,
            "successful_attempts": 0,
            "failed_attempts": 0,
            "retries_performed": 0,
            "total_retry_delay": 0.0,
        }


class RetryManager:
    """Manages retry strategies for different operations."""

    def __init__(self) -> None:
        """Initialize retry manager."""
        self._strategies: dict[str, RetryStrategy] = {}
        self._feature_flags = FeatureFlags()
        self._setup_default_strategies()

    def _setup_default_strategies(self) -> None:
        """Setup default retry strategies."""
        # API request strategy
        api_config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True,
            retryable_status_codes={500, 502, 503, 504, 429},
            retryable_exceptions=(ConnectionError, TimeoutError, asyncio.TimeoutError),
        )
        self._strategies["api_request"] = RetryStrategy(api_config)

        # Cache operation strategy
        cache_config = RetryConfig(
            max_retries=2,
            base_delay=0.5,
            max_delay=5.0,
            exponential_base=1.5,
            jitter=True,
            retryable_exceptions=(ConnectionError, TimeoutError),
        )
        self._strategies["cache_operation"] = RetryStrategy(cache_config)

        # Health check strategy
        health_config = RetryConfig(
            max_retries=1,
            base_delay=0.1,
            max_delay=1.0,
            exponential_base=2.0,
            jitter=False,
            retryable_exceptions=(ConnectionError,),
        )
        self._strategies["health_check"] = RetryStrategy(health_config)

    def get_strategy(self, name: str) -> RetryStrategy:
        """Get retry strategy by name.

        Args:
            name: Strategy name

        Returns:
            RetryStrategy instance
        """
        if name not in self._strategies:
            # Create default strategy if not found
            self._strategies[name] = RetryStrategy()
            log.debug("Created default retry strategy for: %s", name)

        return self._strategies[name]

    def add_strategy(self, name: str, strategy: RetryStrategy) -> None:
        """Add a custom retry strategy.

        Args:
            name: Strategy name
            strategy: RetryStrategy instance
        """
        self._strategies[name] = strategy
        log.debug("Added custom retry strategy: %s", name)

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all retry strategies.

        Returns:
            Dictionary mapping strategy names to their statistics
        """
        return {name: strategy.get_stats() for name, strategy in self._strategies.items()}

    def reset_all_stats(self) -> None:
        """Reset statistics for all retry strategies."""
        for strategy in self._strategies.values():
            strategy.reset_stats()
        log.info("Reset all retry strategy statistics")


class OpenRouterRetryWrapper:
    """Retry wrapper for OpenRouter service operations."""

    def __init__(self, service: OpenRouterService) -> None:
        """Initialize retry wrapper.

        Args:
            service: The OpenRouter service instance
        """
        self._service = service
        self._retry_manager = RetryManager()
        self._feature_flags = FeatureFlags()

    def route_with_retry(
        self,
        prompt: str,
        task_type: str = "general",
        model: str | None = None,
        provider_opts: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> StepResult:
        """Route a prompt with retry logic.

        Args:
            prompt: The prompt to route
            task_type: Type of task
            model: Specific model to use
            provider_opts: Provider-specific options
            **kwargs: Additional routing options

        Returns:
            StepResult with routing response or error
        """
        retry_strategy = self._retry_manager.get_strategy("api_request")

        try:

            def route_func() -> StepResult:
                return self._service.route(prompt, task_type, model, provider_opts, **kwargs)

            result = retry_strategy.execute_with_retry(route_func)
            return result

        except Exception as e:
            log.error("Routing with retry failed: %s", e)
            return StepResult.fail(f"Routing failed after retries: {e!s}")

    async def route_async_with_retry(
        self,
        prompt: str,
        task_type: str = "general",
        model: str | None = None,
        provider_opts: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Route a prompt asynchronously with retry logic.

        Args:
            prompt: The prompt to route
            task_type: Type of task
            model: Specific model to use
            provider_opts: Provider-specific options
            **kwargs: Additional routing options

        Returns:
            Response dictionary
        """
        retry_strategy = self._retry_manager.get_strategy("api_request")

        try:

            async def route_func() -> dict[str, Any]:
                result = self._service.route(prompt, task_type, model, provider_opts, **kwargs)
                return result.data if result.success else {"status": "error", "error": result.error}

            return await retry_strategy.execute_async_with_retry(route_func)

        except Exception as e:
            log.error("Async routing with retry failed: %s", e)
            return {
                "status": "error",
                "error": f"Async routing failed after retries: {e!s}",
                "model": model or "unknown",
                "tokens": 0,
                "provider": provider_opts or {},
            }

    def get_stats(self) -> dict[str, Any]:
        """Get retry wrapper statistics.

        Returns:
            Dictionary with retry statistics
        """
        return self._retry_manager.get_all_stats()

    def reset_stats(self) -> None:
        """Reset retry statistics."""
        self._retry_manager.reset_all_stats()


# Global retry manager instance
_retry_manager: RetryManager | None = None


def get_retry_manager() -> RetryManager:
    """Get or create global retry manager.

    Returns:
        RetryManager instance
    """
    global _retry_manager

    if _retry_manager is None:
        _retry_manager = RetryManager()

    return _retry_manager


def get_openrouter_retry_wrapper(service: OpenRouterService) -> OpenRouterRetryWrapper:
    """Get or create OpenRouter retry wrapper for the service.

    Args:
        service: The OpenRouter service instance

    Returns:
        OpenRouterRetryWrapper instance
    """
    return OpenRouterRetryWrapper(service)
