"""Distributed rate limiting implementation with Redis backend.

This module provides distributed rate limiting capabilities for multi-replica
deployments, ensuring consistent global limit enforcement across all instances.
"""
from __future__ import annotations
import logging
import time
from typing import Any
import redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError
from platform.core.step_result import StepResult
logger = logging.getLogger(__name__)

class DistributedRateLimiter:
    """Redis-backed distributed rate limiter with graceful fallback."""

    def __init__(self, redis_url: str | None=None, capacity: int=60, refill_rate: float=1.0, fallback_enabled: bool=True):
        """Initialize distributed rate limiter.

        Args:
            redis_url: Redis connection URL
            capacity: Maximum tokens per bucket
            refill_rate: Tokens refilled per second
            fallback_enabled: Enable local fallback when Redis unavailable
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.fallback_enabled = fallback_enabled
        if redis_url:
            try:
                self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
                self.redis.ping()
                self.redis_available = True
                logger.info('Distributed rate limiter connected to Redis')
            except (RedisConnectionError, RedisError) as e:
                logger.warning(f'Redis connection failed, using fallback: {e}')
                self.redis_available = False
                self.redis = None
        else:
            self.redis_available = False
            self.redis = None
        self.lua_script = "\n        local key = KEYS[1]\n        local capacity = tonumber(ARGV[1])\n        local refill_rate = tonumber(ARGV[2])\n        local tokens_requested = tonumber(ARGV[3])\n        local now = tonumber(ARGV[4])\n        local ttl = tonumber(ARGV[5])\n\n        local current = redis.call('HMGET', key, 'tokens', 'last_refill')\n        local tokens = tonumber(current[1]) or capacity\n        local last_refill = tonumber(current[2]) or now\n\n        -- Refill tokens based on time elapsed\n        local time_elapsed = now - last_refill\n        local new_tokens = math.min(capacity, tokens + (time_elapsed * refill_rate))\n\n        if new_tokens >= tokens_requested then\n            new_tokens = new_tokens - tokens_requested\n            redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)\n            redis.call('EXPIRE', key, ttl)\n            return {1, new_tokens}  -- allowed, remaining tokens\n        else\n            redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)\n            redis.call('EXPIRE', key, ttl)\n            return {0, new_tokens}  -- denied, remaining tokens\n        end\n        "
        self.local_buckets: dict[str, dict[str, Any]] = {}
        self.metrics = {'redis_operations': 0, 'fallback_operations': 0, 'redis_errors': 0, 'requests_allowed': 0, 'requests_denied': 0}

    def allow(self, key: str, tokens: int=1, ttl: int=3600) -> tuple[bool, int, dict[str, Any]]:
        """Check if request is allowed and consume tokens.

        Args:
            key: Unique identifier for the rate limit bucket
            tokens: Number of tokens to consume
            ttl: Time-to-live for Redis key in seconds

        Returns:
            Tuple of (allowed, remaining_tokens, metadata)
        """
        try:
            if self.redis_available and self.redis:
                return self._redis_allow(key, tokens, ttl)
            elif self.fallback_enabled:
                return self._fallback_allow(key, tokens)
            else:
                return (False, 0, {'method': 'denied_no_backend', 'error': 'No rate limiting backend available'})
        except Exception as e:
            logger.error(f'Rate limiting error for key {key}: {e}')
            self.metrics['redis_errors'] += 1
            if self.fallback_enabled:
                logger.warning('Falling back to local rate limiting due to Redis error')
                return self._fallback_allow(key, tokens)
            else:
                return (False, 0, {'method': 'error', 'error': str(e)})

    def _redis_allow(self, key: str, tokens: int, ttl: int) -> tuple[bool, int, dict[str, Any]]:
        """Handle rate limiting via Redis."""
        try:
            self.metrics['redis_operations'] += 1
            result = self.redis.eval(self.lua_script, keys=[f'rl:{key}'], args=[self.capacity, self.refill_rate, tokens, int(time.time()), ttl])
            allowed = bool(result[0])
            remaining = int(result[1])
            if allowed:
                self.metrics['requests_allowed'] += 1
            else:
                self.metrics['requests_denied'] += 1
            return (allowed, remaining, {'method': 'redis', 'backend': 'distributed', 'capacity': self.capacity, 'refill_rate': self.refill_rate})
        except (ConnectionError, RedisError) as e:
            logger.warning(f'Redis operation failed: {e}')
            self.metrics['redis_errors'] += 1
            self.redis_available = False
            if self.fallback_enabled:
                return self._fallback_allow(key, tokens)
            else:
                raise

    def _fallback_allow(self, key: str, tokens: int) -> tuple[bool, int, dict[str, Any]]:
        """Handle rate limiting via local fallback."""
        self.metrics['fallback_operations'] += 1
        now = time.time()
        if key not in self.local_buckets:
            self.local_buckets[key] = {'tokens': self.capacity, 'last_refill': now}
        bucket = self.local_buckets[key]
        time_elapsed = now - bucket['last_refill']
        new_tokens = min(self.capacity, bucket['tokens'] + time_elapsed * self.refill_rate)
        if new_tokens >= tokens:
            bucket['tokens'] = new_tokens - tokens
            bucket['last_refill'] = now
            self.metrics['requests_allowed'] += 1
            return (True, bucket['tokens'], {'method': 'fallback', 'backend': 'local', 'capacity': self.capacity, 'refill_rate': self.refill_rate})
        else:
            bucket['tokens'] = new_tokens
            bucket['last_refill'] = now
            self.metrics['requests_denied'] += 1
            return (False, bucket['tokens'], {'method': 'fallback', 'backend': 'local', 'capacity': self.capacity, 'refill_rate': self.refill_rate})

    def get_metrics(self) -> dict[str, Any]:
        """Get rate limiter metrics."""
        return {**self.metrics, 'redis_available': self.redis_available, 'fallback_enabled': self.fallback_enabled, 'local_buckets_count': len(self.local_buckets), 'capacity': self.capacity, 'refill_rate': self.refill_rate}

    def reset_bucket(self, key: str) -> StepResult:
        """Reset a specific rate limit bucket."""
        try:
            if self.redis_available and self.redis:
                redis_key = f'rl:{key}'
                self.redis.delete(redis_key)
            if key in self.local_buckets:
                del self.local_buckets[key]
            return StepResult.ok(data={'bucket_reset': key})
        except Exception as e:
            logger.error(f'Failed to reset bucket {key}: {e}')
            return StepResult.fail(f'Failed to reset bucket: {e!s}')

    def health_check(self) -> StepResult:
        """Perform health check on rate limiter."""
        try:
            health_data = {'distributed_rate_limiter_healthy': True, 'redis_available': self.redis_available, 'fallback_enabled': self.fallback_enabled, 'metrics': self.get_metrics()}
            if self.redis_available and self.redis:
                try:
                    self.redis.ping()
                    health_data['redis_connection'] = 'healthy'
                except Exception as e:
                    health_data['redis_connection'] = f'unhealthy: {e}'
                    health_data['distributed_rate_limiter_healthy'] = False
            return StepResult.ok(data=health_data)
        except Exception as e:
            logger.error(f'Rate limiter health check failed: {e}')
            return StepResult.fail(f'Health check failed: {e!s}')

    def reconnect_redis(self, redis_url: str) -> StepResult:
        """Attempt to reconnect to Redis."""
        try:
            new_redis = redis.Redis.from_url(redis_url, decode_responses=True)
            new_redis.ping()
            self.redis = new_redis
            self.redis_available = True
            logger.info('Successfully reconnected to Redis')
            return StepResult.ok(data={'redis_reconnected': True})
        except Exception as e:
            logger.error(f'Failed to reconnect to Redis: {e}')
            return StepResult.fail(f'Redis reconnection failed: {e!s}')
_rate_limiter: DistributedRateLimiter | None = None

def get_distributed_rate_limiter() -> DistributedRateLimiter:
    """Get the global distributed rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        import os
        redis_url = os.getenv('RATE_LIMIT_REDIS_URL')
        capacity = int(os.getenv('RATE_LIMIT_GLOBAL_CAPACITY', '60'))
        refill_rate = float(os.getenv('RATE_LIMIT_GLOBAL_REFILL_PER_SEC', '1.0'))
        _rate_limiter = DistributedRateLimiter(redis_url=redis_url, capacity=capacity, refill_rate=refill_rate)
    return _rate_limiter

def rate_limit_middleware(key_func: callable | None=None):
    """Decorator for adding rate limiting to functions."""

    def decorator(func):

        def wrapper(*args, **kwargs):
            rate_limiter = get_distributed_rate_limiter()
            key = key_func(*args, **kwargs) if key_func else f'{func.__name__}:{hash(str(args) + str(kwargs))}'
            allowed, remaining, _metadata = rate_limiter.allow(key)
            if not allowed:
                raise Exception(f'Rate limit exceeded for key: {key}')
            result = func(*args, **kwargs)
            if hasattr(result, 'headers'):
                result.headers['X-RateLimit-Remaining'] = str(remaining)
                result.headers['X-RateLimit-Limit'] = str(rate_limiter.capacity)
            return result
        return wrapper
    return decorator