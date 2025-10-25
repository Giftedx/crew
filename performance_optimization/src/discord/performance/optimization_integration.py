"""
Performance optimization integration for Discord AI processing.

This module integrates all performance optimization components to provide
a unified optimization system for the Discord AI pipeline.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

from performance_optimization.src.ultimate_discord_intelligence_bot.step_result import StepResult

from .embedding_optimizer import EmbeddingConfig, EmbeddingOptimizer

# Import performance components
from .message_batcher import BatchConfig, MessageBatch, MessageBatcher
from .performance_manager import OptimizationConfig, PerformanceManager, ProcessingMetrics
from .semantic_cache import SemanticCache, SemanticCacheConfig


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


class DiscordAIOptimizationSystem:
    """
    Integrated performance optimization system for Discord AI processing.

    This system coordinates message batching, semantic caching, embedding
    optimization, and performance monitoring to maximize efficiency.
    """

    def __init__(
        self,
        batch_config: BatchConfig,
        cache_config: SemanticCacheConfig,
        embedding_config: EmbeddingConfig,
        performance_config: OptimizationConfig,
        embedding_function: Callable[[str], Any],
        message_processor: Callable[[MessageBatch], Awaitable[StepResult]],
    ):
        self.batch_config = batch_config
        self.cache_config = cache_config
        self.embedding_config = embedding_config
        self.performance_config = performance_config

        # Initialize components
        self.message_batcher = MessageBatcher(batch_config, message_processor)
        self.semantic_cache = SemanticCache(cache_config, embedding_function)
        self.embedding_optimizer = EmbeddingOptimizer(embedding_config, embedding_function)
        self.performance_manager = PerformanceManager(performance_config)

        # Integration state
        self._initialized = False
        self._stats = {
            "total_optimizations": 0,
            "cache_hit_improvements": 0,
            "batch_efficiency_gains": 0,
            "embedding_optimizations": 0,
        }

    async def initialize(self) -> StepResult:
        """Initialize the optimization system."""
        try:
            # Start performance monitoring
            self.performance_manager._start_monitoring()

            # Set up integration callbacks
            self._setup_integration_callbacks()

            self._initialized = True

            return StepResult.ok(data={"action": "optimization_system_initialized"})

        except Exception as e:
            return StepResult.fail(f"Failed to initialize optimization system: {e!s}")

    def _setup_integration_callbacks(self):
        """Set up callbacks between optimization components."""
        # Performance manager alerts trigger optimizations
        self.performance_manager.add_alert_callback(self._handle_performance_alert)

        # Embedding optimizer provides embeddings to semantic cache
        self.semantic_cache.embedding_function = self.embedding_optimizer.get_embedding

    async def _handle_performance_alert(self, alert: dict[str, Any]):
        """Handle performance alerts by triggering optimizations."""
        alert_type = alert["type"]

        if alert_type == "high_cpu":
            await self._optimize_for_cpu()
        elif alert_type == "high_memory":
            await self._optimize_for_memory()

    async def _optimize_for_cpu(self):
        """Optimize system for high CPU usage."""
        # Reduce batch sizes
        self.batch_config.max_batch_size = max(1, self.batch_config.max_batch_size // 2)

        # Reduce embedding batch size
        self.embedding_config.batch_size = max(1, self.embedding_config.batch_size // 2)

        self._stats["total_optimizations"] += 1

    async def _optimize_for_memory(self):
        """Optimize system for high memory usage."""
        # Reduce cache sizes
        self.cache_config.max_entries = max(100, self.cache_config.max_entries // 2)
        self.embedding_config.cache_size = max(1000, self.embedding_config.cache_size // 2)

        # Enable more aggressive quantization
        self.embedding_config.enable_quantization = True
        self.embedding_config.quantization_bits = 6

        self._stats["total_optimizations"] += 1

    async def process_message_optimized(self, message_data: dict[str, Any]) -> StepResult:
        """
        Process a Discord message with full optimization pipeline.

        Args:
            message_data: Discord message data

        Returns:
            StepResult with processing result
        """
        if not self._initialized:
            return StepResult.fail("Optimization system not initialized")

        # Start performance timing
        self.performance_manager.start_operation_timer("message_processing")

        try:
            # Check semantic cache first
            cache_result = await self.semantic_cache.get(message_data["content"])

            if cache_result.success:
                # Cache hit - return cached result
                self._stats["cache_hit_improvements"] += 1

                processing_time = self.performance_manager.end_operation_timer("message_processing")

                # Record metrics
                metrics = ProcessingMetrics(
                    operation_name="message_processing",
                    timestamp=time.time(),
                    duration_ms=processing_time,
                    success=True,
                    input_size=len(message_data["content"]),
                    output_size=len(str(cache_result.data)),
                    memory_used_mb=0.0,
                    cpu_time_ms=processing_time,
                )
                self.performance_manager.record_processing_metrics(metrics)

                return StepResult.ok(
                    data={
                        "result": cache_result.data["result"],
                        "from_cache": True,
                        "processing_time_ms": processing_time,
                        "optimization_applied": "semantic_cache",
                    }
                )

            # Cache miss - process through batcher
            batcher_result = await self.message_batcher.add_message(message_data)

            processing_time = self.performance_manager.end_operation_timer("message_processing")

            # Record metrics
            metrics = ProcessingMetrics(
                operation_name="message_processing",
                timestamp=time.time(),
                duration_ms=processing_time,
                success=batcher_result.success,
                input_size=len(message_data["content"]),
                output_size=len(str(batcher_result.data)) if batcher_result.success else 0,
                memory_used_mb=0.0,
                cpu_time_ms=processing_time,
            )
            self.performance_manager.record_processing_metrics(metrics)

            return batcher_result

        except Exception as e:
            processing_time = self.performance_manager.end_operation_timer("message_processing")

            # Record error metrics
            metrics = ProcessingMetrics(
                operation_name="message_processing",
                timestamp=time.time(),
                duration_ms=processing_time,
                success=False,
                input_size=len(message_data["content"]),
                output_size=0,
                memory_used_mb=0.0,
                cpu_time_ms=processing_time,
                metadata={"error": str(e)},
            )
            self.performance_manager.record_processing_metrics(metrics)

            return StepResult.fail(f"Optimized message processing failed: {e!s}")

    async def get_embedding_optimized(self, content: str) -> StepResult:
        """Get embedding with optimization."""
        # Start timing
        self.performance_manager.start_operation_timer("embedding_generation")

        try:
            result = await self.embedding_optimizer.get_embedding(content)

            processing_time = self.performance_manager.end_operation_timer("embedding_generation")

            # Record metrics
            metrics = ProcessingMetrics(
                operation_name="embedding_generation",
                timestamp=time.time(),
                duration_ms=processing_time,
                success=result.success,
                input_size=len(content),
                output_size=len(result.data["embedding"]) if result.success else 0,
                memory_used_mb=0.0,
                cpu_time_ms=processing_time,
            )
            self.performance_manager.record_processing_metrics(metrics)

            self._stats["embedding_optimizations"] += 1

            return result

        except Exception as e:
            processing_time = self.performance_manager.end_operation_timer("embedding_generation")

            # Record error metrics
            metrics = ProcessingMetrics(
                operation_name="embedding_generation",
                timestamp=time.time(),
                duration_ms=processing_time,
                success=False,
                input_size=len(content),
                output_size=0,
                memory_used_mb=0.0,
                cpu_time_ms=processing_time,
                metadata={"error": str(e)},
            )
            self.performance_manager.record_processing_metrics(metrics)

            return StepResult.fail(f"Optimized embedding generation failed: {e!s}")

    async def get_comprehensive_stats(self) -> StepResult:
        """Get comprehensive optimization statistics."""
        try:
            # Get stats from all components
            batch_stats = await self.message_batcher.get_stats()
            cache_stats = await self.semantic_cache.get_stats()
            embedding_stats = await self.embedding_optimizer.get_stats()
            performance_stats = await self.performance_manager.get_performance_summary()

            # Combine stats
            combined_stats = {
                "system_stats": self._stats,
                "batch_stats": batch_stats.data if batch_stats.success else {},
                "cache_stats": cache_stats.data if cache_stats.success else {},
                "embedding_stats": embedding_stats.data if embedding_stats.success else {},
                "performance_stats": performance_stats.data if performance_stats.success else {},
                "optimization_effectiveness": await self._calculate_effectiveness(),
            }

            return StepResult.ok(data=combined_stats)

        except Exception as e:
            return StepResult.fail(f"Failed to get comprehensive stats: {e!s}")

    async def _calculate_effectiveness(self) -> dict[str, float]:
        """Calculate optimization effectiveness metrics."""
        effectiveness = {}

        try:
            # Cache effectiveness
            if hasattr(self.semantic_cache, "_stats"):
                cache_hits = self.semantic_cache._stats.get("hits", 0)
                cache_total = self.semantic_cache._stats.get("total_queries", 1)
                effectiveness["cache_hit_rate"] = (cache_hits / cache_total) * 100

            # Batch effectiveness
            if hasattr(self.message_batcher, "_stats"):
                avg_batch_size = self.message_batcher._stats.get("avg_batch_size", 1)
                max_batch_size = self.batch_config.max_batch_size
                effectiveness["batch_efficiency"] = (avg_batch_size / max_batch_size) * 100

            # Embedding optimization effectiveness
            if hasattr(self.embedding_optimizer, "_stats"):
                cache_hits = self.embedding_optimizer._stats.get("cache_hits", 0)
                cache_total = self.embedding_optimizer._stats.get(
                    "cache_hits", 0
                ) + self.embedding_optimizer._stats.get("cache_misses", 1)
                effectiveness["embedding_cache_hit_rate"] = (cache_hits / cache_total) * 100

            # Overall system efficiency
            if "cache_hit_rate" in effectiveness and "batch_efficiency" in effectiveness:
                effectiveness["overall_efficiency"] = (
                    effectiveness["cache_hit_rate"] * 0.4
                    + effectiveness["batch_efficiency"] * 0.3
                    + effectiveness.get("embedding_cache_hit_rate", 0) * 0.3
                )

        except Exception as e:
            effectiveness["error"] = str(e)

        return effectiveness

    async def optimize_system(self) -> StepResult:
        """Perform system-wide optimization."""
        try:
            optimizations_applied = []

            # Get performance recommendations
            recommendations = await self.performance_manager.get_optimization_recommendations()

            if recommendations.success:
                for rec in recommendations.data["recommendations"]:
                    if rec["type"] == "cpu_optimization":
                        await self._optimize_for_cpu()
                        optimizations_applied.append("cpu_optimization")

                    elif rec["type"] == "memory_optimization":
                        await self._optimize_for_memory()
                        optimizations_applied.append("memory_optimization")

            # Adaptive cache tuning
            await self._adaptive_cache_tuning()

            # Adaptive batch tuning
            await self._adaptive_batch_tuning()

            self._stats["total_optimizations"] += 1

            return StepResult.ok(
                data={
                    "action": "system_optimized",
                    "optimizations_applied": optimizations_applied,
                    "total_optimizations": self._stats["total_optimizations"],
                }
            )

        except Exception as e:
            return StepResult.fail(f"System optimization failed: {e!s}")

    async def _adaptive_cache_tuning(self):
        """Adaptively tune cache parameters."""
        try:
            # Get cache performance
            cache_stats = await self.semantic_cache.get_stats()

            if cache_stats.success:
                hit_rate = cache_stats.data.get("hit_rate_percent", 0)

                # Adjust similarity threshold based on hit rate
                if hit_rate < 30:
                    # Low hit rate - lower threshold to be more permissive
                    self.cache_config.similarity_threshold = max(0.7, self.cache_config.similarity_threshold - 0.05)
                elif hit_rate > 80:
                    # High hit rate - raise threshold to be more selective
                    self.cache_config.similarity_threshold = min(0.95, self.cache_config.similarity_threshold + 0.02)

                # Adjust cache size based on hit rate
                if hit_rate > 60:
                    # Good hit rate - increase cache size
                    self.cache_config.max_entries = min(2000, int(self.cache_config.max_entries * 1.1))
                elif hit_rate < 20:
                    # Poor hit rate - decrease cache size to free memory
                    self.cache_config.max_entries = max(100, int(self.cache_config.max_entries * 0.9))

        except Exception as e:
            print(f"Adaptive cache tuning error: {e!s}")

    async def _adaptive_batch_tuning(self):
        """Adaptively tune batch parameters."""
        try:
            # Get batch performance
            batch_stats = await self.message_batcher.get_stats()

            if batch_stats.success:
                avg_batch_size = batch_stats.data.get("avg_batch_size", 1)

                # Adjust batch size based on current performance
                if avg_batch_size < self.batch_config.max_batch_size * 0.5:
                    # Small batches - increase max size
                    self.batch_config.max_batch_size = min(20, self.batch_config.max_batch_size + 1)
                elif avg_batch_size > self.batch_config.max_batch_size * 0.9:
                    # Large batches - decrease max size to improve responsiveness
                    self.batch_config.max_batch_size = max(1, self.batch_config.max_batch_size - 1)

        except Exception as e:
            print(f"Adaptive batch tuning error: {e!s}")

    async def shutdown(self) -> StepResult:
        """Gracefully shutdown the optimization system."""
        try:
            # Shutdown all components
            shutdown_results = await asyncio.gather(
                self.message_batcher.shutdown(),
                self.semantic_cache.shutdown(),
                self.embedding_optimizer.shutdown(),
                self.performance_manager.shutdown(),
                return_exceptions=True,
            )

            # Check for any shutdown errors
            errors = [r for r in shutdown_results if isinstance(r, Exception)]

            if errors:
                return StepResult.fail(f"Shutdown completed with errors: {errors}")

            return StepResult.ok(data={"action": "optimization_system_shutdown_complete"})

        except Exception as e:
            return StepResult.fail(f"Optimization system shutdown failed: {e!s}")


# Factory function for creating optimization systems
def create_discord_ai_optimization_system(
    batch_config: BatchConfig,
    cache_config: SemanticCacheConfig,
    embedding_config: EmbeddingConfig,
    performance_config: OptimizationConfig,
    embedding_function: Callable[[str], Any],
    message_processor: Callable[[MessageBatch], Awaitable[StepResult]],
) -> DiscordAIOptimizationSystem:
    """Create a Discord AI optimization system with the specified configuration."""
    return DiscordAIOptimizationSystem(
        batch_config, cache_config, embedding_config, performance_config, embedding_function, message_processor
    )
