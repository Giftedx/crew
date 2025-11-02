"""Distributed rate limiting implementation using Redis."""

from __future__ import annotations

import logging
import time
from platform.core.step_result import StepResult
from typing import Any

import redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)


class DistributedRateLimiter:
    """Redis-based distributed rate limiter with local fallback."""

    def __init__(
        self,
        redis_url: str,
        default_capacity: int = 60,
        default_refill_per_sec: float = 1.0,
        fallback_to_local: bool = True,
    ):
        """Initialize distributed rate limiter.

        Args:
            redis_url: Redis connection URL
            default_capacity: Default bucket capacity in tokens
            default_refill_per_sec: Default refill rate in tokens per second
            fallback_to_local: Whether to fallback to local limiting on Redis errors
        """
        self.redis_url = redis_url
        self.default_capacity = default_capacity
        self.default_refill_per_sec = default_refill_per_sec
        self.fallback_to_local = fallback_to_local
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            self.redis_available = True
            logger.info("Distributed rate limiter connected to Redis")
        except (RedisConnectionError, RedisError) as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.redis_client = None
            self.redis_available = False
        self.local_limiters: dict[str, dict[str, Any]] = {}
        self.lua_script = "\n        local key = KEYS[1]\n        local capacity = tonumber(ARGV[1])\n        local refill_rate = tonumber(ARGV[2])\n        local now = tonumber(ARGV[3])\n        local cost = tonumber(ARGV[4])\n\n        local current = redis.call('HMGET', key, 'tokens', 'last_refill')\n        local tokens = tonumber(current[1]) or capacity\n        local last_refill = tonumber(current[2]) or now\n\n        -- Calculate time elapsed and refill tokens\n        local elapsed = (now - last_refill) / 1000000  -- Convert microseconds to seconds\n        local new_tokens = math.min(capacity, tokens + (elapsed * refill_rate))\n\n        -- Check if we have enough tokens\n        if new_tokens >= cost then\n            -- Consume tokens and update\n            local remaining_tokens = new_tokens - cost\n            redis.call('HMSET', key, 'tokens', remaining_tokens, 'last_refill', now)\n            redis.call('EXPIRE', key, 3600)  -- Expire after 1 hour\n            return {1, remaining_tokens}  -- Success\n        else\n            -- Not enough tokens\n            redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)\n            redis.call('EXPIRE', key, 3600)\n            return {0, new_tokens}  -- Rejected\n        end\n        "

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
        capacity = capacity or self.default_capacity
        refill_per_sec = refill_per_sec or self.default_refill_per_sec
        if self.redis_available:
            try:
                return self._check_distributed(key, cost, capacity, refill_per_sec)
            except (ConnectionError, RedisError) as e:
                logger.warning(f"Redis error in rate limiting: {e}")
                self.redis_available = False
        if self.fallback_to_local:
            return self._check_local(key, cost, capacity, refill_per_sec)
        logger.warning("Rate limiting unavailable, allowing request")
        return StepResult.ok(data={"allowed": True, "remaining": capacity})

    def _check_distributed(self, key: str, cost: int, capacity: int, refill_per_sec: float) -> StepResult:
        """Check rate limit using Redis."""
        now_microseconds = int(time.time() * 1000000)
        try:
            result = self.redis_client.eval(
                self.lua_script, 1, f"rl:{key}", capacity, refill_per_sec, now_microseconds, cost
            )
            allowed = bool(result[0])
            remaining = int(result[1])
            if allowed:
                return StepResult.ok(data={"allowed": True, "remaining": remaining})
            else:
                return StepResult.fail("Rate limit exceeded", data={"allowed": False, "remaining": remaining})
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            raise

    def _check_local(self, key: str, cost: int, capacity: int, refill_per_sec: float) -> StepResult:
        """Check rate limit using local in-memory bucket."""
        now = time.time()
        if key not in self.local_limiters:
            self.local_limiters[key] = {"tokens": capacity, "last_refill": now}
        limiter = self.local_limiters[key]
        elapsed = now - limiter["last_refill"]
        refill_tokens = elapsed * refill_per_sec
        new_tokens = min(capacity, limiter["tokens"] + refill_tokens)
        if new_tokens >= cost:
            remaining = new_tokens - cost
            limiter["tokens"] = remaining
            limiter["last_refill"] = now
            return StepResult.ok(data={"allowed": True, "remaining": remaining})
        else:
            limiter["tokens"] = new_tokens
            limiter["last_refill"] = now
            return StepResult.fail("Rate limit exceeded", data={"allowed": False, "remaining": new_tokens})

    def get_remaining_tokens(self, key: str) -> int:
        """Get remaining tokens for a key without consuming."""
        if self.redis_available:
            try:
                current = self.redis_client.hmget(f"rl:{key}", "tokens")
                if current[0] is not None:
                    return int(current[0])
            except Exception:
                pass
        if key in self.local_limiters:
            return int(self.local_limiters[key]["tokens"])
        return self.default_capacity

    def reset_bucket(self, key: str) -> bool:
        """Reset a rate limit bucket (for testing)."""
        if self.redis_available:
            try:
                self.redis_client.delete(f"rl:{key}")
                return True
            except Exception:
                return False
        if key in self.local_limiters:
            del self.local_limiters[key]
            return True
        return False

    def health_check(self) -> StepResult:
        """Check if the rate limiter is healthy."""
        if self.redis_available:
            try:
                self.redis_client.ping()
                return StepResult.ok(data={"status": "healthy", "backend": "redis"})
            except Exception as e:
                self.redis_available = False
                return StepResult.fail(f"Redis health check failed: {e}")
        return StepResult.ok(data={"status": "degraded", "backend": "local"})
