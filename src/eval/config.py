"""Configuration for enhanced trajectory evaluation.

This module provides configuration management for the trajectory evaluation
system, including feature flags, model selection, and evaluation parameters.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class TrajectoryEvaluationConfig:
    """Configuration for trajectory evaluation system."""

    # Feature flags
    enabled: bool = False
    enhanced_crew_evaluation: bool = False
    trajectory_matching: bool = False
    caching_enabled: bool = False
    metrics_enabled: bool = False
    shadow_mode: bool = False

    # Model configuration
    models: list[str] | None = None
    timeout_seconds: int = 30

    # Cache configuration
    cache_ttl_seconds: int = 3600

    # Batch processing
    batch_size: int = 5

    # Logging
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        """Initialize default values after dataclass construction."""
        if self.models is None:
            self.models = ["gpt-4o-mini", "gpt-3.5-turbo", "claude-3-haiku"]


def load_trajectory_evaluation_config() -> TrajectoryEvaluationConfig:
    """Load trajectory evaluation configuration from environment variables."""
    return TrajectoryEvaluationConfig(
        enabled=os.getenv("ENABLE_TRAJECTORY_EVALUATION", "0") == "1",
        enhanced_crew_evaluation=os.getenv("ENABLE_ENHANCED_CREW_EVALUATION", "0") == "1",
        trajectory_matching=os.getenv("ENABLE_TRAJECTORY_MATCHING", "0") == "1",
        caching_enabled=os.getenv("ENABLE_TRAJECTORY_EVALUATION_CACHE", "0") == "1",
        metrics_enabled=os.getenv("ENABLE_TRAJECTORY_EVALUATION_METRICS", "0") == "1",
        shadow_mode=os.getenv("ENABLE_TRAJECTORY_SHADOW_EVALUATION", "0") == "1",
        models=os.getenv("TRAJECTORY_EVALUATION_MODELS", "gpt-4o-mini,gpt-3.5-turbo,claude-3-haiku").split(","),
        timeout_seconds=int(os.getenv("TRAJECTORY_EVALUATION_TIMEOUT", "30")),
        cache_ttl_seconds=int(os.getenv("TRAJECTORY_EVALUATION_CACHE_TTL", "3600")),
        batch_size=int(os.getenv("TRAJECTORY_EVALUATION_BATCH_SIZE", "5")),
        log_level=os.getenv("TRAJECTORY_EVALUATION_LOG_LEVEL", "INFO"),
    )


# Global configuration instance
_config: TrajectoryEvaluationConfig | None = None


def get_trajectory_evaluation_config() -> TrajectoryEvaluationConfig:
    """Get the global trajectory evaluation configuration."""
    global _config
    if _config is None:
        _config = load_trajectory_evaluation_config()
    return _config


def reset_trajectory_evaluation_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None


__all__ = [
    "TrajectoryEvaluationConfig",
    "load_trajectory_evaluation_config",
    "get_trajectory_evaluation_config",
    "reset_trajectory_evaluation_config",
]
