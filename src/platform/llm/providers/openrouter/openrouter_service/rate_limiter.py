"""Per-tenant rate limiting for OpenRouter service.

This module provides rate limiting capabilities to control request
frequency per tenant and prevent abuse.
"""
from __future__ import annotations
import logging
import time
from collections import deque
from dataclasses import dataclass
from platform.core.step_result import StepResult
from typing import TYPE_CHECKING, Any
from app.config.feature_flags import FeatureFlags
if TYPE_CHECKING:
    from .service import OpenRouterService
log = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    window_size_seconds: int = 60
    enable_rate_limiting: bool = True

class TokenBucket:
    """Token bucket implementation for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float, initial_tokens: int | None=None) -> None:
        """Initialize token bucket.

        Args:
            capacity: Maximum number of tokens in the bucket
            refill_rate: Tokens added per second
            initial_tokens: Initial number of tokens (defaults to capacity)
        """
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._tokens = initial_tokens if initial_tokens is not None else capacity
        self._last_refill = time.time()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_refill
        if elapsed > 0:
            tokens_to_add = elapsed * self._refill_rate
            self._tokens = min(self._capacity, self._tokens + tokens_to_add)
            self._last_refill = now

    def consume(self, tokens: int=1) -> bool:
        """Try to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        self._refill()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

    def get_tokens(self) -> float:
        """Get current number of tokens in the bucket.

        Returns:
            Current token count
        """
        self._refill()
        return self._tokens

    def get_capacity(self) -> int:
        """Get bucket capacity.

        Returns:
            Bucket capacity
        """
        return self._capacity

class SlidingWindowRateLimiter:
    """Sliding window rate limiter implementation."""

    def __init__(self, window_size_seconds: int=60) -> None:
        """Initialize sliding window rate limiter.

        Args:
            window_size_seconds: Size of the sliding window in seconds
        """
        self._window_size = window_size_seconds
        self._requests: deque[float] = deque()

    def _cleanup_old_requests(self, now: float) -> None:
        """Remove requests outside the sliding window.

        Args:
            now: Current timestamp
        """
        cutoff = now - self._window_size
        while self._requests and self._requests[0] < cutoff:
            self._requests.popleft()

    def is_allowed(self, limit: int, now: float | None=None) -> bool:
        """Check if request is allowed within the rate limit.

        Args:
            limit: Maximum number of requests in the window
            now: Current timestamp (defaults to current time)

        Returns:
            True if request is allowed, False otherwise
        """
        if now is None:
            now = time.time()
        self._cleanup_old_requests(now)
        if len(self._requests) < limit:
            self._requests.append(now)
            return True
        return False

    def get_current_count(self, now: float | None=None) -> int:
        """Get current number of requests in the window.

        Args:
            now: Current timestamp (defaults to current time)

        Returns:
            Number of requests in the current window
        """
        if now is None:
            now = time.time()
        self._cleanup_old_requests(now)
        return len(self._requests)

class TenantRateLimiter:
    """Rate limiter for individual tenants."""

    def __init__(self, config: RateLimitConfig) -> None:
        """Initialize tenant rate limiter.

        Args:
            config: Rate limiting configuration
        """
        self._config = config
        self._minute_bucket = TokenBucket(capacity=config.requests_per_minute, refill_rate=config.requests_per_minute / 60.0)
        self._hour_bucket = TokenBucket(capacity=config.requests_per_hour, refill_rate=config.requests_per_hour / 3600.0)
        self._day_bucket = TokenBucket(capacity=config.requests_per_day, refill_rate=config.requests_per_day / 86400.0)
        self._burst_limiter = SlidingWindowRateLimiter(window_size_seconds=10)
        self._stats = {'total_requests': 0, 'allowed_requests': 0, 'rate_limited_requests': 0, 'burst_limited_requests': 0}

    def is_allowed(self) -> bool:
        """Check if request is allowed for this tenant.

        Returns:
            True if request is allowed, False if rate limited
        """
        if not self._config.enable_rate_limiting:
            return True
        self._stats['total_requests'] += 1
        if not self._burst_limiter.is_allowed(self._config.burst_limit):
            self._stats['burst_limited_requests'] += 1
            return False
        if not self._minute_bucket.consume():
            self._stats['rate_limited_requests'] += 1
            return False
        if not self._hour_bucket.consume():
            self._stats['rate_limited_requests'] += 1
            return False
        if not self._day_bucket.consume():
            self._stats['rate_limited_requests'] += 1
            return False
        self._stats['allowed_requests'] += 1
        return True

    def get_status(self) -> dict[str, Any]:
        """Get current rate limiter status.

        Returns:
            Dictionary with rate limiter status
        """
        return {'tokens_available': {'minute': self._minute_bucket.get_tokens(), 'hour': self._hour_bucket.get_tokens(), 'day': self._day_bucket.get_tokens()}, 'bucket_capacity': {'minute': self._minute_bucket.get_capacity(), 'hour': self._hour_bucket.get_capacity(), 'day': self._day_bucket.get_capacity()}, 'burst_window_requests': self._burst_limiter.get_current_count(), 'burst_limit': self._config.burst_limit, 'stats': self._stats.copy()}

    def reset_stats(self) -> None:
        """Reset rate limiter statistics."""
        self._stats = {'total_requests': 0, 'allowed_requests': 0, 'rate_limited_requests': 0, 'burst_limited_requests': 0}

