"""Cold-start priors for bandit model exploration.

This module provides intelligent initialization for new models in bandit routing,
using transfer learning from benchmark data, cross-tenant aggregates, and model
family heuristics to avoid wasteful exploration.

Key features:
- Benchmark-based priors from historical performance data
- Cross-tenant knowledge transfer (with privacy controls)
- Model family inheritance (e.g., claude-3.5-sonnet inherits from claude-3-opus)
- Configurable confidence levels for prior strength
- Fallback to uniform priors when insufficient data

Expected impact: Avoid 50-100 wasted exploration calls per new model

Feature flags:
- ENABLE_COLD_START_PRIORS=1: Enable intelligent priors (default: enabled)
- COLD_START_CROSS_TENANT=1: Allow cross-tenant knowledge transfer (default: disabled)
- COLD_START_BENCHMARK_PATH=./data/model_benchmarks.json: Path to benchmark data
- COLD_START_PRIOR_CONFIDENCE=0.5: Confidence in priors (0.0-1.0, higher = stronger priors)

Usage:
    priors = ColdStartPriorService()

    # Get prior for new model
    alpha, beta = priors.get_prior_for_model(
        model_name="claude-3.5-sonnet",
        context={"task_type": "summarization", "content_type": "video"},
        tenant="default"
    )

    # Thompson: Initialize with ArmState(alpha=alpha, beta=beta)
    # LinUCB: Initialize with mean reward estimate

Benchmark Data Format (JSON):
    {
        "claude-3-opus": {
            "mean_reward": 0.85,
            "variance": 0.02,
            "sample_count": 1000,
            "context_performance": {
                "summarization": {"mean": 0.88, "variance": 0.015},
                "analysis": {"mean": 0.82, "variance": 0.025}
            }
        }
    }
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger(__name__)


# Default priors (uniform)
_DEFAULT_PRIOR_ALPHA = 1.0
_DEFAULT_PRIOR_BETA = 1.0


@dataclass
class ModelPrior:
    """Prior distribution parameters for a model."""

    alpha: float = _DEFAULT_PRIOR_ALPHA
    beta: float = _DEFAULT_PRIOR_BETA
    mean_reward: float = 0.5  # For LinUCB/other bandits
    variance: float = 0.25  # For confidence bounds
    sample_count: int = 0  # Effective sample size
    source: str = "uniform"  # "benchmark", "cross_tenant", "family", "uniform"
    confidence: float = 0.0  # How confident we are in this prior (0.0-1.0)


@dataclass
class BenchmarkData:
    """Benchmark performance data for a model."""

    mean_reward: float
    variance: float
    sample_count: int
    context_performance: dict[str, dict[str, float]] = field(default_factory=dict)


# Model family inheritance rules (child inherits from parent with discounting)
MODEL_FAMILIES = {
    # Claude family
    "claude-3.5-sonnet": "claude-3-opus",
    "claude-3-sonnet": "claude-3-opus",
    "claude-3-haiku": "claude-3-sonnet",
    "claude-2.1": "claude-2",
    # GPT-4 family
    "gpt-4-turbo": "gpt-4",
    "gpt-4o": "gpt-4-turbo",
    "gpt-4o-mini": "gpt-4o",
    # GPT-3.5 family
    "gpt-3.5-turbo-1106": "gpt-3.5-turbo",
    "gpt-3.5-turbo-0125": "gpt-3.5-turbo",
    # Gemini family
    "gemini-1.5-pro": "gemini-1.0-pro",
    "gemini-1.5-flash": "gemini-1.5-pro",
    # Open models
    "llama-3.1-70b": "llama-3-70b",
    "llama-3.1-8b": "llama-3-8b",
    "mixtral-8x22b": "mixtral-8x7b",
}


class ColdStartPriorService:
    """Service for providing intelligent cold-start priors for new models."""

    def __init__(
        self,
        benchmark_path: str | None = None,
        enable_cross_tenant: bool | None = None,
        prior_confidence: float | None = None,
    ):
        """Initialize cold-start prior service.

        Args:
            benchmark_path: Path to benchmark data JSON file
            enable_cross_tenant: Allow cross-tenant knowledge transfer
            prior_confidence: Confidence in priors (0.0-1.0, higher = stronger)
        """
        self._enabled = os.getenv("ENABLE_COLD_START_PRIORS", "1").lower() in {"1", "true", "yes", "on"}

        self._benchmark_path = benchmark_path or os.getenv("COLD_START_BENCHMARK_PATH", "./data/model_benchmarks.json")

        self._enable_cross_tenant = (
            enable_cross_tenant
            if enable_cross_tenant is not None
            else os.getenv("COLD_START_CROSS_TENANT", "0").lower() in {"1", "true", "yes", "on"}
        )

        self._prior_confidence = (
            prior_confidence if prior_confidence is not None else float(os.getenv("COLD_START_PRIOR_CONFIDENCE", "0.5"))
        )

        # Clamp confidence to [0, 1]
        self._prior_confidence = max(0.0, min(1.0, self._prior_confidence))

        # Load benchmark data
        self._benchmarks: dict[str, BenchmarkData] = {}
        if self._enabled:
            self._load_benchmarks()

        # Cross-tenant aggregates (populated on-demand)
        self._cross_tenant_cache: dict[str, ModelPrior] = {}

        logger.info(
            f"ColdStartPriorService initialized: enabled={self._enabled}, "
            f"cross_tenant={self._enable_cross_tenant}, confidence={self._prior_confidence:.2f}"
        )

    def _load_benchmarks(self) -> None:
        """Load benchmark data from JSON file."""
        if not self._benchmark_path or not os.path.isfile(self._benchmark_path):
            logger.warning(f"Benchmark file not found: {self._benchmark_path}")
            return

        try:
            with open(self._benchmark_path, encoding="utf-8") as f:
                raw_data = json.load(f)

            for model_name, data in raw_data.items():
                self._benchmarks[model_name] = BenchmarkData(
                    mean_reward=data.get("mean_reward", 0.5),
                    variance=data.get("variance", 0.25),
                    sample_count=data.get("sample_count", 0),
                    context_performance=data.get("context_performance", {}),
                )

            logger.info(f"Loaded {len(self._benchmarks)} model benchmarks from {self._benchmark_path}")

        except Exception as e:
            logger.error(f"Failed to load benchmarks: {e}")

    def get_prior_for_model(
        self,
        model_name: str,
        context: dict[str, Any] | None = None,
        tenant: str = "default",
    ) -> tuple[float, float]:
        """Get Thompson Sampling prior (alpha, beta) for a model.

        Args:
            model_name: Name of the model
            context: Contextual information (task_type, content_type, etc.)
            tenant: Tenant identifier (for cross-tenant aggregation)

        Returns:
            (alpha, beta) tuple for Beta distribution prior
        """
        if not self._enabled:
            return (_DEFAULT_PRIOR_ALPHA, _DEFAULT_PRIOR_BETA)

        prior = self._compute_prior(model_name, context, tenant)

        # Convert mean/variance to alpha/beta for Beta distribution
        # Beta distribution: mean = alpha / (alpha + beta)
        #                   variance = (alpha * beta) / ((alpha + beta)^2 * (alpha + beta + 1))

        alpha, beta = self._mean_variance_to_beta_params(prior.mean_reward, prior.variance, prior.confidence)

        logger.debug(
            f"Cold-start prior for {model_name}: alpha={alpha:.2f}, beta={beta:.2f}, "
            f"source={prior.source}, confidence={prior.confidence:.2f}"
        )

        return (alpha, beta)

    def get_mean_reward_prior(
        self,
        model_name: str,
        context: dict[str, Any] | None = None,
        tenant: str = "default",
    ) -> float:
        """Get mean reward estimate for a model (useful for LinUCB/other bandits).

        Args:
            model_name: Name of the model
            context: Contextual information
            tenant: Tenant identifier

        Returns:
            Estimated mean reward (0.0-1.0)
        """
        if not self._enabled:
            return 0.5  # Uniform prior

        prior = self._compute_prior(model_name, context, tenant)
        return prior.mean_reward

    def _compute_prior(
        self,
        model_name: str,
        context: dict[str, Any] | None,
        tenant: str,
    ) -> ModelPrior:
        """Compute prior from all available sources (benchmark, cross-tenant, family)."""
        # Priority order:
        # 1. Benchmark data (most reliable)
        # 2. Cross-tenant aggregate (if enabled)
        # 3. Model family inheritance
        # 4. Uniform prior (fallback)

        # Try benchmark data first
        if model_name in self._benchmarks:
            return self._benchmark_prior(model_name, context)

        # Try cross-tenant aggregate
        if self._enable_cross_tenant:
            cross_tenant_prior = self._cross_tenant_prior(model_name, tenant)
            if cross_tenant_prior.source != "uniform":
                return cross_tenant_prior

        # Try model family inheritance
        family_prior = self._family_inheritance_prior(model_name, context, tenant)
        if family_prior.source != "uniform":
            return family_prior

        # Fallback to uniform prior
        return ModelPrior(
            alpha=_DEFAULT_PRIOR_ALPHA,
            beta=_DEFAULT_PRIOR_BETA,
            mean_reward=0.5,
            variance=0.25,
            sample_count=0,
            source="uniform",
            confidence=0.0,
        )

    def _benchmark_prior(
        self,
        model_name: str,
        context: dict[str, Any] | None,
    ) -> ModelPrior:
        """Get prior from benchmark data."""
        benchmark = self._benchmarks[model_name]

        # Check for context-specific performance
        mean_reward = benchmark.mean_reward
        variance = benchmark.variance

        if context:
            task_type = context.get("task_type")
            if task_type and task_type in benchmark.context_performance:
                ctx_perf = benchmark.context_performance[task_type]
                mean_reward = ctx_perf.get("mean", mean_reward)
                variance = ctx_perf.get("variance", variance)

        return ModelPrior(
            mean_reward=mean_reward,
            variance=variance,
            sample_count=benchmark.sample_count,
            source="benchmark",
            confidence=self._prior_confidence,
        )

    def _cross_tenant_prior(
        self,
        model_name: str,
        tenant: str,
    ) -> ModelPrior:
        """Get prior from cross-tenant aggregates.

        Note: This is a placeholder for future implementation.
        Would require reading aggregate statistics from shared storage (Redis/DB).
        """
        # Check cache
        if model_name in self._cross_tenant_cache:
            return self._cross_tenant_cache[model_name]

        # TODO: Implement cross-tenant aggregate retrieval from Redis/DB
        # For now, return uniform prior
        return ModelPrior(source="uniform", confidence=0.0)

    def _family_inheritance_prior(
        self,
        model_name: str,
        context: dict[str, Any] | None,
        tenant: str,
    ) -> ModelPrior:
        """Get prior by inheriting from model family parent."""
        if model_name not in MODEL_FAMILIES:
            return ModelPrior(source="uniform", confidence=0.0)

        parent_model = MODEL_FAMILIES[model_name]

        # Recursively get parent prior (supports multi-level inheritance)
        parent_prior = self._compute_prior(parent_model, context, tenant)

        if parent_prior.source == "uniform":
            return ModelPrior(source="uniform", confidence=0.0)

        # Discount parent prior (child is likely similar but not identical)
        # - Reduce confidence by 30%
        # - Regress mean slightly toward 0.5
        # - Increase variance slightly
        discount_factor = 0.7
        regression_to_mean = 0.2

        discounted_mean = parent_prior.mean_reward * (1 - regression_to_mean) + 0.5 * regression_to_mean
        discounted_variance = parent_prior.variance * 1.3  # Slightly more uncertain
        discounted_confidence = parent_prior.confidence * discount_factor

        return ModelPrior(
            mean_reward=discounted_mean,
            variance=min(0.25, discounted_variance),  # Cap variance
            sample_count=int(parent_prior.sample_count * discount_factor),
            source=f"family:{parent_model}",
            confidence=discounted_confidence,
        )

    def _mean_variance_to_beta_params(
        self,
        mean: float,
        variance: float,
        confidence: float,
    ) -> tuple[float, float]:
        """Convert mean/variance to Beta distribution alpha/beta parameters.

        The confidence parameter controls how strongly we enforce the prior:
        - confidence=0.0: Uniform prior (alpha=1, beta=1)
        - confidence=1.0: Very strong prior (large alpha, beta)
        """
        # Clamp mean and variance
        mean = max(0.01, min(0.99, mean))
        variance = max(0.001, min(0.25, variance))

        # Base sample size from confidence (confidence=1.0 → 100 effective samples)
        max_sample_count = 100
        effective_samples = confidence * max_sample_count

        if effective_samples < 2:
            # Not enough confidence for informative prior
            return (_DEFAULT_PRIOR_ALPHA, _DEFAULT_PRIOR_BETA)

        # Calculate alpha and beta from mean and effective sample count
        # mean = alpha / (alpha + beta) → alpha = mean * (alpha + beta)
        # Let n = alpha + beta (effective sample count)
        # Then: alpha = mean * n, beta = (1 - mean) * n

        alpha = mean * effective_samples
        beta = (1 - mean) * effective_samples

        # Ensure alpha, beta >= 1 (must be valid Beta distribution)
        alpha = max(1.0, alpha)
        beta = max(1.0, beta)

        return (alpha, beta)

    def update_cross_tenant_cache(
        self,
        model_name: str,
        mean_reward: float,
        variance: float,
        sample_count: int,
    ) -> None:
        """Update cross-tenant cache with new aggregate data.

        This would typically be called by a background job that aggregates
        performance data across tenants.
        """
        if not self._enable_cross_tenant:
            return

        self._cross_tenant_cache[model_name] = ModelPrior(
            mean_reward=mean_reward,
            variance=variance,
            sample_count=sample_count,
            source="cross_tenant",
            confidence=self._prior_confidence,
        )

        logger.debug(f"Updated cross-tenant cache for {model_name}: mean={mean_reward:.3f}")


__all__ = ["MODEL_FAMILIES", "BenchmarkData", "ColdStartPriorService", "ModelPrior"]
