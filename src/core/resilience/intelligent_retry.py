"""
Intelligent retry system with exponential backoff and jitter.

This module provides advanced retry mechanisms with adaptive strategies,
circuit breaker integration, and intelligent backoff algorithms.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategies for different failure scenarios."""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    RANDOM_JITTER = "random_jitter"
    ADAPTIVE = "adaptive"


class RetryCondition(Enum):
    """Conditions for retrying operations."""

    ALWAYS = "always"
    ON_EXCEPTION = "on_exception"
    ON_TIMEOUT = "on_timeout"
    ON_HTTP_ERROR = "on_http_error"
    CUSTOM = "custom"


@dataclass
class RetryConfig:
    """Configuration for intelligent retry behavior."""

    # Basic retry configuration
    max_attempts: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds

    # Exponential backoff configuration
    backoff_multiplier: float = 2.0
    jitter_factor: float = 0.1  # Random jitter as fraction of delay

    # Adaptive retry configuration
    adaptive_enabled: bool = True
    success_rate_window: int = 10  # Number of recent attempts to consider
    min_success_rate: float = 0.7  # Minimum success rate to maintain current strategy

    # Circuit breaker integration
    circuit_breaker_enabled: bool = True
    circuit_breaker_name: str | None = None

    # Timeout configuration
    operation_timeout: float = 30.0
    retry_timeout: float = 300.0  # Total time limit for all retries

    # Logging and monitoring
    log_retries: bool = True
    log_success: bool = False
    enable_metrics: bool = True


@dataclass
class RetryMetrics:
    """Metrics for retry performance monitoring."""

    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    total_retry_time: float = 0.0
    average_attempts_per_operation: float = 0.0

    # Success rate tracking
    recent_attempts: list[bool] = None  # Will be initialized in __post_init__

    def __post_init__(self):
        if self.recent_attempts is None:
            self.recent_attempts = []

    @property
    def success_rate(self) -> float:
        """Calculate current success rate."""
        if not self.recent_attempts:
            return 1.0
        return sum(self.recent_attempts) / len(self.recent_attempts)

    @property
    def failure_rate(self) -> float:
        """Calculate current failure rate."""
        return 1.0 - self.success_rate


class RetryError(Exception):
    """Exception raised when all retry attempts are exhausted."""

    def __init__(self, message: str, last_exception: Exception | None = None, attempts: int = 0):
        super().__init__(message)
        self.last_exception = last_exception
        self.attempts = attempts


