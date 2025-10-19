"""Unified memory facade for vector storage and semantic retrieval.

This module provides a tenant-aware facade over the production vector store,
ensuring all memory operations enforce namespace isolation and consistent APIs.

Plugin support enables specialty backends like Mem0, HippoRAG, and Graph memory.

See ADR-0002 for architectural decision rationale.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol, Sequence

from memory.vector_store import VectorRecord, VectorStore

from ..step_result import StepResult

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MemoryNamespace:
    """Details about the memory namespace for tenant isolation."""

    tenant: str
    workspace: str
    creator: str

    def name(self, suffix: str) -> str:
        """Generate namespace name with suffix."""
        return f"{self.tenant}:{self.workspace}:{self.creator}:{suffix}"


class MemoryPlugin(Protocol):
    """Protocol for specialty memory backends.

    Plugins enable integration of specialized memory systems like:
    - Mem0 (long-term episodic memory)
    - HippoRAG (continual learning with active recall)
    - Graph memory (knowledge graph operations)
    """

    async def store(
        self, namespace: str, records: Sequence[Dict[str, Any]]
    ) -> StepResult:
        """Store records in specialty backend.

        Args:
            namespace: Tenant-scoped namespace
            records: Records to store

        Returns:
            StepResult with storage outcome
        """
        ...

    async def retrieve(self, namespace: str, query: str, limit: int) -> StepResult:
        """Retrieve records from specialty backend.

        Args:
            namespace: Tenant-scoped namespace
            query: Query string
            limit: Maximum number of results

        Returns:
            StepResult with retrieved records
        """
        ...


class UnifiedMemoryService:
    """Tenant-aware facade for vector storage with plugin support.

    Provides unified API for:
    - Default vector storage (Qdrant)
    - Specialty plugins (Mem0, HippoRAG, Graph memory)
    """

    def __init__(self, vector_store: VectorStore | None = None):
        """Initialize unified memory service.

        Args:
            vector_store: Optional VectorStore instance; uses global singleton if None
        """
        self._store = vector_store or VectorStore()
        self._plugins: Dict[str, MemoryPlugin] = {}
        logger.info("UnifiedMemoryService initialized")

    def register_plugin(self, name: str, plugin: MemoryPlugin):
        """Register specialty memory backend plugin.

        Args:
            name: Plugin identifier (e.g., "mem0", "hipporag", "graph")
            plugin: Plugin implementation
        """
        self._plugins[name] = plugin
        logger.info(f"Registered memory plugin: {name}")

    def get_namespace(self, tenant: str, workspace: str, creator: str = "") -> str:
        """Get namespace for tenant/workspace/creator scope."""
        return VectorStore.namespace(tenant, workspace, creator or "default")

    async def upsert(
        self,
        tenant: str,
        workspace: str,
        records: Sequence[VectorRecord],
        creator: str = "",
        plugin: Optional[str] = None,
    ) -> StepResult:
        """Upsert vectors into tenant-scoped collection.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            records: Vector records to upsert
            creator: Optional creator identifier for further isolation
            plugin: Optional plugin name for specialty backend

        Returns:
            StepResult indicating success or failure
        """
        try:
            namespace = self.get_namespace(tenant, workspace, creator)

            # Route to plugin if specified
            if plugin and plugin in self._plugins:
                record_dicts = [
                    {"content": r.content, "metadata": r.metadata}
                    if hasattr(r, "content")
                    else r
                    if isinstance(r, dict)
                    else {"content": str(r)}
                    for r in records
                ]
                return await self._plugins[plugin].store(namespace, record_dicts)

            # Default: use vector store
            self._store.upsert(namespace, records)
            return StepResult.ok(upserted=len(records), namespace=namespace)
        except Exception as exc:
            return StepResult.fail(f"Memory upsert failed: {exc}")

    async def query(
        self,
        tenant: str,
        workspace: str,
        vector: Sequence[float],
        top_k: int = 3,
        creator: str = "",
        plugin: Optional[str] = None,
        query_text: Optional[str] = None,
    ) -> StepResult:
        """Query similar vectors from tenant-scoped collection.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            vector: Query vector
            top_k: Number of results to return
            creator: Optional creator identifier
            plugin: Optional plugin name for specialty backend
            query_text: Optional text query (for plugins that support text search)

        Returns:
            StepResult with query results
        """
        try:
            namespace = self.get_namespace(tenant, workspace, creator)

            # Route to plugin if specified
            if plugin and plugin in self._plugins:
                if not query_text:
                    return StepResult.fail("Plugin query requires query_text parameter")
                return await self._plugins[plugin].retrieve(
                    namespace, query_text, top_k
                )

            # Default: use vector store
            results = self._store.query(namespace, vector, top_k=top_k)
            return StepResult.ok(
                results=results, namespace=namespace, count=len(results)
            )
        except Exception as exc:
            return StepResult.fail(f"Memory query failed: {exc}")


_unified_memory: UnifiedMemoryService | None = None


def get_unified_memory() -> UnifiedMemoryService:
    """Get global unified memory service instance."""
    global _unified_memory
    if _unified_memory is None:
        _unified_memory = UnifiedMemoryService()
    return _unified_memory


def get_memory_namespace(tenant: str, workspace: str, creator: str) -> MemoryNamespace:
    """Get memory namespace for tenant/workspace/creator."""
    return MemoryNamespace(tenant=tenant, workspace=workspace, creator=creator)


__all__ = [
    "UnifiedMemoryService",
    "get_unified_memory",
    "get_memory_namespace",
    "MemoryNamespace",
    "MemoryPlugin",
    "VectorRecord",
]
