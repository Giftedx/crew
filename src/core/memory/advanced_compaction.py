"""
Advanced memory compaction algorithms for vector storage optimization.

This module provides sophisticated memory compaction strategies to optimize
vector storage, reduce memory usage, and improve retrieval performance.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class CompactionStrategy(Enum):
    """Compaction strategies for different scenarios."""

    FREQUENCY_BASED = "frequency_based"  # Remove least frequently accessed
    RECENCY_BASED = "recency_based"  # Remove oldest entries
    SIMILARITY_BASED = "similarity_based"  # Remove highly similar entries
    HYBRID = "hybrid"  # Combination of strategies
    QUALITY_BASED = "quality_based"  # Remove low-quality entries
    COST_BASED = "cost_based"  # Remove based on storage cost


class CompactionTrigger(Enum):
    """Triggers for compaction operations."""

    SIZE_THRESHOLD = "size_threshold"  # When storage size exceeds threshold
    TIME_BASED = "time_based"  # Scheduled compaction
    QUALITY_DEGRADATION = "quality_degradation"  # When retrieval quality drops
    MANUAL = "manual"  # Manual compaction request
    MEMORY_PRESSURE = "memory_pressure"  # When memory usage is high


@dataclass
class CompactionConfig:
    """Configuration for memory compaction behavior."""

    # Trigger thresholds
    max_memory_usage_mb: float = 1000.0  # Maximum memory usage before compaction
    max_entries: int = 100000  # Maximum number of entries
    compaction_interval_hours: float = 24.0  # Scheduled compaction interval

    # Strategy selection
    primary_strategy: CompactionStrategy = CompactionStrategy.HYBRID
    fallback_strategies: list[CompactionStrategy] = field(
        default_factory=lambda: [
            CompactionStrategy.FREQUENCY_BASED,
            CompactionStrategy.RECENCY_BASED,
        ]
    )

    # Compaction parameters
    compaction_ratio: float = 0.2  # Fraction of entries to remove (20%)
    similarity_threshold: float = 0.95  # Similarity threshold for deduplication
    min_retention_days: int = 7  # Minimum retention period

    # Quality thresholds
    min_quality_score: float = 0.5  # Minimum quality score to retain
    quality_weight: float = 0.3  # Weight for quality in hybrid strategy

    # Performance settings
    batch_size: int = 1000  # Batch size for compaction operations
    enable_incremental: bool = True  # Enable incremental compaction
    parallel_compaction: bool = True  # Enable parallel processing

    # Monitoring
    enable_metrics: bool = True  # Enable compaction metrics
    log_compaction: bool = True  # Log compaction operations


@dataclass
class CompactionMetrics:
    """Metrics for compaction performance monitoring."""

    # Compaction statistics
    total_compactions: int = 0
    total_entries_removed: int = 0
    total_memory_freed_mb: float = 0.0
    average_compaction_time: float = 0.0

    # Strategy usage
    strategy_usage: dict[CompactionStrategy, int] = field(default_factory=dict)
    trigger_usage: dict[CompactionTrigger, int] = field(default_factory=dict)

    # Performance metrics
    compaction_frequency_per_hour: float = 0.0
    memory_reduction_percentage: float = 0.0
    quality_improvement_percentage: float = 0.0

    # Recent performance
    recent_compaction_times: deque[float] = field(default_factory=lambda: deque(maxlen=50))
    recent_memory_savings: deque[float] = field(default_factory=lambda: deque(maxlen=50))

    @property
    def average_recent_compaction_time(self) -> float:
        """Calculate average recent compaction time."""
        if not self.recent_compaction_times:
            return 0.0
        return sum(self.recent_compaction_times) / len(self.recent_compaction_times)

    @property
    def average_recent_memory_savings(self) -> float:
        """Calculate average recent memory savings."""
        if not self.recent_memory_savings:
            return 0.0
        return sum(self.recent_memory_savings) / len(self.recent_memory_savings)


@dataclass
class MemoryEntry:
    """Represents a memory entry with metadata for compaction."""

    id: str
    embedding: np.ndarray
    content: Any
    metadata: dict[str, Any]

    # Access tracking
    access_count: int = 0
    last_accessed: float = 0.0
    created_at: float = 0.0

    # Quality metrics
    quality_score: float = 1.0
    similarity_scores: dict[str, float] = field(default_factory=dict)

    # Storage metrics
    storage_size_bytes: int = 0
    computation_cost: float = 0.0

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()
        if self.last_accessed == 0.0:
            self.last_accessed = time.time()

    def update_access(self) -> None:
        """Update access tracking."""
        self.access_count += 1
        self.last_accessed = time.time()

    @property
    def age_days(self) -> float:
        """Get age of entry in days."""
        return (time.time() - self.created_at) / (24 * 3600)

    @property
    def access_frequency(self) -> float:
        """Calculate access frequency (accesses per day)."""
        if self.age_days == 0:
            return float("inf")
        return self.access_count / self.age_days

    @property
    def recency_score(self) -> float:
        """Calculate recency score (higher is more recent)."""
        days_since_access = (time.time() - self.last_accessed) / (24 * 3600)
        return 1.0 / (1.0 + days_since_access)


class AdvancedMemoryCompactor:
    """
    Advanced memory compactor with multiple strategies for optimal memory management.

    Provides sophisticated compaction algorithms to optimize vector storage,
    reduce memory usage, and maintain retrieval quality.
    """

    def __init__(self, config: CompactionConfig | None = None):
        """Initialize advanced memory compactor."""
        self.config = config or CompactionConfig()
        self.metrics = CompactionMetrics()
        self.entries: dict[str, MemoryEntry] = {}

        # Compaction state
        self.last_compaction_time = 0.0
        self.compaction_in_progress = False

        # Similarity cache for efficient similarity-based compaction
        self._similarity_cache: dict[tuple[str, str], float] = {}

        logger.info(f"Advanced memory compactor initialized with config: {self.config}")

    async def add_entry(
        self,
        entry_id: str,
        embedding: np.ndarray,
        content: Any,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add entry to memory with compaction tracking."""
        if metadata is None:
            metadata = {}

        # Calculate storage size (approximate)
        storage_size = len(embedding.tobytes()) + len(str(content).encode())

        entry = MemoryEntry(
            id=entry_id,
            embedding=embedding,
            content=content,
            metadata=metadata,
            storage_size_bytes=storage_size,
            computation_cost=self._calculate_computation_cost(embedding),
        )

        self.entries[entry_id] = entry

        # Check if compaction is needed
        if self._should_trigger_compaction(CompactionTrigger.SIZE_THRESHOLD):
            await self.compact(CompactionTrigger.SIZE_THRESHOLD)

    async def get_entry(self, entry_id: str) -> MemoryEntry | None:
        """Get entry and update access tracking."""
        entry = self.entries.get(entry_id)
        if entry:
            entry.update_access()
        return entry

    async def compact(self, trigger: CompactionTrigger = CompactionTrigger.MANUAL) -> dict[str, Any]:
        """Perform memory compaction using configured strategy."""
        if self.compaction_in_progress:
            logger.warning("Compaction already in progress, skipping")
            return {"status": "skipped", "reason": "compaction_in_progress"}

        start_time = time.time()
        self.compaction_in_progress = True

        try:
            # Determine compaction strategy
            strategy = self._select_compaction_strategy(trigger)

            # Perform compaction
            result = await self._execute_compaction(strategy, trigger)

            # Update metrics
            self._update_metrics(strategy, trigger, time.time() - start_time, result)

            self.last_compaction_time = time.time()

            if self.config.log_compaction:
                logger.info(
                    f"Compaction completed using {strategy.value} strategy. "
                    f"Removed {result['entries_removed']} entries, "
                    f"freed {result['memory_freed_mb']:.2f} MB in {result['compaction_time']:.3f}s"
                )

            return result

        finally:
            self.compaction_in_progress = False

    async def _execute_compaction(self, strategy: CompactionStrategy, trigger: CompactionTrigger) -> dict[str, Any]:
        """Execute compaction using specified strategy."""
        start_time = time.time()

        # Calculate entries to remove
        total_entries = len(self.entries)
        entries_to_remove = int(total_entries * self.config.compaction_ratio)

        if entries_to_remove == 0:
            return {
                "status": "skipped",
                "reason": "no_entries_to_remove",
                "entries_removed": 0,
                "memory_freed_mb": 0.0,
                "compaction_time": time.time() - start_time,
            }

        # Select entries for removal based on strategy
        if strategy == CompactionStrategy.FREQUENCY_BASED:
            entries_to_remove_ids = await self._select_by_frequency(entries_to_remove)
        elif strategy == CompactionStrategy.RECENCY_BASED:
            entries_to_remove_ids = await self._select_by_recency(entries_to_remove)
        elif strategy == CompactionStrategy.SIMILARITY_BASED:
            entries_to_remove_ids = await self._select_by_similarity(entries_to_remove)
        elif strategy == CompactionStrategy.QUALITY_BASED:
            entries_to_remove_ids = await self._select_by_quality(entries_to_remove)
        elif strategy == CompactionStrategy.HYBRID:
            entries_to_remove_ids = await self._select_by_hybrid(entries_to_remove)
        else:
            raise ValueError(f"Unknown compaction strategy: {strategy}")

        # Remove entries
        memory_freed = 0.0
        for entry_id in entries_to_remove_ids:
            entry = self.entries.pop(entry_id, None)
            if entry:
                memory_freed += entry.storage_size_bytes

        # Clean up similarity cache
        self._cleanup_similarity_cache(entries_to_remove_ids)

        memory_freed_mb = memory_freed / (1024 * 1024)

        return {
            "status": "completed",
            "strategy_used": strategy.value,
            "entries_removed": len(entries_to_remove_ids),
            "memory_freed_mb": memory_freed_mb,
            "compaction_time": time.time() - start_time,
            "remaining_entries": len(self.entries),
        }

    async def _select_by_frequency(self, count: int) -> list[str]:
        """Select entries with lowest access frequency."""
        entries_list = list(self.entries.values())
        entries_list.sort(key=lambda x: x.access_frequency)

        return [entry.id for entry in entries_list[:count]]

    async def _select_by_recency(self, count: int) -> list[str]:
        """Select oldest entries (lowest recency score)."""
        entries_list = list(self.entries.values())
        entries_list.sort(key=lambda x: x.recency_score)

        return [entry.id for entry in entries_list[:count]]

    async def _select_by_similarity(self, count: int) -> list[str]:
        """Select highly similar entries for removal."""
        if len(self.entries) < 2:
            return []

        # Build similarity matrix
        entries_list = list(self.entries.values())
        similarity_matrix = await self._build_similarity_matrix(entries_list)

        # Find highly similar pairs
        similar_pairs = []
        for i in range(len(entries_list)):
            for j in range(i + 1, len(entries_list)):
                similarity = similarity_matrix[i][j]
                if similarity > self.config.similarity_threshold:
                    similar_pairs.append((similarity, i, j))

        # Sort by similarity (highest first)
        similar_pairs.sort(key=lambda x: x[0], reverse=True)

        # Select entries to remove (keep one from each similar pair)
        removed_ids = set()
        for _similarity, i, j in similar_pairs:
            if len(removed_ids) >= count:
                break

            # Keep the entry with higher quality score
            if entries_list[i].quality_score >= entries_list[j].quality_score:
                removed_ids.add(entries_list[j].id)
            else:
                removed_ids.add(entries_list[i].id)

        return list(removed_ids)

    async def _select_by_quality(self, count: int) -> list[str]:
        """Select entries with lowest quality scores."""
        entries_list = list(self.entries.values())
        entries_list.sort(key=lambda x: x.quality_score)

        # Filter out entries above minimum quality threshold
        low_quality_entries = [entry for entry in entries_list if entry.quality_score < self.config.min_quality_score]

        return [entry.id for entry in low_quality_entries[:count]]

    async def _select_by_hybrid(self, count: int) -> list[str]:
        """Select entries using hybrid scoring."""
        entries_list = list(self.entries.values())

        # Calculate hybrid scores
        for entry in entries_list:
            # Normalize scores (0-1 range)
            freq_score = 1.0 / (1.0 + entry.access_frequency)  # Lower frequency = higher score for removal
            recency_score = 1.0 - entry.recency_score  # Lower recency = higher score for removal
            quality_score = 1.0 - entry.quality_score  # Lower quality = higher score for removal

            # Weighted combination
            hybrid_score = (
                freq_score * 0.4  # 40% frequency weight
                + recency_score * 0.3  # 30% recency weight
                + quality_score * self.config.quality_weight  # Configurable quality weight
            )

            entry.metadata["hybrid_score"] = hybrid_score

        # Sort by hybrid score (highest scores for removal)
        entries_list.sort(key=lambda x: x.metadata.get("hybrid_score", 0), reverse=True)

        return [entry.id for entry in entries_list[:count]]

    async def _build_similarity_matrix(self, entries: list[MemoryEntry]) -> np.ndarray:
        """Build similarity matrix for entries."""
        n = len(entries)
        similarity_matrix = np.zeros((n, n))

        # Use parallel processing if enabled
        if self.config.parallel_compaction and n > 100:
            await self._build_similarity_matrix_parallel(entries, similarity_matrix)
        else:
            await self._build_similarity_matrix_sequential(entries, similarity_matrix)

        return similarity_matrix

    async def _build_similarity_matrix_sequential(
        self, entries: list[MemoryEntry], similarity_matrix: np.ndarray
    ) -> None:
        """Build similarity matrix sequentially."""
        n = len(entries)
        for i in range(n):
            for j in range(i + 1, n):
                similarity = self._calculate_similarity(entries[i], entries[j])
                similarity_matrix[i][j] = similarity
                similarity_matrix[j][i] = similarity

    async def _build_similarity_matrix_parallel(
        self, entries: list[MemoryEntry], similarity_matrix: np.ndarray
    ) -> None:
        """Build similarity matrix in parallel."""
        n = len(entries)

        # Create tasks for parallel computation
        tasks = []
        for i in range(n):
            for j in range(i + 1, n):
                task = asyncio.create_task(
                    self._compute_similarity_pair(entries[i], entries[j], i, j, similarity_matrix)
                )
                tasks.append(task)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

    async def _compute_similarity_pair(
        self,
        entry1: MemoryEntry,
        entry2: MemoryEntry,
        i: int,
        j: int,
        similarity_matrix: np.ndarray,
    ) -> None:
        """Compute similarity for a pair of entries."""
        similarity = self._calculate_similarity(entry1, entry2)
        similarity_matrix[i][j] = similarity
        similarity_matrix[j][i] = similarity

    def _calculate_similarity(self, entry1: MemoryEntry, entry2: MemoryEntry) -> float:
        """Calculate cosine similarity between two entries."""
        # Check cache first
        cache_key = tuple(sorted([entry1.id, entry2.id]))
        if cache_key in self._similarity_cache:
            return self._similarity_cache[cache_key]

        # Calculate cosine similarity
        emb1 = entry1.embedding
        emb2 = entry2.embedding

        # Normalize embeddings
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        similarity = 0.0 if norm1 == 0 or norm2 == 0 else np.dot(emb1, emb2) / (norm1 * norm2)

        # Cache result
        self._similarity_cache[cache_key] = similarity

        return similarity

    def _calculate_computation_cost(self, embedding: np.ndarray) -> float:
        """Calculate computational cost of an embedding."""
        # Simple cost model based on dimension
        return len(embedding) * 0.001  # 0.001 cost per dimension

    def _should_trigger_compaction(self, trigger: CompactionTrigger) -> bool:
        """Check if compaction should be triggered."""
        if trigger == CompactionTrigger.SIZE_THRESHOLD:
            # Check memory usage
            total_memory_mb = sum(entry.storage_size_bytes for entry in self.entries.values()) / (1024 * 1024)
            return total_memory_mb > self.config.max_memory_usage_mb

        elif trigger == CompactionTrigger.TIME_BASED:
            # Check time since last compaction
            time_since_compaction = time.time() - self.last_compaction_time
            return time_since_compaction > (self.config.compaction_interval_hours * 3600)

        elif trigger == CompactionTrigger.MANUAL:
            return True

        return False

    def _select_compaction_strategy(self, trigger: CompactionTrigger) -> CompactionStrategy:
        """Select appropriate compaction strategy based on trigger and conditions."""
        # Use primary strategy by default
        strategy = self.config.primary_strategy

        # Override based on trigger
        if trigger == CompactionTrigger.QUALITY_DEGRADATION:
            strategy = CompactionStrategy.QUALITY_BASED
        elif trigger == CompactionTrigger.MEMORY_PRESSURE:
            strategy = CompactionStrategy.FREQUENCY_BASED

        return strategy

    def _update_metrics(
        self,
        strategy: CompactionStrategy,
        trigger: CompactionTrigger,
        compaction_time: float,
        result: dict[str, Any],
    ) -> None:
        """Update compaction metrics."""
        self.metrics.total_compactions += 1
        self.metrics.total_entries_removed += result.get("entries_removed", 0)
        self.metrics.total_memory_freed_mb += result.get("memory_freed_mb", 0.0)

        # Update strategy and trigger usage
        self.metrics.strategy_usage[strategy] = self.metrics.strategy_usage.get(strategy, 0) + 1
        self.metrics.trigger_usage[trigger] = self.metrics.trigger_usage.get(trigger, 0) + 1

        # Update recent performance
        self.metrics.recent_compaction_times.append(compaction_time)
        self.metrics.recent_memory_savings.append(result.get("memory_freed_mb", 0.0))

        # Update averages
        self.metrics.average_compaction_time = self.metrics.total_memory_freed_mb / max(
            1, self.metrics.total_compactions
        )

    def _cleanup_similarity_cache(self, removed_entry_ids: list[str]) -> None:
        """Clean up similarity cache for removed entries."""
        keys_to_remove = []
        for cache_key in self._similarity_cache:
            if any(entry_id in cache_key for entry_id in removed_entry_ids):
                keys_to_remove.append(cache_key)

        for key in keys_to_remove:
            self._similarity_cache.pop(key, None)

    def get_memory_stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        total_entries = len(self.entries)
        total_memory_mb = sum(entry.storage_size_bytes for entry in self.entries.values()) / (1024 * 1024)

        # Calculate average metrics
        avg_access_count = sum(entry.access_count for entry in self.entries.values()) / max(1, total_entries)
        avg_quality_score = sum(entry.quality_score for entry in self.entries.values()) / max(1, total_entries)
        avg_age_days = sum(entry.age_days for entry in self.entries.values()) / max(1, total_entries)

        return {
            "total_entries": total_entries,
            "total_memory_mb": total_memory_mb,
            "average_access_count": avg_access_count,
            "average_quality_score": avg_quality_score,
            "average_age_days": avg_age_days,
            "compaction_metrics": self.metrics,
            "memory_usage_percentage": (total_memory_mb / self.config.max_memory_usage_mb) * 100,
        }

    async def optimize_quality(self, min_quality_threshold: float | None = None) -> dict[str, Any]:
        """Optimize memory by removing low-quality entries."""
        threshold = min_quality_threshold or self.config.min_quality_score

        low_quality_entries = [entry_id for entry_id, entry in self.entries.items() if entry.quality_score < threshold]

        if not low_quality_entries:
            return {"status": "no_low_quality_entries", "entries_removed": 0}

        # Remove low-quality entries
        memory_freed = 0.0
        for entry_id in low_quality_entries:
            entry = self.entries.pop(entry_id, None)
            if entry:
                memory_freed += entry.storage_size_bytes

        memory_freed_mb = memory_freed / (1024 * 1024)

        return {
            "status": "completed",
            "entries_removed": len(low_quality_entries),
            "memory_freed_mb": memory_freed_mb,
            "quality_threshold": threshold,
        }
