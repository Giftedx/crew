"""Hybrid retrieval combining sparse (BM25) + dense + reranking for Qdrant.

Implements state-of-the-art retrieval with:
- Sparse vectors (SPLADE++ via FastEmbed)
- Dense vectors (BGE embeddings)
- Reciprocal Rank Fusion (RRF) or Distribution-Based Score Fusion (DBSF)
- Reranking (Cohere or BGE reranker)
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from platform.config.configuration import get_config
from domains.memory.vector.qdrant import get_qdrant_client
from platform.observability import metrics
if TYPE_CHECKING:
    from qdrant_client.models import ScoredPoint
logger = logging.getLogger(__name__)

@dataclass
class RetrievalResult:
    """Result from hybrid retrieval."""
    points: list[ScoredPoint]
    scores: list[float]
    reranked: bool
    fusion_method: str
    latency_ms: float
    metadata: dict[str, Any]

class HybridRetriever:
    """Hybrid retrieval with sparse + dense vectors and reranking.

    Architecture:
    1. Parallel prefetch: sparse (BM25-like SPLADE++) + dense (BGE)
    2. Fusion: RRF (Reciprocal Rank Fusion) or DBSF (Distribution-Based Score Fusion)
    3. Optional reranking: Cohere or BGE reranker for top-K

    Features:
    - Async Qdrant client
    - FastEmbed for sparse/dense embeddings
    - Per-collection configuration
    - Metrics export
    """

    def __init__(self, collection_name: str, fusion_method: str | None=None, enable_reranking: bool | None=None) -> None:
        """Initialize hybrid retriever.

        Args:
            collection_name: Qdrant collection name
            fusion_method: "rrf" or "dbsf" (default from config)
            enable_reranking: Whether to rerank results (default from config)
        """
        config = get_config()
        self.enabled = config.enable_hybrid_retrieval
        self.collection_name = collection_name
        self.fusion_method = fusion_method or config.hybrid_retrieval_fusion_method
        self.enable_reranking = enable_reranking if enable_reranking is not None else config.enable_reranker
        self.reranker_model = config.reranker_model
        self.reranker_top_k = config.reranker_top_k
        self._qdrant_client: Any = None
        self._sparse_encoder: Any = None
        self._dense_encoder: Any = None
        self._reranker: Any = None
        if self.enabled:
            self._initialize_components()
            logger.info('Hybrid retriever initialized: collection=%s, fusion=%s, rerank=%s', collection_name, self.fusion_method, self.enable_reranking)

    def _initialize_components(self) -> None:
        """Initialize Qdrant client and embedding models."""
        self._qdrant_client = get_qdrant_client()
        try:
            from fastembed import SparseTextEmbedding, TextEmbedding
            self._sparse_encoder = SparseTextEmbedding(model_name='prithivida/Splade_PP_en_v1', cache_dir='./data/fastembed_cache')
            self._dense_encoder = TextEmbedding(model_name='BAAI/bge-small-en-v1.5', cache_dir='./data/fastembed_cache')
            logger.info('FastEmbed encoders initialized')
        except Exception as e:
            logger.warning('Failed to initialize FastEmbed encoders: %s; hybrid retrieval disabled', e)
            self.enabled = False
            return
        if self.enable_reranking:
            self._initialize_reranker()

    def _initialize_reranker(self) -> None:
        """Initialize reranker model."""
        try:
            config = get_config()
            if config.cohere_api_key:
                import cohere
                self._reranker = cohere.Client(config.cohere_api_key)
                self._reranker_type = 'cohere'
                logger.info('Cohere reranker initialized')
                return
        except Exception as e:
            logger.debug('Cohere reranker unavailable: %s', e)
        try:
            from fastembed.rerank.cross_encoder import TextCrossEncoder
            self._reranker = TextCrossEncoder(model_name=self.reranker_model, cache_dir='./data/fastembed_cache')
            self._reranker_type = 'fastembed'
            logger.info('FastEmbed reranker initialized: %s', self.reranker_model)
        except Exception as e:
            logger.warning('Failed to initialize reranker: %s; reranking disabled', e)
            self.enable_reranking = False

    async def retrieve(self, query: str, limit: int=10, filter_dict: dict[str, Any] | None=None) -> RetrievalResult:
        """Hybrid retrieval: sparse + dense + fusion + rerank.

        Args:
            query: Query text
            limit: Number of results to return
            filter_dict: Optional Qdrant filter

        Returns:
            RetrievalResult with fused and optionally reranked points
        """
        import time
        start = time.perf_counter()
        if not self.enabled:
            return await self._dense_only_retrieve(query, limit, filter_dict)
        try:
            sparse_embedding = await self._encode_sparse(query)
            dense_embedding = await self._encode_dense(query)
            sparse_results = await self._prefetch_sparse(sparse_embedding, limit * 2, filter_dict)
            dense_results = await self._prefetch_dense(dense_embedding, limit * 2, filter_dict)
            fused_results = self._fuse_results(sparse_results, dense_results, limit)
            if self.enable_reranking and len(fused_results) > 0:
                fused_results = await self._rerank_results(query, fused_results, limit)
                reranked = True
            else:
                reranked = False
            latency_ms = (time.perf_counter() - start) * 1000
            scores = [point.score for point in fused_results] if hasattr(fused_results[0], 'score') else []
            self._export_metrics(latency_ms, len(fused_results), reranked)
            return RetrievalResult(points=fused_results, scores=scores, reranked=reranked, fusion_method=self.fusion_method, latency_ms=latency_ms, metadata={'sparse_count': len(sparse_results), 'dense_count': len(dense_results), 'fused_count': len(fused_results)})
        except Exception as e:
            logger.exception('Hybrid retrieval failed: %s', e)
            return await self._dense_only_retrieve(query, limit, filter_dict)

    async def _encode_sparse(self, text: str) -> Any:
        """Encode text with sparse encoder (SPLADE++)."""
        embeddings = list(self._sparse_encoder.embed([text]))
        return embeddings[0] if embeddings else None

    async def _encode_dense(self, text: str) -> list[float]:
        """Encode text with dense encoder (BGE)."""
        embeddings = list(self._dense_encoder.embed([text]))
        return list(embeddings[0]) if embeddings else []

    async def _prefetch_sparse(self, sparse_embedding: Any, limit: int, filter_dict: dict[str, Any] | None) -> list[Any]:
        """Prefetch using sparse vectors."""
        try:
            results = self._qdrant_client.query_points(collection_name=self.collection_name, query=sparse_embedding, using='sparse', limit=limit, query_filter=filter_dict, with_payload=True)
            return results.points if hasattr(results, 'points') else []
        except Exception as e:
            logger.debug('Sparse prefetch failed: %s; skipping', e)
            return []

    async def _prefetch_dense(self, dense_embedding: list[float], limit: int, filter_dict: dict[str, Any] | None) -> list[Any]:
        """Prefetch using dense vectors."""
        try:
            results = self._qdrant_client.query_points(collection_name=self.collection_name, query=dense_embedding, using='dense', limit=limit, query_filter=filter_dict, with_payload=True)
            return results.points if hasattr(results, 'points') else []
        except Exception as e:
            logger.warning('Dense prefetch failed: %s', e)
            return []

    def _fuse_results(self, sparse_results: list[Any], dense_results: list[Any], limit: int) -> list[Any]:
        """Fuse sparse and dense results using RRF or DBSF."""
        if self.fusion_method == 'rrf':
            return self._rrf_fusion(sparse_results, dense_results, limit)
        elif self.fusion_method == 'dbsf':
            return self._dbsf_fusion(sparse_results, dense_results, limit)
        else:
            logger.warning('Unknown fusion method %s; using RRF', self.fusion_method)
            return self._rrf_fusion(sparse_results, dense_results, limit)

    def _rrf_fusion(self, sparse_results: list[Any], dense_results: list[Any], limit: int, k: int=60) -> list[Any]:
        """Reciprocal Rank Fusion (RRF).

        RRF score = sum(1 / (k + rank_i))  for each result list i
        """
        sparse_ranks = {point.id: rank + 1 for rank, point in enumerate(sparse_results)}
        dense_ranks = {point.id: rank + 1 for rank, point in enumerate(dense_results)}
        all_ids = set(sparse_ranks.keys()) | set(dense_ranks.keys())
        rrf_scores = {}
        for point_id in all_ids:
            score = 0.0
            if point_id in sparse_ranks:
                score += 1.0 / (k + sparse_ranks[point_id])
            if point_id in dense_ranks:
                score += 1.0 / (k + dense_ranks[point_id])
            rrf_scores[point_id] = score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:limit]
        id_to_point = {point.id: point for point in dense_results}
        id_to_point.update({point.id: point for point in sparse_results})
        fused = []
        for point_id in sorted_ids:
            if point_id in id_to_point:
                point = id_to_point[point_id]
                point.score = rrf_scores[point_id]
                fused.append(point)
        return fused

    def _dbsf_fusion(self, sparse_results: list[Any], dense_results: list[Any], limit: int) -> list[Any]:
        """Distribution-Based Score Fusion (DBSF).

        Normalizes scores using mean ± 3*std, then sums across result lists.
        """
        import numpy as np
        sparse_scores = np.array([point.score for point in sparse_results]) if sparse_results else np.array([])
        dense_scores = np.array([point.score for point in dense_results]) if dense_results else np.array([])

        def normalize(scores: np.ndarray) -> np.ndarray:
            if len(scores) == 0:
                return scores
            mean = np.mean(scores)
            std = np.std(scores)
            if std == 0:
                return scores - mean
            lower = mean - 3 * std
            upper = mean + 3 * std
            clamped = np.clip(scores, lower, upper)
            return (clamped - lower) / (upper - lower) if upper > lower else clamped * 0
        sparse_norm = normalize(sparse_scores)
        dense_norm = normalize(dense_scores)
        sparse_map = {sparse_results[i].id: sparse_norm[i] for i in range(len(sparse_results))}
        dense_map = {dense_results[i].id: dense_norm[i] for i in range(len(dense_results))}
        all_ids = set(sparse_map.keys()) | set(dense_map.keys())
        dbsf_scores = {}
        for point_id in all_ids:
            dbsf_scores[point_id] = sparse_map.get(point_id, 0.0) + dense_map.get(point_id, 0.0)
        sorted_ids = sorted(dbsf_scores.keys(), key=lambda x: dbsf_scores[x], reverse=True)[:limit]
        id_to_point = {point.id: point for point in dense_results}
        id_to_point.update({point.id: point for point in sparse_results})
        fused = []
        for point_id in sorted_ids:
            if point_id in id_to_point:
                point = id_to_point[point_id]
                point.score = dbsf_scores[point_id]
                fused.append(point)
        return fused

    async def _rerank_results(self, query: str, results: list[Any], limit: int) -> list[Any]:
        """Rerank results using reranker model."""
        if not self._reranker or len(results) == 0:
            return results
        try:
            documents = [point.payload.get('text', '') for point in results]
            if self._reranker_type == 'cohere':
                response = self._reranker.rerank(query=query, documents=documents, top_n=min(limit, self.reranker_top_k), model='rerank-english-v3.0')
                reranked = [results[r.index] for r in response.results]
                for i, r in enumerate(response.results):
                    reranked[i].score = r.relevance_score
                return reranked
            elif self._reranker_type == 'fastembed':
                scores = list(self._reranker.rerank(query, documents))
                scored = list(zip(results, scores, strict=False))
                scored.sort(key=lambda x: x[1], reverse=True)
                reranked = [point for point, _score in scored[:limit]]
                for i, (_point, score) in enumerate(scored[:limit]):
                    reranked[i].score = float(score)
                return reranked
        except Exception as e:
            logger.warning('Reranking failed: %s; returning original results', e)
            return results
        return results

    async def _dense_only_retrieve(self, query: str, limit: int, filter_dict: dict[str, Any] | None) -> RetrievalResult:
        """Fallback: dense-only retrieval (no hybrid)."""
        import time
        start = time.perf_counter()
        try:
            embedding = await self._encode_dense(query)
            results = self._qdrant_client.query_points(collection_name=self.collection_name, query=embedding, limit=limit, query_filter=filter_dict, with_payload=True)
            points = results.points if hasattr(results, 'points') else []
            latency_ms = (time.perf_counter() - start) * 1000
            return RetrievalResult(points=points, scores=[p.score for p in points], reranked=False, fusion_method='dense_only', latency_ms=latency_ms, metadata={'fallback': True})
        except Exception as e:
            logger.exception('Dense-only retrieval failed: %s', e)
            return RetrievalResult(points=[], scores=[], reranked=False, fusion_method='none', latency_ms=(time.perf_counter() - start) * 1000, metadata={'error': str(e)})

    def _export_metrics(self, latency_ms: float, result_count: int, reranked: bool) -> None:
        """Export retrieval metrics."""
        try:
            labels = {'collection': self.collection_name, 'fusion': self.fusion_method, 'reranked': str(reranked)}
            metrics.get_metrics().histogram('hybrid_retrieval_latency_ms', latency_ms, labels=labels)
            metrics.get_metrics().histogram('hybrid_retrieval_results', result_count, labels=labels)
        except Exception as e:
            logger.debug('Failed to export retrieval metrics: %s', e)
__all__ = ['HybridRetriever', 'RetrievalResult']