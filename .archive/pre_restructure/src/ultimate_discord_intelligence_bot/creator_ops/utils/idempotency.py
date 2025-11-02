"""Idempotency management for Creator Operations.

Provides decorators and managers for ensuring operations are executed only once,
with proper caching and result storage.
"""

import asyncio
import hashlib
import json
import logging
import time
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)

T = TypeVar("T")
P = ParamSpec("P")


class IdempotencyKey:
    """Represents an idempotency key with metadata."""

    def __init__(
        self,
        key: str,
        expires_at: float | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.key = key
        self.expires_at = expires_at
        self.metadata = metadata or {}
        self.created_at = time.time()

    def is_expired(self) -> bool:
        """Check if the key has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "key": self.key,
            "expires_at": self.expires_at,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IdempotencyKey":
        """Create from dictionary."""
        return cls(
            key=data["key"],
            expires_at=data.get("expires_at"),
            metadata=data.get("metadata", {}),
        )


class IdempotencyManager:
    """
    Manages idempotency keys to prevent duplicate operations.

    Stores operation results and ensures that repeated calls with the same
    idempotency key return the same result without re-executing the operation.
    """

    def __init__(self, default_ttl: float = 3600.0):  # 1 hour default
        """
        Initialize idempotency manager.

        Args:
            default_ttl: Default time-to-live for idempotency keys in seconds
        """
        self.default_ttl = default_ttl
        self._store: dict[str, IdempotencyKey] = {}
        self._results: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def execute_with_idempotency(
        self,
        operation: Callable[..., T],
        idempotency_key: str | None = None,
        ttl: float | None = None,
        *args,
        **kwargs,
    ) -> T:
        """
        Execute operation with idempotency protection.

        Args:
            operation: Operation to execute
            idempotency_key: Idempotency key (auto-generated if None)
            ttl: Time-to-live for the key
            *args: Operation arguments
            **kwargs: Operation keyword arguments

        Returns:
            Operation result (cached if key exists)
        """
        if idempotency_key is None:
            idempotency_key = self._generate_key(operation, args, kwargs)

        if ttl is None:
            ttl = self.default_ttl

        async with self._lock:
            # Check if key exists and is not expired
            if idempotency_key in self._store:
                existing_key = self._store[idempotency_key]
                if not existing_key.is_expired():
                    logger.info(f"Returning cached result for idempotency key: {idempotency_key}")
                    return self._results[idempotency_key]
                else:
                    # Remove expired key
                    del self._store[idempotency_key]
                    del self._results[idempotency_key]

            # Execute operation
            logger.info(f"Executing operation with idempotency key: {idempotency_key}")

            try:
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)

                # Store result
                expires_at = time.time() + ttl
                self._store[idempotency_key] = IdempotencyKey(
                    key=idempotency_key,
                    expires_at=expires_at,
                    metadata={
                        "operation": operation.__name__,
                        "args_hash": hashlib.md5(str(args).encode(), usedforsecurity=False).hexdigest(),  # nosec B324 - idempotency metadata only
                        "kwargs_hash": hashlib.md5(str(kwargs).encode(), usedforsecurity=False).hexdigest(),  # nosec B324 - idempotency metadata only
                    },
                )
                self._results[idempotency_key] = result

                logger.info(f"Stored result for idempotency key: {idempotency_key}")
                return result

            except Exception as e:
                # Don't store failed results
                logger.error(f"Operation failed for idempotency key {idempotency_key}: {e!s}")
                raise

    async def execute_with_result_idempotency(
        self,
        operation: Callable[..., StepResult],
        idempotency_key: str | None = None,
        ttl: float | None = None,
        *args,
        **kwargs,
    ) -> StepResult:
        """
        Execute StepResult operation with idempotency protection.

        Args:
            operation: Operation returning StepResult
            idempotency_key: Idempotency key (auto-generated if None)
            ttl: Time-to-live for the key
            *args: Operation arguments
            **kwargs: Operation keyword arguments

        Returns:
            StepResult (cached if key exists)
        """
        try:
            result = await self.execute_with_idempotency(operation, idempotency_key, ttl, *args, **kwargs)
            return result
        except Exception as e:
            return StepResult.fail(f"Operation failed: {e!s}")

    def _generate_key(self, operation: Callable, args: tuple, kwargs: dict) -> str:
        """Generate idempotency key from operation and arguments."""
        # Create a deterministic key based on operation and arguments
        operation_name = getattr(operation, "__name__", "unknown")

        # Serialize arguments in a deterministic way
        args_str = json.dumps(args, sort_keys=True, default=str)
        kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)

        # Create hash
        content = f"{operation_name}:{args_str}:{kwargs_str}"
        key_hash = hashlib.sha256(content.encode()).hexdigest()

        # Add timestamp component to make it more unique if needed
        timestamp = str(int(time.time()))

        return f"{operation_name}_{key_hash[:16]}_{timestamp}"

    async def cleanup_expired(self) -> int:
        """
        Clean up expired idempotency keys.

        Returns:
            Number of keys cleaned up
        """
        async with self._lock:
            expired_keys = []

            for key, idempotency_key in self._store.items():
                if idempotency_key.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                del self._store[key]
                del self._results[key]

            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired idempotency keys")

            return len(expired_keys)

    def get_stats(self) -> dict[str, Any]:
        """Get idempotency manager statistics."""
        time.time()
        expired_count = sum(1 for key in self._store.values() if key.is_expired())

        return {
            "total_keys": len(self._store),
            "expired_keys": expired_count,
            "active_keys": len(self._store) - expired_count,
            "default_ttl": self.default_ttl,
        }

    async def clear_all(self) -> None:
        """Clear all idempotency keys and results."""
        async with self._lock:
            self._store.clear()
            self._results.clear()
            logger.info("Cleared all idempotency keys and results")


# Global idempotency manager
idempotency_manager = IdempotencyManager()


def with_idempotency(
    key: str | None = None,
    ttl: float | None = None,
    manager: IdempotencyManager | None = None,
):
    """
    Decorator to add idempotency protection to functions.

    Args:
        key: Idempotency key (auto-generated if None)
        ttl: Time-to-live for the key
        manager: Idempotency manager to use (default: global)
    """
    if manager is None:
        manager = idempotency_manager

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        async def async_wrapper(*args, **kwargs) -> T:
            return await manager.execute_with_idempotency(func, key, ttl, *args, **kwargs)

        def sync_wrapper(*args, **kwargs) -> T:
            return asyncio.run(manager.execute_with_idempotency(func, key, ttl, *args, **kwargs))

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def with_result_idempotency(
    key: str | None = None,
    ttl: float | None = None,
    manager: IdempotencyManager | None = None,
):
    """
    Decorator to add idempotency protection to StepResult functions.

    Args:
        key: Idempotency key (auto-generated if None)
        ttl: Time-to-live for the key
        manager: Idempotency manager to use (default: global)
    """
    if manager is None:
        manager = idempotency_manager

    def decorator(func: Callable[..., StepResult]) -> Callable[..., StepResult]:
        async def async_wrapper(*args, **kwargs) -> StepResult:
            return await manager.execute_with_result_idempotency(func, key, ttl, *args, **kwargs)

        def sync_wrapper(*args, **kwargs) -> StepResult:
            return asyncio.run(manager.execute_with_result_idempotency(func, key, ttl, *args, **kwargs))

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