class IntelligentRetry:
    """
    Intelligent retry system with adaptive strategies and circuit breaker integration.

    Provides sophisticated retry mechanisms that adapt to system performance
    and integrate with circuit breakers for optimal resilience.
    """

    def __init__(self, name: str, config: RetryConfig | None = None):
        """Initialize intelligent retry system."""
        self.name = name
        self.config = config or RetryConfig()
        self.metrics = RetryMetrics()

        # Adaptive retry state
        self.current_strategy = RetryStrategy.EXPONENTIAL_BACKOFF
        self.adaptive_delay_multiplier = 1.0

        # Circuit breaker integration
        self._circuit_breaker = None
        if self.config.circuit_breaker_enabled:
            try:
                from .circuit_breaker import get_circuit_breaker

                self._circuit_breaker = get_circuit_breaker(self.config.circuit_breaker_name or f"{name}_retry")
            except ImportError:
                logger.warning(f"Circuit breaker not available for retry system '{name}'")

    async def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with intelligent retry logic.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            RetryError: If all retry attempts are exhausted
        """
        start_time = time.time()
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                # Check circuit breaker
                if self._circuit_breaker:
                    result = await self._circuit_breaker.call(func, *args, **kwargs)
                else:
                    # Execute with timeout
                    result = await asyncio.wait_for(
                        self._execute_function(func, *args, **kwargs),
                        timeout=self.config.operation_timeout,
                    )

                # Record success
                self._record_success(attempt, time.time() - start_time)

                if self.config.log_success:
                    logger.info(f"Retry system '{self.name}' succeeded on attempt {attempt}")

                return result

            except TimeoutError as e:
                last_exception = e
                if self.config.log_retries:
                    logger.warning(f"Retry system '{self.name}' attempt {attempt} timed out")

            except Exception as e:
                last_exception = e
                if self.config.log_retries:
                    logger.warning(f"Retry system '{self.name}' attempt {attempt} failed: {e}")

            # Check if we should retry
            if attempt < self.config.max_attempts:
                # Check total timeout
                if time.time() - start_time >= self.config.retry_timeout:
                    break

                # Calculate and apply delay
                delay = self._calculate_delay(attempt, last_exception)
                if delay > 0:
                    await asyncio.sleep(delay)

        # All attempts exhausted
        total_time = time.time() - start_time
        self._record_failure(self.config.max_attempts, total_time)

        raise RetryError(
            f"Retry system '{self.name}' exhausted all {self.config.max_attempts} attempts",
            last_exception,
            self.config.max_attempts,
        )

    async def _execute_function(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute function with proper async handling."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    def _calculate_delay(self, attempt: int, last_exception: Exception | None) -> float:
        """Calculate delay for next retry attempt."""
        if attempt >= self.config.max_attempts:
            return 0.0

        # Apply adaptive strategy
        if self.config.adaptive_enabled:
            self._adapt_strategy()

        # Calculate base delay based on strategy
        if self.current_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay * (self.config.backoff_multiplier ** (attempt - 1))
        elif self.current_strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay * attempt
        elif self.current_strategy == RetryStrategy.FIXED_DELAY:
            delay = self.config.base_delay
        else:
            delay = self.config.base_delay * (self.config.backoff_multiplier ** (attempt - 1))

        # Apply adaptive multiplier
        delay *= self.adaptive_delay_multiplier

        # Apply jitter
        if self.current_strategy == RetryStrategy.RANDOM_JITTER:
            jitter = delay * self.config.jitter_factor * random.uniform(-1, 1)
            delay += jitter

        # Clamp to max delay
        delay = min(delay, self.config.max_delay)

        return max(0, delay)

    def _adapt_strategy(self) -> None:
        """Adapt retry strategy based on recent performance."""
        if len(self.metrics.recent_attempts) < self.config.success_rate_window:
            return

        recent_success_rate = self.metrics.success_rate

        if recent_success_rate < self.config.min_success_rate:
            # Low success rate - be more conservative
            self.adaptive_delay_multiplier = min(2.0, self.adaptive_delay_multiplier * 1.1)

            if recent_success_rate < 0.5:
                # Very low success rate - switch to more conservative strategy
                if self.current_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
                    self.current_strategy = RetryStrategy.LINEAR_BACKOFF
                elif self.current_strategy == RetryStrategy.LINEAR_BACKOFF:
                    self.current_strategy = RetryStrategy.FIXED_DELAY

        elif recent_success_rate > 0.9:
            # High success rate - can be more aggressive
            self.adaptive_delay_multiplier = max(0.5, self.adaptive_delay_multiplier * 0.9)

            if self.current_strategy == RetryStrategy.FIXED_DELAY:
                self.current_strategy = RetryStrategy.LINEAR_BACKOFF
            elif self.current_strategy == RetryStrategy.LINEAR_BACKOFF:
                self.current_strategy = RetryStrategy.EXPONENTIAL_BACKOFF

    def _record_success(self, attempt: int, total_time: float) -> None:
        """Record a successful attempt."""
        self.metrics.total_attempts += attempt
        self.metrics.successful_attempts += 1
        self.metrics.total_retry_time += total_time

        # Update recent attempts
        self.metrics.recent_attempts.append(True)
        self._trim_recent_attempts()

        # Update averages
        self.metrics.average_attempts_per_operation = self.metrics.total_attempts / max(
            1, self.metrics.successful_attempts + self.metrics.failed_attempts
        )

    def _record_failure(self, attempts: int, total_time: float) -> None:
        """Record a failed operation."""
        self.metrics.total_attempts += attempts
        self.metrics.failed_attempts += 1
        self.metrics.total_retry_time += total_time

        # Update recent attempts
        for _ in range(attempts):
            self.metrics.recent_attempts.append(False)
        self._trim_recent_attempts()

        # Update averages
        self.metrics.average_attempts_per_operation = self.metrics.total_attempts / max(
            1, self.metrics.successful_attempts + self.metrics.failed_attempts
        )

    def _trim_recent_attempts(self) -> None:
        """Trim recent attempts list to window size."""
        if len(self.metrics.recent_attempts) > self.config.success_rate_window * 2:
            self.metrics.recent_attempts = self.metrics.recent_attempts[-self.config.success_rate_window :]

    def get_metrics(self) -> RetryMetrics:
        """Get current retry metrics."""
        return self.metrics

    def reset_metrics(self) -> None:
        """Reset retry metrics."""
        self.metrics = RetryMetrics()
        self.adaptive_delay_multiplier = 1.0
        self.current_strategy = RetryStrategy.EXPONENTIAL_BACKOFF


def retry(
    name: str,
    config: RetryConfig | None = None,
    condition: RetryCondition = RetryCondition.ON_EXCEPTION,
):
    """
    Decorator for applying intelligent retry to functions.

    Usage:
        @retry("my_service")
        async def my_function():
            # Function implementation
            pass
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        retry_system = IntelligentRetry(name, config)

        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await retry_system.execute(func, *args, **kwargs)

        return wrapper

    return decorator


