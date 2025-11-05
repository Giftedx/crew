"""
Dependency-based cache invalidation system.

This module provides intelligent cache invalidation based on data relationships,
enabling automatic invalidation of dependent cache entries when underlying data changes.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class DependencyNode:
    """Represents a node in the dependency graph."""

    key: str
    depends_on: set[str] = field(default_factory=set)
    depended_by: set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)

    def add_dependency(self, dependency_key: str) -> None:
        """Add a dependency relationship."""
        self.depends_on.add(dependency_key)

    def remove_dependency(self, dependency_key: str) -> None:
        """Remove a dependency relationship."""
        self.depends_on.discard(dependency_key)

    def add_dependent(self, dependent_key: str) -> None:
        """Add a dependent relationship."""
        self.depended_by.add(dependent_key)

    def remove_dependent(self, dependent_key: str) -> None:
        """Remove a dependent relationship."""
        self.depended_by.discard(dependent_key)


class DependencyTracker:
    """Tracks cache key dependencies and manages the dependency graph."""

    def __init__(self, max_graph_size: int = 10000):
        self.max_graph_size = max_graph_size
        self._graph: dict[str, DependencyNode] = {}
        self._lock = asyncio.Lock()
        self._stats = {
            "nodes_created": 0,
            "nodes_removed": 0,
            "dependencies_added": 0,
            "dependencies_removed": 0,
            "invalidations_triggered": 0,
            "circular_refs_detected": 0,
        }

    async def register_dependencies(self, key: str, dependencies: set[str]) -> None:
        """Register dependencies for a cache key."""
        async with self._lock:
            # Create or get node for the key
            if key not in self._graph:
                self._graph[key] = DependencyNode(key=key)
                self._stats["nodes_created"] += 1

            node = self._graph[key]

            # Remove old dependencies that are no longer present
            old_deps = node.depends_on - dependencies
            for old_dep in old_deps:
                await self._remove_dependency_relationship(key, old_dep)

            # Add new dependencies
            new_deps = dependencies - node.depends_on
            for dep in new_deps:
                await self._add_dependency_relationship(key, dep)

            node.last_updated = time.time()

            # Check for circular references
            if await self._detect_circular_reference(key):
                self._stats["circular_refs_detected"] += 1
                logger.warning(f"Circular dependency detected involving key: {key}")

    async def unregister_key(self, key: str) -> None:
        """Remove a key and all its dependency relationships."""
        async with self._lock:
            if key not in self._graph:
                return

            node = self._graph[key]

            # Remove this key from all dependents
            for dependent in list(node.depended_by):
                if dependent in self._graph:
                    self._graph[dependent].remove_dependency(key)

            # Remove this key from all dependencies
            for dependency in list(node.depends_on):
                if dependency in self._graph:
                    self._graph[dependency].remove_dependent(key)

            # Remove the node
            del self._graph[key]
            self._stats["nodes_removed"] += 1

    async def get_dependents(self, key: str) -> set[str]:
        """Get all keys that depend on the given key (directly and indirectly)."""
        async with self._lock:
            if key not in self._graph:
                return set()

            visited: set[str] = set()
            queue = deque([key])
            dependents: set[str] = set()

            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)

                if current in self._graph:
                    # Add direct dependents
                    for dependent in self._graph[current].depended_by:
                        if dependent not in visited:
                            dependents.add(dependent)
                            queue.append(dependent)

            return dependents

    async def get_dependencies(self, key: str) -> set[str]:
        """Get all keys that the given key depends on (directly and indirectly)."""
        async with self._lock:
            if key not in self._graph:
                return set()

            visited: set[str] = set()
            queue = deque([key])
            dependencies: set[str] = set()

            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)

                if current in self._graph:
                    # Add direct dependencies
                    for dependency in self._graph[current].depends_on:
                        if dependency not in visited:
                            dependencies.add(dependency)
                            queue.append(dependency)

            return dependencies

    async def invalidate_key(self, key: str) -> set[str]:
        """Get all keys that should be invalidated when the given key changes."""
        dependents = await self.get_dependents(key)
        self._stats["invalidations_triggered"] += 1
        return dependents

    async def _add_dependency_relationship(self, dependent: str, dependency: str) -> None:
        """Add a dependency relationship between two keys."""
        # Ensure both nodes exist
        if dependency not in self._graph:
            self._graph[dependency] = DependencyNode(key=dependency)
            self._stats["nodes_created"] += 1

        if dependent not in self._graph:
            self._graph[dependent] = DependencyNode(key=dependent)
            self._stats["nodes_created"] += 1

        # Add relationships
        self._graph[dependent].add_dependency(dependency)
        self._graph[dependency].add_dependent(dependent)
        self._stats["dependencies_added"] += 1

    async def _remove_dependency_relationship(self, dependent: str, dependency: str) -> None:
        """Remove a dependency relationship between two keys."""
        if dependent in self._graph:
            self._graph[dependent].remove_dependency(dependency)
            self._stats["dependencies_removed"] += 1

        if dependency in self._graph:
            self._graph[dependency].remove_dependent(dependent)

    async def _detect_circular_reference(self, start_key: str) -> bool:
        """Detect if there's a circular dependency involving the start key."""
        visited: set[str] = set()
        rec_stack: set[str] = set()
        return await self._has_cycle(start_key, visited, rec_stack)

    async def _has_cycle(self, key: str, visited: set[str], rec_stack: set[str]) -> bool:
        """Helper method to detect cycles in dependency graph."""
        if key not in self._graph:
            return False

        visited.add(key)
        rec_stack.add(key)

        for dependency in self._graph[key].depends_on:
            if dependency not in visited:
                if await self._has_cycle(dependency, visited, rec_stack):
                    return True
            elif dependency in rec_stack:
                return True

        rec_stack.remove(key)
        return False

    def get_stats(self) -> dict[str, Any]:
        """Get dependency tracker statistics."""
        return {
            "graph_size": len(self._graph),
            "max_graph_size": self.max_graph_size,
            "utilization_ratio": len(self._graph) / self.max_graph_size if self.max_graph_size > 0 else 0,
            **self._stats,
        }

    async def cleanup_orphaned_nodes(self) -> int:
        """Remove nodes that have no dependencies or dependents."""
        async with self._lock:
            orphaned = []
            for key, node in self._graph.items():
                if not node.depends_on and not node.depended_by:
                    orphaned.append(key)

            for key in orphaned:
                del self._graph[key]
                self._stats["nodes_removed"] += 1

            return len(orphaned)

    def get_graph_snapshot(self) -> dict[str, dict[str, Any]]:
        """Get a snapshot of the current dependency graph."""
        snapshot = {}
        for key, node in self._graph.items():
            snapshot[key] = {
                "depends_on": list(node.depends_on),
                "depended_by": list(node.depended_by),
                "created_at": node.created_at,
                "last_updated": node.last_updated,
            }
        return snapshot


# Global dependency tracker instance
_dependency_tracker = DependencyTracker()


def get_dependency_tracker() -> DependencyTracker:
    """Get the global dependency tracker instance."""
    return _dependency_tracker


__all__ = [
    "DependencyNode",
    "DependencyTracker",
    "get_dependency_tracker",
]
