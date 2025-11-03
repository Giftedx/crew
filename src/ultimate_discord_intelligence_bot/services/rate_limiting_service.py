"""Rate limiting service for the Ultimate Discord Intelligence Bot."""

from __future__ import annotations

import logging
from platform.core.step_result import StepResult

from app.config.settings import (
    ENABLE_DISTRIBUTED_RATE_LIMITING,
    RATE_LIMIT_FALLBACK_TO_LOCAL,
    RATE_LIMIT_GLOBAL_CAPACITY,
    RATE_LIMIT_GLOBAL_REFILL_PER_SEC,
    RATE_LIMIT_REDIS_URL,
)


logger = logging.getLogger(__name__)
try:
    from platform.security.rate_limiting import DistributedRateLimiter

    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    logger.warning("Rate limiting components not available")


class RateLimitingService:
    """Service for managing rate limiting across the application."""

    def __init__(self):
        """Initialize rate limiting service."""
        self.distributed_limiter: DistributedRateLimiter | None = None
        self.enabled = False
        if RATE_LIMITING_AVAILABLE and ENABLE_DISTRIBUTED_RATE_LIMITING:
            self._initialize_distributed_limiter()

    def _initialize_distributed_limiter(self) -> None:
        """Initialize distributed rate limiter if configured."""
        if not RATE_LIMIT_REDIS_URL:
            logger.warning("Distributed rate limiting enabled but no Redis URL provided")
            return
        try:
            self.distributed_limiter = DistributedRateLimiter(
                redis_url=RATE_LIMIT_REDIS_URL,
                default_capacity=RATE_LIMIT_GLOBAL_CAPACITY,
                default_refill_per_sec=RATE_LIMIT_GLOBAL_REFILL_PER_SEC,
                fallback_to_local=RATE_LIMIT_FALLBACK_TO_LOCAL,
            )
            self.enabled = True
            logger.info("Distributed rate limiting service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize distributed rate limiter: {e}")
            self.distributed_limiter = None

    def is_allowed(
        self, key: str, cost: int = 1, capacity: int | None = None, refill_per_sec: float | None = None
    ) -> StepResult:
        """Check if request is allowed and consume tokens if so.

        Args:
            key: Unique identifier for the rate limit bucket
            cost: Number of tokens to consume (default: 1)
            capacity: Bucket capacity (uses default if None)
            refill_per_sec: Refill rate (uses default if None)

        Returns:
            StepResult with success/failure and remaining tokens
        """
        if not self.enabled or not self.distributed_limiter:
            return StepResult.ok(data={"allowed": True, "remaining": capacity or RATE_LIMIT_GLOBAL_CAPACITY})
        return self.distributed_limiter.is_allowed(key, cost, capacity, refill_per_sec)

    def get_remaining_tokens(self, key: str) -> int:
        """Get remaining tokens for a key without consuming."""
        if not self.enabled or not self.distributed_limiter:
            return RATE_LIMIT_GLOBAL_CAPACITY
        return self.distributed_limiter.get_remaining_tokens(key)

    def reset_bucket(self, key: str) -> bool:
        """Reset a rate limit bucket (for testing)."""
        if not self.enabled or not self.distributed_limiter:
            return False
        return self.distributed_limiter.reset_bucket(key)

    def health_check(self) -> StepResult:
        """Check if the rate limiting service is healthy."""
        if not self.enabled:
            return StepResult.ok(data={"status": "disabled"})
        if not self.distributed_limiter:
            return StepResult.fail("Rate limiter not initialized")
        return self.distributed_limiter.health_check()

    def get_stats(self) -> dict:
        """Get rate limiting service statistics."""
        if not self.enabled or not self.distributed_limiter:
            return {"status": "disabled"}
        return {"status": "enabled", "backend": "redis"}


_rate_limiting_service: RateLimitingService | None = None


def get_rate_limiting_service() -> RateLimitingService:
    """Get the global rate limiting service instance."""
    global _rate_limiting_service
    if _rate_limiting_service is None:
        _rate_limiting_service = RateLimitingService()
    return _rate_limiting_service


def check_rate_limit(
    key: str, cost: int = 1, capacity: int | None = None, refill_per_sec: float | None = None
) -> StepResult:
    """Convenience function to check rate limit.

    Args:
        key: Unique identifier for the rate limit bucket
        cost: Number of tokens to consume (default: 1)
        capacity: Bucket capacity (uses default if None)
        refill_per_sec: Refill rate (uses default if None)

    Returns:
        StepResult with success/failure and remaining tokens
    """
    service = get_rate_limiting_service()
    return service.is_allowed(key, cost, capacity, refill_per_sec)
