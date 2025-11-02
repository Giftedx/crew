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
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


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
        min_consolidation_interval_s: float = 3600.0,  # 1 hour
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

        # Statistics
        self.stats = ConsolidationStats()

        # Per-tenant tracking
        self.tenant_stats: dict[str, ConsolidationStats] = defaultdict(ConsolidationStats)

        # Operation history
        self.consolidation_history: list[ConsolidationResult] = []
        self.max_history = 100

        logger.info(
            f"ContinualMemoryConsolidation initialized: "
            f"interval={min_consolidation_interval_s}s, "
            f"batch_size={prune_batch_size}"
        )

    async def consolidate_memory(
        self,
        tenant: str,
        workspace: str,
        trigger_reason: str = "scheduled",
    ) -> StepResult:
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
            # Check if we can consolidate (respect min interval)
            if not self._can_consolidate(tenant):
                return StepResult.skip(
                    message="Skipping consolidation: too soon since last run",
                    data={"last_consolidation": self.stats.last_consolidation},
                )

            logger.info(f"Starting memory consolidation for {tenant}/{workspace}: {trigger_reason}")

            # Get quality feedback system
            from ai.rag.rag_quality_feedback import get_rag_feedback

            rag_feedback = get_rag_feedback()
            if not rag_feedback:
                return StepResult.fail(error="RAG quality feedback system not available")

            # Get memory service
            memory_service = await self._get_memory_service()
            if not memory_service:
                return StepResult.fail(error="Memory service not available")

            # Phase 1: Prune low-quality chunks
            pruned_count = await self._prune_low_quality_chunks(tenant, workspace, rag_feedback, memory_service)

            # Phase 2: Merge similar chunks
            merged_count = await self._merge_similar_chunks(tenant, workspace, rag_feedback, memory_service)

            # Phase 3: Re-compute embeddings
            recomputed_count = await self._recompute_embeddings(tenant, workspace, memory_service)

            # Phase 4: Re-index (optimize vector store)
            reindexed_count = await self._reindex_vectors(tenant, workspace, memory_service)

            # Calculate quality improvement
            quality_improvement = self._calculate_quality_improvement(rag_feedback)

            # Update statistics
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
                f"Consolidation complete: pruned={pruned_count}, merged={merged_count}, "
                f"recomputed={recomputed_count}, quality_improvement={quality_improvement:.2%}, "
                f"time={processing_time:.2f}s"
            )

            return StepResult.ok(data=result)

        except Exception as e:
            logger.error(f"Memory consolidation failed: {e}", exc_info=True)
            return StepResult.fail(error=f"Consolidation failed: {e}")

    async def _prune_low_quality_chunks(
        self,
        tenant: str,
        workspace: str,
        rag_feedback,
        memory_service,
    ) -> int:
        """Prune low-quality chunks from memory.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            rag_feedback: RAG quality feedback system
            memory_service: Memory service instance

        Returns:
            Number of chunks pruned
        """
        # Get pruning candidates
        candidates = rag_feedback.get_pruning_candidates(min_retrievals=5, limit=self.prune_batch_size)

        if not candidates:
            logger.debug("No chunks to prune")
            return 0

        logger.info(f"Pruning {len(candidates)} low-quality chunks")

        pruned = 0
        for chunk_id in candidates:
            try:
                # Delete chunk from memory
                result = await memory_service.delete(tenant=tenant, workspace=workspace, chunk_id=chunk_id)

                if result.success:
                    pruned += 1

                    # Remove from quality tracking
                    if chunk_id in rag_feedback.chunk_metrics:
                        del rag_feedback.chunk_metrics[chunk_id]

            except Exception as e:
                logger.warning(f"Failed to prune chunk {chunk_id}: {e}")

        return pruned

    async def _merge_similar_chunks(
        self,
        tenant: str,
        workspace: str,
        rag_feedback,
        memory_service,
    ) -> int:
        """Merge similar/redundant chunks.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            rag_feedback: RAG quality feedback system
            memory_service: Memory service instance

        Returns:
            Number of chunks merged
        """
        # Get chunks with quality metrics
        chunks_with_metrics = [
            (chunk_id, metrics)
            for chunk_id, metrics in rag_feedback.chunk_metrics.items()
            if metrics.retrieval_count >= 3  # Only merge well-established chunks
        ]

        if len(chunks_with_metrics) < 2:
            logger.debug("Not enough chunks for merging")
            return 0

        # TODO: Implement similarity detection using embeddings
        # For now, return 0 as placeholder
        # This would require:
        # 1. Load chunk embeddings from memory service
        # 2. Compute pairwise similarity
        # 3. Group chunks above similarity threshold
        # 4. Merge content and metadata
        # 5. Re-embed merged content
        # 6. Delete original chunks
        # 7. Store merged chunk

        logger.debug("Chunk merging not yet implemented")
        return 0

    async def _recompute_embeddings(
        self,
        tenant: str,
        workspace: str,
        memory_service,
    ) -> int:
        """Re-compute embeddings for consolidated chunks.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            memory_service: Memory service instance

        Returns:
            Number of embeddings recomputed
        """
        # TODO: Implement embedding re-computation
        # This would require:
        # 1. Identify chunks needing re-embedding (merged, updated)
        # 2. Extract text content
        # 3. Generate new embeddings
        # 4. Update in memory service

        logger.debug("Embedding re-computation not yet implemented")
        return 0

    async def _reindex_vectors(
        self,
        tenant: str,
        workspace: str,
        memory_service,
    ) -> int:
        """Re-index vectors for improved retrieval.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            memory_service: Memory service instance

        Returns:
            Number of vectors re-indexed
        """
        # TODO: Implement vector re-indexing
        # This would require:
        # 1. Trigger vector store optimization
        # 2. Rebuild indexes if needed
        # 3. Compact storage

        logger.debug("Vector re-indexing not yet implemented")
        return 0

    async def _get_memory_service(self):
        """Get unified memory service instance."""
        try:
            from ultimate_discord_intelligence_bot.memory import get_unified_memory

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
        # Get current average quality
        if not rag_feedback.chunk_metrics:
            return 0.0

        current_avg = sum(m.quality_score for m in rag_feedback.chunk_metrics.values()) / len(
            rag_feedback.chunk_metrics
        )

        # Compare to recent trend
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
        # Update global stats
        self.stats.total_operations += 1
        self.stats.total_chunks_pruned += result.chunks_pruned
        self.stats.total_chunks_merged += result.chunks_merged
        self.stats.total_embeddings_recomputed += result.embeddings_recomputed
        self.stats.last_consolidation = time.time()

        # EMA for quality improvement
        alpha = 0.2
        self.stats.avg_quality_improvement = (
            alpha * result.quality_improvement + (1 - alpha) * self.stats.avg_quality_improvement
        )

        # Update tenant stats
        tenant_stats = self.tenant_stats[tenant]
        tenant_stats.total_operations += 1
        tenant_stats.total_chunks_pruned += result.chunks_pruned
        tenant_stats.total_chunks_merged += result.chunks_merged
        tenant_stats.total_embeddings_recomputed += result.embeddings_recomputed
        tenant_stats.last_consolidation = time.time()
        tenant_stats.avg_quality_improvement = (
            alpha * result.quality_improvement + (1 - alpha) * tenant_stats.avg_quality_improvement
        )

        # Add to history
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
                for r in self.consolidation_history[-10:]  # Last 10
            ],
        }


# Global singleton
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


__all__ = [
    "ConsolidationResult",
    "ConsolidationStats",
    "ContinualMemoryConsolidation",
    "get_memory_consolidation",
]
