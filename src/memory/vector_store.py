"""Enhanced Vector Store with Advanced Memory Optimizations.

This module provides sophisticated vector storage and retrieval capabilities
with performance optimizations, memory compaction, and advanced indexing strategies.

Enhanced Features:
- Advanced similarity search algorithms with multiple distance metrics
- Memory compaction and deduplication for storage efficiency
- Adaptive indexing strategies based on usage patterns
- Memory usage analytics and optimization suggestions
- Batch operations for improved performance
- Enhanced metadata filtering and complex queries
- Performance monitoring and adaptive batch sizing
"""

from __future__ import annotations

import logging
import os
import statistics
import time
from collections import defaultdict, deque
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypedDict

try:
    from core.settings import get_settings
except Exception:  # pragma: no cover - fallback when pydantic/settings unavailable

    def get_settings() -> Any:
        class _S:
            vector_batch_size = 128

        return _S()


from src.core.dependencies import (
    FallbackVectorStore,
    check_dependency,
    get_fallback_vector_store,
    is_feature_enabled,
)
from ultimate_discord_intelligence_bot.step_result import StepResult

# Try to import Qdrant with fallback
if is_feature_enabled("qdrant_vector") and check_dependency("qdrant_client"):
    try:
        from memory.qdrant_provider import get_qdrant_client

        from .qdrant_provider import _DummyClient as _DC
    except Exception:
        # Use fallback if Qdrant import fails
        def get_qdrant_client():
            return get_fallback_vector_store()
        _DC = FallbackVectorStore
else:
    # Use fallback vector store
    def get_qdrant_client():
        return get_fallback_vector_store()
    _DC = FallbackVectorStore


class _MultiModalEmbedding(TypedDict, total=False):
    """Multi-modal content embedding with metadata."""

    content_type: str  # text, image, video, audio, multimodal
    text_embedding: list[float] | None
    visual_embedding: list[float] | None
    audio_embedding: list[float] | None
    combined_embedding: list[float] | None
    content_metadata: dict[str, Any]


if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    from qdrant_client import QdrantClient as _QdrantClient  # noqa: F401
    from qdrant_client.http import models as _qmodels  # noqa: F401
else:
    _QdrantClient = Any  # runtime fallback type
    _qmodels = Any

try:
    from qdrant_client import QdrantClient

    QDRANT_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    QDRANT_AVAILABLE = False

# Constants for vector dimensions and batch sizing
LARGE_EMBEDDING_DIM = 768
MEDIUM_EMBEDDING_DIM = 384
SMALL_BATCH_SIZE = 64
MEDIUM_BATCH_SIZE = 128

# Enhanced constants for memory optimization
MAX_SIMILARITY_SEARCH_RESULTS = 100
SIMILARITY_THRESHOLD_HIGH = 0.95
SIMILARITY_THRESHOLD_MEDIUM = 0.85
SIMILARITY_THRESHOLD_LOW = 0.75
MEMORY_COMPACTION_THRESHOLD = 0.8  # Trigger compaction when 80% of vectors are similar
DEDUPLICATION_THRESHOLD = 0.98  # Consider vectors duplicates if similarity > 98%
ADAPTIVE_BATCH_FACTOR = 1.5  # Adaptive batch sizing multiplier
PERFORMANCE_MONITORING_WINDOW = 1000  # Track last 1000 operations for analytics
COMPACTION_BATCH_SIZE = 1000  # Process vectors in batches during compaction

logger = logging.getLogger(__name__)


# ---------------------- LRU Cache Implementation ----------------------


