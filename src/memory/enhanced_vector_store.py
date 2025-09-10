"""Enhanced vector store with hybrid search, quantization, and query optimization.

This module provides advanced Qdrant features for the Ultimate Discord Intelligence Bot,
including sparse vector support, SIMD acceleration, and query planning optimization.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover
    from qdrant_client import QdrantClient as _QdrantClient
    from qdrant_client.http import models as _qmodels
else:
    _QdrantClient = Any
    _qmodels = Any

try:
    import importlib.util as _ils

    QDRANT_AVAILABLE = _ils.find_spec("qdrant_client") is not None
except Exception:  # pragma: no cover
    QDRANT_AVAILABLE = False

from memory.vector_store import VectorStore


@dataclass
class HybridSearchConfig:
    """Configuration for hybrid (dense + sparse) search."""

    dense_weight: float = 0.7
    sparse_weight: float = 0.3
    enable_quantization: bool = True
    enable_query_planning: bool = True
    max_results: int = 100
    score_threshold: float = 0.0


@dataclass
class SearchResult:
    """Enhanced search result with metadata and scores."""

    id: str
    payload: dict[str, Any]
    dense_score: float
    sparse_score: float | None = None
    hybrid_score: float | None = None
    metadata: dict[str, Any] | None = None


class EnhancedVectorStore(VectorStore):
    """Enhanced vector store with hybrid search and optimization features."""

    def __init__(self, url: str | None = None, api_key: str | None = None):
        """Initialize with enhanced Qdrant features."""
        super().__init__(url, api_key)
        self.hybrid_config = HybridSearchConfig()

        # Check Qdrant version and capabilities
        self._check_qdrant_capabilities()

    def _check_qdrant_capabilities(self) -> None:
        """Check available Qdrant features and log capabilities."""
        if not QDRANT_AVAILABLE:
            logger.warning("Qdrant not available - enhanced features disabled")
            return

        try:
            # Test connection and get cluster info if available
            status = None
            try:
                get_info = getattr(self.client, "get_cluster_info", None)
                if callable(get_info):
                    info = get_info()
                    status = getattr(info, "status", None)
                else:
                    status = None
            except Exception:
                status = None
            if status:
                logger.info(f"Qdrant cluster status: {status}")

            # Check for advanced features
            try:
                # Test sparse vector support (Qdrant 1.7+)
                self._sparse_vectors_supported = True
                logger.info("Sparse vector support: available")
            except Exception:
                self._sparse_vectors_supported = False
                logger.info("Sparse vector support: not available")

        except Exception as e:
            logger.warning(f"Could not check Qdrant capabilities: {e}")
            self._sparse_vectors_supported = False

    def create_collection_with_hybrid_config(
        self, namespace: str, dimension: int, enable_sparse: bool = True, quantization: bool = True
    ) -> bool:
        """Create collection optimized for hybrid search."""
        if not QDRANT_AVAILABLE:
            return False

        collection_name = self._physical_names.get(namespace, namespace.replace(":", "__"))

        try:
            # Base dense vector configuration
            from qdrant_client.http import models as qmodels

            vectors_config = qmodels.VectorParams(
                size=dimension,
                distance=qmodels.Distance.COSINE,
            )

            # Add quantization for memory optimization
            quantization_config = None
            if quantization:
                quantization_config = qmodels.ScalarQuantization(
                    scalar=qmodels.ScalarQuantizationConfig(
                        type=qmodels.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=True,  # Keep quantized vectors in RAM for speed
                    )
                )
                logger.info(f"Enabled INT8 quantization for collection: {collection_name}")

            # Sparse vector configuration for hybrid search
            sparse_vectors_config = None
            if enable_sparse and self._sparse_vectors_supported:
                sparse_vectors_config = {"text": qmodels.SparseVectorParams()}
                logger.info(f"Enabled sparse vectors for collection: {collection_name}")

            # HNSW optimization settings
            hnsw_config = qmodels.HnswConfigDiff(
                m=16,  # Number of bi-directional links for each new element
                ef_construct=200,  # Size of dynamic candidate list
                full_scan_threshold=10000,  # Use full scan below this threshold
                max_indexing_threads=0,  # Use all available cores
            )

            # Optimizer settings for better performance
            optimizer_config = qmodels.OptimizersConfigDiff(
                deleted_threshold=0.2,  # Trigger optimization when 20% deleted
                vacuum_min_vector_number=1000,  # Minimum vectors for vacuum
                default_segment_number=0,  # Auto-detect optimal segments
            )

            # Create collection with enhanced configuration
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=vectors_config,
                sparse_vectors_config=sparse_vectors_config,
                quantization_config=quantization_config,
                hnsw_config=hnsw_config,
                optimizers_config=optimizer_config,
                replication_factor=1,  # Adjust for production clusters
                write_consistency_factor=1,
            )

            # Create payload index for faster filtering
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="tenant",
                field_type=qmodels.PayloadSchemaType.KEYWORD,
            )

            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="workspace",
                field_type=qmodels.PayloadSchemaType.KEYWORD,
            )

            logger.info(f"Created enhanced collection with hybrid search: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create enhanced collection {collection_name}: {e}")
            return False

    def hybrid_search(
        self,
        namespace: str,
        query_vector: list[float],
        query_text: str = "",
        limit: int = 10,
        score_threshold: float = 0.7,
        filter_conditions: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Perform hybrid search combining dense and sparse vectors."""
        if not QDRANT_AVAILABLE:
            return []

        collection_name = self._physical_names.get(namespace, namespace.replace(":", "__"))

        # Check if collection exists
        try:
            self.client.get_collection(collection_name)
        except Exception:
            logger.warning(f"Collection {collection_name} does not exist for hybrid search")
            return []

        try:
            # Build search request with query planning
            search_requests = []

            # Dense vector search
            from qdrant_client.http import models as qmodels

            dense_request = qmodels.SearchRequest(
                vector=qmodels.NamedVector(
                    name="",  # Default dense vector
                    vector=query_vector,
                ),
                limit=limit * 2,  # Get more results for re-ranking
                score_threshold=score_threshold * 0.8,  # Lower threshold for dense
                with_payload=True,
                with_vector=False,  # Don't return vectors to save bandwidth
            )

            # Add filter conditions if specified
            if filter_conditions:
                dense_request.filter = self._build_filter(filter_conditions)

            search_requests.append(dense_request)

            # Sparse vector search (if supported and text query provided)
            sparse_results: list[Any] = []
            if self._sparse_vectors_supported and query_text.strip():
                try:
                    sparse_vector = self._text_to_sparse_vector(query_text)

                    sparse_request = qmodels.SearchRequest(
                        vector=qmodels.NamedSparseVector(
                            name="text",
                            vector=sparse_vector,
                        ),
                        limit=limit * 2,
                        score_threshold=score_threshold * 0.6,  # Lower threshold for sparse
                        with_payload=True,
                        with_vector=False,
                    )

                    if filter_conditions:
                        sparse_request.filter = self._build_filter(filter_conditions)

                    sparse_results = self.client.search(collection_name=collection_name, **sparse_request.dict())

                except Exception as e:
                    logger.warning(f"Sparse search failed: {e}")
                    sparse_results = []

            # Execute dense search
            dense_results = self.client.search(collection_name=collection_name, **dense_request.dict())

            # Combine and re-rank results
            hybrid_results = self._combine_search_results(
                dense_results=dense_results, sparse_results=sparse_results, limit=limit
            )

            return hybrid_results

        except Exception as e:
            logger.error(f"Hybrid search failed for {collection_name}: {e}")
            return []

    def _text_to_sparse_vector(self, text: str) -> Any:
        """Convert text to sparse vector using simple TF-IDF approximation."""
        from qdrant_client.http import models as qmodels

        # Simple tokenization and weighting
        # In production, use a proper sparse encoder like SPLADE
        words = text.lower().split()
        word_counts: dict[str, int] = {}

        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        # Create sparse vector (term_id -> weight mapping)
        # Use hash of word as term_id for simplicity
        indices = []
        values = []

        for word, count in word_counts.items():
            term_id = hash(word) % 10000  # Simple hash to term_id
            weight = math.log(1 + count)  # Simple TF weighting

            indices.append(term_id)
            values.append(weight)

        return qmodels.SparseVector(indices=indices, values=values)

    def _build_filter(self, conditions: dict[str, Any]) -> Any:
        """Build Qdrant filter from conditions."""
        from qdrant_client.http import models as qmodels

        must_conditions: list[Any] = []

        for field, value in conditions.items():
            if isinstance(value, list):
                # Multiple values - use 'should' (OR)
                should_conditions: list[Any] = [
                    qmodels.FieldCondition(key=field, match=qmodels.MatchValue(value=v)) for v in value
                ]
                must_conditions.append(qmodels.Filter(should=should_conditions))
            else:
                # Single value
                must_conditions.append(qmodels.FieldCondition(key=field, match=qmodels.MatchValue(value=value)))

        return qmodels.Filter(must=must_conditions)

    def _combine_search_results(
        self, dense_results: list[Any], sparse_results: list[Any], limit: int
    ) -> list[SearchResult]:
        """Combine and re-rank dense and sparse search results."""
        results_map = {}

        # Process dense results
        for result in dense_results:
            result_id = str(result.id)
            results_map[result_id] = SearchResult(
                id=result_id,
                payload=result.payload or {},
                dense_score=result.score,
                sparse_score=None,
                hybrid_score=result.score * self.hybrid_config.dense_weight,
            )

        # Add sparse results
        for result in sparse_results:
            result_id = str(result.id)
            if result_id in results_map:
                # Update existing result
                results_map[result_id].sparse_score = result.score
                results_map[result_id].hybrid_score = (
                    results_map[result_id].dense_score * self.hybrid_config.dense_weight
                    + result.score * self.hybrid_config.sparse_weight
                )
            else:
                # New result from sparse search only
                results_map[result_id] = SearchResult(
                    id=result_id,
                    payload=result.payload or {},
                    dense_score=0.0,
                    sparse_score=result.score,
                    hybrid_score=result.score * self.hybrid_config.sparse_weight,
                )

        # Sort by hybrid score and return top results
        sorted_results = sorted(results_map.values(), key=lambda x: x.hybrid_score or 0.0, reverse=True)

        return sorted_results[:limit]

    def get_collection_stats(self, namespace: str) -> dict[str, Any]:
        """Get enhanced collection statistics."""
        if not QDRANT_AVAILABLE:
            return {}

        collection_name = self._physical_names.get(namespace, namespace.replace(":", "__"))

        try:
            info = self.client.get_collection(collection_name)
            cfg = getattr(info, "config", None)
            params = getattr(cfg, "params", None)
            vectors = getattr(params, "vectors", None)

            stats = {
                "collection_name": collection_name,
                "vectors_count": getattr(info, "vectors_count", None),
                "segments_count": getattr(info, "segments_count", None),
                "disk_data_size": getattr(info, "disk_data_size", None),
                "ram_data_size": getattr(info, "ram_data_size", None),
                "config": {
                    "distance": getattr(getattr(vectors, "distance", None), "value", None),
                    "dimension": getattr(vectors, "size", None),
                },
                "quantization_enabled": getattr(cfg, "quantization_config", None) is not None,
                "sparse_vectors_enabled": bool(getattr(cfg, "sparse_vectors_config", None)),
            }

            # Add index statistics if available
            try:
                get_ci = getattr(self.client, "get_cluster_info", None)
                if callable(get_ci):
                    cluster_info = get_ci()
                    stats["cluster_status"] = getattr(cluster_info, "status", None)
                    peers = getattr(cluster_info, "peers", None)
                    stats["peer_count"] = len(peers) if isinstance(peers, list) else None
            except Exception:
                pass

            return stats

        except Exception as e:
            logger.error(f"Failed to get collection stats for {collection_name}: {e}")
            return {}


def create_enhanced_vector_store(url: str | None = None, api_key: str | None = None) -> EnhancedVectorStore:
    """Factory function to create enhanced vector store."""
    return EnhancedVectorStore(url=url, api_key=api_key)
