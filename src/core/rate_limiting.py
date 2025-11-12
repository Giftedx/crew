"""Compatibility shim for core.rate_limiting imports.

Re-exports from platform.security.rate_limiting for backward compatibility.
"""

from platform.security.rate_limiting.distributed_limiter import DistributedRateLimiter
from platform.security.rate_limiting.redis_backend import RedisBackend


__all__ = ["DistributedRateLimiter", "RedisBackend"]
