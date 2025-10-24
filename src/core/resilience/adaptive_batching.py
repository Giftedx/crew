"""
Adaptive batching system for improved pipeline throughput.

This module provides intelligent batching capabilities that automatically adjust
batch sizes based on system performance, load, and resource utilization.
"""

from __future__ import annotations

import asyncio
import logging
import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, TypeVar


if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


class BatchStrategy(Enum):
    """Batching strategies for different scenarios."""

    FIXED = "fixed"  # Fixed batch size
    ADAPTIVE = "adaptive"  # Dynamically adjust based on performance
    TIME_BASED = "time_based"  # Batch based on time windows
    LOAD_BASED = "load_based"  # Adjust based on system load
    HYBRID = "hybrid"  # Combination of strategies


@dataclass
class BatchConfig:
    """Configuration for adaptive batching behavior."""

    # Basic configuration
    initial_batch_size: int = 10
    min_batch_size: int = 1
    max_batch_size: int = 100
    batch_timeout_seconds: float = 5.0

    # Adaptive configuration
    target_processing_time_ms: float = 1000.0  # Target processing time per batch
    adaptation_factor: float = 0.1  # How aggressively to adjust batch size
    adaptation_window: int = 10  # Number of batches to consider for adaptation

    # Performance thresholds
    performance_threshold_high: float = 0.8  # High performance threshold
    performance_threshold_low: float = 0.6  # Low performance threshold

    # Load-based configuration
    max_concurrent_batches: int = 5
    load_check_interval_seconds: float = 1.0

    # Monitoring
    enable_metrics: bool = True
    log_adaptations: bool = True


@dataclass
class BatchMetrics:
    """Metrics for batch performance monitoring."""

    total_batches: int = 0
    total_items: int = 0
    total_processing_time: float = 0.0
    average_batch_size: float = 0.0
    average_processing_time: float = 0.0
    throughput_items_per_second: float = 0.0

    # Performance tracking
    recent_batch_times: deque[float] = field(default_factory=lambda: deque(maxlen=50))
    recent_batch_sizes: deque[int] = field(default_factory=lambda: deque(maxlen=50))

    # Adaptation tracking
    adaptation_count: int = 0
    last_adaptation_time: float | None = None

    @property
    def average_recent_processing_time(self) -> float:
        """Calculate average processing time from recent batches."""
        if not self.recent_batch_times:
            return 0.0
        return statistics.mean(self.recent_batch_times)

    @property
    def average_recent_batch_size(self) -> float:
        """Calculate average batch size from recent batches."""
        if not self.recent_batch_sizes:
            return 0.0
        return statistics.mean(self.recent_batch_sizes)

    @property
    def efficiency_score(self) -> float:
        """Calculate efficiency score (items processed per millisecond)."""
        if self.average_recent_processing_time == 0:
            return 0.0
        return self.average_recent_batch_size / (self.average_recent_processing_time / 1000.0)


