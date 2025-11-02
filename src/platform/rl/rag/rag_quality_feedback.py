"""RAG Quality Feedback System

Instrument retrieval relevance → memory re-ranking/pruning with quality signals.
Provides feedback loop for continuous RAG improvement.
"""
from __future__ import annotations
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any
import numpy as np
from platform.core.step_result import StepResult
logger = logging.getLogger(__name__)

@dataclass
class RetrievalQualitySignal:
    """Quality signal for a retrieval operation"""
    query_id: str
    query_text: str
    retrieved_chunks: list[dict[str, Any]]
    relevance_scores: list[float]
    user_feedback: float | None = None
    implicit_feedback: float | None = None
    timestamp: float = field(default_factory=time.time)

@dataclass
class ChunkQualityMetrics:
    """Quality metrics for a memory chunk"""
    chunk_id: str
    retrieval_count: int = 0
    avg_relevance: float = 0.5
    avg_position: float = 5.0
    click_through_rate: float = 0.0
    dwell_time_avg: float = 0.0
    last_accessed: float = field(default_factory=time.time)
    quality_score: float = 0.5

class RAGQualityFeedback:
    """
    RAG Quality Feedback System

    Responsibilities:
    1. Collect relevance feedback from retrieval operations
    2. Track chunk-level quality metrics
    3. Identify low-quality chunks for pruning
    4. Re-rank chunks based on quality signals
    5. Trigger memory consolidation when quality degrades
    """

    def __init__(self, max_feedback_history: int=5000):
        self.feedback_history: deque[RetrievalQualitySignal] = deque(maxlen=max_feedback_history)
        self.chunk_metrics: dict[str, ChunkQualityMetrics] = {}
        self.total_retrievals = 0
        self.avg_relevance_trend: deque[float] = deque(maxlen=100)
        self.pruning_threshold = 0.3
        self.consolidation_threshold = 0.6

    def submit_retrieval_feedback(self, query_id: str, query_text: str, retrieved_chunks: list[dict[str, Any]], relevance_scores: list[float], user_feedback: float | None=None) -> StepResult:
        """Submit feedback for a retrieval operation"""
        try:
            signal = RetrievalQualitySignal(query_id=query_id, query_text=query_text, retrieved_chunks=retrieved_chunks, relevance_scores=relevance_scores, user_feedback=user_feedback)
            if relevance_scores:
                signal.implicit_feedback = np.mean(relevance_scores)
            self.feedback_history.append(signal)
            self._update_chunk_metrics(signal)
            if signal.implicit_feedback is not None:
                self.avg_relevance_trend.append(signal.implicit_feedback)
            self.total_retrievals += 1
            logger.debug(f'Retrieval feedback submitted: query={query_id}, relevance={signal.implicit_feedback:.2f if signal.implicit_feedback else \'N/A\'}')
            return StepResult.ok(message='Feedback submitted')
        except Exception as e:
            logger.error(f'Failed to submit retrieval feedback: {e}')
            return StepResult.fail(f'Feedback submission failed: {e}')

    def _update_chunk_metrics(self, signal: RetrievalQualitySignal) -> None:
        """Update quality metrics for retrieved chunks"""
        for i, chunk in enumerate(signal.retrieved_chunks):
            chunk_id = chunk.get('id') or chunk.get('chunk_id', f'chunk_{i}')
            if chunk_id not in self.chunk_metrics:
                self.chunk_metrics[chunk_id] = ChunkQualityMetrics(chunk_id=chunk_id)
            metrics = self.chunk_metrics[chunk_id]
            metrics.retrieval_count += 1
            metrics.last_accessed = time.time()
            if i < len(signal.relevance_scores):
                relevance = signal.relevance_scores[i]
                alpha = 0.2
                metrics.avg_relevance = (1 - alpha) * metrics.avg_relevance + alpha * relevance
            metrics.avg_position = 0.9 * metrics.avg_position + 0.1 * i
            metrics.quality_score = self._calculate_chunk_quality(metrics)

    def _calculate_chunk_quality(self, metrics: ChunkQualityMetrics) -> float:
        """Calculate overall quality score for a chunk"""
        relevance_score = metrics.avg_relevance
        usage_score = min(1.0, np.log1p(metrics.retrieval_count) / 5.0)
        age_days = (time.time() - metrics.last_accessed) / 86400
        recency_score = np.exp(-age_days / 30.0)
        position_bonus = 1.0 - min(metrics.avg_position, 10.0) / 20.0
        quality = 0.4 * relevance_score + 0.2 * usage_score + 0.2 * recency_score + 0.2 * position_bonus
        return min(1.0, max(0.0, quality))

    def get_pruning_candidates(self, min_retrievals: int=5, limit: int=100) -> list[str]:
        """Get list of chunk IDs that are candidates for pruning"""
        candidates = []
        for chunk_id, metrics in self.chunk_metrics.items():
            if metrics.retrieval_count < min_retrievals:
                continue
            if metrics.quality_score < self.pruning_threshold:
                candidates.append((chunk_id, metrics.quality_score))
        candidates.sort(key=lambda x: x[1])
        return [chunk_id for chunk_id, _ in candidates[:limit]]

    def get_re_ranking_scores(self, chunk_ids: list[str]) -> dict[str, float]:
        """Get quality-based re-ranking scores for chunks"""
        scores = {}
        for chunk_id in chunk_ids:
            if chunk_id in self.chunk_metrics:
                scores[chunk_id] = self.chunk_metrics[chunk_id].quality_score
            else:
                scores[chunk_id] = 0.5
        return scores

    def should_trigger_consolidation(self) -> tuple[bool, str]:
        """Check if memory consolidation should be triggered"""
        if len(self.avg_relevance_trend) < 20:
            return (False, 'insufficient_data')
        recent_avg = np.mean(list(self.avg_relevance_trend)[-20:])
        if recent_avg < self.consolidation_threshold:
            return (True, f'quality_degradation (avg={recent_avg:.2f})')
        low_quality_count = sum((1 for m in self.chunk_metrics.values() if m.quality_score < self.pruning_threshold))
        if low_quality_count > 100:
            return (True, f'excessive_low_quality_chunks ({low_quality_count})')
        return (False, 'quality_acceptable')

    def get_quality_report(self) -> dict[str, Any]:
        """Get comprehensive quality report"""
        if not self.chunk_metrics:
            return {'total_chunks': 0, 'total_retrievals': self.total_retrievals, 'avg_quality': 0.0}
        quality_scores = [m.quality_score for m in self.chunk_metrics.values()]
        return {'total_chunks': len(self.chunk_metrics), 'total_retrievals': self.total_retrievals, 'avg_quality': np.mean(quality_scores), 'quality_distribution': {'high (>0.7)': sum((1 for q in quality_scores if q > 0.7)), 'medium (0.4-0.7)': sum((1 for q in quality_scores if 0.4 <= q <= 0.7)), 'low (<0.4)': sum((1 for q in quality_scores if q < 0.4))}, 'pruning_candidates': len(self.get_pruning_candidates()), 'recent_relevance_trend': list(self.avg_relevance_trend)[-10:] if self.avg_relevance_trend else [], 'should_consolidate': self.should_trigger_consolidation()[0]}
_rag_feedback: RAGQualityFeedback | None = None

def get_rag_feedback(auto_create: bool=True) -> RAGQualityFeedback | None:
    """Get global RAG feedback instance"""
    global _rag_feedback
    if _rag_feedback is None and auto_create:
        _rag_feedback = RAGQualityFeedback()
    return _rag_feedback

def set_rag_feedback(feedback: RAGQualityFeedback) -> None:
    """Set global RAG feedback instance"""
    global _rag_feedback
    _rag_feedback = feedback
__all__ = ['ChunkQualityMetrics', 'RAGQualityFeedback', 'RetrievalQualitySignal', 'get_rag_feedback', 'set_rag_feedback']