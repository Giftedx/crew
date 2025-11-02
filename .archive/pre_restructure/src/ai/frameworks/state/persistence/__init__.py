"""State persistence backends for workflow state management.

This package provides multiple storage backends for persisting workflow state:

- MemoryBackend: In-memory storage (testing/development)
- SQLiteBackend: File-based SQL storage (single-instance deployments)
- RedisBackend: Distributed cache storage (multi-instance deployments)
- PostgreSQLBackend: Production database storage (enterprise deployments)
"""

from .memory import MemoryBackend
from .postgresql import PostgreSQLBackend
from .redis import RedisBackend
from .sqlite import SQLiteBackend


__all__ = [
    "MemoryBackend",
    "PostgreSQLBackend",
    "RedisBackend",
    "SQLiteBackend",
]
