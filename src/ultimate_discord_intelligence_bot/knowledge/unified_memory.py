"""Unified Memory Service - Single interface for all memory backends

This service consolidates all memory implementations into a single, coherent
interface that provides agents with access to the complete knowledge graph
while maintaining tenant isolation and performance optimization.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant


# Import existing memory implementations
try:
    from memory.api import retrieve as memory_retrieve
    from memory.api import store as memory_store
    from memory.qdrant_provider import get_qdrant_client
    from memory.store import MemoryStore
    from memory.vector_store import VectorStore
except ImportError:
    memory_store = None
    memory_retrieve = None
    MemoryStore = None
    VectorStore = None
    get_qdrant_client = None

# Import semantic cache
try:
    from core.cache.semantic_cache import get_semantic_cache
except ImportError:
    get_semantic_cache = None

# Import mem0 service
try:
    from ultimate_discord_intelligence_bot.services.mem0_service import (
        Mem0MemoryService,
    )
    from ultimate_discord_intelligence_bot.tools.mem0_memory_tool import Mem0MemoryTool
except ImportError:
    Mem0MemoryService = None
    Mem0MemoryTool = None

logger = logging.getLogger(__name__)


@dataclass
class MemoryResult:
    """Result from unified memory operations"""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"  # Which backend provided this result
    confidence: float = 1.0
    timestamp: float | None = None
    tenant_id: str = "default"
    workspace_id: str = "main"


@dataclass
class UnifiedMemoryConfig:
    """Configuration for unified memory service"""

    enable_vector_store: bool = True
    enable_sqlite_store: bool = True
    enable_semantic_cache: bool = True
    enable_mem0: bool = False  # Optional external knowledge graph
    vector_similarity_threshold: float = 0.7
    max_results_per_backend: int = 50
    deduplication_enabled: bool = True


class UnifiedMemoryService:
    """Unified interface to all memory backends with tenant isolation"""

    def __init__(self, config: UnifiedMemoryConfig | None = None):
        self.config = config or UnifiedMemoryConfig()
        self._initialized = False
        self._backends = {}

        # Initialize backends based on configuration
        self._initialize_backends()

    def _initialize_backends(self) -> None:
        """Initialize all configured memory backends"""
        try:
            # Vector Store (Qdrant)
            if self.config.enable_vector_store and get_qdrant_client:
                try:
                    self._backends["vector"] = get_qdrant_client()
                    logger.info("Vector store backend initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize vector store: {e}")

            # SQLite Memory Store
            if self.config.enable_sqlite_store and MemoryStore:
                try:
                    self._backends["sqlite"] = MemoryStore()
                    logger.info("SQLite memory store backend initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize SQLite store: {e}")

            # Semantic Cache
            if self.config.enable_semantic_cache and get_semantic_cache:
                try:
                    self._backends["semantic"] = get_semantic_cache()
                    logger.info("Semantic cache backend initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize semantic cache: {e}")

            # Mem0 External Knowledge Graph (optional)
            if self.config.enable_mem0 and Mem0MemoryService:
                try:
                    self._backends["mem0"] = Mem0MemoryService()
                    logger.info("Mem0 knowledge graph backend initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Mem0: {e}")

            self._initialized = True
            logger.info(f"Unified memory service initialized with {len(self._backends)} backends")

        except Exception as e:
            logger.error(f"Failed to initialize unified memory service: {e}")
            self._initialized = False

    async def store(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
        namespace: str | None = None,
    ) -> StepResult:
        """Store content across all configured backends atomically"""
        try:
            if not self._initialized:
                return StepResult.fail("Unified memory service not initialized")

            # Resolve tenant context
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"

            # Create namespace for tenant isolation
            if namespace is None:
                # Create a simple namespace string instead of using mem_ns
                namespace = f"{tenant_id}:{workspace_id}"

            metadata = metadata or {}
            metadata.update(
                {
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                    "namespace": namespace,
                    "timestamp": asyncio.get_event_loop().time(),
                }
            )

            # Store in all backends concurrently
            store_tasks = []
            backend_results = {}

            # Vector Store
            if "vector" in self._backends and memory_store:
                task = self._store_vector(content, metadata, namespace)
                store_tasks.append(("vector", task))

            # SQLite Store
            if "sqlite" in self._backends:
                task = self._store_sqlite(content, metadata, namespace)
                store_tasks.append(("sqlite", task))

            # Semantic Cache
            if "semantic" in self._backends:
                task = self._store_semantic(content, metadata, namespace)
                store_tasks.append(("semantic", task))

            # Mem0 (optional)
            if "mem0" in self._backends:
                task = self._store_mem0(content, metadata, namespace)
                store_tasks.append(("mem0", task))

            # Execute all stores concurrently
            if store_tasks:
                results = await asyncio.gather(*[task for _, task in store_tasks], return_exceptions=True)

                for i, (backend_name, _) in enumerate(store_tasks):
                    result = results[i]
                    if isinstance(result, Exception):
                        logger.warning(f"Failed to store in {backend_name}: {result}")
                        backend_results[backend_name] = False
                    else:
                        backend_results[backend_name] = True
                        logger.debug(f"Successfully stored in {backend_name}")

            # Return success if at least one backend succeeded
            successful_backends = [name for name, success in backend_results.items() if success]
            if successful_backends:
                return StepResult.ok(
                    data={
                        "stored_backends": successful_backends,
                        "total_backends": len(self._backends),
                        "namespace": namespace,
                        "metadata": metadata,
                    }
                )
            else:
                return StepResult.fail("Failed to store in any backend")

        except Exception as e:
            logger.error(f"Error in unified store: {e}", exc_info=True)
            return StepResult.fail(f"Unified store failed: {e!s}")

    async def retrieve(
        self,
        query: str,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> StepResult:
        """Retrieve from all backends and merge results"""
        try:
            if not self._initialized:
                return StepResult.fail("Unified memory service not initialized")

            # Resolve tenant context
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"

            namespace = f"{tenant_id}:{workspace_id}"
            filters = filters or {}

            # Retrieve from all backends concurrently
            retrieve_tasks = []

            # Vector Store
            if "vector" in self._backends and memory_retrieve:
                task = self._retrieve_vector(query, namespace, filters, limit)
                retrieve_tasks.append(("vector", task))

            # SQLite Store
            if "sqlite" in self._backends:
                task = self._retrieve_sqlite(query, namespace, filters, limit)
                retrieve_tasks.append(("sqlite", task))

            # Semantic Cache
            if "semantic" in self._backends:
                task = self._retrieve_semantic(query, namespace, filters, limit)
                retrieve_tasks.append(("semantic", task))

            # Mem0 (optional)
            if "mem0" in self._backends:
                task = self._retrieve_mem0(query, namespace, filters, limit)
                retrieve_tasks.append(("mem0", task))

            # Execute all retrievals concurrently
            all_results = []
            if retrieve_tasks:
                results = await asyncio.gather(*[task for _, task in retrieve_tasks], return_exceptions=True)

                for i, (backend_name, _) in enumerate(retrieve_tasks):
                    result = results[i]
                    if isinstance(result, Exception):
                        logger.warning(f"Failed to retrieve from {backend_name}: {result}")
                        continue

                    if result and hasattr(result, "success") and result.success:
                        backend_results = result.data or []
                        for item in backend_results:
                            if isinstance(item, dict):
                                all_results.append(
                                    MemoryResult(
                                        content=item.get("content", ""),
                                        metadata=item.get("metadata", {}),
                                        source=backend_name,
                                        confidence=item.get("confidence", 1.0),
                                        timestamp=item.get("timestamp"),
                                        tenant_id=tenant_id,
                                        workspace_id=workspace_id,
                                    )
                                )

            # Deduplicate and rank results
            if self.config.deduplication_enabled:
                all_results = self._deduplicate_results(all_results)

            # Sort by confidence and relevance
            all_results = sorted(all_results, key=lambda x: x.confidence, reverse=True)

            # Limit results
            final_results = all_results[:limit]

            return StepResult.ok(
                data={
                    "results": final_results,
                    "total_found": len(all_results),
                    "returned": len(final_results),
                    "backends_queried": len(retrieve_tasks),
                    "namespace": namespace,
                }
            )

        except Exception as e:
            logger.error(f"Error in unified retrieve: {e}", exc_info=True)
            return StepResult.fail(f"Unified retrieve failed: {e!s}")

    async def _store_vector(self, content: str, metadata: dict[str, Any], namespace: str) -> bool:
        """Store content in vector store"""
        try:
            if not memory_store:
                return False

            # Use the existing memory API
            result = await memory_store(
                store=self._backends.get("sqlite"),
                vstore=self._backends["vector"],
                tenant=metadata.get("tenant_id", "default"),
                workspace=metadata.get("workspace_id", "main"),
                text=content,
                item_type="long",
                policy="default",
            )
            return result is not None
        except Exception as e:
            logger.debug(f"Vector store failed: {e}")
            return False

    async def _store_sqlite(self, content: str, metadata: dict[str, Any], namespace: str) -> bool:
        """Store content in SQLite store"""
        try:
            store = self._backends["sqlite"]
            store.add(content, metadata, namespace)
            return True
        except Exception as e:
            logger.debug(f"SQLite store failed: {e}")
            return False

    async def _store_semantic(self, content: str, metadata: dict[str, Any], namespace: str) -> bool:
        """Store content in semantic cache"""
        try:
            cache = self._backends["semantic"]
            if hasattr(cache, "set"):
                # Run in thread if sync
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, cache.set, content, "unified", content, namespace)
            return True
        except Exception as e:
            logger.debug(f"Semantic cache store failed: {e}")
            return False

    async def _store_mem0(self, content: str, metadata: dict[str, Any], namespace: str) -> bool:
        """Store content in Mem0 knowledge graph"""
        try:
            mem0 = self._backends["mem0"]
            # Mem0 typically uses async methods
            if hasattr(mem0, "add_memory"):
                await mem0.add_memory(content, metadata)
            return True
        except Exception as e:
            logger.debug(f"Mem0 store failed: {e}")
            return False

    async def _retrieve_vector(self, query: str, namespace: str, filters: dict[str, Any], limit: int) -> StepResult:
        """Retrieve from vector store"""
        try:
            if not memory_retrieve:
                return StepResult.fail("Vector retrieve not available")

            result = await memory_retrieve(
                store=self._backends.get("sqlite"),
                vstore=self._backends["vector"],
                tenant=namespace.split(":")[0] if ":" in namespace else "default",
                workspace=namespace.split(":")[1] if ":" in namespace else "main",
                query=query,
            )

            return StepResult.ok(data=result)
        except Exception as e:
            logger.debug(f"Vector retrieve failed: {e}")
            return StepResult.fail(str(e))

    async def _retrieve_sqlite(self, query: str, namespace: str, filters: dict[str, Any], limit: int) -> StepResult:
        """Retrieve from SQLite store"""
        try:
            store = self._backends["sqlite"]
            # Simple text search in SQLite
            results = []
            for memory in store.memories:
                if query.lower() in memory.get("text", "").lower():
                    results.append(
                        {
                            "content": memory.get("text", ""),
                            "metadata": memory.get("metadata", {}),
                            "confidence": 0.8,  # Lower confidence for text search
                        }
                    )

            return StepResult.ok(data=results[:limit])
        except Exception as e:
            logger.debug(f"SQLite retrieve failed: {e}")
            return StepResult.fail(str(e))

    async def _retrieve_semantic(self, query: str, namespace: str, filters: dict[str, Any], limit: int) -> StepResult:
        """Retrieve from semantic cache"""
        try:
            cache = self._backends["semantic"]
            if hasattr(cache, "get"):
                # Run in thread if sync
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, cache.get, query, "unified", namespace)
                if result:
                    return StepResult.ok(
                        data=[
                            {
                                "content": result.get("response", ""),
                                "metadata": result.get("metadata", {}),
                                "confidence": result.get("similarity", 0.9),
                            }
                        ]
                    )
            return StepResult.ok(data=[])
        except Exception as e:
            logger.debug(f"Semantic cache retrieve failed: {e}")
            return StepResult.fail(str(e))

    async def _retrieve_mem0(self, query: str, namespace: str, filters: dict[str, Any], limit: int) -> StepResult:
        """Retrieve from Mem0 knowledge graph"""
        try:
            mem0 = self._backends["mem0"]
            if hasattr(mem0, "search_memories"):
                results = await mem0.search_memories(query, limit=limit)
                return StepResult.ok(data=results)
            return StepResult.ok(data=[])
        except Exception as e:
            logger.debug(f"Mem0 retrieve failed: {e}")
            return StepResult.fail(str(e))

    def _deduplicate_results(self, results: list[MemoryResult]) -> list[MemoryResult]:
        """Remove duplicate results based on content similarity"""
        if not results:
            return results

        unique_results = []
        seen_content = set()

        for result in results:
            # Simple deduplication by content hash
            content_hash = hash(result.content)
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)

        return unique_results

    def get_backend_status(self) -> dict[str, bool]:
        """Get status of all backends"""
        return {
            "initialized": self._initialized,
            "backends": dict.fromkeys(self._backends.keys(), True),
            "config": {
                "vector_store": self.config.enable_vector_store,
                "sqlite_store": self.config.enable_sqlite_store,
                "semantic_cache": self.config.enable_semantic_cache,
                "mem0": self.config.enable_mem0,
            },
        }
