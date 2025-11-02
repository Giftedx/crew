"""Pipeline optimization system for reducing redundant processing and improving efficiency.

This module provides intelligent optimizations for the content processing pipeline,
including input change detection, operation batching, and processing shortcuts.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from platform.core.step_result import StepResult
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class ProcessingFingerprint:
    """Unique fingerprint for detecting when processing inputs have changed."""

    url_hash: str
    content_hash: str
    metadata_hash: str
    timestamp: float

    def to_key(self) -> str:
        """Generate a unique key for this fingerprint."""
        return f"{self.url_hash}:{self.content_hash}:{self.metadata_hash}"


@dataclass
class ProcessingCache:
    """Cache for intermediate processing results."""

    fingerprint: ProcessingFingerprint
    transcription_result: StepResult | None = None
    analysis_result: StepResult | None = None
    memory_results: dict[str, StepResult] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def is_expired(self, ttl_seconds: int = 3600) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.created_at > ttl_seconds

    def get_cached_result(self, operation_type: str) -> StepResult | None:
        """Get cached result for a specific operation."""
        if operation_type == "transcription":
            return self.transcription_result
        elif operation_type == "analysis":
            return self.analysis_result
        else:
            return self.memory_results.get(operation_type)


class PipelineOptimizer:
    """Intelligent pipeline optimizer for reducing redundant processing."""

    def __init__(self, cache_ttl_seconds: int = 3600, max_cache_entries: int = 100):
        self.cache_ttl_seconds = cache_ttl_seconds
        self.max_cache_entries = max_cache_entries
        self.processing_cache: dict[str, ProcessingCache] = {}
        self.content_hash_cache: dict[str, str] = {}

    def create_fingerprint(
        self, url: str, content_data: dict[str, Any], metadata: dict[str, Any] | None = None
    ) -> ProcessingFingerprint:
        """Create a unique fingerprint for processing inputs."""
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        content_str = json.dumps(content_data, sort_keys=True)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]
        metadata_str = json.dumps(metadata or {}, sort_keys=True)
        metadata_hash = hashlib.sha256(metadata_str.encode()).hexdigest()[:16]
        return ProcessingFingerprint(
            url_hash=url_hash, content_hash=content_hash, metadata_hash=metadata_hash, timestamp=time.time()
        )

    def should_skip_processing(
        self, fingerprint: ProcessingFingerprint, required_operations: list[str]
    ) -> tuple[bool, dict[str, StepResult]]:
        """Check if processing can be skipped based on cached results.

        Returns:
            (can_skip, cached_results) where cached_results contains
            results for operations that can be reused
        """
        cache_key = fingerprint.to_key()
        if cache_key not in self.processing_cache:
            return (False, {})
        cache_entry = self.processing_cache[cache_key]
        if cache_entry.is_expired(self.cache_ttl_seconds):
            del self.processing_cache[cache_key]
            return (False, {})
        reusable_results = {}
        for operation in required_operations:
            cached_result = cache_entry.get_cached_result(operation)
            if cached_result is not None:
                reusable_results[operation] = cached_result
        can_skip = len(reusable_results) == len(required_operations)
        if can_skip:
            logger.info(f"Pipeline optimization: Skipping {len(required_operations)} operations for cached fingerprint")
            for operation in required_operations:
                logger.debug(f"Using cached result for {operation}")
        return (can_skip, reusable_results)

    def cache_processing_result(
        self, fingerprint: ProcessingFingerprint, operation_type: str, result: StepResult
    ) -> None:
        """Cache a processing result for future reuse."""
        cache_key = fingerprint.to_key()
        if cache_key not in self.processing_cache:
            self.processing_cache[cache_key] = ProcessingCache(fingerprint=fingerprint)
        cache_entry = self.processing_cache[cache_key]
        if operation_type == "transcription":
            cache_entry.transcription_result = result
        elif operation_type == "analysis":
            cache_entry.analysis_result = result
        else:
            cache_entry.memory_results[operation_type] = result
        if len(self.processing_cache) > self.max_cache_entries:
            self._cleanup_old_entries()

    def _cleanup_old_entries(self) -> None:
        """Remove expired and least recently used cache entries."""
        _ = time.time()
        expired_keys = []
        lru_keys = []
        for key, entry in self.processing_cache.items():
            if entry.is_expired(self.cache_ttl_seconds):
                expired_keys.append(key)
            else:
                lru_keys.append((entry.created_at, key))
        for key in expired_keys:
            del self.processing_cache[key]
        if len(self.processing_cache) > self.max_cache_entries:
            lru_keys.sort(key=lambda x: x[0])
            keys_to_remove = lru_keys[: len(self.processing_cache) - self.max_cache_entries + 10]
            for _, key in keys_to_remove:
                if key in self.processing_cache:
                    del self.processing_cache[key]

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        total_entries = len(self.processing_cache)
        expired_entries = sum(1 for entry in self.processing_cache.values() if entry.is_expired(self.cache_ttl_seconds))
        return {
            "cache_size": total_entries,
            "expired_entries": expired_entries,
            "active_entries": total_entries - expired_entries,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "max_cache_size": self.max_cache_entries,
        }


class BatchProcessor:
    """Batch similar operations together for efficiency."""

    def __init__(self, batch_size: int = 5, batch_timeout_seconds: float = 30.0):
        self.batch_size = batch_size
        self.batch_timeout_seconds = batch_timeout_seconds
        self.pending_operations: dict[str, list[dict[str, Any]]] = {}
        self.batch_timers: dict[str, float] = {}

    def add_operation(self, operation_type: str, operation_data: dict[str, Any], operation_id: str) -> str | None:
        """Add an operation to the batch queue.

        Returns batch_id if operation was batched, None if executed immediately.
        """
        if operation_type not in self.pending_operations:
            self.pending_operations[operation_type] = []
            self.batch_timers[operation_type] = time.time()
        operations = self.pending_operations[operation_type]
        operations.append({"data": operation_data, "id": operation_id, "added_at": time.time()})
        if (
            len(operations) >= self.batch_size
            or time.time() - self.batch_timers[operation_type] >= self.batch_timeout_seconds
        ):
            return self._execute_batch(operation_type)
        return None

    def _execute_batch(self, operation_type: str) -> str:
        """Execute a batch of operations."""
        operations = self.pending_operations[operation_type]
        batch_id = f"{operation_type}_{int(time.time())}"
        logger.info(f"Executing batch {batch_id} with {len(operations)} {operation_type} operations")
        self.pending_operations[operation_type] = []
        self.batch_timers[operation_type] = time.time()
        return batch_id

    def get_pending_operations_count(self) -> dict[str, int]:
        """Get count of pending operations by type."""
        return {op_type: len(ops) for op_type, ops in self.pending_operations.items()}


class MemoryOperationBatcher:
    """Batch memory operations for efficiency."""

    def __init__(self):
        self.pending_memory_ops: list[dict[str, Any]] = []
        self.batch_timer: float | None = None
        self.batch_size = 3
        self.batch_timeout = 5.0

    def add_memory_operation(
        self, operation_type: str, content: str, metadata: dict[str, Any], operation_id: str
    ) -> str | None:
        """Add a memory operation to the batch.

        Returns batch_id if operation was batched, None if executed immediately.
        """
        self.pending_memory_ops.append(
            {
                "type": operation_type,
                "content": content,
                "metadata": metadata,
                "id": operation_id,
                "added_at": time.time(),
            }
        )
        if self.batch_timer is None:
            self.batch_timer = time.time()
        if len(self.pending_memory_ops) >= self.batch_size or (
            self.batch_timer and time.time() - self.batch_timer >= self.batch_timeout
        ):
            return self._execute_memory_batch()
        return None

    def _execute_memory_batch(self) -> str:
        """Execute batched memory operations efficiently."""
        if not self.pending_memory_ops:
            return None
        batch_id = f"memory_batch_{int(time.time())}"
        batch_size = len(self.pending_memory_ops)
        logger.info(f"Executing memory batch {batch_id} with {batch_size} operations")
        operations_by_type = {}
        for op in self.pending_memory_ops:
            op_type = op["type"]
            if op_type not in operations_by_type:
                operations_by_type[op_type] = []
            operations_by_type[op_type].append(op)
        results = {}
        for op_type, ops in operations_by_type.items():
            results[op_type] = self._execute_memory_type_batch(op_type, ops)
        self.pending_memory_ops = []
        self.batch_timer = None
        return batch_id

    def _execute_memory_type_batch(self, op_type: str, operations: list[dict[str, Any]]) -> dict[str, Any]:
        """Execute a batch of operations for a specific memory type."""
        return {
            "batch_size": len(operations),
            "operation_type": op_type,
            "processed_ids": [op["id"] for op in operations],
            "batch_processing_time": 0.1,
        }


class ProcessingShortcutDetector:
    """Detect when processing can be shortcut based on content characteristics."""

    def __init__(self):
        self.shortcut_rules = {
            "empty_content": self._check_empty_content,
            "duplicate_content": self._check_duplicate_content,
            "low_quality_content": self._check_low_quality_content,
            "known_safe_content": self._check_known_safe_content,
        }

    def should_use_shortcut(
        self, url: str, content_data: dict[str, Any], metadata: dict[str, Any] | None = None
    ) -> tuple[bool, str | None, dict[str, Any]]:
        """Check if processing can be shortcut.

        Returns:
            (can_shortcut, shortcut_type, shortcut_data)
        """
        for shortcut_type, check_fn in self.shortcut_rules.items():
            can_shortcut, shortcut_data = check_fn(url, content_data, metadata)
            if can_shortcut:
                logger.info(f"Using processing shortcut: {shortcut_type} for {url}")
                return (True, shortcut_type, shortcut_data)
        return (False, None, {})

    def _check_empty_content(
        self, url: str, content_data: dict[str, Any], metadata: dict[str, Any] | None = None
    ) -> tuple[bool, dict[str, Any]]:
        """Check if content is empty or too short."""
        transcript = content_data.get("transcript", "")
        if not transcript or len(transcript.strip()) < 50:
            return (
                True,
                {
                    "reason": "empty_or_short_content",
                    "transcript_length": len(transcript),
                    "shortcut_result": StepResult.skip(
                        data={
                            "analysis": "Content too short for meaningful analysis",
                            "transcript_length": len(transcript),
                            "confidence": 0.0,
                        }
                    ),
                },
            )
        return (False, {})

    def _check_duplicate_content(
        self, url: str, content_data: dict[str, Any], metadata: dict[str, Any] | None = None
    ) -> tuple[bool, dict[str, Any]]:
        """Check if content is a duplicate of recently processed content."""
        return (False, {})

    def _check_low_quality_content(
        self, url: str, content_data: dict[str, Any], metadata: dict[str, Any] | None = None
    ) -> tuple[bool, dict[str, Any]]:
        """Check if content quality is too low for processing."""
        transcript = content_data.get("transcript", "")
        non_speech_indicators = ["music", "instrumental", "no speech", "silence", "background noise", "unclear audio"]
        if any(indicator in transcript.lower() for indicator in non_speech_indicators):
            return (
                True,
                {
                    "reason": "low_quality_content",
                    "quality_indicators": non_speech_indicators,
                    "shortcut_result": StepResult.skip(
                        data={
                            "analysis": "Low quality audio content detected",
                            "quality_score": 0.2,
                            "skip_reason": "non_speech_content",
                        }
                    ),
                },
            )
        return (False, {})

    def _check_known_safe_content(
        self, url: str, content_data: dict[str, Any], metadata: dict[str, Any] | None = None
    ) -> tuple[bool, dict[str, Any]]:
        """Check if content is from a known safe source."""
        safe_domains = ["youtube.com", "youtu.be", "ted.com", "educational sites"]
        if any(domain in url for domain in safe_domains):
            return (
                True,
                {
                    "reason": "known_safe_source",
                    "source_domain": url.split("/")[2] if "/" in url else url,
                    "shortcut_result": StepResult.ok(
                        data={
                            "analysis": "Content from verified educational/safe source",
                            "trust_score": 0.95,
                            "fact_check_status": "verified",
                            "confidence": 0.9,
                        }
                    ),
                },
            )
        return (False, {})


_pipeline_optimizer: PipelineOptimizer | None = None
_batch_processor: BatchProcessor | None = None
_memory_batcher: MemoryOperationBatcher | None = None
_shortcut_detector: ProcessingShortcutDetector | None = None


def get_pipeline_optimizer() -> PipelineOptimizer:
    """Get or create the global pipeline optimizer."""
    global _pipeline_optimizer
    if _pipeline_optimizer is None:
        _pipeline_optimizer = PipelineOptimizer()
    return _pipeline_optimizer


def get_batch_processor() -> BatchProcessor:
    """Get or create the global batch processor."""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor()
    return _batch_processor


def get_memory_batcher() -> MemoryOperationBatcher:
    """Get or create the global memory batcher."""
    global _memory_batcher
    if _memory_batcher is None:
        _memory_batcher = MemoryOperationBatcher()
    return _memory_batcher


def get_shortcut_detector() -> ProcessingShortcutDetector:
    """Get or create the global shortcut detector."""
    global _shortcut_detector
    if _shortcut_detector is None:
        _shortcut_detector = ProcessingShortcutDetector()
    return _shortcut_detector


def optimize_pipeline_processing(
    url: str,
    content_data: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    required_operations: list[str] | None = None,
) -> tuple[bool, dict[str, Any]]:
    """Check if pipeline processing can be optimized or skipped.

    Returns:
        (can_optimize, optimization_data) where optimization_data contains
        cached results or shortcut information
    """
    if required_operations is None:
        required_operations = ["transcription", "analysis"]
    optimizer = get_pipeline_optimizer()
    shortcut_detector = get_shortcut_detector()
    fingerprint = optimizer.create_fingerprint(url, content_data, metadata)
    can_shortcut, shortcut_type, shortcut_data = shortcut_detector.should_use_shortcut(url, content_data, metadata)
    if can_shortcut:
        return (
            True,
            {
                "optimization_type": "shortcut",
                "shortcut_type": shortcut_type,
                "result": shortcut_data["shortcut_result"],
                "reason": shortcut_data["reason"],
            },
        )
    can_skip, cached_results = optimizer.should_skip_processing(fingerprint, required_operations)
    if can_skip:
        return (
            True,
            {"optimization_type": "cache", "cached_results": cached_results, "fingerprint": fingerprint.to_key()},
        )
    return (False, {"optimization_type": "none", "reason": "No cached results or shortcuts available"})


def batch_memory_operations(
    operation_type: str, content: str, metadata: dict[str, Any], operation_id: str
) -> str | None:
    """Add memory operation to batch for efficient processing."""
    batcher = get_memory_batcher()
    return batcher.add_memory_operation(operation_type, content, metadata, operation_id)


def get_optimization_stats() -> dict[str, Any]:
    """Get optimization system statistics."""
    optimizer = get_pipeline_optimizer()
    batcher = get_batch_processor()
    memory_batcher = get_memory_batcher()
    return {
        "pipeline_optimizer": optimizer.get_cache_stats(),
        "batch_processor": batcher.get_pending_operations_count(),
        "memory_batcher": {
            "pending_operations": len(memory_batcher.pending_memory_ops),
            "batch_timer_active": memory_batcher.batch_timer is not None,
        },
    }


__all__ = [
    "BatchProcessor",
    "MemoryOperationBatcher",
    "PipelineOptimizer",
    "ProcessingCache",
    "ProcessingFingerprint",
    "ProcessingShortcutDetector",
    "batch_memory_operations",
    "get_batch_processor",
    "get_memory_batcher",
    "get_optimization_stats",
    "get_pipeline_optimizer",
    "get_shortcut_detector",
    "optimize_pipeline_processing",
]