class AdaptiveBatcher(Generic[T, R]):
    """
    Adaptive batching system that automatically adjusts batch sizes
    based on performance metrics and system load.
    """

    def __init__(
        self,
        name: str,
        processor: Callable[[list[T]], R],
        config: BatchConfig | None = None,
    ):
        """Initialize adaptive batcher."""
        self.name = name
        self.processor = processor
        self.config = config or BatchConfig()
        self.metrics = BatchMetrics()

        # State tracking
        self.current_batch_size = self.config.initial_batch_size
        self.pending_items: list[T] = []
        self.active_batches = 0
        self.last_adaptation_time = 0.0

        # Performance tracking
        self.performance_history: deque[float] = deque(maxlen=self.config.adaptation_window)

        # Synchronization
        self._lock = asyncio.Lock()
        self._batch_timer: asyncio.Task | None = None

        logger.info(f"Adaptive batcher '{name}' initialized with batch size {self.current_batch_size}")

    async def add_item(self, item: T) -> None:
        """Add item to current batch."""
        async with self._lock:
            self.pending_items.append(item)

            # Check if we should process batch
            if len(self.pending_items) >= self.current_batch_size:
                await self._process_batch()
            elif self._batch_timer is None:
                # Start timer for timeout-based batching
                self._batch_timer = asyncio.create_task(self._batch_timeout())

    async def add_items(self, items: list[T]) -> None:
        """Add multiple items to current batch."""
        async with self._lock:
            self.pending_items.extend(items)

            # Process in batches if we exceed current batch size
            while len(self.pending_items) >= self.current_batch_size:
                batch = self.pending_items[: self.current_batch_size]
                self.pending_items = self.pending_items[self.current_batch_size :]
                await self._process_batch_items(batch)

            # Start timer if we have pending items
            if self.pending_items and self._batch_timer is None:
                self._batch_timer = asyncio.create_task(self._batch_timeout())

    async def flush(self) -> None:
        """Force processing of all pending items."""
        async with self._lock:
            if self.pending_items:
                await self._process_batch()

    async def _batch_timeout(self) -> None:
        """Handle batch timeout."""
        try:
            await asyncio.sleep(self.config.batch_timeout_seconds)
            async with self._lock:
                if self.pending_items:
                    await self._process_batch()
        except asyncio.CancelledError:
            pass
        finally:
            self._batch_timer = None

    async def _process_batch(self) -> None:
        """Process current batch."""
        if not self.pending_items:
            return

        batch = self.pending_items.copy()
        self.pending_items.clear()

        # Cancel timer if running
        if self._batch_timer:
            self._batch_timer.cancel()
            self._batch_timer = None

        await self._process_batch_items(batch)

    async def _process_batch_items(self, batch: list[T]) -> None:
        """Process a batch of items."""
        if not batch:
            return

        # Check concurrent batch limit
        if self.active_batches >= self.config.max_concurrent_batches:
            # Wait for a batch to complete
            while self.active_batches >= self.config.max_concurrent_batches:
                await asyncio.sleep(0.01)

        self.active_batches += 1

        try:
            start_time = time.time()

            # Process batch
            result = await self._execute_processor(batch)

            # Record metrics
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            await self._record_batch_metrics(len(batch), processing_time)

            # Adapt batch size if needed
            await self._adapt_batch_size(processing_time, len(batch))

            return result

        finally:
            self.active_batches -= 1

    async def _execute_processor(self, batch: list[T]) -> R:
        """Execute the processor function with proper error handling."""
        try:
            if asyncio.iscoroutinefunction(self.processor):
                return await self.processor(batch)
            else:
                return self.processor(batch)
        except Exception as e:
            logger.error(f"Batch processor failed for batcher '{self.name}': {e}")
            raise

    async def _record_batch_metrics(self, batch_size: int, processing_time: float) -> None:
        """Record metrics for a processed batch."""
        self.metrics.total_batches += 1
        self.metrics.total_items += batch_size
        self.metrics.total_processing_time += processing_time

        # Update averages
        self.metrics.average_batch_size = self.metrics.total_items / self.metrics.total_batches
        self.metrics.average_processing_time = self.metrics.total_processing_time / self.metrics.total_batches

        # Update throughput
        total_time_seconds = self.metrics.total_processing_time / 1000.0
        if total_time_seconds > 0:
            self.metrics.throughput_items_per_second = self.metrics.total_items / total_time_seconds

        # Track recent performance
        self.metrics.recent_batch_times.append(processing_time)
        self.metrics.recent_batch_sizes.append(batch_size)

        # Calculate performance score
        performance_score = self._calculate_performance_score(processing_time, batch_size)
        self.performance_history.append(performance_score)

    def _calculate_performance_score(self, processing_time: float, batch_size: int) -> float:
        """Calculate performance score for a batch."""
        # Normalize processing time (lower is better)
        time_score = max(0, 1 - (processing_time / self.config.target_processing_time_ms))

        # Normalize batch size (higher is better, up to a point)
        size_score = min(1, batch_size / self.config.max_batch_size)

        # Combine scores (weighted average)
        return 0.7 * time_score + 0.3 * size_score

    async def _adapt_batch_size(self, processing_time: float, batch_size: int) -> None:
        """Adapt batch size based on performance."""
        if time.time() - self.last_adaptation_time < 1.0:  # Throttle adaptations
            return

        if len(self.performance_history) < self.config.adaptation_window:
            return

        # Calculate average performance
        avg_performance = statistics.mean(self.performance_history)

        # Determine adaptation direction
        if avg_performance > self.config.performance_threshold_high:
            # High performance - can increase batch size
            new_size = min(
                self.config.max_batch_size,
                int(self.current_batch_size * (1 + self.config.adaptation_factor)),
            )
            if new_size != self.current_batch_size:
                await self._update_batch_size(new_size, "high_performance")

        elif avg_performance < self.config.performance_threshold_low:
            # Low performance - decrease batch size
            new_size = max(
                self.config.min_batch_size,
                int(self.current_batch_size * (1 - self.config.adaptation_factor)),
            )
            if new_size != self.current_batch_size:
                await self._update_batch_size(new_size, "low_performance")

    async def _update_batch_size(self, new_size: int, reason: str) -> None:
        """Update batch size with logging."""
        old_size = self.current_batch_size
        self.current_batch_size = new_size
        self.last_adaptation_time = time.time()

        self.metrics.adaptation_count += 1
        self.metrics.last_adaptation_time = self.last_adaptation_time

        if self.config.log_adaptations:
            logger.info(f"Batcher '{self.name}' adapted batch size from {old_size} to {new_size} (reason: {reason})")

    def get_metrics(self) -> BatchMetrics:
        """Get current batch metrics."""
        return self.metrics

    def get_current_batch_size(self) -> int:
        """Get current batch size."""
        return self.current_batch_size

    def set_batch_size(self, size: int) -> None:
        """Manually set batch size."""
        size = max(self.config.min_batch_size, min(self.config.max_batch_size, size))
        self.current_batch_size = size
        logger.info(f"Batcher '{self.name}' batch size manually set to {size}")


