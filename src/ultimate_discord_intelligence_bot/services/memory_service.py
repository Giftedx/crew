"""Enhanced memory service with vector database support.

The :class:`MemoryService` provides vector-based storage and retrieval capabilities
for the multi-agent orchestration system, supporting caching, RAG enrichment,
and session continuity.
"""

from __future__ import annotations

import asyncio
import logging
import time
from copy import deepcopy
from dataclasses import dataclass, field
from platform.config.flags import enabled
from typing import Any

import yaml
from domains.memory.vector.qdrant import get_qdrant_client

from ..observability.stepresult_observer import observe_step_result
from ..step_result import StepResult
from ..tenancy.context import TenantContext, current_tenant, mem_ns
from ..tenancy.helpers import require_tenant


@dataclass
class MemoryService:
    """Enhanced memory service with vector database support."""

    memories: list[dict[str, Any]] = field(default_factory=list)
    qdrant_client: Any | None = None
    embedding_service: Any | None = None
    requests_collection: str = "requests"
    artifacts_collection: str = "artifacts"
    cache_hits_collection: str = "cache_hits"
    similarity_threshold: float = 0.85
    max_results: int = 50
    cache_ttl_hours: int = 24

    def __post_init__(self):
        """Initialize vector database components."""
        if self.qdrant_client is None:
            self._initialize_qdrant()
        if self.embedding_service is None:
            try:
                from .embedding_service import create_embedding_service as _create_embedding_service

                self.embedding_service = _create_embedding_service()
            except Exception as exc:
                logging.getLogger(__name__).debug("Embedding service unavailable: %s", exc)
                self.embedding_service = None

    def _initialize_qdrant(self) -> None:
        """Initialize Qdrant client and collections."""
        try:
            self.qdrant_client = get_qdrant_client()
            self._load_collection_config()
            self._ensure_collections_exist()
        except Exception as e:
            logging.error("Failed to initialize Qdrant client: %s", str(e))
            self.qdrant_client = None

    def _load_collection_config(self) -> None:
        """Load collection configuration from YAML file."""
        try:
            from pathlib import Path

            config_path = Path("config/qdrant_collections.yaml")
            if config_path.exists():
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                if "collections" in config:
                    collections = config["collections"]
                    self.requests_collection = collections.get("requests", {}).get("name", "requests")
                    self.artifacts_collection = collections.get("artifacts", {}).get("name", "artifacts")
                    self.cache_hits_collection = collections.get("cache_hits", {}).get("name", "cache_hits")
                if "metadata" in config:
                    metadata = config["metadata"]
                    self.cache_ttl_hours = metadata.get("cache_ttl_hours", 24)
                if "performance" in config:
                    perf = config["performance"]
                    self.similarity_threshold = perf.get("similarity_threshold", 0.85)
                    self.max_results = perf.get("max_results", 50)
        except Exception as e:
            logging.warning("Failed to load collection config: %s", str(e))

    def _ensure_collections_exist(self) -> None:
        """Ensure all required collections exist in Qdrant."""
        if not self.qdrant_client:
            return
        try:
            collections = self.qdrant_client.get_collections()
            existing_names = {col.name for col in collections.collections}
            collections_to_create = [self.requests_collection, self.artifacts_collection, self.cache_hits_collection]
            for collection_name in collections_to_create:
                if collection_name not in existing_names:
                    self._create_collection(collection_name)
        except Exception as e:
            logging.error("Failed to ensure collections exist: %s", str(e))

    def _create_collection(self, collection_name: str) -> None:
        """Create a new collection in Qdrant."""
        if not self.qdrant_client:
            return
        try:
            dimension = self.embedding_service.get_embedding_dimension() if self.embedding_service else 1536
            try:
                from qdrant_client.http import models as _qmodels

                vec_cfg = _qmodels.VectorParams(size=dimension, distance=_qmodels.Distance.COSINE)
            except Exception:
                try:
                    from qdrant_client import models as _legacy_models

                    vec_cfg = _legacy_models.VectorParams(
                        size=dimension, distance=getattr(_legacy_models.Distance, "COSINE", "Cosine")
                    )
                except Exception:
                    vec_cfg = {"size": dimension, "distance": "Cosine"}
            try:
                self.qdrant_client.create_collection(
                    collection_name=collection_name, vectors_config=vec_cfg, on_disk_payload=True
                )
            except TypeError:
                self.qdrant_client.create_collection(collection_name=collection_name, vectors_config=vec_cfg)
            logging.info("Created collection: %s", collection_name)
        except Exception as e:
            logging.error("Failed to create collection %s: %s", collection_name, str(e))

    def _get_tenant_collection_name(self, base_collection: str, tenant: str, workspace: str) -> str:
        """Get tenant-aware collection name."""
        return f"{tenant}_{workspace}_{base_collection}"

    async def cache_lookup(
        self, request: str, tenant: str, workspace: str, similarity_threshold: float | None = None
    ) -> StepResult:
        """Look up cached results for a request.

        Args:
            request: Request text to search for
            tenant: Tenant identifier
            workspace: Workspace identifier
            similarity_threshold: Minimum similarity for cache hit

        Returns:
            StepResult containing cached result or None if no hit
        """
        try:
            if not self.qdrant_client or not self.embedding_service:
                return StepResult.ok(data=None)
            embedding_result = await self.embedding_service.generate_embedding(request, tenant, workspace)
            if not embedding_result.success:
                return StepResult.fail(f"Failed to generate embedding: {embedding_result.error}")
            collection_name = self._get_tenant_collection_name(self.cache_hits_collection, tenant, workspace)
            threshold = similarity_threshold or self.similarity_threshold
            embedding_vector: list[float] = embedding_result.data if isinstance(embedding_result.data, list) else []
            search_result = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=embedding_vector,
                limit=1,
                score_threshold=threshold,
                with_payload=True,
            )
            if search_result:
                hit = search_result[0]
                payload = hit.payload or {}
                if "timestamp" in payload:
                    age_hours = (time.time() - payload["timestamp"]) / 3600
                    if age_hours > self.cache_ttl_hours:
                        return StepResult.ok(data=None)
                return StepResult.ok(
                    data={
                        "content": payload.get("content"),
                        "metadata": payload.get("metadata", {}),
                        "score": hit.score,
                        "id": hit.id,
                    }
                )
            return StepResult.ok(data=None)
        except Exception as e:
            logging.error("Cache lookup failed: %s", str(e))
            return StepResult.fail(f"Cache lookup failed: {e!s}")

    async def store_artifact(self, content: str, metadata: dict[str, Any], tenant: str, workspace: str) -> StepResult:
        """Store an artifact with embedding.

        Args:
            content: Artifact content
            metadata: Artifact metadata
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult indicating success or failure
        """
        try:
            if not self.qdrant_client or not self.embedding_service:
                return StepResult.fail("Vector database not available")
            embedding_result = await self.embedding_service.generate_embedding(content, tenant, workspace)
            if not embedding_result.success:
                return StepResult.fail(f"Failed to generate embedding: {embedding_result.error}")
            collection_name = self._get_tenant_collection_name(self.artifacts_collection, tenant, workspace)
            point_id = int(time.time() * 1000)
            try:
                from qdrant_client.http import models as _qmodels

                point_struct = _qmodels.PointStruct(
                    id=point_id,
                    vector=embedding_result.data,
                    payload={
                        "content": content,
                        "metadata": metadata,
                        "timestamp": time.time(),
                        "tenant": tenant,
                        "workspace": workspace,
                    },
                )
            except Exception:
                try:
                    from qdrant_client import models as _legacy_models

                    point_struct = _legacy_models.PointStruct(
                        id=point_id,
                        vector=embedding_result.data,
                        payload={
                            "content": content,
                            "metadata": metadata,
                            "timestamp": time.time(),
                            "tenant": tenant,
                            "workspace": workspace,
                        },
                    )
                except Exception:
                    point_struct = {
                        "id": point_id,
                        "vector": embedding_result.data,
                        "payload": {
                            "content": content,
                            "metadata": metadata,
                            "timestamp": time.time(),
                            "tenant": tenant,
                            "workspace": workspace,
                        },
                    }
            self.qdrant_client.upsert(collection_name=collection_name, points=[point_struct])
            logging.debug(
                "Stored artifact (tenant: %s, workspace: %s, content_length: %d)", tenant, workspace, len(content)
            )
            return StepResult.ok(data={"id": point_id})
        except Exception as e:
            logging.error("Failed to store artifact: %s", str(e))
            return StepResult.fail(f"Failed to store artifact: {e!s}")

    async def retrieve_context(self, query: str, top_k: int, tenant: str, workspace: str) -> StepResult:
        """Retrieve relevant context for RAG enrichment.

        Args:
            query: Query text
            top_k: Number of results to return
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult containing list of relevant artifacts
        """
        try:
            if not self.qdrant_client or not self.embedding_service:
                return StepResult.fail("Vector database not available")
            embedding_result = await self.embedding_service.generate_embedding(query, tenant, workspace)
            if not embedding_result.success:
                return StepResult.fail(f"Failed to generate embedding: {embedding_result.error}")
            collection_name = self._get_tenant_collection_name(self.artifacts_collection, tenant, workspace)
            embedding_vector: list[float] = embedding_result.data if isinstance(embedding_result.data, list) else []
            search_result = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=embedding_vector,
                limit=min(top_k, self.max_results),
                score_threshold=self.similarity_threshold,
                with_payload=True,
            )
            results = []
            for hit in search_result:
                payload = hit.payload or {}
                results.append(
                    {
                        "content": payload.get("content"),
                        "metadata": payload.get("metadata", {}),
                        "score": hit.score,
                        "id": hit.id,
                    }
                )
            return StepResult.ok(data=results)
        except Exception as e:
            logging.error("Context retrieval failed: %s", str(e))
            return StepResult.fail(f"Context retrieval failed: {e!s}")

    async def store_cache_hit(self, request: str, response: dict[str, Any], tenant: str, workspace: str) -> StepResult:
        """Store a cache hit for future lookups.

        Args:
            request: Original request text
            response: Cached response
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult indicating success or failure
        """
        try:
            if not self.qdrant_client or not self.embedding_service:
                return StepResult.fail("Vector database not available")
            embedding_result = await self.embedding_service.generate_embedding(request, tenant, workspace)
            if not embedding_result.success:
                return StepResult.fail(f"Failed to generate embedding: {embedding_result.error}")
            collection_name = self._get_tenant_collection_name(self.cache_hits_collection, tenant, workspace)
            point_id = int(time.time() * 1000)
            try:
                from qdrant_client.http import models as _qmodels

                point_struct = _qmodels.PointStruct(
                    id=point_id,
                    vector=embedding_result.data,
                    payload={
                        "request": request,
                        "response": response,
                        "timestamp": time.time(),
                        "tenant": tenant,
                        "workspace": workspace,
                    },
                )
            except Exception:
                try:
                    from qdrant_client import models as _legacy_models

                    point_struct = _legacy_models.PointStruct(
                        id=point_id,
                        vector=embedding_result.data,
                        payload={
                            "request": request,
                            "response": response,
                            "timestamp": time.time(),
                            "tenant": tenant,
                            "workspace": workspace,
                        },
                    )
                except Exception:
                    point_struct = {
                        "id": point_id,
                        "vector": embedding_result.data,
                        "payload": {
                            "request": request,
                            "response": response,
                            "timestamp": time.time(),
                            "tenant": tenant,
                            "workspace": workspace,
                        },
                    }
            self.qdrant_client.upsert(collection_name=collection_name, points=[point_struct])
            logging.debug("Stored cache hit (tenant: %s, workspace: %s)", tenant, workspace)
            return StepResult.ok(data={"id": point_id})
        except Exception as e:
            logging.error("Failed to store cache hit: %s", str(e))
            return StepResult.fail(f"Failed to store cache hit: {e!s}")

    @require_tenant(strict_flag_enabled=False)
    @observe_step_result(tool_name="memory_service.add")
    def add(self, text: str, metadata: dict[str, Any] | None = None, namespace: str | None = None) -> StepResult:
        """Store a text snippet with optional metadata and namespace.

        This method maintains backward compatibility with the original
        in-memory storage while also storing in vector database.
        """
        from ..privacy import privacy_filter

        clean_text, _report = privacy_filter.filter_text(text, metadata or {})
        ctx = current_tenant()
        if ctx is None:
            if enabled("ENABLE_TENANCY_STRICT", False) or enabled("ENABLE_INGEST_STRICT", False):
                raise RuntimeError("TenantContext required but not set (strict mode)")
            logging.getLogger("tenancy").warning(
                "TenantContext missing; defaulting to 'default:main' namespace (non-strict mode)"
            )
            try:
                pass
            except Exception as exc:
                logging.debug("tenancy metric increment failed: %s", exc)
            ctx = TenantContext("default", "main")
        ns = namespace or mem_ns(ctx, "mem")
        self.memories.append({"namespace": ns, "text": clean_text, "metadata": deepcopy(metadata) or {}})
        if self.qdrant_client and self.embedding_service:
            task = asyncio.create_task(
                self._async_store_text(clean_text, metadata or {}, ctx.tenant_id, ctx.workspace_id)
            )
            _ = task
        return StepResult.ok(data={"stored": True})

    async def _async_store_text(self, text: str, metadata: dict[str, Any], tenant: str, workspace: str) -> None:
        """Asynchronously store text in vector database."""
        try:
            await self.store_artifact(text, metadata, tenant, workspace)
        except Exception as e:
            logging.warning("Failed to store text in vector database: %s", str(e))

    @require_tenant(strict_flag_enabled=False)
    @observe_step_result(tool_name="memory_service.retrieve")
    def retrieve(
        self, query: str, limit: int = 5, metadata: dict[str, Any] | None = None, namespace: str | None = None
    ) -> StepResult:
        """Return stored memories matching query within namespace.

        This method maintains backward compatibility with the original
        in-memory retrieval while also supporting vector search.
        """
        query_norm = query.strip().lower()
        if limit < 1 or not query_norm:
            return StepResult.ok(data=[])
        ctx = current_tenant()
        if ctx is None:
            if enabled("ENABLE_TENANCY_STRICT", False) or enabled("ENABLE_INGEST_STRICT", False):
                raise RuntimeError("TenantContext required but not set (strict mode)")
            logging.getLogger("tenancy").warning(
                "TenantContext missing; defaulting to 'default:main' namespace (non-strict mode)"
            )
            try:
                pass
            except Exception as exc:
                logging.debug("tenancy metric increment failed: %s", exc)
            ctx = TenantContext("default", "main")
        ns = namespace or mem_ns(ctx, "mem")
        import time as _t

        phase_start = _t.perf_counter()
        results = [m for m in self.memories if m.get("namespace") == ns and query_norm in m["text"].lower()]
        _ = (_t.perf_counter() - phase_start) * 1000.0
        if metadata:
            lowered = {str(k).lower(): str(v).lower() for k, v in metadata.items()}
            filtered: list[dict[str, Any]] = []
            for m in results:
                meta_lower = {str(mk).lower(): str(mv).lower() for mk, mv in m["metadata"].items()}
                if all((meta_lower.get(k, "") == v for k, v in lowered.items())):
                    filtered.append(m)
            results = filtered
        sanitized = []
        for m in results[:limit]:
            copy = deepcopy(m)
            copy.pop("namespace", None)
            sanitized.append(copy)
        return StepResult.ok(data=sanitized)
