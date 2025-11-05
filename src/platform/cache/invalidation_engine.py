"""
Cache invalidation engine for dependency-based cache invalidation.

This module provides the core invalidation logic that handles cascading invalidation
of cache entries based on their dependency relationships.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from platform.cache.dependency_tracker import DependencyTracker, get_dependency_tracker
from typing import Any


logger = logging.getLogger(__name__)
CIRCUIT_BREAKER_RESET_TIMEOUT = 30

@dataclass
class InvalidationResult:
    """Result of an invalidation operation."""
    invalidated_keys: set[str] = field(default_factory=set)
    skipped_keys: set[str] = field(default_factory=set)
    errors: list[str] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: float = field(default_factory=time.time)

    @property
    def duration_ms(self) -> float:
        """Get the duration of the invalidation operation in milliseconds."""
        return (self.end_time - self.start_time) * 1000

    @property
    def total_processed(self) -> int:
        """Get the total number of keys processed."""
        return len(self.invalidated_keys) + len(self.skipped_keys)

    @property
    def success_rate(self) -> float:
        """Get the success rate of the invalidation operation."""
        if self.total_processed == 0:
            return 1.0
        return len(self.invalidated_keys) / self.total_processed

@dataclass
class InvalidationBatch:
    """Batch of keys to be invalidated together."""
    keys: set[str]
    reason: str
    priority: int = 1
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other: InvalidationBatch) -> bool:
        """Compare batches by priority (higher priority first)."""
        return self.priority > other.priority

class InvalidationEngine:
    """Engine for handling cache invalidation operations."""

    def __init__(self, dependency_tracker: DependencyTracker | None=None, max_batch_size: int=100, max_concurrent_invalidations: int=10, enable_circuit_breaker: bool=True, circuit_breaker_threshold: int=5):
        self.dependency_tracker = dependency_tracker or get_dependency_tracker()
        self.max_batch_size = max_batch_size
        self.max_concurrent_invalidations = max_concurrent_invalidations
        self.enable_circuit_breaker = enable_circuit_breaker
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._circuit_open = False
        self._stats = {'total_invalidations': 0, 'successful_invalidations': 0, 'failed_invalidations': 0, 'circuit_breaker_trips': 0, 'average_batch_size': 0.0, 'max_batch_size_processed': 0}
        self._semaphore = asyncio.Semaphore(max_concurrent_invalidations)
        self._batch_queue: asyncio.Queue[InvalidationBatch] = asyncio.Queue()
        self._batch_processor_task: asyncio.Task | None = None
        self._monitor: Any | None = None

    async def start(self) -> None:
        """Start the invalidation engine."""
        if self._batch_processor_task is None:
            self._batch_processor_task = asyncio.create_task(self._process_batch_queue())
            logger.info('Invalidation engine started')

    async def stop(self) -> None:
        """Stop the invalidation engine."""
        if self._batch_processor_task:
            self._batch_processor_task.cancel()
            try:
                await self._batch_processor_task
            except asyncio.CancelledError:
                pass
            self._batch_processor_task = None
            logger.info('Invalidation engine stopped')

    def set_monitor(self, monitor: Any) -> None:
        """Set the cache monitor for this invalidation engine."""
        self._monitor = monitor

    async def invalidate_key(self, key: str, cascade: bool=True, reason: str='manual_invalidation') -> InvalidationResult:
        """Invalidate a single key and optionally its dependents."""
        start_time = time.time()
        async with self._semaphore:
            if self._circuit_open and (not await self._should_attempt_reset()):
                return InvalidationResult(skipped_keys={key}, errors=[f'Circuit breaker open, skipping invalidation of {key}'], start_time=start_time, end_time=time.time())
            try:
                keys_to_invalidate = {key}
                if cascade:
                    dependents = await self.dependency_tracker.invalidate_key(key)
                    keys_to_invalidate.update(dependents)
                result = await self._invalidate_keys(keys_to_invalidate, reason)
                if cascade:
                    for invalidated_key in result.invalidated_keys:
                        await self.dependency_tracker.unregister_key(invalidated_key)
                if self._monitor:
                    self._monitor.record_invalidation(len(result.invalidated_keys), reason)
                    if cascade:
                        self._monitor.record_invalidation_latency(result.duration_ms, cascade=True)
                if result.errors:
                    await self._record_failure()
                else:
                    await self._record_success()
                result.start_time = start_time
                result.end_time = time.time()
                return result
            except Exception as e:
                await self._record_failure()
                return InvalidationResult(skipped_keys={key}, errors=[f'Invalidation failed: {e!s}'], start_time=start_time, end_time=time.time())

    async def invalidate_keys(self, keys: set[str], cascade: bool=True, reason: str='batch_invalidation') -> InvalidationResult:
        """Invalidate multiple keys with optional cascading."""
        if len(keys) <= self.max_batch_size:
            return await self._invalidate_keys_batch(keys, cascade, reason)
        else:
            batch = InvalidationBatch(keys=keys, reason=reason, metadata={'cascade': cascade})
            await self._batch_queue.put(batch)
            return InvalidationResult(skipped_keys=keys, errors=['Queued for batch processing'], start_time=time.time(), end_time=time.time())

    async def _invalidate_keys_batch(self, keys: set[str], cascade: bool, reason: str) -> InvalidationResult:
        """Invalidate a batch of keys."""
        start_time = time.time()
        invalidated_keys: set[str] = set()
        skipped_keys: set[str] = set()
        errors: list[str] = []
        async with self._semaphore:
            if self._circuit_open and (not await self._should_attempt_reset()):
                return InvalidationResult(skipped_keys=keys, errors=['Circuit breaker open'], start_time=start_time, end_time=time.time())
            try:
                all_keys_to_invalidate = set(keys)
                if cascade:
                    for key in keys:
                        dependents = await self.dependency_tracker.invalidate_key(key)
                        all_keys_to_invalidate.update(dependents)
                invalidated_keys = await self._perform_invalidation(all_keys_to_invalidate)
                if cascade:
                    for invalidated_key in invalidated_keys:
                        await self.dependency_tracker.unregister_key(invalidated_key)
                self._stats['total_invalidations'] += len(all_keys_to_invalidate)
                self._stats['successful_invalidations'] += len(invalidated_keys)
                if errors:
                    self._stats['failed_invalidations'] += len(errors)
                    await self._record_failure()
                else:
                    await self._record_success()
                return InvalidationResult(invalidated_keys=invalidated_keys, skipped_keys=skipped_keys, errors=errors, start_time=start_time, end_time=time.time())
            except Exception as e:
                await self._record_failure()
                return InvalidationResult(skipped_keys=keys, errors=[f'Batch invalidation failed: {e!s}'], start_time=start_time, end_time=time.time())

    async def _invalidate_keys(self, keys: set[str], reason: str) -> InvalidationResult:
        """Internal method to invalidate keys without batching logic."""
        start_time = time.time()
        invalidated_keys: set[str] = set()
        errors: list[str] = []
        try:
            invalidated_keys = await self._perform_invalidation(keys)
            self._stats['total_invalidations'] += len(keys)
            self._stats['successful_invalidations'] += len(invalidated_keys)
            if len(invalidated_keys) < len(keys):
                failed_count = len(keys) - len(invalidated_keys)
                self._stats['failed_invalidations'] += failed_count
                errors.append(f'Failed to invalidate {failed_count} keys')
        except Exception as e:
            errors.append(f'Invalidation error: {e!s}')
            self._stats['failed_invalidations'] += len(keys)
        return InvalidationResult(invalidated_keys=invalidated_keys, errors=errors, start_time=start_time, end_time=time.time())

    async def _perform_invalidation(self, keys: set[str]) -> set[str]:
        """Perform the actual cache invalidation.

        This is a placeholder that should be implemented to call the actual cache.
        """
        invalidated = set()
        for key in keys:
            try:
                invalidated.add(key)
                logger.debug(f'Invalidated cache key: {key}')
            except Exception as e:
                logger.warning(f'Failed to invalidate key {key}: {e}')
        return invalidated

    async def _process_batch_queue(self) -> None:
        """Process queued invalidation batches."""
        while True:
            try:
                batch = await self._batch_queue.get()
                if batch.metadata.get('cascade', True):
                    result = await self._invalidate_keys_batch(batch.keys, True, batch.reason)
                else:
                    result = await self._invalidate_keys(batch.keys, batch.reason)
                batch_size = len(batch.keys)
                self._stats['average_batch_size'] = (self._stats['average_batch_size'] + batch_size) / 2
                self._stats['max_batch_size_processed'] = max(self._stats['max_batch_size_processed'], batch_size)
                logger.info(f'Processed invalidation batch: {batch.reason}, keys: {len(batch.keys)}, invalidated: {len(result.invalidated_keys)}, errors: {len(result.errors)}')
                self._batch_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f'Error processing invalidation batch: {e}')

    async def _record_failure(self) -> None:
        """Record a failure for circuit breaker logic."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self.enable_circuit_breaker and self._failure_count >= self.circuit_breaker_threshold:
            self._circuit_open = True
            self._stats['circuit_breaker_trips'] += 1
            logger.warning('Circuit breaker opened due to repeated failures')

    async def _record_success(self) -> None:
        """Record a success for circuit breaker logic."""
        if self._failure_count > 0:
            self._failure_count = 0
            if self._circuit_open:
                self._circuit_open = False
                logger.info('Circuit breaker closed - service recovered')

    async def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        if not self._circuit_open:
            return True
        if self._last_failure_time <= 0.0:
            return False
        time_since_failure = time.time() - self._last_failure_time
        if time_since_failure > CIRCUIT_BREAKER_RESET_TIMEOUT:
            logger.info('Attempting circuit breaker reset')
            return True
        return False

    def get_stats(self) -> dict[str, Any]:
        """Get invalidation engine statistics."""
        return {'circuit_breaker': {'open': self._circuit_open, 'failure_count': self._failure_count, 'last_failure_time': self._last_failure_time, 'trips': self._stats['circuit_breaker_trips']}, 'performance': {'total_invalidations': self._stats['total_invalidations'], 'successful_invalidations': self._stats['successful_invalidations'], 'failed_invalidations': self._stats['failed_invalidations'], 'success_rate': self._stats['successful_invalidations'] / self._stats['total_invalidations'] if self._stats['total_invalidations'] > 0 else 1.0, 'average_batch_size': self._stats['average_batch_size'], 'max_batch_size_processed': self._stats['max_batch_size_processed']}, 'queue': {'size': self._batch_queue.qsize(), 'max_concurrent': self.max_concurrent_invalidations}}

    def is_healthy(self) -> bool:
        """Check if the invalidation engine is healthy."""
        return not self._circuit_open
_invalidation_engine: InvalidationEngine | None = None

def get_invalidation_engine() -> InvalidationEngine:
    """Get the global invalidation engine instance."""
    global _invalidation_engine
    if _invalidation_engine is None:
        _invalidation_engine = InvalidationEngine()
    return _invalidation_engine

async def start_invalidation_engine() -> None:
    """Start the global invalidation engine."""
    engine = get_invalidation_engine()
    await engine.start()

async def stop_invalidation_engine() -> None:
    """Stop the global invalidation engine."""
    if _invalidation_engine:
        await _invalidation_engine.stop()
__all__ = ['InvalidationBatch', 'InvalidationEngine', 'InvalidationResult', 'get_invalidation_engine', 'start_invalidation_engine', 'stop_invalidation_engine']