class BatchManager:
    """Manager for multiple adaptive batchers."""

    def __init__(self):
        self._batchers: dict[str, AdaptiveBatcher] = {}
        self._lock = asyncio.Lock()

    async def create_batcher(
        self,
        name: str,
        processor: Callable[[list[T]], R],
        config: BatchConfig | None = None,
    ) -> AdaptiveBatcher[T, R]:
        """Create a new adaptive batcher."""
        async with self._lock:
            if name in self._batchers:
                raise ValueError(f"Batcher '{name}' already exists")

            batcher = AdaptiveBatcher(name, processor, config)
            self._batchers[name] = batcher
            return batcher

    def get_batcher(self, name: str) -> AdaptiveBatcher | None:
        """Get an existing batcher."""
        return self._batchers.get(name)

    def get_all_batchers(self) -> dict[str, AdaptiveBatcher]:
        """Get all batchers."""
        return self._batchers.copy()

    async def flush_all(self) -> None:
        """Flush all pending batches."""
        for batcher in self._batchers.values():
            await batcher.flush()

    def get_global_metrics(self) -> dict[str, Any]:
        """Get aggregated metrics from all batchers."""
        total_batches = sum(batcher.metrics.total_batches for batcher in self._batchers.values())
        total_items = sum(batcher.metrics.total_items for batcher in self._batchers.values())
        total_time = sum(batcher.metrics.total_processing_time for batcher in self._batchers.values())

        return {
            "total_batchers": len(self._batchers),
            "total_batches": total_batches,
            "total_items": total_items,
            "total_processing_time": total_time,
            "overall_throughput": total_items / max(1, total_time / 1000.0),
            "batchers": {
                name: {
                    "current_batch_size": batcher.current_batch_size,
                    "metrics": {
                        "total_batches": batcher.metrics.total_batches,
                        "total_items": batcher.metrics.total_items,
                        "average_batch_size": batcher.metrics.average_batch_size,
                        "throughput": batcher.metrics.throughput_items_per_second,
                        "efficiency_score": batcher.metrics.efficiency_score,
                    },
                }
                for name, batcher in self._batchers.items()
            },
        }


# Global batch manager
_global_batch_manager = BatchManager()


def get_batch_manager() -> BatchManager:
    """Get the global batch manager."""
    return _global_batch_manager


async def create_batcher(
    name: str, processor: Callable[[list[T]], R], config: BatchConfig | None = None
) -> AdaptiveBatcher[T, R]:
    """Create a new batcher using the global manager."""
    return await _global_batch_manager.create_batcher(name, processor, config)


def get_batcher(name: str) -> AdaptiveBatcher | None:
    """Get a batcher from the global manager."""
    return _global_batch_manager.get_batcher(name)