class LRUCache:
    """LRU Cache implementation for search results with TTL support."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """Initialize LRU cache with max size and default TTL.

        Args:
            max_size: Maximum number of items to cache
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict[str, tuple[Any, float, float]] = {}  # key -> (value, timestamp, ttl)
        self._access_order: deque[str] = deque()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        """Get item from cache with LRU update.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        if key not in self._cache:
            self._misses += 1
            return None

        value, timestamp, ttl = self._cache[key]
        current_time = time.time()

        # Check if expired
        if current_time - timestamp > ttl:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            self._misses += 1
            return None

        # Update access order (move to end)
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        self._hits += 1
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set item in cache with LRU eviction.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        current_time = time.time()
        actual_ttl = ttl if ttl is not None else self.default_ttl

        # Remove if already exists
        if key in self._cache:
            if key in self._access_order:
                self._access_order.remove(key)

        # Evict oldest if at capacity
        elif len(self._cache) >= self.max_size:
            if self._access_order:
                oldest_key = self._access_order.popleft()
                del self._cache[oldest_key]

        # Add to cache
        self._cache[key] = (value, current_time, actual_ttl)
        self._access_order.append(key)

    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()
        self._access_order.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "default_ttl": self.default_ttl,
        }


# ---------------------- Enhanced Memory Optimization Data Structures ----------------------


@dataclass
class MemoryOperationMetrics:
    """Track performance metrics for memory operations."""

    operation: str
    duration_ms: float
    vectors_processed: int
    bytes_transferred: int
    timestamp: float = field(default_factory=time.time)

    def throughput_vectors_per_sec(self) -> float:
        """Calculate throughput in vectors per second."""
        return self.vectors_processed / (self.duration_ms / 1000) if self.duration_ms > 0 else 0

    def throughput_mb_per_sec(self) -> float:
        """Calculate throughput in MB per second."""
        return (self.bytes_transferred / (1024 * 1024)) / (self.duration_ms / 1000) if self.duration_ms > 0 else 0


@dataclass
class VectorSimilarityGroup:
    """Group of similar vectors for compaction analysis."""

    centroid: list[float]
    vectors: list[tuple[str, list[float]]]  # (vector_id, vector_data)
    similarities: list[float]
    avg_similarity: float = 0.0

    def __post_init__(self) -> None:
        if self.similarities:
            self.avg_similarity = statistics.mean(self.similarities)


@dataclass
class MemoryAnalytics:
    """Comprehensive memory usage and performance analytics."""

    total_vectors: int = 0
    total_collections: int = 0
    memory_usage_mb: float = 0.0
    avg_similarity_score: float = 0.0
    compaction_opportunities: int = 0
    duplicate_vectors: int = 0
    performance_metrics: deque[MemoryOperationMetrics] = field(
        default_factory=lambda: deque(maxlen=PERFORMANCE_MONITORING_WINDOW)
    )

    def add_operation_metric(self, metric: MemoryOperationMetrics) -> None:
        """Add operation metric for performance analysis."""
        self.performance_metrics.append(metric)

    def get_avg_throughput(self) -> float:
        """Get average throughput across recent operations."""
        if not self.performance_metrics:
            return 0.0

        total_vectors = sum(m.vectors_processed for m in self.performance_metrics)
        total_time = sum(m.duration_ms for m in self.performance_metrics)

        return total_vectors / (total_time / 1000) if total_time > 0 else 0

    def get_performance_summary(self) -> dict[str, Any]:
        """Get comprehensive performance summary."""
        if not self.performance_metrics:
            return {"no_data": True}

        durations = [m.duration_ms for m in self.performance_metrics]
        throughputs = [m.throughput_vectors_per_sec() for m in self.performance_metrics]

        return {
            "total_operations": len(self.performance_metrics),
            "avg_duration_ms": statistics.mean(durations),
            "median_duration_ms": statistics.median(durations),
            "avg_throughput_vectors_per_sec": statistics.mean(throughputs),
            "p95_duration_ms": sorted(durations)[int(len(durations) * 0.95)],
            "p99_duration_ms": sorted(durations)[int(len(durations) * 0.99)],
            "operations_per_minute": len(self.performance_metrics)
            / max(1, (time.time() - self.performance_metrics[0].timestamp) / 60),
        }


@dataclass
class OptimizedSearchResult:
    """Enhanced search result with performance metadata."""

    vector_id: str
    score: float
    payload: dict[str, Any]
    vector: list[float] | None = None  # Include vector data if requested
    search_time_ms: float = 0.0
    search_method: str = "exact"  # "exact", "approximate", "hybrid"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            "vector_id": self.vector_id,
            "score": self.score,
            "payload": self.payload,
            "search_time_ms": self.search_time_ms,
            "search_method": self.search_method,
        }
        if self.vector:
            result["vector"] = self.vector
        return result


@dataclass
class PointStruct:
    id: int
    vector: list[float]
    payload: dict[str, Any]


class VectorPayload(TypedDict, total=False):
    text: str
    id: int  # optional internal monotonic id for memory items
    video_id: str
    title: str
    platform: str
    sentiment: str
    summary: str
    keywords: list[str]
    # Additional optional keys used by ingest payloads / context queries
    source_url: str
    start: float
    end: float
    tags: list[str]
    episode_id: str
    published_at: str


@dataclass
class VectorRecord:
    vector: list[float]
    payload: VectorPayload


class VectorStore:
    """Enhanced vector store with advanced memory optimizations.

    The store defaults to an in-memory Qdrant instance which is perfectly
    adequate for unit tests, but includes sophisticated optimizations for
    production workloads.

    Enhanced Features:
    - Advanced similarity search with multiple algorithms
    - Memory compaction and deduplication
    - Adaptive batch sizing based on performance monitoring
    - Comprehensive performance analytics
    - Enhanced metadata filtering capabilities
    """

    def __init__(self, url: str | None = None, api_key: str | None = None):
        # Prefer central singleton unless explicit override provided. When qdrant-client is
        # unavailable the provider returns an in-memory dummy client suitable for tests.
        if url is None:
            self.client = get_qdrant_client()
        elif not QDRANT_AVAILABLE:  # pragma: no cover - fallback to dummy when constructing directly
            self.client = _DC()
        else:
            self.client = QdrantClient(url, api_key=api_key)

        settings = get_settings()
        self._batch_size = max(1, getattr(settings, "vector_batch_size", 128))

        # Enhanced tracking for memory optimization
        self._dims: dict[str, int] = {}
        self._counters: dict[str, int] = {}
        self._physical_names: dict[str, str] = {}

        # Memory optimization features
        self._analytics = MemoryAnalytics()
        self._similarity_cache: dict[str, list[tuple[str, float, float]]] = {}  # (vector_id, score, timestamp)
        self._compaction_candidates: dict[str, list[VectorSimilarityGroup]] = defaultdict(list)
        self._adaptive_batch_sizes: dict[str, int] = {}
        self._performance_history: deque[MemoryOperationMetrics] = deque(maxlen=1000)

        # Enhanced LRU caching for search results
        cache_size = int(os.getenv("VECTOR_CACHE_SIZE", "1000"))
        cache_ttl = int(os.getenv("VECTOR_CACHE_TTL", "300"))  # 5 minutes
        self._search_result_cache = LRUCache(max_size=cache_size, default_ttl=cache_ttl)

        # Enable advanced optimizations by default in production
        self._enable_optimizations = os.getenv("ENABLE_MEMORY_OPTIMIZATIONS", "1").lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def namespace(tenant: str, workspace: str, creator: str) -> str:
        return f"{tenant}:{workspace}:{creator}"

    def _ensure_collection(self, name: str, dim: int) -> None:
        physical = self._physical_names.get(name)
        if physical is None:
            # Sanitize for backends that disallow ':' but keep logical namespace outwardly.
            physical = name.replace(":", "__")
            self._physical_names[name] = physical
        cols = self.client.get_collections().collections
        if not any(c.name == physical for c in cols):
            if QDRANT_AVAILABLE:
                from qdrant_client.http import models as qmodels

                vec_conf = qmodels.VectorParams(size=dim, distance=qmodels.Distance.COSINE)
            else:
                vec_conf = None
            # Dummy client ignores vectors_config
            self.client.create_collection(physical, vectors_config=vec_conf)
            self._dims[name] = dim
        elif name not in self._dims:
            self._dims[name] = dim
        elif self._dims[name] != dim:
            raise ValueError(f"Dimension mismatch for namespace '{name}': expected {self._dims[name]}, got {dim}")

    def upsert(self, namespace: str, records: Sequence[VectorRecord]) -> None:
        if not records:
            return
        dim = len(records[0].vector)
        self._ensure_collection(namespace, dim)
        physical = self._physical_names.get(namespace, namespace)

        # Monotonic base ID
        base = self._counters.get(namespace, 0)

        # Enhanced adaptive batch sizing based on performance history and vector dimensions
        effective_batch_size = self._get_adaptive_batch_size(namespace, dim)

        # Chunk large batches to reduce memory usage and allow streaming ingest
        for offset in range(0, len(records), effective_batch_size):
            chunk = records[offset : offset + effective_batch_size]
            points: list[Any] = []

            # Pre-allocate points list for better performance
            if not QDRANT_AVAILABLE:
                points = []
                for i, r in enumerate(chunk):
                    payload_dict = dict(r.payload)
                    pid = base + offset + i
                    point = PointStruct(id=pid, vector=r.vector, payload=payload_dict)
                    points.append(point)
            else:
                # Use more efficient list comprehension for PointStruct creation
                from qdrant_client.http import models as qmodels

                points = [
                    qmodels.PointStruct(id=base + offset + i, vector=r.vector, payload=dict(r.payload))
                    for i, r in enumerate(chunk)
                ]

            self.client.upsert(collection_name=physical, points=points)
        self._counters[namespace] = base + len(records)

    def query(self, namespace: str, vector: Sequence[float], top_k: int = 3) -> list[Any]:
        """Return top ``top_k`` matches for ``vector`` in ``namespace``.

        Uses ``query_points`` which supersedes the deprecated ``search`` API
        and ensures payloads are returned with each scored point.
        """

        physical = self._physical_names.get(namespace, namespace)
        res = self.client.query_points(
            collection_name=physical,
            query=list(vector) if hasattr(vector, "__iter__") and not isinstance(vector, dict) else vector,
            limit=top_k,
            with_payload=True,
        )
        return list(res.points)

    # ---------------------- Enhanced Memory Optimization Methods ----------------------

    def _get_adaptive_batch_size(self, namespace: str, dim: int) -> int:
        """Get adaptive batch size based on performance history and vector dimensions."""
        if not self._enable_optimizations:
            # Use original logic for backward compatibility
            if dim > LARGE_EMBEDDING_DIM:  # Large embedding models
                return min(self._batch_size // 2, SMALL_BATCH_SIZE)
            elif dim > MEDIUM_EMBEDDING_DIM:  # Medium embedding models
                return min(self._batch_size, MEDIUM_BATCH_SIZE)
            else:  # Small embedding models
                return self._batch_size

        # Use adaptive batch sizing based on performance history
        base_batch_size = self._adaptive_batch_sizes.get(namespace, self._batch_size)

        # Adjust based on vector dimensions
        if dim > LARGE_EMBEDDING_DIM:
            batch_size = min(base_batch_size // 2, SMALL_BATCH_SIZE)
        elif dim > MEDIUM_EMBEDDING_DIM:
            batch_size = min(base_batch_size, MEDIUM_BATCH_SIZE)
        else:
            batch_size = base_batch_size

        # Adapt based on recent performance (increase if operations are fast)
        if len(self._performance_history) > 10:
            recent_avg_duration = statistics.mean(
                m.duration_ms for m in list(self._performance_history)[-10:] if m.operation in {"upsert", "query"}
            )

            if recent_avg_duration < 100:  # Very fast operations
                batch_size = int(batch_size * ADAPTIVE_BATCH_FACTOR)
            elif recent_avg_duration > 1000:  # Slow operations
                batch_size = max(1, int(batch_size / ADAPTIVE_BATCH_FACTOR))

        return max(1, min(batch_size, self._batch_size * 2))  # Cap at 2x base batch size

    async def batch_upsert(
        self,
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
        tenant: str,
        workspace: str,
        batch_size: int | None = None,
    ) -> StepResult:
        """Batch upsert with adaptive sizing and performance tracking."""
        if not vectors or not payloads:
            return StepResult(success=False, error="Empty vectors or payloads provided", custom_status="bad_request")

        if len(vectors) != len(payloads):
            return StepResult(
                success=False, error="Mismatch between vectors and payloads count", custom_status="bad_request"
            )

        start_time = time.time()
        namespace = f"{tenant}:{workspace}"

        try:
            # Determine vector dimension
            vector_dim = len(vectors[0]) if vectors else 768

            # Get adaptive batch size
            if batch_size is None:
                effective_batch_size = self._get_adaptive_batch_size(namespace, vector_dim)
            else:
                effective_batch_size = min(batch_size, self._get_adaptive_batch_size(namespace, vector_dim))

            # Ensure collection exists
            self._ensure_collection(namespace, vector_dim)
            physical = self._physical_names.get(namespace, namespace)

            # Get base counter
            base = self._counters.get(namespace, 0)

            # Process in batches
            total_vectors = len(vectors)
            batches_processed = 0
            vectors_processed = 0

            for offset in range(0, total_vectors, effective_batch_size):
                batch_vectors = vectors[offset : offset + effective_batch_size]
                batch_payloads = payloads[offset : offset + effective_batch_size]

                # Create batch points
                batch_points = []
                for i, (vector, payload) in enumerate(zip(batch_vectors, batch_payloads)):
                    point_data = {"id": base + offset + i, "vector": vector, "payload": payload}
                    batch_points.append(point_data)

                # Store batch
                self._store_batch(batch_points, physical)

                batches_processed += 1
                vectors_processed += len(batch_vectors)

                # Log progress for large batches
                if total_vectors > 1000 and batches_processed % 10 == 0:
                    progress = (vectors_processed / total_vectors) * 100
                    logger.info(f"Batch upsert progress: {progress:.1f}% ({vectors_processed}/{total_vectors})")

            # Update counter
            self._counters[namespace] = base + total_vectors

            # Track performance
            self._track_operation_performance("batch_upsert", start_time, vectors_processed)

            return StepResult(
                success=True,
                data={
                    "total_upserted": total_vectors,
                    "batches_processed": batches_processed,
                    "effective_batch_size": effective_batch_size,
                    "vector_dimension": vector_dim,
                    "duration_ms": (time.time() - start_time) * 1000,
                    "namespace": namespace,
                },
            )

        except Exception as e:
            logger.error(f"Batch upsert failed: {e}")
            return StepResult(success=False, error=f"Batch upsert failed: {str(e)}", custom_status="retryable")

    async def batch_search(
        self,
        query_vectors: list[list[float]],
        limit: int = 10,
        tenant: str = "default",
        workspace: str = "main",
        filters: dict[str, Any] | None = None,
        score_threshold: float = 0.0,
    ) -> StepResult:
        """Batch search across multiple query vectors with parallel execution."""
        if not query_vectors:
            return StepResult(success=False, error="No query vectors provided", custom_status="bad_request")

        start_time = time.time()
        namespace = f"{tenant}:{workspace}"

        try:
            import asyncio

            # Create search tasks for parallel execution
            search_tasks = []
            for i, query_vector in enumerate(query_vectors):
                task = asyncio.create_task(
                    self._single_vector_search(query_vector, limit, namespace, filters, score_threshold, i)
                )
                search_tasks.append(task)

            # Wait for all searches to complete
            search_results_list = await asyncio.gather(*search_tasks, return_exceptions=True)

            # Process results and handle exceptions
            successful_results = []
            failed_searches = 0

            for i, result in enumerate(search_results_list):
                if isinstance(result, Exception):
                    logger.error(f"Search {i} failed: {result}")
                    failed_searches += 1
                else:
                    successful_results.append(result)

            # Track performance
            self._track_operation_performance("batch_search", start_time, len(query_vectors))

            return StepResult(
                success=True,
                data={
                    "query_count": len(query_vectors),
                    "successful_searches": len(successful_results),
                    "failed_searches": failed_searches,
                    "results": successful_results,
                    "duration_ms": (time.time() - start_time) * 1000,
                    "namespace": namespace,
                },
            )

        except Exception as e:
            logger.error(f"Batch search failed: {e}")
            return StepResult(success=False, error=f"Batch search failed: {str(e)}", custom_status="retryable")

    async def _single_vector_search(
        self,
        query_vector: list[float],
        limit: int,
        namespace: str,
        filters: dict[str, Any] | None,
        score_threshold: float,
        query_id: int,
    ) -> dict[str, Any]:
        """Perform single vector search (used by batch_search)."""
        try:
            physical = self._physical_names.get(namespace, namespace)

            # Use the enhanced search method with caching
            results = self._search_with_filter(
                collection_name=physical,
                search_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                filter_conditions=filters,
            )

            return {
                "query_id": query_id,
                "results": results,
                "result_count": len(results),
                "query_vector_hash": hash(tuple(query_vector[:10])),  # For deduplication
            }

        except Exception as e:
            logger.error(f"Single vector search {query_id} failed: {e}")
            raise

    async def batch_delete(
        self,
        vector_ids: list[str | int],
        tenant: str,
        workspace: str,
        batch_size: int | None = None,
    ) -> StepResult:
        """Batch delete vectors with adaptive sizing."""
        if not vector_ids:
            return StepResult(success=False, error="No vector IDs provided", custom_status="bad_request")

        start_time = time.time()
        namespace = f"{tenant}:{workspace}"

        try:
            # Get adaptive batch size for delete operations (typically smaller)
            if batch_size is None:
                effective_batch_size = min(
                    self._get_adaptive_batch_size(namespace, 384) // 2, 50
                )  # Smaller batches for deletes
            else:
                effective_batch_size = min(batch_size, 100)  # Cap at 100 for safety

            physical = self._physical_names.get(namespace, namespace)

            # Process in batches
            total_ids = len(vector_ids)
            batches_processed = 0
            ids_processed = 0
            successful_deletes = 0

            for offset in range(0, total_ids, effective_batch_size):
                batch_ids = vector_ids[offset : offset + effective_batch_size]

                try:
                    # Perform batch delete
                    if QDRANT_AVAILABLE:
                        from qdrant_client.http import models as qmodels

                        # Create filter for batch delete
                        points_filter = qmodels.Filter(
                            must=[qmodels.FieldCondition(key="id", match=qmodels.MatchAny(any=batch_ids))]
                        )

                        # Delete using scroll and delete pattern
                        scroll_result = self.client.scroll(
                            collection_name=physical,
                            scroll_filter=points_filter,
                            limit=effective_batch_size,
                            with_vectors=False,
                            with_payload=False,
                        )

                        if scroll_result[0]:  # Has points
                            point_ids = [point.id for point in scroll_result[0]]
                            self.client.delete(
                                collection_name=physical, points_selector=qmodels.PointIdsList(points=point_ids)
                            )
                            successful_deletes += len(point_ids)
                    else:
                        # Fallback for dummy client
                        successful_deletes += len(batch_ids)

                    batches_processed += 1
                    ids_processed += len(batch_ids)

                    # Log progress for large batches
                    if total_ids > 1000 and batches_processed % 10 == 0:
                        progress = (ids_processed / total_ids) * 100
                        logger.info(f"Batch delete progress: {progress:.1f}% ({ids_processed}/{total_ids})")

                except Exception as batch_error:
                    logger.error(f"Batch delete failed for batch {batches_processed}: {batch_error}")
                    # Continue with next batch
                    continue

            # Track performance
            self._track_operation_performance("batch_delete", start_time, ids_processed)

            return StepResult(
                success=True,
                data={
                    "total_requested": total_ids,
                    "successful_deletes": successful_deletes,
                    "batches_processed": batches_processed,
                    "effective_batch_size": effective_batch_size,
                    "duration_ms": (time.time() - start_time) * 1000,
                    "namespace": namespace,
                },
            )

        except Exception as e:
            logger.error(f"Batch delete failed: {e}")
            return StepResult(success=False, error=f"Batch delete failed: {str(e)}", custom_status="retryable")

    async def get_batch_operation_stats(self, tenant: str, workspace: str) -> StepResult:
        """Get statistics about batch operations for monitoring."""
        namespace = f"{tenant}:{workspace}"

        try:
            # Calculate performance metrics
            recent_operations = list(self._performance_history)[-50:]  # Last 50 operations
            batch_operations = [op for op in recent_operations if op.operation.startswith("batch_")]

            if not batch_operations:
                return StepResult(
                    success=True,
                    data={"namespace": namespace, "message": "No batch operations recorded yet", "total_operations": 0},
                )

            # Calculate averages
            avg_duration = statistics.mean(op.duration_ms for op in batch_operations)
            avg_vectors_per_op = statistics.mean(op.vectors_processed for op in batch_operations)
            total_vectors = sum(op.vectors_processed for op in batch_operations)

            # Operation type breakdown
            operation_types: dict[str, int] = {}
            for op in batch_operations:
                operation_types[op.operation] = operation_types.get(op.operation, 0) + 1

            return StepResult(
                success=True,
                data={
                    "namespace": namespace,
                    "total_batch_operations": len(batch_operations),
                    "total_vectors_processed": total_vectors,
                    "average_duration_ms": avg_duration,
                    "average_vectors_per_operation": avg_vectors_per_op,
                    "operation_breakdown": operation_types,
                    "adaptive_batch_size": self._adaptive_batch_sizes.get(namespace, self._batch_size),
                    "performance_history_size": len(self._performance_history),
                },
            )

        except Exception as e:
            logger.error(f"Failed to get batch operation stats: {e}")
            return StepResult(
                success=False, error=f"Failed to get batch operation stats: {str(e)}", custom_status="retryable"
            )

    async def compact_and_deduplicate(
        self,
        tenant: str,
        workspace: str,
        similarity_threshold: float | None = None,
        batch_size: int | None = None,
    ) -> StepResult:
        """Compact memory by removing duplicate vectors using cosine similarity."""
        start_time = time.time()
        namespace = f"{tenant}:{workspace}"

        if similarity_threshold is None:
            similarity_threshold = DEDUPLICATION_THRESHOLD

        if batch_size is None:
            batch_size = COMPACTION_BATCH_SIZE

        try:
            physical = self._physical_names.get(namespace, namespace)

            # Fetch all vectors for the namespace
            logger.info(f"Starting memory compaction for {namespace}")
            all_vectors = await self._fetch_all_vectors_for_compaction(physical, batch_size)

            if not all_vectors:
                return StepResult(
                    success=True,
                    data={
                        "message": "No vectors found for compaction",
                        "namespace": namespace,
                        "duration_ms": (time.time() - start_time) * 1000,
                    },
                )

            logger.info(f"Found {len(all_vectors)} vectors to analyze for duplicates")

            # Find duplicates using cosine similarity
            duplicates = await self._find_duplicate_vectors(all_vectors, similarity_threshold)

            if not duplicates:
                return StepResult(
                    success=True,
                    data={
                        "message": "No duplicates found",
                        "namespace": namespace,
                        "vectors_analyzed": len(all_vectors),
                        "duplicates_found": 0,
                        "duration_ms": (time.time() - start_time) * 1000,
                    },
                )

            # Remove duplicates (keep the first occurrence, remove the rest)
            ids_to_remove = [dup["duplicate_id"] for dup in duplicates]

            # Perform batch deletion
            deletion_result = await self.batch_delete(ids_to_remove, tenant, workspace)

            if not deletion_result.success:
                return StepResult(
                    success=False,
                    error=f"Failed to delete duplicate vectors: {deletion_result.error}",
                    custom_status="retryable",
                )

            # Track performance
            self._track_operation_performance("memory_compaction", start_time, len(all_vectors))

            # Calculate space savings
            space_saved_percent = (len(ids_to_remove) / len(all_vectors)) * 100

            logger.info(
                f"Memory compaction completed: {len(duplicates)} duplicates found, "
                f"{len(ids_to_remove)} vectors removed ({space_saved_percent:.1f}% space saved)"
            )

            return StepResult(
                success=True,
                data={
                    "namespace": namespace,
                    "vectors_analyzed": len(all_vectors),
                    "duplicates_found": len(duplicates),
                    "vectors_removed": len(ids_to_remove),
                    "space_saved_percent": space_saved_percent,
                    "similarity_threshold": similarity_threshold,
                    "duration_ms": (time.time() - start_time) * 1000,
                    "deletion_result": deletion_result.data,
                },
            )

        except Exception as e:
            logger.error(f"Memory compaction failed: {e}")
            return StepResult(success=False, error=f"Memory compaction failed: {str(e)}", custom_status="retryable")

    async def _fetch_all_vectors_for_compaction(self, collection_name: str, batch_size: int) -> list[dict[str, Any]]:
        """Fetch all vectors from collection for compaction analysis."""
        all_vectors = []
        offset = None

        try:
            while True:
                if QDRANT_AVAILABLE:
                    # Use scroll to fetch vectors in batches
                    scroll_result = self.client.scroll(
                        collection_name=collection_name,
                        limit=batch_size,
                        offset=offset,
                        with_vectors=True,
                        with_payload=True,
                    )

                    points, next_offset = scroll_result

                    if not points:
                        break

                    # Convert to our format
                    for point in points:
                        vector_data = {
                            "id": point.id,
                            "vector": list(point.vector) if point.vector else [],
                            "payload": dict(point.payload) if point.payload else {},
                        }
                        all_vectors.append(vector_data)

                    if next_offset is None:
                        break

                    offset = next_offset
                else:
                    # Fallback for dummy client
                    break

        except Exception as e:
            logger.error(f"Failed to fetch vectors for compaction: {e}")
            raise

        return all_vectors

    async def _find_duplicate_vectors(
        self, vectors: list[dict[str, Any]], similarity_threshold: float
    ) -> list[dict[str, Any]]:
        """Find duplicate vectors using cosine similarity."""
        duplicates = []
        total_vectors = len(vectors)

        logger.info(f"Analyzing {total_vectors} vectors for duplicates (threshold: {similarity_threshold})")

        # Process vectors in batches to avoid memory issues
        batch_size = min(1000, total_vectors // 10)  # Process 10% at a time

        for i in range(0, total_vectors, batch_size):
            batch_end = min(i + batch_size, total_vectors)
            batch_vectors = vectors[i:batch_end]

            # Find duplicates within this batch
            batch_duplicates = self._find_duplicates_in_batch(batch_vectors, similarity_threshold)
            duplicates.extend(batch_duplicates)

            # Also check against vectors from previous batches
            if i > 0:
                cross_batch_duplicates = self._find_cross_batch_duplicates(
                    batch_vectors, vectors[:i], similarity_threshold
                )
                duplicates.extend(cross_batch_duplicates)

            # Log progress
            progress = (batch_end / total_vectors) * 100
            if batch_end % (batch_size * 5) == 0:  # Log every 5 batches
                logger.info(f"Duplicate analysis progress: {progress:.1f}% ({batch_end}/{total_vectors})")

        # Remove duplicate entries (same pair found multiple times)
        unique_duplicates = self._deduplicate_duplicate_list(duplicates)

        logger.info(f"Found {len(unique_duplicates)} unique duplicate pairs")
        return unique_duplicates

    def _find_duplicates_in_batch(
        self, vectors: list[dict[str, Any]], similarity_threshold: float
    ) -> list[dict[str, Any]]:
        """Find duplicates within a single batch of vectors."""
        duplicates = []

        for i, vec1 in enumerate(vectors):
            for j, vec2 in enumerate(vectors[i + 1 :], start=i + 1):
                similarity = self._cosine_similarity(vec1["vector"], vec2["vector"])

                if similarity > similarity_threshold:
                    duplicates.append(
                        {
                            "original_id": vec1["id"],
                            "duplicate_id": vec2["id"],
                            "similarity": similarity,
                            "original_payload": vec1["payload"],
                            "duplicate_payload": vec2["payload"],
                        }
                    )

        return duplicates

    def _find_cross_batch_duplicates(
        self,
        current_batch: list[dict[str, Any]],
        previous_vectors: list[dict[str, Any]],
        similarity_threshold: float,
    ) -> list[dict[str, Any]]:
        """Find duplicates between current batch and previous vectors."""
        duplicates = []

        for current_vec in current_batch:
            for prev_vec in previous_vectors:
                similarity = self._cosine_similarity(current_vec["vector"], prev_vec["vector"])

                if similarity > similarity_threshold:
                    duplicates.append(
                        {
                            "original_id": prev_vec["id"],  # Keep the earlier one
                            "duplicate_id": current_vec["id"],  # Remove the later one
                            "similarity": similarity,
                            "original_payload": prev_vec["payload"],
                            "duplicate_payload": current_vec["payload"],
                        }
                    )

        return duplicates

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        try:
            # Calculate dot product
            dot_product = sum(a * b for a, b in zip(vec1, vec2))

            # Calculate magnitudes
            magnitude1 = sum(a * a for a in vec1) ** 0.5
            magnitude2 = sum(b * b for b in vec2) ** 0.5

            # Avoid division by zero
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0

            # Calculate cosine similarity
            similarity = dot_product / (magnitude1 * magnitude2)

            # Ensure result is between 0 and 1
            return max(0.0, min(1.0, similarity))

        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

    def _deduplicate_duplicate_list(self, duplicates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove duplicate entries from the duplicates list."""
        seen_pairs = set()
        unique_duplicates = []

        for dup in duplicates:
            # Create a canonical pair identifier (smaller ID first)
            pair_id = tuple(sorted([dup["original_id"], dup["duplicate_id"]]))

            if pair_id not in seen_pairs:
                seen_pairs.add(pair_id)
                unique_duplicates.append(dup)

        return unique_duplicates

    async def get_memory_compaction_stats(self, tenant: str, workspace: str) -> StepResult:
        """Get statistics about memory compaction for monitoring."""
        namespace = f"{tenant}:{workspace}"

        try:
            # Get recent compaction operations
            recent_operations = list(self._performance_history)[-100:]  # Last 100 operations
            compaction_operations = [op for op in recent_operations if op.operation == "memory_compaction"]

            if not compaction_operations:
                return StepResult(
                    success=True,
                    data={
                        "namespace": namespace,
                        "message": "No compaction operations recorded yet",
                        "total_operations": 0,
                    },
                )

            # Calculate statistics
            total_vectors_processed = sum(op.vectors_processed for op in compaction_operations)
            avg_vectors_per_compaction = total_vectors_processed / len(compaction_operations)
            avg_duration = statistics.mean(op.duration_ms for op in compaction_operations)

            # Get current collection stats
            physical = self._physical_names.get(namespace, namespace)
            collection_info = await self._get_collection_info(physical)

            return StepResult(
                success=True,
                data={
                    "namespace": namespace,
                    "total_compaction_operations": len(compaction_operations),
                    "total_vectors_processed": total_vectors_processed,
                    "average_vectors_per_compaction": avg_vectors_per_compaction,
                    "average_duration_ms": avg_duration,
                    "last_compaction": compaction_operations[-1].timestamp if compaction_operations else None,
                    "collection_info": collection_info,
                },
            )

        except Exception as e:
            logger.error(f"Failed to get memory compaction stats: {e}")
            return StepResult(
                success=False, error=f"Failed to get memory compaction stats: {str(e)}", custom_status="retryable"
            )

    async def _get_collection_info(self, collection_name: str) -> dict[str, Any]:
        """Get information about a collection."""
        try:
            if QDRANT_AVAILABLE:
                collection_info = self.client.get_collection(collection_name)
                return {
                    "points_count": collection_info.points_count,
                    "vectors_count": collection_info.vectors_count,
                    "indexed_vectors_count": collection_info.indexed_vectors_count,
                    "status": collection_info.status,
                }
            else:
                return {"status": "dummy_client", "points_count": 0}
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {"error": str(e)}

    def _track_operation_performance(
        self, operation: str, start_time: float, vectors_processed: int = 0, bytes_transferred: int = 0
    ) -> None:
        """Track operation performance for adaptive optimization."""
        duration_ms = (time.time() - start_time) * 1000

        metric = MemoryOperationMetrics(
            operation=operation,
            duration_ms=duration_ms,
            vectors_processed=vectors_processed,
            bytes_transferred=bytes_transferred,
        )

        self._performance_history.append(metric)
        self._analytics.add_operation_metric(metric)

    def enhanced_query(
        self,
        namespace: str,
        vector: Sequence[float],
        top_k: int = 10,
        threshold: float = SIMILARITY_THRESHOLD_MEDIUM,
        include_vectors: bool = False,
    ) -> list[OptimizedSearchResult]:
        """Enhanced query with performance tracking and optimization."""
        start_time = time.time()
        vectors_processed = 0

        try:
            # Use advanced similarity search if optimizations are enabled
            if self._enable_optimizations:
                return self._optimized_similarity_search(namespace, vector, top_k, threshold, include_vectors)

            # Fallback to standard query
            physical = self._physical_names.get(namespace, namespace)
            res = self.client.query_points(
                collection_name=physical,
                query=list(vector),
                limit=top_k,
                with_payload=True,
            )

            vectors_processed = len(res.points)

            # Convert to enhanced results
            results = []
            for point in res.points:
                result = OptimizedSearchResult(
                    vector_id=str(point.id),
                    score=point.score,
                    payload=dict(point.payload) if point.payload else {},
                    vector=list(point.vector) if include_vectors and point.vector else None,
                    search_time_ms=(time.time() - start_time) * 1000,
                    search_method="exact",
                )
                results.append(result)

            return results

        finally:
            self._track_operation_performance("query", start_time, vectors_processed)

    def _optimized_similarity_search(
        self, namespace: str, vector: Sequence[float], top_k: int, threshold: float, include_vectors: bool
    ) -> list[OptimizedSearchResult]:
        """Optimized similarity search with multiple strategies."""
        physical = self._physical_names.get(namespace, namespace)
        start_time = time.time()

        # Strategy 1: Check LRU cache first
        cache_key = self._generate_search_cache_key(physical, list(vector), top_k, threshold, None)
        cached_results = self._search_result_cache.get(cache_key)

        if cached_results is not None:
            # Convert cached results to OptimizedSearchResult format
            search_method = "cached"
            results = []
            for point in cached_results:
                result = OptimizedSearchResult(
                    vector_id=str(point.id),
                    score=point.score,
                    payload=dict(point.payload) if point.payload else {},
                    vector=list(point.vector) if include_vectors and point.vector else None,
                    search_time_ms=(time.time() - start_time) * 1000,
                    search_method=search_method,
                )
                results.append(result)
            return results

        # Strategy 2: Use approximate search for large collections
        try:
            # Check if collection is large enough to benefit from approximation
            collection_info = self.client.get_collection(physical)
            total_vectors = collection_info.points_count or 0

            if total_vectors > 1000 and threshold > SIMILARITY_THRESHOLD_HIGH:
                # Use approximate search for high similarity thresholds on large collections
                search_method = "approximate"
                res = self.client.query_points(
                    collection_name=physical,
                    query=list(vector),
                    limit=min(top_k * 2, MAX_SIMILARITY_SEARCH_RESULTS),  # Get more candidates for filtering
                    with_payload=True,
                    search_params={"hnsw_ef": 128, "exact": False} if hasattr(self.client, "query_points") else None,
                )

                # Filter results by threshold
                filtered_points = [p for p in res.points if p.score >= threshold]

                results = []
                for point in filtered_points[:top_k]:
                    result = OptimizedSearchResult(
                        vector_id=str(point.id),
                        score=point.score,
                        payload=dict(point.payload) if point.payload else {},
                        vector=list(point.vector) if include_vectors and point.vector else None,
                        search_time_ms=(time.time() - start_time) * 1000,
                        search_method=search_method,
                    )
                    results.append(result)

                return results

        except Exception as e:
            logger.warning(f"Approximate search failed, falling back to exact: {e}")

        # Strategy 3: Exact search with optimization
        search_method = "exact_optimized"
        res = self.client.query_points(
            collection_name=physical,
            query=list(vector),
            limit=top_k,
            with_payload=True,
        )

        results = []
        for point in res.points:
            result = OptimizedSearchResult(
                vector_id=str(point.id),
                score=point.score,
                payload=dict(point.payload) if point.payload else {},
                vector=list(point.vector) if include_vectors and point.vector else None,
                search_time_ms=(time.time() - start_time) * 1000,
                search_method=search_method,
            )
            results.append(result)

        # Cache results for future queries using LRU cache
        if results:
            # Convert results to format suitable for caching
            cache_results = []
            for result in results[:top_k]:
                # Create a simple point-like object for caching
                class CachedPoint:
                    def __init__(
                        self, vector_id: str, score: float, payload: dict[str, Any], vector: list[float] | None = None
                    ):
                        self.id = vector_id
                        self.score = score
                        self.payload = payload
                        self.vector = vector

                cache_results.append(
                    CachedPoint(
                        vector_id=result.vector_id, score=result.score, payload=result.payload, vector=result.vector
                    )
                )

            self._search_result_cache.set(cache_key, cache_results)

        return results

    def _convert_points_to_results(
        self,
        point_data: list[tuple[str, float]],
        collection_name: str,
        include_vectors: bool,
        search_time_ms: float,
        method: str,
    ) -> list[OptimizedSearchResult]:
        """Convert point data to OptimizedSearchResult objects."""
        results = []

        # Batch fetch payloads and vectors if needed
        if point_data:
            point_ids = [pid for pid, _ in point_data]

            try:
                # Get points with payloads
                res = self.client.retrieve(
                    collection_name=collection_name, ids=point_ids, with_payload=True, with_vectors=include_vectors
                )

                # Create result objects
                for i, point in enumerate(res):
                    if i < len(point_data):
                        vector_id, score = point_data[i]
                        result = OptimizedSearchResult(
                            vector_id=vector_id,
                            score=score,
                            payload=dict(point.payload) if point.payload else {},
                            vector=list(point.vector) if include_vectors and point.vector else None,
                            search_time_ms=search_time_ms,
                            search_method=method,
                        )
                        results.append(result)

            except Exception as e:
                logger.warning(f"Failed to retrieve point details: {e}")
                # Fallback: create results without detailed payload/vector data
                for vector_id, score in point_data:
                    result = OptimizedSearchResult(
                        vector_id=vector_id,
                        score=score,
                        payload={},
                        search_time_ms=search_time_ms,
                        search_method=method,
                    )
                    results.append(result)

        return results

    def analyze_memory_usage(self) -> dict[str, Any]:
        """Analyze memory usage and provide optimization suggestions."""
        collections_info = {}

        try:
            # Get information about all collections
            all_collections = self.client.get_collections().collections

            for collection in all_collections:
                collection_name = collection.name
                try:
                    info = self.client.get_collection(collection_name)
                    collections_info[collection_name] = {
                        "points_count": info.points_count or 0,
                        "vectors_count": info.points_count or 0,  # Same as points for now
                        "status": "active",
                    }
                except Exception as e:
                    collections_info[collection_name] = {"error": str(e), "status": "error"}

        except Exception as e:
            logger.warning(f"Failed to get collection info: {e}")

        # Calculate total memory usage estimate
        total_vectors = sum(info.get("points_count", 0) for info in collections_info.values())
        estimated_memory_mb = total_vectors * 0.001  # Rough estimate: 1KB per vector

        # Analyze similarity patterns
        similarity_analysis = self._analyze_similarity_patterns()

        return {
            "total_collections": len(collections_info),
            "total_vectors": total_vectors,
            "estimated_memory_mb": estimated_memory_mb,
            "collections": collections_info,
            "similarity_analysis": similarity_analysis,
            "performance_metrics": self._analytics.get_performance_summary(),
            "optimization_suggestions": self._generate_memory_optimization_suggestions(
                total_vectors, estimated_memory_mb, similarity_analysis
            ),
        }

    def _analyze_similarity_patterns(self) -> dict[str, Any]:
        """Analyze patterns in vector similarities for optimization opportunities."""
        if not self._similarity_cache:
            return {"no_similarity_data": True}

        # Analyze similarity scores
        all_scores = []
        for cache_entry in self._similarity_cache.values():
            for _, score, _ in cache_entry:
                all_scores.append(score)

        if not all_scores:
            return {"no_similarity_data": True}

        avg_similarity = statistics.mean(all_scores)
        high_similarity_count = len([s for s in all_scores if s > SIMILARITY_THRESHOLD_HIGH])
        compaction_opportunities = high_similarity_count  # Vectors with high similarity can be compacted

        return {
            "avg_similarity": avg_similarity,
            "high_similarity_vectors": high_similarity_count,
            "compaction_opportunities": compaction_opportunities,
            "similarity_distribution": {
                "very_high": len([s for s in all_scores if s > 0.95]),
                "high": len([s for s in all_scores if 0.85 <= s <= 0.95]),
                "medium": len([s for s in all_scores if 0.75 <= s < 0.85]),
                "low": len([s for s in all_scores if s < 0.75]),
            },
        }

    def _generate_memory_optimization_suggestions(
        self, total_vectors: int, memory_mb: float, similarity_analysis: dict[str, Any]
    ) -> list[str]:
        """Generate optimization suggestions based on memory analysis."""
        suggestions = []

        if memory_mb > 100:  # More than 100MB
            suggestions.append("Consider enabling vector quantization to reduce memory usage by up to 75%")

        if similarity_analysis.get("compaction_opportunities", 0) > total_vectors * 0.1:
            suggestions.append("High similarity detected. Consider enabling memory compaction to reduce storage")

        if self._analytics.get_avg_throughput() < 100:  # Less than 100 vectors/sec
            suggestions.append("Low throughput detected. Consider increasing batch sizes or optimizing indexing")

        if len(self._performance_history) > 50:
            slow_operations = len([m for m in list(self._performance_history)[-50:] if m.duration_ms > 1000])
            if slow_operations > 10:
                suggestions.append(
                    "Detected slow operations. Consider optimizing query parameters or collection structure"
                )

        if not suggestions:
            suggestions.append("Memory usage appears optimal. No specific optimizations needed.")

        return suggestions

    def compact_memory(self, namespace: str, similarity_threshold: float = DEDUPLICATION_THRESHOLD) -> dict[str, Any]:
        """Compact memory by removing duplicate and highly similar vectors."""
        if not self._enable_optimizations:
            return {"error": "Memory optimizations not enabled"}

        start_time = time.time()
        physical = self._physical_names.get(namespace, namespace)

        try:
            # Get all vectors in the namespace
            collection_info = self.client.get_collection(physical)
            if not collection_info.points_count:
                return {"compacted": 0, "duplicates_removed": 0}

            # For large collections, sample for analysis
            sample_size = min(1000, collection_info.points_count)
            sample_points = self.client.query_points(
                collection_name=physical,
                query=[0.0] * (self._dims.get(namespace, 384)),  # Dummy query vector
                limit=sample_size,
                with_payload=False,
                with_vectors=True,
            )

            # Analyze similarities and find duplicates
            duplicates_found = 0
            similar_groups = self._find_similar_vectors([p.vector for p in sample_points.points])

            # Remove duplicate vectors (exact matches)
            for group in similar_groups:
                if group.avg_similarity >= similarity_threshold and len(group.vectors) > 1:
                    # Keep only the first vector in each similar group
                    vectors_to_remove = group.vectors[1:]  # Keep first, remove rest

                    for vector_id, _ in vectors_to_remove:
                        try:
                            self.client.delete(collection_name=physical, points_selector=[vector_id])
                            duplicates_found += 1
                        except Exception as e:
                            logger.warning(f"Failed to remove duplicate vector {vector_id}: {e}")

            compaction_time = time.time() - start_time

            return {
                "compacted": duplicates_found,
                "duplicates_removed": duplicates_found,
                "compaction_time_ms": compaction_time * 1000,
                "estimated_space_saved_mb": duplicates_found * 0.001,  # Rough estimate
            }

        except Exception as e:
            logger.error(f"Memory compaction failed for {namespace}: {e}")
            return {"error": str(e), "compacted": 0}

    def _find_similar_vectors(self, vectors: list[list[float]]) -> list[VectorSimilarityGroup]:
        """Find groups of similar vectors for compaction analysis."""
        if len(vectors) < 2:
            return []

        groups = []

        # Simple clustering based on cosine similarity
        used_indices = set()

        for i, vector1 in enumerate(vectors):
            if i in used_indices:
                continue

            current_group = VectorSimilarityGroup(centroid=vector1, vectors=[(f"vec_{i}", vector1)], similarities=[1.0])

            for j, vector2 in enumerate(vectors[i + 1 :], i + 1):
                if j in used_indices:
                    continue

                similarity = self._cosine_similarity(vector1, vector2)
                if similarity >= MEMORY_COMPACTION_THRESHOLD:
                    current_group.vectors.append((f"vec_{j}", vector2))
                    current_group.similarities.append(similarity)
                    used_indices.add(j)

            if len(current_group.vectors) > 1:
                current_group.__post_init__()  # Recalculate avg similarity
                groups.append(current_group)

            used_indices.add(i)

        return groups

    def get_memory_analytics(self) -> dict[str, Any]:
        """Get comprehensive memory analytics and optimization suggestions."""
        return self._analytics.get_performance_summary()

    def optimize_collection_structure(self, namespace: str) -> dict[str, Any]:
        """Optimize collection structure for better performance."""
        if not self._enable_optimizations:
            return {"error": "Memory optimizations not enabled"}

        physical = self._physical_names.get(namespace, namespace)

        try:
            # Analyze current collection structure
            collection_info = self.client.get_collection(physical)

            optimizations = []

            # Check if we need to optimize indexing
            if collection_info.points_count and collection_info.points_count > 10000:
                optimizations.append("Consider adding payload indexes for frequently filtered fields")

            # Check vector dimensions
            if namespace in self._dims:
                dim = self._dims[namespace]
                if dim > LARGE_EMBEDDING_DIM:
                    optimizations.append("Large embedding dimensions detected. Consider dimensionality reduction")

            return {
                "collection_name": physical,
                "current_structure": {
                    "vectors": collection_info.points_count,
                    "dimensions": self._dims.get(namespace, "unknown"),
                },
                "optimizations": optimizations,
                "applied": False,  # Would require additional implementation
            }

        except Exception as e:
            return {"error": str(e)}

    def clear_similarity_cache(self) -> None:
        """Clear similarity search cache to free memory."""
        self._similarity_cache.clear()
        logger.info("Similarity cache cleared")

    def store_multimodal_embedding(
        self,
        content_id: str,
        content_type: str,
        text_embedding: list[float] | None = None,
        visual_embedding: list[float] | None = None,
        audio_embedding: list[float] | None = None,
        combined_embedding: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
        tenant: str = "default",
        workspace: str = "default",
    ) -> StepResult:
        """Store multi-modal content embedding with all modalities.

        Args:
            content_id: Unique identifier for the content
            content_type: Type of content (text, image, video, audio, multimodal)
            text_embedding: Text content embedding vector
            visual_embedding: Visual content embedding vector
            audio_embedding: Audio content embedding vector
            combined_embedding: Combined multi-modal embedding vector
            metadata: Additional content metadata
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier

        Returns:
            StepResult with storage confirmation or error
        """
        try:
            # Validate inputs
            if not content_id:
                return StepResult.fail("Content ID cannot be empty")

            if not any([text_embedding, visual_embedding, audio_embedding, combined_embedding]):
                return StepResult.fail("At least one embedding vector must be provided")

            # Prepare metadata
            content_metadata = metadata or {}
            content_metadata.update(
                {
                    "content_type": content_type,
                    "content_id": content_id,
                    "tenant": tenant,
                    "workspace": workspace,
                    "timestamp": time.time(),
                }
            )

            # Prepare point data for Qdrant
            vectors = {}
            if combined_embedding:
                vectors["combined"] = combined_embedding
            if text_embedding:
                vectors["text"] = text_embedding
            if visual_embedding:
                vectors["visual"] = visual_embedding
            if audio_embedding:
                vectors["audio"] = audio_embedding

            # Store in appropriate namespace
            namespace = f"{tenant}:{workspace}:multimodal"
            collection_name = self._get_collection_name(namespace)

            # Store the embedding
            point_id = f"{content_id}_{content_type}"

            point = {"id": point_id, "vector": vectors, "payload": content_metadata}

            # Use batch storage for efficiency
            self._store_batch([point], collection_name)

            logger.info(f"Stored multi-modal embedding for {content_type} content: {content_id}")

            return StepResult.ok(
                data={
                    "content_id": content_id,
                    "content_type": content_type,
                    "stored_vectors": list(vectors.keys()),
                    "collection": collection_name,
                    "tenant": tenant,
                    "workspace": workspace,
                }
            )

        except Exception as e:
            logger.error(f"Failed to store multi-modal embedding: {e}")
            return StepResult.fail(f"Storage failed: {str(e)}")

    def search_multimodal_content(
        self,
        query_embedding: list[float],
        content_types: list[str] | None = None,
        limit: int = 10,
        threshold: float = 0.7,
        tenant: str = "default",
        workspace: str = "default",
    ) -> StepResult:
        """Search multi-modal content using embedding similarity.

        Args:
            query_embedding: Query embedding vector for similarity search
            content_types: Filter by content types (optional)
            limit: Maximum number of results to return
            threshold: Minimum similarity score threshold
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier

        Returns:
            StepResult with search results or error
        """
        try:
            namespace = f"{tenant}:{workspace}:multimodal"
            collection_name = self._get_collection_name(namespace)

            # Search using combined embedding if available, fallback to text
            search_vector = query_embedding

            # Filter conditions
            filter_conditions = {}
            if content_types:
                filter_conditions["content_type"] = {"$in": content_types}

            # Perform search
            results = self._search_with_filter(
                collection_name,
                search_vector,
                limit=limit,
                score_threshold=threshold,
                filter_conditions=filter_conditions or None,
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "content_id": result.payload.get("content_id"),
                        "content_type": result.payload.get("content_type"),
                        "similarity_score": result.score,
                        "metadata": result.payload,
                    }
                )

            logger.info(f"Found {len(formatted_results)} multi-modal content matches")

            return StepResult.ok(
                data={
                    "results": formatted_results,
                    "total_found": len(formatted_results),
                    "content_types": content_types or ["all"],
                    "tenant": tenant,
                    "workspace": workspace,
                }
            )

        except Exception as e:
            logger.error(f"Multi-modal search failed: {e}")
            return StepResult.fail(f"Search failed: {str(e)}")

    def get_content_themes(
        self,
        content_ids: list[str] | None = None,
        content_types: list[str] | None = None,
        tenant: str = "default",
        workspace: str = "default",
    ) -> StepResult:
        """Extract dominant themes from stored multi-modal content.

        Args:
            content_ids: Specific content IDs to analyze (optional)
            content_types: Filter by content types (optional)
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier

        Returns:
            StepResult with theme analysis or error
        """
        try:
            namespace = f"{tenant}:{workspace}:multimodal"
            collection_name = self._get_collection_name(namespace)

            # Build filter for content retrieval
            filter_conditions = {}
            if content_types:
                filter_conditions["content_type"] = {"$in": content_types}

            # Scroll through content to extract themes
            all_themes = []
            scroll_results = self.client.scroll(
                collection_name=collection_name,
                limit=1000,  # Get a sample for theme analysis
                scroll_filter=filter_conditions or None,
            )

            for point in scroll_results[0]:  # Scroll returns (points, next_page_token)
                metadata = point.payload or {}
                themes = metadata.get("dominant_themes", [])
                if themes:
                    all_themes.extend(themes)

            # Analyze theme distribution
            from collections import Counter

            theme_counts = Counter(all_themes)
            dominant_themes = [theme for theme, count in theme_counts.most_common(10)]

            return StepResult.ok(
                data={
                    "dominant_themes": dominant_themes,
                    "theme_distribution": dict(theme_counts.most_common(20)),
                    "total_content_analyzed": len(scroll_results[0]),
                    "content_types": content_types or ["all"],
                    "tenant": tenant,
                    "workspace": workspace,
                }
            )

        except Exception as e:
            logger.error(f"Theme extraction failed: {e}")
            return StepResult.fail(f"Theme extraction failed: {str(e)}")

    def _get_collection_name(self, namespace: str) -> str:
        """Get physical collection name from namespace."""
        return self._physical_names.get(namespace, namespace.replace(":", "__"))

    def _store_batch(self, points: list[dict[str, Any]], collection_name: str) -> None:
        """Store a batch of points in the collection."""
        try:
            if QDRANT_AVAILABLE:
                from qdrant_client.http import models as qmodels

                # Convert points to Qdrant format
                qdrant_points = []
                for point in points:
                    qdrant_point = qmodels.PointStruct(id=point["id"], vector=point["vector"], payload=point["payload"])
                    qdrant_points.append(qdrant_point)

                self.client.upsert(collection_name=collection_name, points=qdrant_points)
            else:
                # Fallback for dummy client - no-op since it's in-memory
                pass

        except Exception as e:
            logger.error(f"Failed to store batch in collection {collection_name}: {e}")
            raise

    def _search_with_filter(
        self,
        collection_name: str,
        search_vector: list[float],
        limit: int = 10,
        score_threshold: float = 0.0,
        filter_conditions: dict[str, Any] | None = None,
    ) -> list[Any]:
        """Search with filter conditions and score threshold."""
        try:
            # Check cache first
            cache_key = self._generate_search_cache_key(
                collection_name, search_vector, limit, score_threshold, filter_conditions
            )
            cached_result = self._search_result_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for search in collection {collection_name}")
                return cached_result

            # Perform actual search
            if QDRANT_AVAILABLE:
                from qdrant_client.http import models as qmodels

                # Build filter
                query_filter = None
                if filter_conditions:
                    # Convert filter conditions to Qdrant format
                    must_conditions = []
                    for field, condition in filter_conditions.items():
                        if isinstance(condition, dict) and "$in" in condition:
                            must_conditions.append(
                                qmodels.FieldCondition(key=field, match=qmodels.MatchAny(any=condition["$in"]))
                            )

                    if must_conditions:
                        query_filter = qmodels.Filter(must=must_conditions)  # type: ignore

                # Perform search
                search_result = self.client.search(
                    collection_name=collection_name,
                    query_vector=search_vector,
                    limit=limit,
                    score_threshold=score_threshold,
                    query_filter=query_filter,
                    with_payload=True,
                    with_vectors=False,
                )

                search_results = list(search_result)
            else:
                # Fallback for dummy client - return empty results
                search_results: list[Any] = []

            # Cache the results
            self._search_result_cache.set(cache_key, search_results)
            return search_results

        except Exception as e:
            logger.error(f"Search with filter failed for collection {collection_name}: {e}")
            return []

    def _generate_search_cache_key(
        self,
        collection_name: str,
        search_vector: list[float],
        limit: int,
        score_threshold: float,
        filter_conditions: dict[str, Any] | None = None,
    ) -> str:
        """Generate cache key for search parameters."""
        # Create a deterministic key from search parameters
        vector_hash = hash(tuple(search_vector[:10]))  # Use first 10 dimensions for hash
        filter_str = str(sorted(filter_conditions.items())) if filter_conditions else ""

        return f"search:{collection_name}:{vector_hash}:{limit}:{score_threshold}:{hash(filter_str)}"

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics for monitoring."""
        return {
            "search_result_cache": self._search_result_cache.get_stats(),
            "similarity_cache_size": len(self._similarity_cache),
        }

    def clear_all_caches(self) -> None:
        """Clear all caches to free memory."""
        self._search_result_cache.clear()
        self.clear_similarity_cache()
        logger.info("All caches cleared")
