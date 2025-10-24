"""
Performance optimization configuration for Discord AI processing.

This module provides configuration management for all performance optimization
components including batching, caching, embedding optimization, and monitoring.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from performance_optimization.src.ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags


@dataclass
class PerformanceOptimizationConfig:
    """Main configuration for performance optimization system."""

    # Feature flags
    enable_message_batching: bool = True
    enable_semantic_caching: bool = True
    enable_embedding_optimization: bool = True
    enable_performance_monitoring: bool = True
    enable_adaptive_optimization: bool = True

    # Message batching configuration
    batch_config: BatchConfig | None = None

    # Semantic caching configuration
    cache_config: SemanticCacheConfig | None = None

    # Embedding optimization configuration
    embedding_config: EmbeddingConfig | None = None

    # Performance monitoring configuration
    performance_config: OptimizationConfig | None = None

    def __post_init__(self):
        """Initialize default configurations if not provided."""
        if self.batch_config is None:
            self.batch_config = BatchConfig()

        if self.cache_config is None:
            self.cache_config = SemanticCacheConfig()

        if self.embedding_config is None:
            self.embedding_config = EmbeddingConfig()

        if self.performance_config is None:
            self.performance_config = OptimizationConfig()


@dataclass
class BatchConfig:
    """Configuration for message batching."""

    max_batch_size: int = 10
    max_batch_age_seconds: float = 5.0
    max_concurrent_batches: int = 3
    priority_threshold: int = 5
    enable_smart_batching: bool = True
    guild_isolation: bool = True


@dataclass
class SemanticCacheConfig:
    """Configuration for semantic caching."""

    max_entries: int = 1000
    max_age_seconds: float = 3600.0  # 1 hour
    similarity_threshold: float = 0.85
    embedding_dimension: int = 384
    enable_lru: bool = True
    enable_frequency_tracking: bool = True
    cache_ttl_seconds: float = 1800.0  # 30 minutes
    cleanup_interval_seconds: float = 300.0  # 5 minutes


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


@dataclass
class OptimizationConfig:
    """Configuration for performance monitoring and optimization."""

    monitoring_interval_seconds: float = 1.0
    metrics_history_size: int = 1000
    alert_thresholds: dict[str, float] = field(
        default_factory=lambda: {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "processing_time_ms": 5000.0,
            "error_rate_percent": 10.0,
        }
    )
    enable_adaptive_optimization: bool = True
    optimization_interval_seconds: float = 60.0
    enable_alerts: bool = True


class PerformanceConfigManager:
    """Manager for performance optimization configuration."""

    def __init__(self):
        self.config: PerformanceOptimizationConfig | None = None
        self.feature_flags = FeatureFlags()

    def load_config(self) -> PerformanceOptimizationConfig:
        """Load performance optimization configuration."""
        # Load from environment variables
        config = PerformanceOptimizationConfig(
            enable_message_batching=self._get_bool_env("ENABLE_MESSAGE_BATCHING", True),
            enable_semantic_caching=self._get_bool_env("ENABLE_SEMANTIC_CACHING", True),
            enable_embedding_optimization=self._get_bool_env("ENABLE_EMBEDDING_OPTIMIZATION", True),
            enable_performance_monitoring=self._get_bool_env("ENABLE_PERFORMANCE_MONITORING", True),
            enable_adaptive_optimization=self._get_bool_env("ENABLE_ADAPTIVE_OPTIMIZATION", True),
        )

        # Configure message batching
        config.batch_config = BatchConfig(
            max_batch_size=self._get_int_env("BATCH_MAX_SIZE", 10),
            max_batch_age_seconds=self._get_float_env("BATCH_MAX_AGE_SECONDS", 5.0),
            max_concurrent_batches=self._get_int_env("BATCH_MAX_CONCURRENT", 3),
            priority_threshold=self._get_int_env("BATCH_PRIORITY_THRESHOLD", 5),
            enable_smart_batching=self._get_bool_env("BATCH_ENABLE_SMART", True),
            guild_isolation=self._get_bool_env("BATCH_GUILD_ISOLATION", True),
        )

        # Configure semantic caching
        config.cache_config = SemanticCacheConfig(
            max_entries=self._get_int_env("CACHE_MAX_ENTRIES", 1000),
            max_age_seconds=self._get_float_env("CACHE_MAX_AGE_SECONDS", 3600.0),
            similarity_threshold=self._get_float_env("CACHE_SIMILARITY_THRESHOLD", 0.85),
            embedding_dimension=self._get_int_env("CACHE_EMBEDDING_DIMENSION", 384),
            enable_lru=self._get_bool_env("CACHE_ENABLE_LRU", True),
            enable_frequency_tracking=self._get_bool_env("CACHE_ENABLE_FREQUENCY_TRACKING", True),
            cache_ttl_seconds=self._get_float_env("CACHE_TTL_SECONDS", 1800.0),
            cleanup_interval_seconds=self._get_float_env("CACHE_CLEANUP_INTERVAL_SECONDS", 300.0),
        )

        # Configure embedding optimization
        config.embedding_config = EmbeddingConfig(
            embedding_dimension=self._get_int_env("EMBEDDING_DIMENSION", 384),
            cache_size=self._get_int_env("EMBEDDING_CACHE_SIZE", 10000),
            cache_ttl_seconds=self._get_float_env("EMBEDDING_CACHE_TTL_SECONDS", 3600.0),
            batch_size=self._get_int_env("EMBEDDING_BATCH_SIZE", 32),
            enable_quantization=self._get_bool_env("EMBEDDING_ENABLE_QUANTIZATION", True),
            quantization_bits=self._get_int_env("EMBEDDING_QUANTIZATION_BITS", 8),
            enable_pruning=self._get_bool_env("EMBEDDING_ENABLE_PRUNING", True),
            similarity_threshold=self._get_float_env("EMBEDDING_SIMILARITY_THRESHOLD", 0.7),
            max_concurrent_requests=self._get_int_env("EMBEDDING_MAX_CONCURRENT_REQUESTS", 10),
        )

        # Configure performance monitoring
        config.performance_config = OptimizationConfig(
            monitoring_interval_seconds=self._get_float_env("PERFORMANCE_MONITORING_INTERVAL_SECONDS", 1.0),
            metrics_history_size=self._get_int_env("PERFORMANCE_METRICS_HISTORY_SIZE", 1000),
            alert_thresholds=self._load_alert_thresholds(),
            enable_adaptive_optimization=self._get_bool_env("PERFORMANCE_ENABLE_ADAPTIVE_OPTIMIZATION", True),
            optimization_interval_seconds=self._get_float_env("PERFORMANCE_OPTIMIZATION_INTERVAL_SECONDS", 60.0),
            enable_alerts=self._get_bool_env("PERFORMANCE_ENABLE_ALERTS", True),
        )

        self.config = config
        return config

    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    def _get_int_env(self, key: str, default: int) -> int:
        """Get integer environment variable."""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    def _get_float_env(self, key: str, default: float) -> float:
        """Get float environment variable."""
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default

    def _load_alert_thresholds(self) -> dict[str, float]:
        """Load alert thresholds from environment variables."""
        thresholds = {
            "cpu_percent": self._get_float_env("ALERT_CPU_PERCENT", 80.0),
            "memory_percent": self._get_float_env("ALERT_MEMORY_PERCENT", 85.0),
            "processing_time_ms": self._get_float_env("ALERT_PROCESSING_TIME_MS", 5000.0),
            "error_rate_percent": self._get_float_env("ALERT_ERROR_RATE_PERCENT", 10.0),
        }

        # Load custom thresholds from environment
        for key in ["disk_usage_percent", "network_latency_ms", "queue_size"]:
            env_key = f"ALERT_{key.upper()}"
            if os.getenv(env_key):
                thresholds[key] = self._get_float_env(env_key, 0.0)

        return thresholds

    def get_config(self) -> PerformanceOptimizationConfig:
        """Get current configuration."""
        if self.config is None:
            return self.load_config()
        return self.config

    def update_config(self, updates: dict[str, Any]) -> PerformanceOptimizationConfig:
        """Update configuration with new values."""
        if self.config is None:
            self.config = self.load_config()

        # Update main config
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        # Update sub-configs
        if "batch_config" in updates:
            for key, value in updates["batch_config"].items():
                if hasattr(self.config.batch_config, key):
                    setattr(self.config.batch_config, key, value)

        if "cache_config" in updates:
            for key, value in updates["cache_config"].items():
                if hasattr(self.config.cache_config, key):
                    setattr(self.config.cache_config, key, value)

        if "embedding_config" in updates:
            for key, value in updates["embedding_config"].items():
                if hasattr(self.config.embedding_config, key):
                    setattr(self.config.embedding_config, key, value)

        if "performance_config" in updates:
            for key, value in updates["performance_config"].items():
                if hasattr(self.config.performance_config, key):
                    setattr(self.config.performance_config, key, value)

        return self.config

    def validate_config(self) -> dict[str, Any]:
        """Validate configuration and return validation results."""
        if self.config is None:
            self.config = self.load_config()

        validation_results = {"valid": True, "errors": [], "warnings": []}

        # Validate batch config
        if self.config.batch_config and self.config.batch_config.max_batch_size <= 0:
            validation_results["errors"].append("Batch max size must be positive")
            validation_results["valid"] = False

        if self.config.batch_config and self.config.batch_config.max_batch_age_seconds <= 0:
            validation_results["errors"].append("Batch max age must be positive")
            validation_results["valid"] = False

        # Validate cache config
        if self.config.cache_config and self.config.cache_config.max_entries <= 0:
            validation_results["errors"].append("Cache max entries must be positive")
            validation_results["valid"] = False

        if self.config.cache_config and not 0.0 <= self.config.cache_config.similarity_threshold <= 1.0:
            validation_results["errors"].append("Cache similarity threshold must be between 0 and 1")
            validation_results["valid"] = False

        # Validate embedding config
        if self.config.embedding_config and self.config.embedding_config.embedding_dimension <= 0:
            validation_results["errors"].append("Embedding dimension must be positive")
            validation_results["valid"] = False

        if self.config.embedding_config and self.config.embedding_config.batch_size <= 0:
            validation_results["errors"].append("Embedding batch size must be positive")
            validation_results["valid"] = False

        if self.config.embedding_config and (
            self.config.embedding_config.quantization_bits < 1 or self.config.embedding_config.quantization_bits > 32
        ):
            validation_results["warnings"].append("Quantization bits should be between 1 and 32")

        # Validate performance config
        if self.config.performance_config and self.config.performance_config.monitoring_interval_seconds <= 0:
            validation_results["errors"].append("Monitoring interval must be positive")
            validation_results["valid"] = False

        if self.config.performance_config and self.config.performance_config.metrics_history_size <= 0:
            validation_results["errors"].append("Metrics history size must be positive")
            validation_results["valid"] = False

        return validation_results

    def get_optimized_config_for_environment(self, environment: str) -> PerformanceOptimizationConfig:
        """Get optimized configuration for specific environment."""
        base_config = self.get_config()

        if environment == "development":
            # Development optimizations
            if base_config.batch_config:
                base_config.batch_config.max_batch_size = 5
            if base_config.cache_config:
                base_config.cache_config.max_entries = 500
            if base_config.embedding_config:
                base_config.embedding_config.cache_size = 1000
            base_config.performance_config.monitoring_interval_seconds = 5.0

        elif environment == "production":
            # Production optimizations
            if base_config.batch_config:
                base_config.batch_config.max_batch_size = 15
            if base_config.cache_config:
                base_config.cache_config.max_entries = 2000
            if base_config.embedding_config:
                base_config.embedding_config.cache_size = 20000
            base_config.performance_config.monitoring_interval_seconds = 1.0
            base_config.enable_adaptive_optimization = True

        elif environment == "testing":
            # Testing optimizations
            if base_config.batch_config:
                base_config.batch_config.max_batch_size = 2
            if base_config.cache_config:
                base_config.cache_config.max_entries = 100
            if base_config.embedding_config:
                base_config.embedding_config.cache_size = 500
            base_config.performance_config.monitoring_interval_seconds = 10.0
            base_config.enable_adaptive_optimization = False

        return base_config


# Global configuration manager instance
_config_manager = PerformanceConfigManager()


def get_performance_config() -> PerformanceOptimizationConfig:
    """Get the global performance configuration."""
    return _config_manager.get_config()


def load_performance_config() -> PerformanceOptimizationConfig:
    """Load performance configuration from environment."""
    return _config_manager.load_config()


def update_performance_config(updates: dict[str, Any]) -> PerformanceOptimizationConfig:
    """Update global performance configuration."""
    return _config_manager.update_config(updates)


def validate_performance_config() -> dict[str, Any]:
    """Validate global performance configuration."""
    return _config_manager.validate_config()


def get_environment_optimized_config(environment: str) -> PerformanceOptimizationConfig:
    """Get environment-optimized performance configuration."""
    return _config_manager.get_optimized_config_for_environment(environment)
