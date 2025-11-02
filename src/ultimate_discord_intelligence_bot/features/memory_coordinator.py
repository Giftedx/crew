"""Memory coordination layer for shared context and cross-agent memory access.

This module provides memory pooling, shared context management, and
cross-agent memory access patterns for the crew system.
"""

from __future__ import annotations
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any
from platform.core.step_result import StepResult

if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags
logger = logging.getLogger(__name__)


class MemoryAccessLevel(Enum):
    """Memory access levels for agent isolation."""

    PRIVATE = "private"
    SHARED = "shared"
    GLOBAL = "global"


class MemoryOperation(Enum):
    """Types of memory operations."""

    READ = "read"
    WRITE = "write"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"


@dataclass
class MemoryEntry:
    """Represents a memory entry with metadata."""

    key: str
    value: Any
    agent_id: str
    access_level: MemoryAccessLevel
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    ttl: float | None = None
    tags: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryAccess:
    """Represents a memory access operation."""

    agent_id: str
    operation: MemoryOperation
    key: str
    access_level: MemoryAccessLevel
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    error: str | None = None


class MemoryCoordinator:
    """Coordinates memory access and sharing across agents."""

    def __init__(self, feature_flags: FeatureFlags):
        """Initialize memory coordinator.

        Args:
            feature_flags: Feature flags configuration
        """
        self.feature_flags = feature_flags
        self.memory_pool: dict[str, MemoryEntry] = {}
        self.access_log: list[MemoryAccess] = []
        self.agent_memory_quotas: dict[str, int] = {}
        self.shared_context: dict[str, Any] = {}
        self._lock = threading.RLock()

    def is_enabled(self) -> bool:
        """Check if memory coordination is enabled."""
        return self.feature_flags.ENABLE_MEMORY_COORDINATION

    def store_memory(
        self,
        key: str,
        value: Any,
        agent_id: str,
        access_level: MemoryAccessLevel = MemoryAccessLevel.PRIVATE,
        ttl: float | None = None,
        tags: set[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StepResult:
        """Store memory with coordination and isolation.

        Args:
            key: Memory key
            value: Memory value
            agent_id: ID of the agent storing the memory
            access_level: Access level for the memory
            ttl: Time to live in seconds
            tags: Optional tags for categorization
            metadata: Optional metadata

        Returns:
            StepResult: Result of the storage operation
        """
        if not self.is_enabled():
            return StepResult.fail("Memory coordination disabled")
        try:
            with self._lock:
                if not self._check_agent_quota(agent_id):
                    return StepResult.fail(f"Agent {agent_id} quota exceeded")
                entry = MemoryEntry(
                    key=key,
                    value=value,
                    agent_id=agent_id,
                    access_level=access_level,
                    ttl=ttl,
                    tags=tags or set(),
                    metadata=metadata or {},
                )
                self.memory_pool[key] = entry
                if access_level in [MemoryAccessLevel.SHARED, MemoryAccessLevel.GLOBAL]:
                    self.shared_context[key] = value
                self._log_access(agent_id, MemoryOperation.WRITE, key, access_level, True)
                return StepResult.ok(
                    data={
                        "key": key,
                        "access_level": access_level.value,
                        "agent_id": agent_id,
                        "stored_at": entry.created_at,
                    }
                )
        except Exception as e:
            logger.error(f"Memory storage failed for agent {agent_id}: {e}")
            self._log_access(agent_id, MemoryOperation.WRITE, key, access_level, False, str(e))
            return StepResult.fail(f"Memory storage failed: {e}")

    def retrieve_memory(
        self, key: str, agent_id: str, access_level: MemoryAccessLevel = MemoryAccessLevel.PRIVATE
    ) -> StepResult:
        """Retrieve memory with access control.

        Args:
            key: Memory key
            agent_id: ID of the agent retrieving the memory
            access_level: Required access level

        Returns:
            StepResult: Result containing the memory value
        """
        if not self.is_enabled():
            return StepResult.fail("Memory coordination disabled")
        try:
            with self._lock:
                if key not in self.memory_pool:
                    self._log_access(agent_id, MemoryOperation.READ, key, access_level, False, "Key not found")
                    return StepResult.fail("Memory key not found")
                entry = self.memory_pool[key]
                if not self._check_access_permission(entry, agent_id, access_level):
                    self._log_access(agent_id, MemoryOperation.READ, key, access_level, False, "Access denied")
                    return StepResult.fail("Access denied to memory key")
                if entry.ttl and time.time() - entry.created_at > entry.ttl:
                    del self.memory_pool[key]
                    self._log_access(agent_id, MemoryOperation.READ, key, access_level, False, "Memory expired")
                    return StepResult.fail("Memory expired")
                self._log_access(agent_id, MemoryOperation.READ, key, access_level, True)
                return StepResult.ok(
                    data={
                        "key": key,
                        "value": entry.value,
                        "agent_id": entry.agent_id,
                        "access_level": entry.access_level.value,
                        "created_at": entry.created_at,
                        "metadata": entry.metadata,
                    }
                )
        except Exception as e:
            logger.error(f"Memory retrieval failed for agent {agent_id}: {e}")
            self._log_access(agent_id, MemoryOperation.READ, key, access_level, False, str(e))
            return StepResult.fail(f"Memory retrieval failed: {e}")

    def search_memory(
        self,
        query: str,
        agent_id: str,
        access_level: MemoryAccessLevel = MemoryAccessLevel.PRIVATE,
        tags: set[str] | None = None,
        limit: int = 10,
    ) -> StepResult:
        """Search memory with filtering and access control.

        Args:
            query: Search query
            agent_id: ID of the agent searching
            access_level: Required access level
            tags: Optional tags to filter by
            limit: Maximum number of results

        Returns:
            StepResult: Result containing matching memories
        """
        if not self.is_enabled():
            return StepResult.fail("Memory coordination disabled")
        try:
            with self._lock:
                matches = []
                query_lower = query.lower()
                for key, entry in self.memory_pool.items():
                    if not self._check_access_permission(entry, agent_id, access_level):
                        continue
                    if entry.ttl and time.time() - entry.created_at > entry.ttl:
                        continue
                    if tags and (not tags.intersection(entry.tags)):
                        continue
                    if query_lower in key.lower() or (
                        isinstance(entry.value, str) and query_lower in entry.value.lower()
                    ):
                        matches.append(
                            {
                                "key": key,
                                "value": entry.value,
                                "agent_id": entry.agent_id,
                                "access_level": entry.access_level.value,
                                "created_at": entry.created_at,
                                "tags": list(entry.tags),
                                "metadata": entry.metadata,
                            }
                        )
                matches.sort(key=lambda x: x["created_at"], reverse=True)
                matches = matches[:limit]
                self._log_access(agent_id, MemoryOperation.SEARCH, f"query:{query}", access_level, True)
                return StepResult.ok(
                    data={"query": query, "matches": matches, "total_found": len(matches), "agent_id": agent_id}
                )
        except Exception as e:
            logger.error(f"Memory search failed for agent {agent_id}: {e}")
            self._log_access(agent_id, MemoryOperation.SEARCH, f"query:{query}", access_level, False, str(e))
            return StepResult.fail(f"Memory search failed: {e}")

    def get_shared_context(self, agent_id: str) -> StepResult:
        """Get shared context available to an agent.

        Args:
            agent_id: ID of the agent requesting context

        Returns:
            StepResult: Result containing shared context
        """
        if not self.is_enabled():
            return StepResult.fail("Memory coordination disabled")
        try:
            with self._lock:
                accessible_context = {}
                for key, value in self.shared_context.items():
                    if key in self.memory_pool:
                        entry = self.memory_pool[key]
                        if self._check_access_permission(entry, agent_id, MemoryAccessLevel.SHARED):
                            accessible_context[key] = value
                return StepResult.ok(
                    data={
                        "agent_id": agent_id,
                        "shared_context": accessible_context,
                        "context_size": len(accessible_context),
                    }
                )
        except Exception as e:
            logger.error(f"Shared context retrieval failed for agent {agent_id}: {e}")
            return StepResult.fail(f"Shared context retrieval failed: {e}")

    def update_memory(
        self, key: str, value: Any, agent_id: str, access_level: MemoryAccessLevel = MemoryAccessLevel.PRIVATE
    ) -> StepResult:
        """Update existing memory with access control.

        Args:
            key: Memory key
            value: New value
            agent_id: ID of the agent updating
            access_level: Required access level

        Returns:
            StepResult: Result of the update operation
        """
        if not self.is_enabled():
            return StepResult.fail("Memory coordination disabled")
        try:
            with self._lock:
                if key not in self.memory_pool:
                    return StepResult.fail("Memory key not found")
                entry = self.memory_pool[key]
                if not self._check_access_permission(entry, agent_id, access_level):
                    return StepResult.fail("Access denied to memory key")
                entry.value = value
                entry.updated_at = time.time()
                if entry.access_level in [MemoryAccessLevel.SHARED, MemoryAccessLevel.GLOBAL]:
                    self.shared_context[key] = value
                self._log_access(agent_id, MemoryOperation.UPDATE, key, access_level, True)
                return StepResult.ok(data={"key": key, "updated_at": entry.updated_at, "agent_id": agent_id})
        except Exception as e:
            logger.error(f"Memory update failed for agent {agent_id}: {e}")
            self._log_access(agent_id, MemoryOperation.UPDATE, key, access_level, False, str(e))
            return StepResult.fail(f"Memory update failed: {e}")

    def delete_memory(
        self, key: str, agent_id: str, access_level: MemoryAccessLevel = MemoryAccessLevel.PRIVATE
    ) -> StepResult:
        """Delete memory with access control.

        Args:
            key: Memory key
            agent_id: ID of the agent deleting
            access_level: Required access level

        Returns:
            StepResult: Result of the delete operation
        """
        if not self.is_enabled():
            return StepResult.fail("Memory coordination disabled")
        try:
            with self._lock:
                if key not in self.memory_pool:
                    return StepResult.fail("Memory key not found")
                entry = self.memory_pool[key]
                if not self._check_access_permission(entry, agent_id, access_level):
                    return StepResult.fail("Access denied to memory key")
                del self.memory_pool[key]
                if key in self.shared_context:
                    del self.shared_context[key]
                self._log_access(agent_id, MemoryOperation.DELETE, key, access_level, True)
                return StepResult.ok(data={"key": key, "deleted_at": time.time(), "agent_id": agent_id})
        except Exception as e:
            logger.error(f"Memory deletion failed for agent {agent_id}: {e}")
            self._log_access(agent_id, MemoryOperation.DELETE, key, access_level, False, str(e))
            return StepResult.fail(f"Memory deletion failed: {e}")

    def get_memory_stats(self, agent_id: str | None = None) -> StepResult:
        """Get memory statistics.

        Args:
            agent_id: Optional agent ID to filter stats

        Returns:
            StepResult: Result containing memory statistics
        """
        if not self.is_enabled():
            return StepResult.fail("Memory coordination disabled")
        try:
            with self._lock:
                total_memories = len(self.memory_pool)
                total_accesses = len(self.access_log)
                if agent_id:
                    agent_memories = sum((1 for entry in self.memory_pool.values() if entry.agent_id == agent_id))
                    agent_accesses = sum((1 for access in self.access_log if access.agent_id == agent_id))
                else:
                    agent_memories = total_memories
                    agent_accesses = total_accesses
                access_levels = {}
                for entry in self.memory_pool.values():
                    level = entry.access_level.value
                    access_levels[level] = access_levels.get(level, 0) + 1
                return StepResult.ok(
                    data={
                        "total_memories": total_memories,
                        "agent_memories": agent_memories,
                        "total_accesses": total_accesses,
                        "agent_accesses": agent_accesses,
                        "access_levels": access_levels,
                        "shared_context_size": len(self.shared_context),
                        "agent_id": agent_id,
                    }
                )
        except Exception as e:
            logger.error(f"Memory stats retrieval failed: {e}")
            return StepResult.fail(f"Memory stats retrieval failed: {e}")

    def _check_agent_quota(self, agent_id: str) -> bool:
        """Check if agent has quota for new memory.

        Args:
            agent_id: Agent ID to check

        Returns:
            bool: True if agent has quota
        """
        agent_memory_count = sum((1 for entry in self.memory_pool.values() if entry.agent_id == agent_id))
        max_quota = self.agent_memory_quotas.get(agent_id, 1000)
        return agent_memory_count < max_quota

    def _check_access_permission(self, entry: MemoryEntry, agent_id: str, required_level: MemoryAccessLevel) -> bool:
        """Check if agent has permission to access memory entry.

        Args:
            entry: Memory entry to check
            agent_id: Agent requesting access
            required_level: Required access level

        Returns:
            bool: True if access is permitted
        """
        if entry.agent_id == agent_id:
            return True
        if entry.access_level == MemoryAccessLevel.PRIVATE:
            return False
        elif entry.access_level == MemoryAccessLevel.SHARED:
            return required_level in [MemoryAccessLevel.SHARED, MemoryAccessLevel.GLOBAL]
        elif entry.access_level == MemoryAccessLevel.GLOBAL:
            return True
        return False

    def _log_access(
        self,
        agent_id: str,
        operation: MemoryOperation,
        key: str,
        access_level: MemoryAccessLevel,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Log memory access for auditing.

        Args:
            agent_id: Agent performing the operation
            operation: Type of operation
            key: Memory key
            access_level: Access level used
            success: Whether operation succeeded
            error: Error message if failed
        """
        access = MemoryAccess(
            agent_id=agent_id, operation=operation, key=key, access_level=access_level, success=success, error=error
        )
        self.access_log.append(access)
        if len(self.access_log) > 10000:
            self.access_log = self.access_log[-5000:]

    def cleanup_expired_memories(self) -> int:
        """Clean up expired memories.

        Returns:
            int: Number of memories cleaned up
        """
        if not self.is_enabled():
            return 0
        try:
            with self._lock:
                current_time = time.time()
                expired_keys = []
                for key, entry in self.memory_pool.items():
                    if entry.ttl and current_time - entry.created_at > entry.ttl:
                        expired_keys.append(key)
                for key in expired_keys:
                    del self.memory_pool[key]
                    if key in self.shared_context:
                        del self.shared_context[key]
                return len(expired_keys)
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
            return 0
