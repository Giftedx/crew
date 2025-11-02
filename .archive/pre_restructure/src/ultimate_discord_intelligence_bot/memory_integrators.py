"""Multi-layer memory integration system.

This module provides comprehensive memory integration capabilities across multiple
storage paradigms including vector stores, graph databases, and traditional databases.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .step_result import StepResult


if TYPE_CHECKING:
    from .tenancy.context import TenantContext


logger = logging.getLogger(__name__)


class MemoryIntegrator:
    """Multi-layer memory integration coordinator.

    Coordinates memory operations across vector stores, graph databases,
    and traditional storage systems with tenant isolation.
    """

    def __init__(self, tenant_context: TenantContext):
        """Initialize memory integrator with tenant context.

        Args:
            tenant_context: Tenant context for data isolation
        """
        self.tenant_context = tenant_context
        self.vector_store = None
        self.graph_db = None
        self.traditional_db = None
        self._initialize_stores()

    def _initialize_stores(self) -> None:
        """Initialize memory storage systems."""
        try:
            # Initialize vector store
            from .services.memory_service import MemoryService

            self.vector_store = MemoryService()

            # Initialize graph database
            from .services.graph_memory_service import GraphMemoryService

            self.graph_db = GraphMemoryService()

            # Initialize traditional database
            from .services.traditional_memory_service import TraditionalMemoryService

            self.traditional_db = TraditionalMemoryService()

        except ImportError as e:
            logger.warning(f"Some memory services not available: {e}")

    def store_content(self, content: str, metadata: dict[str, Any], content_type: str = "text") -> StepResult:
        """Store content across multiple memory systems.

        Args:
            content: Content to store
            metadata: Associated metadata
            content_type: Type of content (text, image, audio, etc.)

        Returns:
            StepResult with storage results
        """
        try:
            results = {}

            # Store in vector store
            if self.vector_store:
                vector_result = self.vector_store.store_content(
                    content=content,
                    metadata=metadata,
                    tenant=self.tenant_context.tenant,
                    workspace=self.tenant_context.workspace,
                )
                results["vector_store"] = vector_result

            # Store in graph database
            if self.graph_db:
                graph_result = self.graph_db.store_entity(
                    content=content,
                    metadata=metadata,
                    tenant=self.tenant_context.tenant,
                    workspace=self.tenant_context.workspace,
                )
                results["graph_db"] = graph_result

            # Store in traditional database
            if self.traditional_db:
                traditional_result = self.traditional_db.store_document(
                    content=content,
                    metadata=metadata,
                    tenant=self.tenant_context.tenant,
                    workspace=self.tenant_context.workspace,
                )
                results["traditional_db"] = traditional_result

            return StepResult.ok(
                data={
                    "storage_results": results,
                    "content_type": content_type,
                    "tenant": self.tenant_context.tenant,
                    "workspace": self.tenant_context.workspace,
                }
            )

        except Exception as e:
            logger.error(f"Failed to store content: {e}")
            return StepResult.fail(f"Content storage failed: {e!s}")

    def retrieve_content(self, query: str, content_type: str | None = None, limit: int = 10) -> StepResult:
        """Retrieve content from multiple memory systems.

        Args:
            query: Search query
            content_type: Filter by content type
            limit: Maximum number of results

        Returns:
            StepResult with retrieved content
        """
        try:
            results = {}

            # Search vector store
            if self.vector_store:
                vector_results = self.vector_store.search_content(
                    query=query,
                    tenant=self.tenant_context.tenant,
                    workspace=self.tenant_context.workspace,
                    limit=limit,
                )
                results["vector_store"] = vector_results

            # Search graph database
            if self.graph_db:
                graph_results = self.graph_db.search_entities(
                    query=query,
                    tenant=self.tenant_context.tenant,
                    workspace=self.tenant_context.workspace,
                    limit=limit,
                )
                results["graph_db"] = graph_results

            # Search traditional database
            if self.traditional_db:
                traditional_results = self.traditional_db.search_documents(
                    query=query,
                    tenant=self.tenant_context.tenant,
                    workspace=self.tenant_context.workspace,
                    limit=limit,
                )
                results["traditional_db"] = traditional_results

            # Merge and rank results
            merged_results = self._merge_search_results(results, limit)

            return StepResult.ok(
                data={
                    "results": merged_results,
                    "query": query,
                    "content_type": content_type,
                    "tenant": self.tenant_context.tenant,
                    "workspace": self.tenant_context.workspace,
                }
            )

        except Exception as e:
            logger.error(f"Failed to retrieve content: {e}")
            return StepResult.fail(f"Content retrieval failed: {e!s}")

    def _merge_search_results(self, results: dict[str, Any], limit: int) -> list[dict[str, Any]]:
        """Merge and rank search results from multiple sources.

        Args:
            results: Results from different memory systems
            limit: Maximum number of results to return

        Returns:
            Merged and ranked results
        """
        merged = []

        # Collect all results
        for source, source_results in results.items():
            if source_results and hasattr(source_results, "data"):
                for result in source_results.data:
                    result["source"] = source
                    merged.append(result)

        # Simple ranking by relevance score (if available)
        merged.sort(key=lambda x: x.get("score", 0), reverse=True)

        return merged[:limit]

    def update_content(self, content_id: str, content: str, metadata: dict[str, Any]) -> StepResult:
        """Update content across multiple memory systems.

        Args:
            content_id: ID of content to update
            content: New content
            metadata: Updated metadata

        Returns:
            StepResult with update results
        """
        try:
            results = {}

            # Update in vector store
            if self.vector_store:
                vector_result = self.vector_store.update_content(
                    content_id=content_id,
                    content=content,
                    metadata=metadata,
                    tenant=self.tenant_context.tenant,
                    workspace=self.tenant_context.workspace,
                )
                results["vector_store"] = vector_result

            # Update in graph database
            if self.graph_db:
                graph_result = self.graph_db.update_entity(
                    entity_id=content_id,
                    content=content,
                    metadata=metadata,
                    tenant=self.tenant_context.tenant,
                    workspace=self.tenant_context.workspace,
                )
                results["graph_db"] = graph_result

            # Update in traditional database
            if self.traditional_db:
                traditional_result = self.traditional_db.update_document(
                    document_id=content_id,
                    content=content,
                    metadata=metadata,
                    tenant=self.tenant_context.tenant,
                    workspace=self.tenant_context.workspace,
                )
                results["traditional_db"] = traditional_result

            return StepResult.ok(
                data={
                    "update_results": results,
                    "content_id": content_id,
                    "tenant": self.tenant_context.tenant,
                    "workspace": self.tenant_context.workspace,
                }
            )

        except Exception as e:
            logger.error(f"Failed to update content: {e}")
            return StepResult.fail(f"Content update failed: {e!s}")

    def delete_content(self, content_id: str) -> StepResult:
        """Delete content from multiple memory systems.

        Args:
            content_id: ID of content to delete

        Returns:
            StepResult with deletion results
        """
        try:
            results = {}

            # Delete from vector store
            if self.vector_store:
                vector_result = self.vector_store.delete_content(
                    content_id=content_id,
                    tenant=self.tenant_context.tenant,
                    workspace=self.tenant_context.workspace,
                )
                results["vector_store"] = vector_result

            # Delete from graph database
            if self.graph_db:
                graph_result = self.graph_db.delete_entity(
                    entity_id=content_id,
                    tenant=self.tenant_context.tenant,
                    workspace=self.tenant_context.workspace,
                )
                results["graph_db"] = graph_result

            # Delete from traditional database
            if self.traditional_db:
                traditional_result = self.traditional_db.delete_document(
                    document_id=content_id,
                    tenant=self.tenant_context.tenant,
                    workspace=self.tenant_context.workspace,
                )
                results["traditional_db"] = traditional_result

            return StepResult.ok(
                data={
                    "deletion_results": results,
                    "content_id": content_id,
                    "tenant": self.tenant_context.tenant,
                    "workspace": self.tenant_context.workspace,
                }
            )

        except Exception as e:
            logger.error(f"Failed to delete content: {e}")
            return StepResult.fail(f"Content deletion failed: {e!s}")

    def get_memory_stats(self) -> StepResult:
        """Get statistics about memory usage across all systems.

        Returns:
            StepResult with memory statistics
        """
        try:
            stats = {}

            # Get vector store stats
            if self.vector_store:
                vector_stats = self.vector_store.get_stats(
                    tenant=self.tenant_context.tenant,
                    workspace=self.tenant_context.workspace,
                )
                stats["vector_store"] = vector_stats

            # Get graph database stats
            if self.graph_db:
                graph_stats = self.graph_db.get_stats(
                    tenant=self.tenant_context.tenant,
                    workspace=self.tenant_context.workspace,
                )
                stats["graph_db"] = graph_stats

            # Get traditional database stats
            if self.traditional_db:
                traditional_stats = self.traditional_db.get_stats(
                    tenant=self.tenant_context.tenant,
                    workspace=self.tenant_context.workspace,
                )
                stats["traditional_db"] = traditional_stats

            return StepResult.ok(
                data={
                    "memory_stats": stats,
                    "tenant": self.tenant_context.tenant,
                    "workspace": self.tenant_context.workspace,
                }
            )

        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return StepResult.fail(f"Memory stats retrieval failed: {e!s}")


class MemoryIntegrationManager:
    """Manager for multiple memory integrators across tenants."""

    def __init__(self):
        """Initialize memory integration manager."""
        self.integrators: dict[str, MemoryIntegrator] = {}

    def get_integrator(self, tenant_context: TenantContext) -> MemoryIntegrator:
        """Get or create memory integrator for tenant.

        Args:
            tenant_context: Tenant context

        Returns:
            Memory integrator for the tenant
        """
        key = f"{tenant_context.tenant}:{tenant_context.workspace}"

        if key not in self.integrators:
            self.integrators[key] = MemoryIntegrator(tenant_context)

        return self.integrators[key]

    def cleanup_tenant(self, tenant_context: TenantContext) -> StepResult:
        """Clean up memory integrator for tenant.

        Args:
            tenant_context: Tenant context

        Returns:
            StepResult with cleanup results
        """
        try:
            key = f"{tenant_context.tenant}:{tenant_context.workspace}"

            if key in self.integrators:
                # Perform cleanup operations
                integrator = self.integrators[key]
                cleanup_result = integrator.get_memory_stats()

                # Remove from manager
                del self.integrators[key]

                return StepResult.ok(
                    data={
                        "cleanup_completed": True,
                        "final_stats": cleanup_result.data if cleanup_result.success else None,
                        "tenant": tenant_context.tenant,
                        "workspace": tenant_context.workspace,
                    }
                )
            else:
                return StepResult.ok(
                    data={
                        "cleanup_completed": True,
                        "message": "No integrator found for tenant",
                        "tenant": tenant_context.tenant,
                        "workspace": tenant_context.workspace,
                    }
                )

        except Exception as e:
            logger.error(f"Failed to cleanup tenant: {e}")
            return StepResult.fail(f"Tenant cleanup failed: {e!s}")


# Global memory integration manager
_memory_manager = MemoryIntegrationManager()


def get_memory_integrator(tenant_context: TenantContext) -> MemoryIntegrator:
    """Get memory integrator for tenant.

    Args:
        tenant_context: Tenant context

    Returns:
        Memory integrator for the tenant
    """
    return _memory_manager.get_integrator(tenant_context)


def cleanup_tenant_memory(tenant_context: TenantContext) -> StepResult:
    """Clean up memory for tenant.

    Args:
        tenant_context: Tenant context

    Returns:
        StepResult with cleanup results
    """
    return _memory_manager.cleanup_tenant(tenant_context)
