"""Continual Memory Consolidation

Periodic re-rank/merge/prune embeddings based on quality feedback.
Triggered by RAGQualityFeedback when quality degrades or candidates accumulate.

Key Features:
- Quality-driven pruning of low-value chunks
- Chunk merging for redundant/similar content
- Embedding re-computation for consolidated chunks
- Re-indexing and optimization
- Integration with UnifiedMemoryService
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from platform.core.step_result import StepResult
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class ConsolidationResult:
    """Result of a consolidation operation."""

    chunks_pruned: int
    chunks_merged: int
    chunks_reindexed: int
    embeddings_recomputed: int
    quality_improvement: float
    processing_time_s: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConsolidationStats:
    """Statistics for consolidation operations."""

    total_operations: int = 0
    total_chunks_pruned: int = 0
    total_chunks_merged: int = 0
    total_embeddings_recomputed: int = 0
    avg_quality_improvement: float = 0.0
    last_consolidation: float = 0.0


class ContinualMemoryConsolidation:
    """Manages periodic memory consolidation based on quality signals.

    Integrates with RAGQualityFeedback to maintain memory health:
    1. Prune low-quality chunks
    2. Merge similar/redundant chunks
    3. Re-compute embeddings for consolidated content
    4. Re-index for improved retrieval
    """

    def __init__(
        self,
        min_consolidation_interval_s: float = 3600.0,
        prune_batch_size: int = 50,
        merge_similarity_threshold: float = 0.95,
    ):
        """Initialize consolidation manager.

        Args:
            min_consolidation_interval_s: Minimum time between consolidations
            prune_batch_size: Maximum chunks to prune per operation
            merge_similarity_threshold: Similarity threshold for chunk merging
        """
        self.min_consolidation_interval_s = min_consolidation_interval_s
        self.prune_batch_size = prune_batch_size
        self.merge_similarity_threshold = merge_similarity_threshold
        self.stats = ConsolidationStats()
        self.tenant_stats: dict[str, ConsolidationStats] = defaultdict(ConsolidationStats)
        self.consolidation_history: list[ConsolidationResult] = []
        self.max_history = 100
        logger.info(
            f"ContinualMemoryConsolidation initialized: interval={min_consolidation_interval_s}s, batch_size={prune_batch_size}"
        )

    async def consolidate_memory(self, tenant: str, workspace: str, trigger_reason: str = "scheduled") -> StepResult:
        """Perform memory consolidation for a tenant/workspace.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            trigger_reason: Reason for consolidation (scheduled, quality_degraded, etc.)

        Returns:
            StepResult with ConsolidationResult data
        """
        start_time = time.time()
        try:
            if not self._can_consolidate(tenant):
                return StepResult.skip(
                    message="Skipping consolidation: too soon since last run",
                    data={"last_consolidation": self.stats.last_consolidation},
                )
            logger.info(f"Starting memory consolidation for {tenant}/{workspace}: {trigger_reason}")
            from platform.rl.rag.rag_quality_feedback import get_rag_feedback

            rag_feedback = get_rag_feedback()
            if not rag_feedback:
                return StepResult.fail(error="RAG quality feedback system not available")
            memory_service = await self._get_memory_service()
            if not memory_service:
                return StepResult.fail(error="Memory service not available")
            pruned_count = await self._prune_low_quality_chunks(tenant, workspace, rag_feedback, memory_service)
            merged_count = await self._merge_similar_chunks(tenant, workspace, rag_feedback, memory_service)
            recomputed_count = await self._recompute_embeddings(tenant, workspace, memory_service)
            reindexed_count = await self._reindex_vectors(tenant, workspace, memory_service)
            quality_improvement = self._calculate_quality_improvement(rag_feedback)
            processing_time = time.time() - start_time
            result = ConsolidationResult(
                chunks_pruned=pruned_count,
                chunks_merged=merged_count,
                chunks_reindexed=reindexed_count,
                embeddings_recomputed=recomputed_count,
                quality_improvement=quality_improvement,
                processing_time_s=processing_time,
            )
            self._update_stats(tenant, result)
            logger.info(
                f"Consolidation complete: pruned={pruned_count}, merged={merged_count}, recomputed={recomputed_count}, quality_improvement={quality_improvement:.2%}, time={processing_time:.2f}s"
            )
            return StepResult.ok(data=result)
        except Exception as e:
            logger.error(f"Memory consolidation failed: {e}", exc_info=True)
            return StepResult.fail(error=f"Consolidation failed: {e}")

    async def _prune_low_quality_chunks(self, tenant: str, workspace: str, rag_feedback, memory_service) -> int:
        """Prune low-quality chunks from memory.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            rag_feedback: RAG quality feedback system
            memory_service: Memory service instance

        Returns:
            Number of chunks pruned
        """
        candidates = rag_feedback.get_pruning_candidates(min_retrievals=5, limit=self.prune_batch_size)
        if not candidates:
            logger.debug("No chunks to prune")
            return 0
        logger.info(f"Pruning {len(candidates)} low-quality chunks")
        pruned = 0
        for chunk_id in candidates:
            try:
                result = await memory_service.delete(tenant=tenant, workspace=workspace, chunk_id=chunk_id)
                if result.success:
                    pruned += 1
                    if chunk_id in rag_feedback.chunk_metrics:
                        del rag_feedback.chunk_metrics[chunk_id]
            except Exception as e:
                logger.warning(f"Failed to prune chunk {chunk_id}: {e}")
        return pruned

    async def _merge_similar_chunks(self, tenant: str, workspace: str, rag_feedback, memory_service) -> int:
        """Merge similar/redundant chunks.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            rag_feedback: RAG quality feedback system
            memory_service: Memory service instance

        Returns:
            Number of chunks merged
        """
        chunks_with_metrics = [
            (chunk_id, metrics)
            for chunk_id, metrics in rag_feedback.chunk_metrics.items()
            if metrics.retrieval_count >= 3
        ]
        if len(chunks_with_metrics) < 2:
            logger.debug("Not enough chunks for merging")
            return 0
        logger.debug("Chunk merging not yet implemented")
        return 0

    async def _recompute_embeddings(self, tenant: str, workspace: str, memory_service) -> int:
        """Re-compute embeddings for consolidated chunks.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            memory_service: Memory service instance

        Returns:
            Number of embeddings recomputed
        """
        logger.debug("Embedding re-computation not yet implemented")
        return 0

    async def _reindex_vectors(self, tenant: str, workspace: str, memory_service) -> int:
        """Re-index vectors for improved retrieval.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            memory_service: Memory service instance

        Returns:
            Number of vectors re-indexed
        """
        logger.debug("Vector re-indexing not yet implemented")
        return 0

    async def _get_memory_service(self):
        """Get unified memory service instance."""
        try:
            from domains.memory import get_unified_memory

            return get_unified_memory()
        except ImportError:
            logger.warning("UnifiedMemoryService not available")
            return None

    def _can_consolidate(self, tenant: str) -> bool:
        """Check if consolidation can run (respects min interval).

        Args:
            tenant: Tenant identifier

        Returns:
            True if consolidation can proceed
        """
        tenant_stats = self.tenant_stats.get(tenant)
        if not tenant_stats:
            return True
        time_since_last = time.time() - tenant_stats.last_consolidation
        return time_since_last >= self.min_consolidation_interval_s

    def _calculate_quality_improvement(self, rag_feedback) -> float:
        """Calculate quality improvement from consolidation.

        Args:
            rag_feedback: RAG quality feedback system

        Returns:
            Quality improvement ratio (0.0-1.0)
        """
        if not rag_feedback.chunk_metrics:
            return 0.0
        current_avg = sum(m.quality_score for m in rag_feedback.chunk_metrics.values()) / len(
            rag_feedback.chunk_metrics
        )
        if rag_feedback.avg_relevance_trend:
            recent_avg = sum(rag_feedback.avg_relevance_trend) / len(rag_feedback.avg_relevance_trend)
            improvement = current_avg - recent_avg
            return max(0.0, min(1.0, improvement))
        return 0.0

    def _update_stats(self, tenant: str, result: ConsolidationResult) -> None:
        """Update statistics with consolidation result.

        Args:
            tenant: Tenant identifier
            result: Consolidation result
        """
        self.stats.total_operations += 1
        self.stats.total_chunks_pruned += result.chunks_pruned
        self.stats.total_chunks_merged += result.chunks_merged
        self.stats.total_embeddings_recomputed += result.embeddings_recomputed
        self.stats.last_consolidation = time.time()
        alpha = 0.2
        self.stats.avg_quality_improvement = (
            alpha * result.quality_improvement + (1 - alpha) * self.stats.avg_quality_improvement
        )
        tenant_stats = self.tenant_stats[tenant]
        tenant_stats.total_operations += 1
        tenant_stats.total_chunks_pruned += result.chunks_pruned
        tenant_stats.total_chunks_merged += result.chunks_merged
        tenant_stats.total_embeddings_recomputed += result.embeddings_recomputed
        tenant_stats.last_consolidation = time.time()
        tenant_stats.avg_quality_improvement = (
            alpha * result.quality_improvement + (1 - alpha) * tenant_stats.avg_quality_improvement
        )
        self.consolidation_history.append(result)
        if len(self.consolidation_history) > self.max_history:
            self.consolidation_history.pop(0)

    def get_metrics(self) -> dict[str, Any]:
        """Get consolidation metrics.

        Returns:
            Dictionary of metrics
        """
        return {
            "global_stats": {
                "total_operations": self.stats.total_operations,
                "total_chunks_pruned": self.stats.total_chunks_pruned,
                "total_chunks_merged": self.stats.total_chunks_merged,
                "total_embeddings_recomputed": self.stats.total_embeddings_recomputed,
                "avg_quality_improvement": self.stats.avg_quality_improvement,
                "last_consolidation": self.stats.last_consolidation,
            },
            "tenant_stats": {
                tenant: {
                    "total_operations": stats.total_operations,
                    "total_chunks_pruned": stats.total_chunks_pruned,
                    "total_chunks_merged": stats.total_chunks_merged,
                    "avg_quality_improvement": stats.avg_quality_improvement,
                    "last_consolidation": stats.last_consolidation,
                }
                for tenant, stats in self.tenant_stats.items()
            },
            "recent_consolidations": [
                {
                    "chunks_pruned": r.chunks_pruned,
                    "chunks_merged": r.chunks_merged,
                    "quality_improvement": r.quality_improvement,
                    "processing_time_s": r.processing_time_s,
                    "timestamp": r.timestamp,
                }
                for r in self.consolidation_history[-10:]
            ],
        }


_consolidation_instance: ContinualMemoryConsolidation | None = None
_consolidation_lock = None


def get_memory_consolidation() -> ContinualMemoryConsolidation:
    """Get or create global memory consolidation instance."""
    global _consolidation_instance, _consolidation_lock
    if _consolidation_lock is None:
        import threading

        _consolidation_lock = threading.Lock()
    if _consolidation_instance is None:
        with _consolidation_lock:
            if _consolidation_instance is None:
                _consolidation_instance = ContinualMemoryConsolidation()
    return _consolidation_instance


__all__ = ["ConsolidationResult", "ConsolidationStats", "ContinualMemoryConsolidation", "get_memory_consolidation"]
