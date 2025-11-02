"""
Optimization Pipeline for prompt efficiency and cost optimization.

This module provides a comprehensive pipeline for optimizing prompts,
tracking performance metrics, and managing cost optimization.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from ..step_result import StepResult
from ..tenancy.helpers import require_tenant
from .prompt_compressor import PromptCompressor


logger = logging.getLogger(__name__)


@dataclass
class OptimizationMetrics:
    """Metrics for optimization pipeline."""

    prompt_id: str
    original_tokens: int
    optimized_tokens: int
    compression_ratio: float
    quality_score: float
    cost_savings: float
    optimization_time_ms: float
    timestamp: float


@dataclass
class OptimizationConfig:
    """Configuration for optimization pipeline."""

    enable_compression: bool = True
    enable_caching: bool = True
    enable_quality_validation: bool = True
    target_cost_reduction: float = 0.3  # Target 30% cost reduction
    max_optimization_time_ms: float = 5000.0  # Max 5 seconds
    quality_threshold: float = 0.8


class OptimizationPipeline:
    """Pipeline for prompt optimization and cost management."""

    def __init__(
        self,
        compressor: PromptCompressor | None = None,
        config: OptimizationConfig | None = None,
    ):
        """Initialize optimization pipeline.

        Args:
            compressor: Prompt compressor instance
            config: Optimization configuration
        """
        self.compressor = compressor or PromptCompressor()
        self.config = config or OptimizationConfig()
        self.optimization_history: list[OptimizationMetrics] = []
        self.cache: dict[str, str] = {}

        logger.info("Initialized OptimizationPipeline with compression: %s", self.config.enable_compression)

    @require_tenant(strict_flag_enabled=False)
    async def optimize_prompt(
        self,
        prompt: str,
        prompt_id: str | None = None,
        tenant: str = "",
        workspace: str = "",
        **kwargs: Any,
    ) -> StepResult:
        """Optimize a prompt for efficiency and cost.

        Args:
            prompt: Original prompt to optimize
            prompt_id: Unique identifier for the prompt
            tenant: Tenant identifier
            workspace: Workspace identifier
            **kwargs: Additional optimization parameters

        Returns:
            StepResult with optimized prompt and metrics
        """
        try:
            start_time = time.time()

            # Generate prompt ID if not provided
            if not prompt_id:
                prompt_id = f"prompt_{int(time.time() * 1000)}"

            # Check cache first
            if self.config.enable_caching and prompt_id in self.cache:
                logger.debug("Using cached optimization for prompt: %s", prompt_id)
                cached_result = self.cache[prompt_id]
                return StepResult.ok(
                    data={
                        "optimized_prompt": cached_result,
                        "prompt_id": prompt_id,
                        "from_cache": True,
                        "metrics": {"cached": True},
                    }
                )

            # Estimate original metrics
            original_tokens = self._estimate_tokens(prompt)
            original_cost = self._estimate_cost(original_tokens)

            optimized_prompt = prompt
            optimization_metrics = {
                "original_tokens": original_tokens,
                "optimized_tokens": original_tokens,
                "compression_ratio": 1.0,
                "quality_score": 1.0,
                "cost_savings": 0.0,
                "optimization_time_ms": 0.0,
            }

            # Apply compression if enabled
            if self.config.enable_compression:
                compression_result = await self.compressor.compress_prompt(
                    prompt=prompt,
                    tenant=tenant,
                    workspace=workspace,
                    **kwargs,
                )

                if compression_result.success:
                    compression_data = compression_result.data
                    optimized_prompt = compression_data["compressed_prompt"]
                    compression_metrics = compression_data["metrics"]

                    optimization_metrics.update(
                        {
                            "optimized_tokens": compression_metrics["compressed_tokens"],
                            "compression_ratio": compression_metrics["compression_ratio"],
                            "quality_score": compression_metrics["quality_score"],
                        }
                    )

                    # Validate quality if enabled
                    if (
                        self.config.enable_quality_validation
                        and compression_metrics["quality_score"] < self.config.quality_threshold
                    ):
                        logger.warning(
                            "Quality score %.2f below threshold %.2f, using original prompt",
                            compression_metrics["quality_score"],
                            self.config.quality_threshold,
                        )
                        optimized_prompt = prompt
                        optimization_metrics["optimized_tokens"] = original_tokens
                        optimization_metrics["compression_ratio"] = 1.0
                        optimization_metrics["quality_score"] = 1.0

            # Calculate final metrics
            optimization_time = (time.time() - start_time) * 1000
            optimized_tokens = self._estimate_tokens(optimized_prompt)
            optimized_cost = self._estimate_cost(optimized_tokens)
            cost_savings = original_cost - optimized_cost

            optimization_metrics.update(
                {
                    "cost_savings": cost_savings,
                    "optimization_time_ms": optimization_time,
                }
            )

            # Check if optimization time exceeds limit
            if optimization_time > self.config.max_optimization_time_ms:
                logger.warning(
                    "Optimization time %.1fms exceeds limit %.1fms, using original prompt",
                    optimization_time,
                    self.config.max_optimization_time_ms,
                )
                optimized_prompt = prompt
                optimization_metrics["optimized_tokens"] = original_tokens
                optimization_metrics["compression_ratio"] = 1.0
                optimization_metrics["quality_score"] = 1.0
                optimization_metrics["cost_savings"] = 0.0

            # Store metrics
            metrics = OptimizationMetrics(
                prompt_id=prompt_id,
                original_tokens=original_tokens,
                optimized_tokens=optimized_tokens,
                compression_ratio=optimization_metrics["compression_ratio"],
                quality_score=optimization_metrics["quality_score"],
                cost_savings=cost_savings,
                optimization_time_ms=optimization_time,
                timestamp=time.time(),
            )
            self.optimization_history.append(metrics)

            # Cache result if caching is enabled
            if self.config.enable_caching:
                self.cache[prompt_id] = optimized_prompt

            logger.debug(
                "Optimized prompt %s: %d -> %d tokens (ratio: %.2f, savings: $%.4f)",
                prompt_id,
                original_tokens,
                optimized_tokens,
                optimization_metrics["compression_ratio"],
                cost_savings,
            )

            return StepResult.ok(
                data={
                    "optimized_prompt": optimized_prompt,
                    "prompt_id": prompt_id,
                    "from_cache": False,
                    "metrics": optimization_metrics,
                }
            )

        except Exception as e:
            logger.error("Prompt optimization failed: %s", str(e))
            return StepResult.fail(f"Prompt optimization failed: {e!s}")

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Simple token estimation (4 chars per token average)
        return len(text) // 4

    def _estimate_cost(self, tokens: int) -> float:
        """Estimate cost for token count.

        Args:
            tokens: Number of tokens

        Returns:
            Estimated cost in USD
        """
        # Assume $0.001 per token (rough estimate)
        return tokens * 0.001

    async def batch_optimize(
        self,
        prompts: list[tuple[str, str]],  # (prompt_id, prompt_text)
        tenant: str = "",
        workspace: str = "",
    ) -> StepResult:
        """Optimize multiple prompts in batch.

        Args:
            prompts: List of (prompt_id, prompt_text) tuples
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with batch optimization results
        """
        try:
            results = []
            total_original_tokens = 0
            total_optimized_tokens = 0
            total_cost_savings = 0.0

            for prompt_id, prompt_text in prompts:
                result = await self.optimize_prompt(
                    prompt=prompt_text,
                    prompt_id=prompt_id,
                    tenant=tenant,
                    workspace=workspace,
                )

                if result.success:
                    data = result.data
                    results.append(
                        {
                            "prompt_id": prompt_id,
                            "optimized_prompt": data["optimized_prompt"],
                            "metrics": data["metrics"],
                        }
                    )

                    total_original_tokens += data["metrics"]["original_tokens"]
                    total_optimized_tokens += data["metrics"]["optimized_tokens"]
                    total_cost_savings += data["metrics"]["cost_savings"]

            batch_metrics = {
                "total_prompts": len(prompts),
                "successful_optimizations": len(results),
                "total_original_tokens": total_original_tokens,
                "total_optimized_tokens": total_optimized_tokens,
                "total_cost_savings": total_cost_savings,
                "average_compression_ratio": total_optimized_tokens / total_original_tokens
                if total_original_tokens > 0
                else 1.0,
            }

            return StepResult.ok(
                data={
                    "results": results,
                    "batch_metrics": batch_metrics,
                }
            )

        except Exception as e:
            logger.error("Batch optimization failed: %s", str(e))
            return StepResult.fail(f"Batch optimization failed: {e!s}")

    def get_optimization_stats(self) -> StepResult:
        """Get optimization statistics.

        Returns:
            StepResult with optimization statistics
        """
        try:
            if not self.optimization_history:
                return StepResult.ok(data={"message": "No optimization history available"})

            # Calculate aggregate statistics
            total_optimizations = len(self.optimization_history)
            avg_compression_ratio = sum(m.compression_ratio for m in self.optimization_history) / total_optimizations
            avg_quality_score = sum(m.quality_score for m in self.optimization_history) / total_optimizations
            avg_optimization_time = sum(m.optimization_time_ms for m in self.optimization_history) / total_optimizations

            total_tokens_saved = sum(m.original_tokens - m.optimized_tokens for m in self.optimization_history)
            total_cost_savings = sum(m.cost_savings for m in self.optimization_history)

            return StepResult.ok(
                data={
                    "total_optimizations": total_optimizations,
                    "average_compression_ratio": avg_compression_ratio,
                    "average_quality_score": avg_quality_score,
                    "average_optimization_time_ms": avg_optimization_time,
                    "total_tokens_saved": total_tokens_saved,
                    "total_cost_savings": total_cost_savings,
                    "cache_size": len(self.cache),
                    "config": {
                        "enable_compression": self.config.enable_compression,
                        "enable_caching": self.config.enable_caching,
                        "enable_quality_validation": self.config.enable_quality_validation,
                        "target_cost_reduction": self.config.target_cost_reduction,
                        "quality_threshold": self.config.quality_threshold,
                    },
                }
            )

        except Exception as e:
            logger.error("Failed to get optimization stats: %s", str(e))
            return StepResult.fail(f"Failed to get optimization stats: {e!s}")

    def clear_cache(self) -> StepResult:
        """Clear optimization cache.

        Returns:
            StepResult indicating success/failure
        """
        try:
            self.cache.clear()
            logger.info("Cleared optimization cache")
            return StepResult.ok(data={"cache_cleared": True})

        except Exception as e:
            logger.error("Failed to clear cache: %s", str(e))
            return StepResult.fail(f"Failed to clear cache: {e!s}")

    def reset_optimization_history(self) -> StepResult:
        """Reset optimization history.

        Returns:
            StepResult indicating success/failure
        """
        try:
            self.optimization_history.clear()
            logger.info("Reset optimization history")
            return StepResult.ok(data={"history_reset": True})

        except Exception as e:
            logger.error("Failed to reset optimization history: %s", str(e))
            return StepResult.fail(f"Failed to reset optimization history: {e!s}")

    def update_config(self, new_config: OptimizationConfig) -> StepResult:
        """Update optimization configuration.

        Args:
            new_config: New optimization configuration

        Returns:
            StepResult indicating success/failure
        """
        try:
            self.config = new_config
            logger.info("Updated optimization configuration")
            return StepResult.ok(data={"config_updated": True})

        except Exception as e:
            logger.error("Failed to update optimization config: %s", str(e))
            return StepResult.fail(f"Failed to update optimization config: {e!s}")
