"""Redis backend for distributed rate limiting."""

from __future__ import annotations

import logging
from typing import Any

import redis
from redis.exceptions import ConnectionError, RedisError


logger = logging.getLogger(__name__)


class RedisBackend:
    """Redis backend for rate limiting operations."""

    def __init__(self, redis_url: str, key_prefix: str = "rl"):
        """Initialize Redis backend.

        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for rate limiting keys
        """
        self.redis_url = redis_url
        self.key_prefix = key_prefix

        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.client.ping()
            self.available = True
            logger.info("Redis backend connected successfully")
        except (ConnectionError, RedisError) as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.client = None
            self.available = False

    def get_tokens(self, key: str) -> int | None:
        """Get current token count for a key."""
        if not self.available:
            return None

        try:
            result = self.client.hget(f"{self.key_prefix}:{key}", "tokens")
            return int(result) if result is not None else None
        except Exception as e:
            logger.error(f"Error getting tokens for {key}: {e}")
            return None

    def set_tokens(self, key: str, tokens: int, ttl: int = 3600) -> bool:
        """Set token count for a key."""
        if not self.available:
            return False

        try:
            self.client.hset(f"{self.key_prefix}:{key}", "tokens", tokens)
            self.client.expire(f"{self.key_prefix}:{key}", ttl)
            return True
        except Exception as e:
            logger.error(f"Error setting tokens for {key}: {e}")
            return False

    def increment_tokens(self, key: str, amount: int) -> int | None:
        """Increment tokens for a key and return new count."""
        if not self.available:
            return None

        try:
            return self.client.hincrby(f"{self.key_prefix}:{key}", "tokens", amount)
        except Exception as e:
            logger.error(f"Error incrementing tokens for {key}: {e}")
            return None

    def decrement_tokens(self, key: str, amount: int) -> int | None:
        """Decrement tokens for a key and return new count."""
        if not self.available:
            return None

        try:
            return self.client.hincrby(f"{self.key_prefix}:{key}", "tokens", -amount)
        except Exception as e:
            logger.error(f"Error decrementing tokens for {key}: {e}")
            return None

    def set_last_refill(self, key: str, timestamp: float) -> bool:
        """Set last refill timestamp for a key."""
        if not self.available:
            return False

        try:
            self.client.hset(f"{self.key_prefix}:{key}", "last_refill", timestamp)
            return True
        except Exception as e:
            logger.error(f"Error setting last refill for {key}: {e}")
            return False

    def get_last_refill(self, key: str) -> float | None:
        """Get last refill timestamp for a key."""
        if not self.available:
            return None

        try:
            result = self.client.hget(f"{self.key_prefix}:{key}", "last_refill")
            return float(result) if result is not None else None
        except Exception as e:
            logger.error(f"Error getting last refill for {key}: {e}")
            return None

    def delete_key(self, key: str) -> bool:
        """Delete a rate limiting key."""
        if not self.available:
            return False

        try:
            return bool(self.client.delete(f"{self.key_prefix}:{key}"))
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False

    def get_all_keys(self, pattern: str = "*") -> list[str]:
        """Get all rate limiting keys matching pattern."""
        if not self.available:
            return []

        try:
            return self.client.keys(f"{self.key_prefix}:{pattern}")
        except Exception as e:
            logger.error(f"Error getting keys with pattern {pattern}: {e}")
            return []

    def get_key_info(self, key: str) -> dict[str, Any]:
        """Get complete information for a rate limiting key."""
        if not self.available:
            return {}

        try:
            result = self.client.hmget(f"{self.key_prefix}:{key}", "tokens", "last_refill")
            return {
                "tokens": int(result[0]) if result[0] is not None else None,
                "last_refill": float(result[1]) if result[1] is not None else None,
            }
        except Exception as e:
            logger.error(f"Error getting key info for {key}: {e}")
            return {}

    def health_check(self) -> bool:
        """Check if Redis backend is healthy."""
        if not self.available:
            return False

        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            self.available = False
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get Redis backend statistics."""
        if not self.available:
            return {"status": "unavailable"}

        try:
            info = self.client.info()
            return {
                "status": "available",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "keyspace": info.get("keyspace", {}),
            }
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {"status": "error", "error": str(e)}