class RateLimitManager:
    """Manages rate limiting for multiple tenants."""

    def __init__(self) -> None:
        """Initialize rate limit manager."""
        self._tenant_limiters: dict[str, TenantRateLimiter] = {}
        self._default_config = RateLimitConfig()
        self._feature_flags = FeatureFlags()

    def get_tenant_limiter(self, tenant: str, config: RateLimitConfig | None=None) -> TenantRateLimiter:
        """Get or create rate limiter for a tenant.

        Args:
            tenant: Tenant identifier
            config: Rate limiting configuration (uses default if None)

        Returns:
            TenantRateLimiter instance
        """
        if tenant not in self._tenant_limiters:
            limiter_config = config or self._default_config
            self._tenant_limiters[tenant] = TenantRateLimiter(limiter_config)
            log.debug('Created rate limiter for tenant: %s', tenant)
        return self._tenant_limiters[tenant]

    def is_request_allowed(self, tenant: str, config: RateLimitConfig | None=None) -> bool:
        """Check if request is allowed for a tenant.

        Args:
            tenant: Tenant identifier
            config: Rate limiting configuration (uses default if None)

        Returns:
            True if request is allowed, False if rate limited
        """
        if not self._feature_flags.ENABLE_RATE_LIMITING:
            return True
        limiter = self.get_tenant_limiter(tenant, config)
        return limiter.is_allowed()

    def get_tenant_status(self, tenant: str) -> dict[str, Any]:
        """Get rate limiting status for a tenant.

        Args:
            tenant: Tenant identifier

        Returns:
            Dictionary with tenant rate limiting status
        """
        if tenant not in self._tenant_limiters:
            return {'tenant': tenant, 'limiter_exists': False, 'message': 'No rate limiter found for tenant'}
        limiter = self._tenant_limiters[tenant]
        status = limiter.get_status()
        status['tenant'] = tenant
        status['limiter_exists'] = True
        return status

    def get_all_tenant_status(self) -> dict[str, dict[str, Any]]:
        """Get rate limiting status for all tenants.

        Returns:
            Dictionary mapping tenant names to their status
        """
        return {tenant: self.get_tenant_status(tenant) for tenant in self._tenant_limiters}

    def reset_tenant_stats(self, tenant: str) -> None:
        """Reset statistics for a specific tenant.

        Args:
            tenant: Tenant identifier
        """
        if tenant in self._tenant_limiters:
            self._tenant_limiters[tenant].reset_stats()
            log.debug('Reset rate limiter stats for tenant: %s', tenant)

    def reset_all_stats(self) -> None:
        """Reset statistics for all tenants."""
        for limiter in self._tenant_limiters.values():
            limiter.reset_stats()
        log.info('Reset rate limiter stats for all tenants')

    def remove_tenant(self, tenant: str) -> bool:
        """Remove rate limiter for a tenant.

        Args:
            tenant: Tenant identifier

        Returns:
            True if tenant was removed, False if not found
        """
        if tenant in self._tenant_limiters:
            del self._tenant_limiters[tenant]
            log.debug('Removed rate limiter for tenant: %s', tenant)
            return True
        return False

