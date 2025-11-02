"""Creator Intelligence Collection Management for Vector Database.

This module provides specialized collection schemas and management for the
Creator Intelligence system, building on the existing VectorStore infrastructure.

Collections:
- creator_episodes: Video/stream episodes with platform metadata
- creator_segments: Timestamped segments within episodes
- creator_claims: Factual claims with verification status
- creator_quotes: Notable quotes with speaker attribution
- creator_topics: Topic embeddings for narrative tracking

All collections support:
- Tenant-aware namespacing
- Semantic caching (similarity > 0.95)
- Multi-modal RAG payloads
- Durable agent memory
"""

from __future__ import annotations
import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal
from memory.enhanced_vector_store import EnhancedVectorStore, SearchResult
from platform.core.step_result import StepResult

if TYPE_CHECKING:
    from qdrant_client.http import models as _qmodels
else:
    _qmodels = Any
logger = logging.getLogger(__name__)
EMBEDDING_DIMENSIONS = {
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "sentence-transformers/all-mpnet-base-v2": 768,
    "openai/text-embedding-3-small": 1536,
    "openai/text-embedding-3-large": 3072,
}
CACHE_SIMILARITY_THRESHOLD = 0.95
try:
    from platform.cache.unified_config import get_unified_cache_config

    CACHE_TTL_SECONDS = int(get_unified_cache_config().get_ttl_for_domain("analysis"))
except Exception:
    CACHE_TTL_SECONDS = 3600


@dataclass
class CollectionConfig:
    """Configuration for a creator intelligence collection."""

    name: str
    description: str
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    enable_quantization: bool = True
    enable_sparse_vectors: bool = False
    enable_semantic_cache: bool = True
    payload_schema: dict[str, str] = field(default_factory=dict)

    @property
    def dimension(self) -> int:
        """Get embedding dimension for the configured model."""
        return EMBEDDING_DIMENSIONS.get(self.embedding_model, 384)


COLLECTION_CONFIGS = {
    "episodes": CollectionConfig(
        name="creator_episodes",
        description="Full episodes/videos with platform metadata",
        embedding_model="sentence-transformers/all-mpnet-base-v2",
        enable_quantization=True,
        enable_sparse_vectors=True,
        payload_schema={
            "content_type": "string",
            "platform": "string",
            "creator_id": "string",
            "episode_id": "string",
            "title": "string",
            "published_at": "datetime",
            "duration_seconds": "integer",
            "url": "string",
            "thumbnail_url": "string",
            "view_count": "integer",
            "tenant": "string",
            "workspace": "string",
        },
    ),
    "segments": CollectionConfig(
        name="creator_segments",
        description="Timestamped segments within episodes",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        enable_quantization=True,
        payload_schema={
            "content_type": "string",
            "episode_id": "string",
            "segment_id": "string",
            "start_time_seconds": "integer",
            "end_time_seconds": "integer",
            "title": "string",
            "segment_type": "string",
            "speaker": "string",
            "text": "string",
            "tenant": "string",
            "workspace": "string",
        },
    ),
    "claims": CollectionConfig(
        name="creator_claims",
        description="Factual claims with verification status",
        embedding_model="sentence-transformers/all-mpnet-base-v2",
        enable_quantization=False,
        enable_sparse_vectors=True,
        payload_schema={
            "content_type": "string",
            "claim_id": "string",
            "text": "string",
            "speaker": "string",
            "episode_id": "string",
            "timestamp_seconds": "integer",
            "verification_status": "string",
            "confidence_score": "float",
            "sources": "json",
            "tenant": "string",
            "workspace": "string",
        },
    ),
    "quotes": CollectionConfig(
        name="creator_quotes",
        description="Notable quotes with speaker attribution",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        enable_quantization=True,
        payload_schema={
            "content_type": "string",
            "quote_id": "string",
            "text": "string",
            "speaker": "string",
            "episode_id": "string",
            "timestamp_seconds": "integer",
            "context": "string",
            "tenant": "string",
            "workspace": "string",
        },
    ),
    "topics": CollectionConfig(
        name="creator_topics",
        description="Topic embeddings for narrative tracking",
        embedding_model="sentence-transformers/all-mpnet-base-v2",
        enable_quantization=True,
        enable_sparse_vectors=True,
        payload_schema={
            "content_type": "string",
            "topic_id": "string",
            "name": "string",
            "category": "string",
            "first_mention": "datetime",
            "last_mention": "datetime",
            "mention_count": "integer",
            "episodes": "json",
            "tenant": "string",
            "workspace": "string",
        },
    ),
}