class RetryManager:
    """Manager for multiple retry systems."""

    def __init__(self):
        self._retry_systems: dict[str, IntelligentRetry] = {}

    def create_retry_system(self, name: str, config: RetryConfig | None = None) -> IntelligentRetry:
        """Create a new retry system."""
        if name in self._retry_systems:
            raise ValueError(f"Retry system '{name}' already exists")

        retry_system = IntelligentRetry(name, config)
        self._retry_systems[name] = retry_system
        return retry_system

    def get_retry_system(self, name: str) -> IntelligentRetry | None:
        """Get an existing retry system."""
        return self._retry_systems.get(name)

    def get_all_retry_systems(self) -> dict[str, IntelligentRetry]:
        """Get all retry systems."""
        return self._retry_systems.copy()

    def get_global_metrics(self) -> dict[str, Any]:
        """Get aggregated metrics from all retry systems."""
        total_attempts = sum(system.metrics.total_attempts for system in self._retry_systems.values())
        total_successes = sum(system.metrics.successful_attempts for system in self._retry_systems.values())
        total_failures = sum(system.metrics.failed_attempts for system in self._retry_systems.values())
        total_time = sum(system.metrics.total_retry_time for system in self._retry_systems.values())

        return {
            "total_retry_systems": len(self._retry_systems),
            "total_attempts": total_attempts,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "total_retry_time": total_time,
            "overall_success_rate": total_successes / max(1, total_attempts),
            "average_attempts_per_operation": total_attempts / max(1, total_successes + total_failures),
            "systems": {
                name: {
                    "success_rate": system.metrics.success_rate,
                    "total_attempts": system.metrics.total_attempts,
                    "average_attempts": system.metrics.average_attempts_per_operation,
                    "current_strategy": system.current_strategy.value,
                }
                for name, system in self._retry_systems.items()
            },
        }


# Global retry manager
_global_retry_manager = RetryManager()


def get_retry_manager() -> RetryManager:
    """Get the global retry manager."""
    return _global_retry_manager


def create_retry_system(name: str, config: RetryConfig | None = None) -> IntelligentRetry:
    """Create a new retry system using the global manager."""
    return _global_retry_manager.create_retry_system(name, config)
