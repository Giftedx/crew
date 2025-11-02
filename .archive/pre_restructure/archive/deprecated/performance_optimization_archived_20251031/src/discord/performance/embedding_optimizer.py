"""
Embedding optimization system for efficient vector operations.

This module implements optimized embedding generation, caching, and similarity
computation for Discord message processing.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import time
import typing
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from performance_optimization.src.ultimate_discord_intelligence_bot.step_result import StepResult


@dataclass
class EmbeddingCacheEntry:
    """Represents a cached embedding."""

    content_hash: str
    embedding: np.ndarray
    timestamp: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingConfig:
    """Configuration for embedding optimization."""

    embedding_dimension: int = 384
    cache_size: int = 10000
    cache_ttl_seconds: float = 3600.0  # 1 hour
    batch_size: int = 32
    enable_quantization: bool = True
    quantization_bits: int = 8
    enable_pruning: bool = True
    similarity_threshold: float = 0.7
    max_concurrent_requests: int = 10


class EmbeddingOptimizer:
    """
    Optimized embedding generation and caching system.

    This optimizer provides efficient embedding generation with caching,
    batching, quantization, and similarity computation optimizations.
    """

    def __init__(
        self,
        config: EmbeddingConfig,
        embedding_function: typing.Callable[[str | list[str]], np.ndarray | list[np.ndarray]],
    ):
        self.config = config
        self.embedding_function = embedding_function

        # Embedding cache
        self._embedding_cache: dict[str, EmbeddingCacheEntry] = {}
        self._cache_lock = asyncio.Lock()

        # Batch processing
        self._batch_queue: list[tuple[str, asyncio.Future]] = []
        self._batch_lock = asyncio.Lock()
        self._batch_processing_task: asyncio.Task | None = None

        # Request throttling
        self._request_semaphore = asyncio.Semaphore(config.max_concurrent_requests)

        # Statistics
        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "batch_requests": 0,
            "avg_processing_time": 0.0,
            "quantization_savings": 0.0,
        }

        # Start batch processing
        self._start_batch_processor()

    async def get_embedding(self, content: str) -> StepResult:
        """
        Get embedding for a single piece of content.

        Args:
            content: Text content to embed

        Returns:
            StepResult with normalized embedding
        """
        try:
            async with self._request_semaphore:
                return await self._get_embedding_single(content)
        except Exception as e:
            return StepResult.fail(f"Embedding generation failed: {e!s}")

    async def get_embeddings_batch(self, contents: list[str]) -> StepResult:
        """
        Get embeddings for multiple pieces of content efficiently.

        Args:
            contents: List of text content to embed

        Returns:
            StepResult with list of normalized embeddings
        """
        try:
            async with self._request_semaphore:
                return await self._get_embeddings_batch(contents)
        except Exception as e:
            return StepResult.fail(f"Batch embedding generation failed: {e!s}")

    async def _get_embedding_single(self, content: str) -> StepResult:
        """Get embedding for a single content with caching."""
        content_hash = self._hash_content(content)

        # Check cache first
        async with self._cache_lock:
            if content_hash in self._embedding_cache:
                entry = self._embedding_cache[content_hash]

                # Check if entry is expired
                if time.time() - entry.timestamp < self.config.cache_ttl_seconds:
                    entry.access_count += 1
                    entry.last_accessed = time.time()
                    self._stats["cache_hits"] += 1

                    return StepResult.ok(
                        data={
                            "embedding": entry.embedding.copy(),
                            "from_cache": True,
                            "access_count": entry.access_count,
                        }
                    )
                else:
                    # Remove expired entry
                    del self._embedding_cache[content_hash]

        self._stats["cache_misses"] += 1

        # Generate new embedding
        start_time = time.time()

        if asyncio.iscoroutinefunction(self.embedding_function):
            embedding = await self.embedding_function(content)
        else:
            embedding = self.embedding_function(content)

        processing_time = time.time() - start_time

        # Ensure embedding is numpy array
        if not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding)

        # Normalize embedding
        embedding = self._normalize_embedding(embedding)

        # Quantize if enabled
        if self.config.enable_quantization:
            embedding = self._quantize_embedding(embedding)

        # Cache the result
        await self._cache_embedding(content_hash, content, embedding)

        # Update statistics
        self._stats["total_requests"] += 1
        self._update_processing_time(processing_time)

        return StepResult.ok(data={"embedding": embedding, "from_cache": False, "processing_time": processing_time})

    async def _get_embeddings_batch(self, contents: list[str]) -> StepResult:
        """Get embeddings for multiple contents with batching optimization."""
        if not contents:
            return StepResult.ok(data={"embeddings": []})

        # Check cache for each content
        cached_embeddings = []
        uncached_contents = []
        uncached_indices = []

        async with self._cache_lock:
            for i, content in enumerate(contents):
                content_hash = self._hash_content(content)

                if content_hash in self._embedding_cache:
                    entry = self._embedding_cache[content_hash]

                    if time.time() - entry.timestamp < self.config.cache_ttl_seconds:
                        entry.access_count += 1
                        entry.last_accessed = time.time()
                        cached_embeddings.append((i, entry.embedding.copy()))
                        self._stats["cache_hits"] += 1
                        continue
                    else:
                        del self._embedding_cache[content_hash]

                uncached_contents.append(content)
                uncached_indices.append(i)
                self._stats["cache_misses"] += 1

        # Generate embeddings for uncached contents
        new_embeddings = []
        processing_time = 0.0
        if uncached_contents:
            start_time = time.time()

            # Process in batches if necessary
            batch_size = self.config.batch_size
            for i in range(0, len(uncached_contents), batch_size):
                batch_contents = uncached_contents[i : i + batch_size]

                if asyncio.iscoroutinefunction(self.embedding_function):
                    batch_embeddings = await self.embedding_function(batch_contents)
                else:
                    batch_embeddings = self.embedding_function(batch_contents)

                # Ensure embeddings are numpy arrays
                if isinstance(batch_embeddings, list):
                    batch_embeddings = [np.array(emb) for emb in batch_embeddings]
                else:
                    batch_embeddings = [batch_embeddings]

                # Normalize and quantize embeddings
                for embedding in batch_embeddings:
                    embedding = self._normalize_embedding(embedding)
                    if self.config.enable_quantization:
                        embedding = self._quantize_embedding(embedding)
                    new_embeddings.append(embedding)

            processing_time = time.time() - start_time

            # Cache new embeddings
            for content, embedding in zip(uncached_contents, new_embeddings, strict=False):
                content_hash = self._hash_content(content)
                await self._cache_embedding(content_hash, content, embedding)

            self._stats["batch_requests"] += 1
            self._update_processing_time(processing_time / len(uncached_contents))

        # Combine cached and new embeddings in correct order
        all_embeddings = [None] * len(contents)

        # Add cached embeddings
        for idx, embedding in cached_embeddings:
            all_embeddings[idx] = embedding

        # Add new embeddings
        for index, embedding in zip(uncached_indices, new_embeddings, strict=False):
            all_embeddings[index] = embedding

        self._stats["total_requests"] += len(contents)

        return StepResult.ok(
            data={
                "embeddings": all_embeddings,
                "cached_count": len(cached_embeddings),
                "new_count": len(new_embeddings),
                "processing_time": processing_time if uncached_contents else 0.0,
            }
        )

    def _hash_content(self, content: str) -> str:
        """Generate hash for content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """Normalize embedding to unit vector."""
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return embedding / norm
        return embedding

    def _quantize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """Quantize embedding to reduce memory usage."""
        if not self.config.enable_quantization:
            return embedding

        # Simple quantization to specified bits
        bits = self.config.quantization_bits
        max_val = 2**bits - 1

        # Scale to [0, max_val] range
        scaled = (embedding + 1) * max_val / 2
        quantized = np.round(scaled).astype(np.uint8)

        # Scale back to [-1, 1] range
        dequantized = (quantized / max_val) * 2 - 1

        # Update statistics
        memory_savings = (embedding.nbytes - quantized.nbytes) / embedding.nbytes
        self._stats["quantization_savings"] = (self._stats["quantization_savings"] + memory_savings) / 2

        return dequantized.astype(np.float32)

    async def _cache_embedding(self, content_hash: str, content: str, embedding: np.ndarray):
        """Cache an embedding."""
        async with self._cache_lock:
            # Check cache size limit
            if len(self._embedding_cache) >= self.config.cache_size:
                await self._evict_cache_entries()

            # Create cache entry
            entry = EmbeddingCacheEntry(content_hash=content_hash, embedding=embedding, timestamp=time.time())

            self._embedding_cache[content_hash] = entry

    async def _evict_cache_entries(self):
        """Evict cache entries when cache is full."""
        if not self._embedding_cache:
            return

        # Remove least recently accessed entries
        entries_to_remove = len(self._embedding_cache) - self.config.cache_size + 10

        # Sort by last accessed time
        sorted_entries = sorted(self._embedding_cache.items(), key=lambda x: x[1].last_accessed)

        for i in range(min(entries_to_remove, len(sorted_entries))):
            key, _ = sorted_entries[i]
            del self._embedding_cache[key]

    def _update_processing_time(self, processing_time: float):
        """Update average processing time statistics."""
        self._stats["avg_processing_time"] = (
            self._stats["avg_processing_time"] * (self._stats["total_requests"] - 1) + processing_time
        ) / self._stats["total_requests"]

    def _start_batch_processor(self):
        """Start background batch processor."""
        if self._batch_processing_task is None or self._batch_processing_task.done():
            self._batch_processing_task = asyncio.create_task(self._process_batches())

    async def _process_batches(self):
        """Background task to process embedding batches."""
        while True:
            try:
                await asyncio.sleep(0.1)  # Check every 100ms

                async with self._batch_lock:
                    if self._batch_queue:
                        # Process batches
                        batch_requests = self._batch_queue[: self.config.batch_size]
                        self._batch_queue = self._batch_queue[self.config.batch_size :]

                        if batch_requests:
                            await self._process_batch_requests(batch_requests)

            except Exception as e:
                print(f"Batch processor error: {e!s}")

    async def _process_batch_requests(self, batch_requests: list[tuple[str, asyncio.Future]]):
        """Process a batch of embedding requests."""
        contents = [content for content, _ in batch_requests]
        futures = [future for _, future in batch_requests]

        try:
            result = await self._get_embeddings_batch(contents)

            if result.success:
                embeddings = result.data["embeddings"]
                for i, future in enumerate(futures):
                    if not future.done():
                        future.set_result(embeddings[i])
            else:
                # Set exception for all futures
                for future in futures:
                    if not future.done():
                        future.set_exception(Exception(result.error))

        except Exception as e:
            # Set exception for all futures
            for future in futures:
                if not future.done():
                    future.set_exception(e)

    async def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        # Ensure embeddings are normalized
        emb1 = embedding1 / np.linalg.norm(embedding1)
        emb2 = embedding2 / np.linalg.norm(embedding2)

        return float(np.dot(emb1, emb2))

    async def find_similar_embeddings(
        self, query_embedding: np.ndarray, candidate_embeddings: list[np.ndarray], threshold: float | None = None
    ) -> list[tuple[int, float]]:
        """Find embeddings similar to query embedding."""
        threshold = threshold or self.config.similarity_threshold
        similar_indices = []

        for i, candidate in enumerate(candidate_embeddings):
            similarity = await self.compute_similarity(query_embedding, candidate)
            if similarity >= threshold:
                similar_indices.append((i, similarity))

        # Sort by similarity (highest first)
        similar_indices.sort(key=lambda x: x[1], reverse=True)

        return similar_indices

    async def get_stats(self) -> StepResult:
        """Get optimization statistics."""
        async with self._cache_lock:
            hit_rate = self._stats["cache_hits"] / max(self._stats["cache_hits"] + self._stats["cache_misses"], 1) * 100

            stats = self._stats.copy()
            stats.update(
                {
                    "cache_hit_rate_percent": hit_rate,
                    "cache_size": len(self._embedding_cache),
                    "batch_queue_size": len(self._batch_queue),
                }
            )

            return StepResult.ok(data=stats)

    async def clear_cache(self) -> StepResult:
        """Clear embedding cache."""
        async with self._cache_lock:
            self._embedding_cache.clear()
            return StepResult.ok(data={"action": "cache_cleared"})

    async def shutdown(self) -> StepResult:
        """Gracefully shutdown the optimizer."""
        # Cancel batch processing task
        if self._batch_processing_task:
            self._batch_processing_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._batch_processing_task

        # Clear cache
        await self.clear_cache()

        return StepResult.ok(data={"action": "optimizer_shutdown_complete"})


# Factory function for creating embedding optimizers
def create_embedding_optimizer(
    config: EmbeddingConfig,
    embedding_function: typing.Callable[[str | list[str]], np.ndarray | list[np.ndarray]],
) -> EmbeddingOptimizer:
    """Create an embedding optimizer with the specified configuration."""
    return EmbeddingOptimizer(config, embedding_function)
