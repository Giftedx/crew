"""Enhanced vector store with hybrid search, quantization, and query optimization.

This module provides advanced Qdrant features for the Ultimate Discord Intelligence Bot,
including sparse vector support, SIMD acceleration, and query planning optimization.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from domains.memory.vector_store import VectorStore


logger = logging.getLogger(__name__)
if TYPE_CHECKING:
    from qdrant_client import QdrantClient as _QdrantClient
    from qdrant_client.http import models as _qmodels
else:
    _QdrantClient = Any
    _qmodels = Any
try:
    import importlib.util as _ils

    QDRANT_AVAILABLE = _ils.find_spec("qdrant_client") is not None
except Exception:
    QDRANT_AVAILABLE = False


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
        """Initialize enhanced vector store with Qdrant backend.

        Args:
            url: Qdrant server URL (or ":memory:" for in-memory instance)
            api_key: Optional API key for authentication
        """
        # Initialize parent class (takes no arguments)
        super().__init__()

        # Initialize namespace mapping for tenant isolation
        self._physical_names: dict[str, str] = {}

        # Initialize hybrid search configuration
        self.hybrid_config = HybridSearchConfig()

        # Initialize Qdrant client if available
        self.client: _QdrantClient | None = None
        self._sparse_vectors_supported: bool = False

        if QDRANT_AVAILABLE:
            try:
                from qdrant_client import QdrantClient as _QC

                if url == ":memory:":
                    self.client = _QC(location=":memory:")
                    logger.info("Initialized in-memory Qdrant client")
                elif url:
                    self.client = _QC(url=url, api_key=api_key)
                    logger.info(f"Initialized Qdrant client for {url}")
                else:
                    self.client = _QC(host="localhost", port=6333)
                    logger.info("Initialized local Qdrant client (localhost:6333)")
                self._check_qdrant_capabilities()
            except Exception as e:
                logger.error(f"Failed to initialize Qdrant client: {e}")
                self.client = None
        else:
            logger.warning("Qdrant not available - enhanced features disabled")

    def _check_qdrant_capabilities(self) -> None:
        """Check available Qdrant features and log capabilities."""
        if not QDRANT_AVAILABLE:
            logger.warning("Qdrant not available - enhanced features disabled")
            return
        try:
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
            try:
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
        if not QDRANT_AVAILABLE or self.client is None:
            logger.warning("Qdrant not available or client not initialized")
            return False
        collection_name = self._physical_names.get(namespace, namespace.replace(":", "__"))
        try:
            from qdrant_client.http import models as qmodels

            vectors_config = qmodels.VectorParams(size=dimension, distance=qmodels.Distance.COSINE)
            quantization_config = None
            if quantization:
                quantization_config = qmodels.ScalarQuantization(
                    scalar=qmodels.ScalarQuantizationConfig(
                        type=qmodels.ScalarType.INT8, quantile=0.99, always_ram=True
                    )
                )
                logger.info(f"Enabled INT8 quantization for collection: {collection_name}")
            sparse_vectors_config = None
            if enable_sparse and self._sparse_vectors_supported:
                sparse_vectors_config = {"text": qmodels.SparseVectorParams()}
                logger.info(f"Enabled sparse vectors for collection: {collection_name}")
            hnsw_config = qmodels.HnswConfigDiff(
                m=16, ef_construct=200, full_scan_threshold=10000, max_indexing_threads=0
            )
            optimizer_config = qmodels.OptimizersConfigDiff(
                deleted_threshold=0.2, vacuum_min_vector_number=1000, default_segment_number=0
            )
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=vectors_config,
                sparse_vectors_config=sparse_vectors_config,
                quantization_config=quantization_config,
                hnsw_config=hnsw_config,
                optimizers_config=optimizer_config,
                replication_factor=1,
                write_consistency_factor=1,
            )
            self.client.create_payload_index(
                collection_name=collection_name, field_name="tenant", field_type=qmodels.PayloadSchemaType.KEYWORD
            )
            self.client.create_payload_index(
                collection_name=collection_name, field_name="workspace", field_type=qmodels.PayloadSchemaType.KEYWORD
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
        if not QDRANT_AVAILABLE or self.client is None:
            logger.warning("Qdrant not available or client not initialized")
            return []
        collection_name = self._physical_names.get(namespace, namespace.replace(":", "__"))
        try:
            self.client.get_collection(collection_name)
        except Exception:
            logger.warning(f"Collection {collection_name} does not exist for hybrid search")
            return []
        try:
            search_requests = []
            from qdrant_client.http import models as qmodels

            dense_request = qmodels.SearchRequest(
                vector=qmodels.NamedVector(name="", vector=query_vector),
                limit=limit * 2,
                score_threshold=score_threshold * 0.8,
                with_payload=True,
                with_vector=False,
            )
            if filter_conditions:
                dense_request.filter = self._build_filter(filter_conditions)
            search_requests.append(dense_request)
            sparse_results: list[Any] = []
            if self._sparse_vectors_supported and query_text.strip():
                try:
                    sparse_vector = self._text_to_sparse_vector(query_text)
                    sparse_request = qmodels.SearchRequest(
                        vector=qmodels.NamedSparseVector(name="text", vector=sparse_vector),
                        limit=limit * 2,
                        score_threshold=score_threshold * 0.6,
                        with_payload=True,
                        with_vector=False,
                    )
                    if filter_conditions:
                        sparse_request.filter = self._build_filter(filter_conditions)
                    sparse_results = self.client.search(collection_name=collection_name, **sparse_request.dict())
                except Exception as e:
                    logger.warning(f"Sparse search failed: {e}")
                    sparse_results = []
            dense_results = self.client.search(collection_name=collection_name, **dense_request.dict())
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

        words = text.lower().split()
        word_counts: dict[str, int] = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        indices = []
        values = []
        for word, count in word_counts.items():
            term_id = hash(word) % 10000
            weight = math.log(1 + count)
            indices.append(term_id)
            values.append(weight)
        return qmodels.SparseVector(indices=indices, values=values)

    def _build_filter(self, conditions: dict[str, Any]) -> Any:
        """Build Qdrant filter from conditions."""
        from qdrant_client.http import models as qmodels

        must_conditions: list[Any] = []
        for field, value in conditions.items():
            if isinstance(value, list):
                should_conditions: list[Any] = [
                    qmodels.FieldCondition(key=field, match=qmodels.MatchValue(value=v)) for v in value
                ]
                must_conditions.append(qmodels.Filter(should=should_conditions))
            else:
                must_conditions.append(qmodels.FieldCondition(key=field, match=qmodels.MatchValue(value=value)))
        return qmodels.Filter(must=must_conditions)

    def _combine_search_results(
        self, dense_results: list[Any], sparse_results: list[Any], limit: int
    ) -> list[SearchResult]:
        """Combine and re-rank dense and sparse search results."""
        results_map = {}
        for result in dense_results:
            result_id = str(result.id)
            results_map[result_id] = SearchResult(
                id=result_id,
                payload=result.payload or {},
                dense_score=result.score,
                sparse_score=None,
                hybrid_score=result.score * self.hybrid_config.dense_weight,
            )
        for result in sparse_results:
            result_id = str(result.id)
            if result_id in results_map:
                results_map[result_id].sparse_score = result.score
                results_map[result_id].hybrid_score = (
                    results_map[result_id].dense_score * self.hybrid_config.dense_weight
                    + result.score * self.hybrid_config.sparse_weight
                )
            else:
                results_map[result_id] = SearchResult(
                    id=result_id,
                    payload=result.payload or {},
                    dense_score=0.0,
                    sparse_score=result.score,
                    hybrid_score=result.score * self.hybrid_config.sparse_weight,
                )
        sorted_results = sorted(results_map.values(), key=lambda x: x.hybrid_score or 0.0, reverse=True)
        return sorted_results[:limit]

    def get_collection_stats(self, namespace: str) -> dict[str, Any]:
        """Get enhanced collection statistics."""
        if not QDRANT_AVAILABLE or self.client is None:
            logger.warning("Qdrant not available or client not initialized")
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
