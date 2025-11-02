"""
Rate limiter implementation for API call throttling.
Provides token bucket and sliding window rate limiting.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)

T = TypeVar("T")


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class TokenBucket:
    """
    Token bucket rate limiter implementation.

    Allows bursts up to bucket capacity while maintaining average rate.
    """

    def __init__(self, capacity: int, refill_rate: float, name: str = "token_bucket"):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum number of tokens in bucket
            refill_rate: Tokens added per second
            name: Name for logging
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.name = name

        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from bucket.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False if rate limited
        """
        async with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                logger.debug(f"Token bucket {self.name}: acquired {tokens} tokens, {self.tokens} remaining")
                return True
            else:
                logger.debug(
                    f"Token bucket {self.name}: rate limited, {tokens} tokens requested, {self.tokens} available"
                )
                return False

    async def wait_for_tokens(self, tokens: int = 1, timeout: float | None = None) -> bool:
        """
        Wait for tokens to become available.

        Args:
            tokens: Number of tokens needed
            timeout: Maximum time to wait in seconds

        Returns:
            True if tokens acquired, False if timeout
        """
        start_time = time.time()

        while True:
            if await self.acquire(tokens):
                return True

            if timeout and (time.time() - start_time) >= timeout:
                return False

            # Wait before retry
            await asyncio.sleep(0.1)

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.last_refill = now

        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)

    def get_status(self) -> dict[str, Any]:
        """Get current bucket status."""
        self._refill()
        return {
            "name": self.name,
            "tokens": self.tokens,
            "capacity": self.capacity,
            "refill_rate": self.refill_rate,
            "utilization": (self.capacity - self.tokens) / self.capacity,
        }


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter implementation.

    Tracks requests within a sliding time window.
    """

    def __init__(self, max_requests: int, window_seconds: float, name: str = "sliding_window"):
        """
        Initialize sliding window rate limiter.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Window size in seconds
            name: Name for logging
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.name = name

        self.requests: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """
        Try to acquire permission for a request.

        Returns:
            True if request allowed, False if rate limited
        """
        async with self._lock:
            now = time.time()
            window_start = now - self.window_seconds

            # Remove old requests outside window
            self.requests = [req_time for req_time in self.requests if req_time > window_start]

            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                logger.debug(
                    f"Sliding window {self.name}: request allowed, {len(self.requests)}/{self.max_requests} in window"
                )
                return True
            else:
                logger.debug(
                    f"Sliding window {self.name}: rate limited, {len(self.requests)}/{self.max_requests} in window"
                )
                return False

    async def wait_for_permission(self, timeout: float | None = None) -> bool:
        """
        Wait for permission to make a request.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if permission granted, False if timeout
        """
        start_time = time.time()

        while True:
            if await self.acquire():
                return True

            if timeout and (time.time() - start_time) >= timeout:
                return False

            # Wait before retry
            await asyncio.sleep(0.1)

    def get_status(self) -> dict[str, Any]:
        """Get current rate limiter status."""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean up old requests
        self.requests = [req_time for req_time in self.requests if req_time > window_start]

        return {
            "name": self.name,
            "requests_in_window": len(self.requests),
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "utilization": len(self.requests) / self.max_requests,
        }