class OpenRouterRateLimiter:
    """Rate limiter wrapper for OpenRouter service operations."""

    def __init__(self, service: OpenRouterService) -> None:
        """Initialize OpenRouter rate limiter.

        Args:
            service: The OpenRouter service instance
        """
        self._service = service
        self._rate_limit_manager = RateLimitManager()
        self._feature_flags = FeatureFlags()

    def route_with_rate_limit(self, prompt: str, task_type: str='general', model: str | None=None, provider_opts: dict[str, Any] | None=None, tenant: str='default', **kwargs: Any) -> StepResult:
        """Route a prompt with rate limiting.

        Args:
            prompt: The prompt to route
            task_type: Type of task
            model: Specific model to use
            provider_opts: Provider-specific options
            tenant: Tenant identifier for rate limiting
            **kwargs: Additional routing options

        Returns:
            StepResult with routing response or error
        """
        if not self._rate_limit_manager.is_request_allowed(tenant):
            log.warning('Rate limit exceeded for tenant: %s', tenant)
            return StepResult.fail('Rate limit exceeded. Please try again later.', status='rate_limited')
        return self._service.route(prompt, task_type, model, provider_opts, **kwargs)

    async def route_async_with_rate_limit(self, prompt: str, task_type: str='general', model: str | None=None, provider_opts: dict[str, Any] | None=None, tenant: str='default', **kwargs: Any) -> dict[str, Any]:
        """Route a prompt asynchronously with rate limiting.

        Args:
            prompt: The prompt to route
            task_type: Type of task
            model: Specific model to use
            provider_opts: Provider-specific options
            tenant: Tenant identifier for rate limiting
            **kwargs: Additional routing options

        Returns:
            Response dictionary
        """
        if not self._rate_limit_manager.is_request_allowed(tenant):
            log.warning('Rate limit exceeded for tenant: %s', tenant)
            return {'status': 'error', 'error': 'Rate limit exceeded. Please try again later.', 'model': model or 'unknown', 'tokens': 0, 'provider': provider_opts or {}, 'rate_limited': True}
        result = self._service.route(prompt, task_type, model, provider_opts, **kwargs)
        return result.data if result.success else {'status': 'error', 'error': result.error}

    def get_tenant_rate_limit_status(self, tenant: str) -> dict[str, Any]:
        """Get rate limiting status for a tenant.

        Args:
            tenant: Tenant identifier

        Returns:
            Dictionary with tenant rate limiting status
        """
        return self._rate_limit_manager.get_tenant_status(tenant)

    def get_all_rate_limit_status(self) -> dict[str, dict[str, Any]]:
        """Get rate limiting status for all tenants.

        Returns:
            Dictionary with all tenant rate limiting status
        """
        return self._rate_limit_manager.get_all_tenant_status()

    def configure_tenant_rate_limit(self, tenant: str, config: RateLimitConfig) -> None:
        """Configure rate limiting for a specific tenant.

        Args:
            tenant: Tenant identifier
            config: Rate limiting configuration
        """
        self._rate_limit_manager.get_tenant_limiter(tenant, config)
        log.info('Configured rate limiting for tenant: %s', tenant)

    def get_stats(self) -> dict[str, Any]:
        """Get rate limiter statistics.

        Returns:
            Dictionary with rate limiter statistics
        """
        return {'rate_limiting_enabled': self._feature_flags.ENABLE_RATE_LIMITING, 'tenant_count': len(self._rate_limit_manager._tenant_limiters), 'tenant_status': self._rate_limit_manager.get_all_tenant_status()}

    def reset_stats(self) -> None:
        """Reset rate limiter statistics."""
        self._rate_limit_manager.reset_all_stats()
_rate_limit_manager: RateLimitManager | None = None

def get_rate_limit_manager() -> RateLimitManager:
    """Get or create global rate limit manager.

    Returns:
        RateLimitManager instance
    """
    global _rate_limit_manager
    if _rate_limit_manager is None:
        _rate_limit_manager = RateLimitManager()
    return _rate_limit_manager

def get_openrouter_rate_limiter(service: OpenRouterService) -> OpenRouterRateLimiter:
    """Get or create OpenRouter rate limiter for the service.

    Args:
        service: The OpenRouter service instance

    Returns:
        OpenRouterRateLimiter instance
    """
    return OpenRouterRateLimiter(service)