@dataclass
class CachedQuery:
    """Cached query result for semantic caching."""

    query_hash: str
    query_embedding: list[float]
    results: list[SearchResult]
    cache_time: float
    ttl_seconds: float = CACHE_TTL_SECONDS

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.cache_time > self.ttl_seconds


class CreatorIntelligenceCollectionManager:
    """Manages specialized collections for the Creator Intelligence system.

    Features:
    - Automatic collection initialization with optimal settings
    - Semantic caching for query deduplication
    - Multi-modal RAG payload support
    - Tenant-aware namespace management
    - Durable agent memory persistence
    """

    def __init__(self, vector_store: EnhancedVectorStore | None = None, enable_semantic_cache: bool = True):
        """Initialize the collection manager.

        Args:
            vector_store: Enhanced vector store instance (creates one if not provided)
            enable_semantic_cache: Enable semantic query caching
        """
        self.vector_store = vector_store or EnhancedVectorStore()
        self.enable_semantic_cache = enable_semantic_cache
        self._query_cache: dict[str, CachedQuery] = {}
        self._initialized_collections: set[str] = set()

    def initialize_collections(self, tenant: str, workspace: str) -> StepResult:
        """Initialize all creator intelligence collections for a tenant/workspace.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with initialization status
        """
        try:
            initialized = []
            failed = []
            for _collection_type, config in COLLECTION_CONFIGS.items():
                namespace = self._get_namespace(tenant, workspace, config.name)
                if namespace in self._initialized_collections:
                    logger.info(f"Collection {namespace} already initialized")
                    continue
                success = self.vector_store.create_collection_with_hybrid_config(
                    namespace=namespace,
                    dimension=config.dimension,
                    enable_sparse=config.enable_sparse_vectors,
                    quantization=config.enable_quantization,
                )
                if success:
                    initialized.append(namespace)
                    self._initialized_collections.add(namespace)
                    logger.info(f"✅ Initialized collection: {namespace}")
                else:
                    failed.append(namespace)
                    logger.warning(f"❌ Failed to initialize collection: {namespace}")
            if failed:
                return StepResult.fail(
                    f"Some collections failed to initialize: {', '.join(failed)}",
                    metadata={"initialized": initialized, "failed": failed},
                )
            return StepResult.ok(
                data={
                    "initialized": initialized,
                    "total": len(initialized),
                    "collections": list(COLLECTION_CONFIGS.keys()),
                }
            )
        except Exception as e:
            logger.error(f"Collection initialization failed: {e}")
            return StepResult.fail(f"Collection initialization failed: {e!s}")

    def query_with_cache(
        self,
        collection_type: Literal["episodes", "segments", "claims", "quotes", "topics"],
        query_embedding: list[float],
        query_text: str,
        tenant: str,
        workspace: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        filter_conditions: dict[str, Any] | None = None,
        bypass_cache: bool = False,
    ) -> StepResult:
        """Query collection with semantic caching.

        Args:
            collection_type: Type of collection to query
            query_embedding: Query vector embedding
            query_text: Original query text for sparse search
            tenant: Tenant identifier
            workspace: Workspace identifier
            limit: Maximum results to return
            score_threshold: Minimum similarity score
            filter_conditions: Optional payload filters
            bypass_cache: Force fresh query, skip cache

        Returns:
            StepResult with search results and cache metadata
        """
        try:
            if collection_type not in COLLECTION_CONFIGS:
                return StepResult.fail(f"Invalid collection type: {collection_type}", status="bad_request")
            config = COLLECTION_CONFIGS[collection_type]
            namespace = self._get_namespace(tenant, workspace, config.name)
            if not bypass_cache and self.enable_semantic_cache:
                cache_result = self._check_semantic_cache(query_embedding, namespace, limit)
                if cache_result:
                    logger.info(f"✅ Semantic cache hit for {namespace}")
                    return StepResult.ok(
                        data={
                            "results": [r.__dict__ for r in cache_result.results],
                            "cache_hit": True,
                            "cache_age_seconds": time.time() - cache_result.cache_time,
                        }
                    )
            results = self.vector_store.hybrid_search(
                namespace=namespace,
                query_vector=query_embedding,
                query_text=query_text,
                limit=limit,
                score_threshold=score_threshold,
                filter_conditions=filter_conditions,
            )
            if self.enable_semantic_cache and results:
                self._cache_query_results(query_embedding, namespace, results, limit)
            return StepResult.ok(
                data={"results": [r.__dict__ for r in results], "cache_hit": False, "result_count": len(results)}
            )
        except Exception as e:
            logger.error(f"Query failed for {collection_type}: {e}")
            return StepResult.fail(f"Query failed: {e!s}", status="retryable")

    def _check_semantic_cache(self, query_embedding: list[float], namespace: str, limit: int) -> CachedQuery | None:
        """Check if a semantically similar query exists in cache.

        Args:
            query_embedding: Query vector
            namespace: Collection namespace
            limit: Result limit

        Returns:
            Cached query if similarity > threshold and not expired, else None
        """
        query_hash = self._compute_query_hash(query_embedding, namespace, limit)
        if query_hash in self._query_cache:
            cached = self._query_cache[query_hash]
            if not cached.is_expired():
                return cached
            else:
                del self._query_cache[query_hash]
        for cached in self._query_cache.values():
            if cached.is_expired():
                continue
            similarity = self._cosine_similarity(query_embedding, cached.query_embedding)
            if similarity >= CACHE_SIMILARITY_THRESHOLD:
                logger.info(f"Semantic cache hit with similarity {similarity:.3f}")
                return cached
        return None

    def _cache_query_results(
        self, query_embedding: list[float], namespace: str, results: list[SearchResult], limit: int
    ) -> None:
        """Cache query results for future semantic lookups.

        Args:
            query_embedding: Query vector
            namespace: Collection namespace
            results: Search results to cache
            limit: Result limit
        """
        query_hash = self._compute_query_hash(query_embedding, namespace, limit)
        cached_query = CachedQuery(
            query_hash=query_hash, query_embedding=query_embedding, results=results, cache_time=time.time()
        )
        self._query_cache[query_hash] = cached_query
        if len(self._query_cache) > 1000:
            self._evict_expired_cache()

    def _evict_expired_cache(self) -> None:
        """Remove expired entries from query cache."""
        expired_keys = [k for k, v in self._query_cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._query_cache[key]
        logger.info(f"Evicted {len(expired_keys)} expired cache entries")

    def get_collection_stats(
        self,
        collection_type: Literal["episodes", "segments", "claims", "quotes", "topics"],
        tenant: str,
        workspace: str,
    ) -> StepResult:
        """Get statistics for a collection.

        Args:
            collection_type: Type of collection
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with collection statistics
        """
        try:
            if collection_type not in COLLECTION_CONFIGS:
                return StepResult.fail(f"Invalid collection type: {collection_type}", status="bad_request")
            config = COLLECTION_CONFIGS[collection_type]
            namespace = self._get_namespace(tenant, workspace, config.name)
            stats = self.vector_store.get_collection_stats(namespace)
            if not stats:
                return StepResult.fail(f"Collection {namespace} not found or not initialized", status="bad_request")
            return StepResult.ok(data=stats)
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return StepResult.fail(f"Failed to get stats: {e!s}", status="retryable")

    def clear_semantic_cache(self) -> StepResult:
        """Clear all cached queries.

        Returns:
            StepResult with cache clear status
        """
        try:
            cache_size = len(self._query_cache)
            self._query_cache.clear()
            self.vector_store.clear_similarity_cache()
            logger.info(f"Cleared {cache_size} cached queries")
            return StepResult.ok(data={"cleared_entries": cache_size})
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return StepResult.fail(f"Failed to clear cache: {e!s}")

    def _get_namespace(self, tenant: str, workspace: str, collection_name: str) -> str:
        """Build tenant-aware namespace for collection.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            collection_name: Base collection name

        Returns:
            Namespaced collection name
        """
        return f"{tenant}:{workspace}:{collection_name}"

    @staticmethod
    def _compute_query_hash(query_embedding: list[float], namespace: str, limit: int) -> str:
        """Compute deterministic hash for query.

        Args:
            query_embedding: Query vector
            namespace: Collection namespace
            limit: Result limit

        Returns:
            SHA256 hash string
        """
        query_str = f"{namespace}:{limit}:{','.join((f'{v:.6f}' for v in query_embedding[:10]))}"
        return hashlib.sha256(query_str.encode()).hexdigest()

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        import math

        if len(vec1) != len(vec2):
            return 0.0
        dot_product = sum((a * b for a, b in zip(vec1, vec2, strict=False)))
        norm1 = math.sqrt(sum((a * a for a in vec1)))
        norm2 = math.sqrt(sum((b * b for b in vec2)))
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        return float(dot_product / (norm1 * norm2))


def get_collection_manager(enable_semantic_cache: bool = True) -> CreatorIntelligenceCollectionManager:
    """Factory function to create collection manager.

    Args:
        enable_semantic_cache: Enable semantic query caching

    Returns:
        Initialized collection manager instance
    """
    return CreatorIntelligenceCollectionManager(enable_semantic_cache=enable_semantic_cache)