class RateLimiter:
    """
    Combined rate limiter supporting multiple strategies.

    Can use token bucket, sliding window, or both together.
    """

    def __init__(
        self,
        token_bucket: TokenBucket | None = None,
        sliding_window: SlidingWindowRateLimiter | None = None,
        name: str = "rate_limiter",
    ):
        """
        Initialize rate limiter.

        Args:
            token_bucket: Token bucket limiter
            sliding_window: Sliding window limiter
            name: Name for logging
        """
        self.token_bucket = token_bucket
        self.sliding_window = sliding_window
        self.name = name

    async def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire permission for request(s).

        Args:
            tokens: Number of tokens for token bucket

        Returns:
            True if permission granted, False if rate limited
        """
        # Check token bucket if available
        if self.token_bucket and not await self.token_bucket.acquire(tokens):
            return False

        # Check sliding window if available
        return not (self.sliding_window and not await self.sliding_window.acquire())

    async def wait_for_permission(self, tokens: int = 1, timeout: float | None = None) -> bool:
        """
        Wait for permission to make request(s).

        Args:
            tokens: Number of tokens for token bucket
            timeout: Maximum time to wait in seconds

        Returns:
            True if permission granted, False if timeout
        """
        start_time = time.time()

        while True:
            if await self.acquire(tokens):
                return True

            if timeout and (time.time() - start_time) >= timeout:
                return False

            # Wait before retry
            await asyncio.sleep(0.1)

    def get_status(self) -> dict[str, Any]:
        """Get current rate limiter status."""
        status = {"name": self.name}

        if self.token_bucket:
            status["token_bucket"] = self.token_bucket.get_status()

        if self.sliding_window:
            status["sliding_window"] = self.sliding_window.get_status()

        return status


class RateLimiterManager:
    """Manages multiple rate limiters for different services."""

    def __init__(self):
        self.limiters: dict[str, RateLimiter] = {}

    def get_limiter(
        self,
        name: str,
        token_bucket: TokenBucket | None = None,
        sliding_window: SlidingWindowRateLimiter | None = None,
    ) -> RateLimiter:
        """
        Get or create a rate limiter.

        Args:
            name: Rate limiter name
            token_bucket: Token bucket configuration
            sliding_window: Sliding window configuration

        Returns:
            Rate limiter instance
        """
        if name not in self.limiters:
            self.limiters[name] = RateLimiter(
                token_bucket=token_bucket,
                sliding_window=sliding_window,
                name=name,
            )

        return self.limiters[name]

    def get_all_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all rate limiters."""
        return {name: limiter.get_status() for name, limiter in self.limiters.items()}


# Global rate limiter manager
rate_limiter_manager = RateLimiterManager()


def with_rate_limit(
    limiter_name: str,
    tokens: int = 1,
    timeout: float | None = None,
    manager: RateLimiterManager | None = None,
):
    """
    Decorator to add rate limiting to functions.

    Args:
        limiter_name: Name of rate limiter to use
        tokens: Number of tokens to acquire
        timeout: Maximum time to wait for permission
        manager: Rate limiter manager to use (default: global)
    """
    if manager is None:
        manager = rate_limiter_manager

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        async def async_wrapper(*args, **kwargs) -> T:
            limiter = manager.get_limiter(limiter_name)

            if not await limiter.wait_for_permission(tokens, timeout):
                raise RateLimitExceededError(f"Rate limit exceeded for {limiter_name}")

            return await func(*args, **kwargs)

        def sync_wrapper(*args, **kwargs) -> T:
            limiter = manager.get_limiter(limiter_name)

            if not asyncio.run(limiter.wait_for_permission(tokens, timeout)):
                raise RateLimitExceededError(f"Rate limit exceeded for {limiter_name}")

            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def with_result_rate_limit(
    limiter_name: str,
    tokens: int = 1,
    timeout: float | None = None,
    manager: RateLimiterManager | None = None,
):
    """
    Decorator to add rate limiting to StepResult functions.

    Args:
        limiter_name: Name of rate limiter to use
        tokens: Number of tokens to acquire
        timeout: Maximum time to wait for permission
        manager: Rate limiter manager to use (default: global)
    """
    if manager is None:
        manager = rate_limiter_manager

    def decorator(func: Callable[..., StepResult]) -> Callable[..., StepResult]:
        async def async_wrapper(*args, **kwargs) -> StepResult:
            limiter = manager.get_limiter(limiter_name)

            if not await limiter.wait_for_permission(tokens, timeout):
                return StepResult.fail(f"Rate limit exceeded for {limiter_name}")

            return await func(*args, **kwargs)

        def sync_wrapper(*args, **kwargs) -> StepResult:
            limiter = manager.get_limiter(limiter_name)

            if not asyncio.run(limiter.wait_for_permission(tokens, timeout)):
                return StepResult.fail(f"Rate limit exceeded for {limiter_name}")

            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
