"""Redis state persistence backend for distributed cache storage."""

import json
from typing import Any

import structlog


logger = structlog.get_logger(__name__)


class RedisBackend:
    """Redis storage backend for workflow state.

    This backend stores state in Redis, providing distributed, in-memory
    storage with optional persistence. Suitable for multi-instance deployments
    and high-performance requirements.

    Note: Requires redis-py package. Install with: pip install redis

    Attributes:
        redis_client: Redis client instance
        key_prefix: Prefix for all keys (default: "workflow:")
        ttl: Optional time-to-live for keys in seconds
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "workflow:",
        ttl: int | None = None,
    ) -> None:
        """Initialize the Redis backend.

        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for all keys
            ttl: Optional time-to-live for keys in seconds
        """
        try:
            import redis
        except ImportError as e:
            raise ImportError("Redis support requires the 'redis' package. Install it with: pip install redis") from e

        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.key_prefix = key_prefix
        self.ttl = ttl

        # Test connection
        self.redis_client.ping()
        logger.info("redis_backend_initialized", url=redis_url, key_prefix=key_prefix, ttl=ttl)

    def _make_key(self, workflow_id: str) -> str:
        """Create Redis key from workflow ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Full Redis key
        """
        return f"{self.key_prefix}{workflow_id}"

    async def save(self, workflow_id: str, state: dict[str, Any]) -> None:
        """Save state to Redis.

        Args:
            workflow_id: Unique identifier for the workflow
            state: Serialized state dictionary
        """
        key = self._make_key(workflow_id)
        state_json = json.dumps(state)

        if self.ttl:
            self.redis_client.setex(key, self.ttl, state_json)
        else:
            self.redis_client.set(key, state_json)

        logger.info(
            "state_saved",
            workflow_id=workflow_id,
            backend="redis",
            size=len(state_json),
            ttl=self.ttl,
        )

    async def load(self, workflow_id: str) -> dict[str, Any] | None:
        """Load state from Redis.

        Args:
            workflow_id: Unique identifier for the workflow

        Returns:
            Serialized state dictionary or None if not found
        """
        key = self._make_key(workflow_id)
        state_json = self.redis_client.get(key)

        if state_json:
            state = json.loads(state_json)
            logger.info("state_loaded", workflow_id=workflow_id, backend="redis")
            return state
        else:
            logger.warning("state_not_found", workflow_id=workflow_id, backend="redis")
            return None

    async def delete(self, workflow_id: str) -> bool:
        """Delete state from Redis.

        Args:
            workflow_id: Unique identifier for the workflow

        Returns:
            True if deleted, False if not found
        """
        key = self._make_key(workflow_id)
        deleted = self.redis_client.delete(key) > 0

        if deleted:
            logger.info("state_deleted", workflow_id=workflow_id, backend="redis")
        else:
            logger.warning("state_not_found_for_delete", workflow_id=workflow_id, backend="redis")

        return deleted

    async def list_workflows(self) -> list[str]:
        """List all workflow IDs in Redis.

        Returns:
            List of workflow IDs
        """
        pattern = f"{self.key_prefix}*"
        keys = self.redis_client.keys(pattern)
        workflows = [key[len(self.key_prefix) :] for key in keys]

        logger.info("workflows_listed", count=len(workflows), backend="redis")
        return workflows

    def close(self) -> None:
        """Close the Redis connection."""
        self.redis_client.close()
        logger.info("connection_closed", backend="redis")
