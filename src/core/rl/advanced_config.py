"""Advanced configuration management for contextual bandit algorithms.

This module provides sophisticated configuration options for DoublyRobust and
OffsetTree bandit algorithms, including learning rate scheduling, tree depth
optimization, and gradual rollout mechanisms with feature flags.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DoublyRobustConfig:
    """Configuration for DoublyRobust bandit algorithm."""

    # Core algorithm parameters
    alpha: float = 1.0  # Confidence parameter for exploration
    learning_rate: float = 0.1  # Reward model learning rate
    dim: int = 8  # Context feature dimension

    # Learning rate scheduling
    learning_rate_decay: float = 0.995  # Decay factor per update
    min_learning_rate: float = 0.001  # Minimum learning rate
    adaptive_learning_rate: bool = True  # Enable adaptive scheduling

    # Importance sampling controls
    max_importance_weight: float = 10.0  # Clamp importance weights
    min_importance_weight: float = 0.01  # Minimum weight threshold
    importance_weight_smoothing: float = 0.9  # Exponential smoothing factor

    # Reward model regularization
    l2_regularization: float = 0.001  # L2 penalty on weights
    variance_smoothing: float = 0.9  # Variance estimate smoothing
    confidence_scaling: float = 1.0  # Scale confidence intervals

    # Memory management
    max_history_size: int = 1000  # Maximum importance weights to keep
    cleanup_threshold: float = 0.8  # Cleanup when history reaches this fraction

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.alpha <= 0:
            raise ValueError("alpha must be positive")
        if not 0 < self.learning_rate <= 1.0:
            raise ValueError("learning_rate must be in (0, 1]")
        if self.dim <= 0:
            raise ValueError("dim must be positive")
        if self.learning_rate_decay < 0 or self.learning_rate_decay > 1:
            raise ValueError("learning_rate_decay must be in [0, 1]")
        if self.min_learning_rate <= 0:
            raise ValueError("min_learning_rate must be positive")
        if self.max_importance_weight <= self.min_importance_weight:
            raise ValueError("max_importance_weight must be > min_importance_weight")


@dataclass
class OffsetTreeConfig:
    """Configuration for OffsetTree bandit algorithm."""

    # Tree structure parameters
    max_depth: int = 3  # Maximum tree depth
    min_samples_split: int = 10  # Minimum samples to split node
    split_threshold: float = 0.1  # Minimum variance reduction for split

    # Tree optimization
    split_strategy: str = "variance"  # variance, information_gain, mse
    feature_selection: str = "all"  # all, random, best
    max_features_per_split: int | None = None  # Limit features considered

    # Node management
    max_leaf_nodes: int | None = None  # Maximum number of leaf nodes
    min_samples_leaf: int = 5  # Minimum samples per leaf
    pruning_threshold: float = 0.05  # Prune if improvement < threshold

    # Context handling
    context_history_size: int = 10000  # Maximum context history
    history_cleanup_size: int = 5000  # Size after cleanup
    missing_feature_strategy: str = "default_left"  # default_left, median, mode

    # Base bandit configuration
    base_bandit_type: str = "thompson"  # thompson, epsilon_greedy, ucb1
    base_bandit_params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.max_depth <= 0:
            raise ValueError("max_depth must be positive")
        if self.min_samples_split <= 1:
            raise ValueError("min_samples_split must be > 1")
        if self.split_threshold < 0:
            raise ValueError("split_threshold must be non-negative")
        if self.split_strategy not in ["variance", "information_gain", "mse"]:
            raise ValueError("split_strategy must be variance, information_gain, or mse")
        if self.feature_selection not in ["all", "random", "best"]:
            raise ValueError("feature_selection must be all, random, or best")
        if self.min_samples_leaf <= 0:
            raise ValueError("min_samples_leaf must be positive")
        if self.context_history_size <= 0:
            raise ValueError("context_history_size must be positive")
        if self.history_cleanup_size >= self.context_history_size:
            raise ValueError("history_cleanup_size must be < context_history_size")


@dataclass
class AdvancedBanditGlobalConfig:
    """Global configuration for advanced bandit system."""

    # Feature flags
    enable_advanced_bandits: bool = False
    enable_shadow_evaluation: bool = False
    enable_auto_tuning: bool = False
    enable_performance_monitoring: bool = True

    # Rollout controls
    rollout_percentage: float = 0.0  # Percentage of traffic to route to advanced bandits
    rollout_domains: list[str] = field(default_factory=list)  # Specific domains to enable
    rollout_tenants: list[str] = field(default_factory=list)  # Specific tenants to enable

    # A/B testing configuration
    shadow_sample_threshold: int = 500  # Samples before considering activation
    performance_improvement_threshold: float = 0.05  # 5% improvement required
    degradation_threshold: float = -0.10  # 10% degradation triggers alarm

    # Auto-tuning parameters
    tuning_interval_hours: int = 24  # How often to retune parameters
    tuning_sample_size: int = 1000  # Samples needed for tuning
    learning_rate_search_space: tuple[float, float] = (0.001, 0.5)
    confidence_search_space: tuple[float, float] = (0.5, 3.0)

    # Monitoring and alerting
    metric_collection_interval: int = 300  # Seconds between metric collection
    alert_on_degradation: bool = True
    alert_threshold_minutes: int = 60  # Alert if degradation persists

    def __post_init__(self):
        """Validate global configuration."""
        if not 0 <= self.rollout_percentage <= 1.0:
            raise ValueError("rollout_percentage must be in [0, 1]")
        if self.shadow_sample_threshold <= 0:
            raise ValueError("shadow_sample_threshold must be positive")
        if self.performance_improvement_threshold < 0:
            raise ValueError("performance_improvement_threshold must be non-negative")
        if self.degradation_threshold > 0:
            raise ValueError("degradation_threshold must be negative")


class AdvancedBanditConfigManager:
    """Centralized configuration manager for advanced bandit algorithms."""

    def __init__(self):
        self._global_config: AdvancedBanditGlobalConfig | None = None
        self._doubly_robust_configs: dict[str, DoublyRobustConfig] = {}
        self._offset_tree_configs: dict[str, OffsetTreeConfig] = {}
        self._config_cache: dict[str, Any] = {}

    def load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        # Global configuration
        global_config = AdvancedBanditGlobalConfig(
            enable_advanced_bandits=self._get_bool_env("ENABLE_RL_ADVANCED", False),
            enable_shadow_evaluation=self._get_bool_env("ENABLE_RL_SHADOW_EVAL", False),
            enable_auto_tuning=self._get_bool_env("ENABLE_RL_AUTO_TUNING", False),
            enable_performance_monitoring=self._get_bool_env("ENABLE_RL_MONITORING", True),
            rollout_percentage=self._get_float_env("RL_ROLLOUT_PERCENTAGE", 0.0),
            rollout_domains=self._get_list_env("RL_ROLLOUT_DOMAINS", []),
            rollout_tenants=self._get_list_env("RL_ROLLOUT_TENANTS", []),
            shadow_sample_threshold=self._get_int_env("RL_SHADOW_THRESHOLD", 500),
            performance_improvement_threshold=self._get_float_env("RL_IMPROVEMENT_THRESHOLD", 0.05),
            degradation_threshold=self._get_float_env("RL_DEGRADATION_THRESHOLD", -0.10),
        )

        self._global_config = global_config

        # DoublyRobust default configuration
        dr_config = DoublyRobustConfig(
            alpha=self._get_float_env("RL_DR_ALPHA", 1.0),
            learning_rate=self._get_float_env("RL_DR_LEARNING_RATE", 0.1),
            dim=self._get_int_env("RL_DR_DIM", 8),
            learning_rate_decay=self._get_float_env("RL_DR_LR_DECAY", 0.995),
            min_learning_rate=self._get_float_env("RL_DR_MIN_LR", 0.001),
            adaptive_learning_rate=self._get_bool_env("RL_DR_ADAPTIVE_LR", True),
            max_importance_weight=self._get_float_env("RL_DR_MAX_WEIGHT", 10.0),
            min_importance_weight=self._get_float_env("RL_DR_MIN_WEIGHT", 0.01),
        )
        self._doubly_robust_configs["default"] = dr_config

        # OffsetTree default configuration
        ot_config = OffsetTreeConfig(
            max_depth=self._get_int_env("RL_OT_MAX_DEPTH", 3),
            min_samples_split=self._get_int_env("RL_OT_MIN_SPLIT", 10),
            split_threshold=self._get_float_env("RL_OT_SPLIT_THRESHOLD", 0.1),
            split_strategy=self._get_str_env("RL_OT_SPLIT_STRATEGY", "variance"),
            feature_selection=self._get_str_env("RL_OT_FEATURE_SELECTION", "all"),
            context_history_size=self._get_int_env("RL_OT_HISTORY_SIZE", 10000),
            base_bandit_type=self._get_str_env("RL_OT_BASE_BANDIT", "thompson"),
        )
        self._offset_tree_configs["default"] = ot_config

        logger.info("Advanced bandit configuration loaded from environment")

    def get_global_config(self) -> AdvancedBanditGlobalConfig:
        """Get global configuration."""
        if self._global_config is None:
            self.load_from_environment()
        return self._global_config

    def get_doubly_robust_config(self, domain: str = "default") -> DoublyRobustConfig:
        """Get DoublyRobust configuration for a specific domain."""
        if domain not in self._doubly_robust_configs:
            # Return default if domain-specific config doesn't exist
            domain = "default"
            if domain not in self._doubly_robust_configs:
                self.load_from_environment()
        return self._doubly_robust_configs[domain]

    def get_offset_tree_config(self, domain: str = "default") -> OffsetTreeConfig:
        """Get OffsetTree configuration for a specific domain."""
        if domain not in self._offset_tree_configs:
            # Return default if domain-specific config doesn't exist
            domain = "default"
            if domain not in self._offset_tree_configs:
                self.load_from_environment()
        return self._offset_tree_configs[domain]

    def set_domain_config(
        self,
        domain: str,
        doubly_robust_config: DoublyRobustConfig | None = None,
        offset_tree_config: OffsetTreeConfig | None = None,
    ) -> None:
        """Set domain-specific configurations."""
        if doubly_robust_config:
            self._doubly_robust_configs[domain] = doubly_robust_config
        if offset_tree_config:
            self._offset_tree_configs[domain] = offset_tree_config

        # Clear cache for this domain
        cache_keys_to_remove = [k for k in self._config_cache.keys() if k.startswith(f"{domain}:")]
        for key in cache_keys_to_remove:
            del self._config_cache[key]

        logger.info("Updated configuration for domain: %s", domain)

    def is_enabled_for_domain(self, domain: str) -> bool:
        """Check if advanced bandits are enabled for a specific domain."""
        global_config = self.get_global_config()

        if not global_config.enable_advanced_bandits:
            return False

        # Check domain-specific rollout
        if global_config.rollout_domains and domain not in global_config.rollout_domains:
            return False

        # If domain is explicitly allowed, skip percentage check
        if global_config.rollout_domains and domain in global_config.rollout_domains:
            return True

        # Check rollout percentage (simple hash-based routing)
        if global_config.rollout_percentage < 1.0:
            import hashlib

            domain_hash = int(hashlib.md5(domain.encode()).hexdigest()[:8], 16)
            rollout_threshold = int(global_config.rollout_percentage * 2**32)
            if domain_hash > rollout_threshold:
                return False

        return True

    def is_enabled_for_tenant(self, tenant_id: str) -> bool:
        """Check if advanced bandits are enabled for a specific tenant."""
        global_config = self.get_global_config()

        if not global_config.enable_advanced_bandits:
            return False

        # Check tenant-specific rollout
        if global_config.rollout_tenants and tenant_id not in global_config.rollout_tenants:
            return False

        return True

    def should_use_shadow_evaluation(self) -> bool:
        """Check if shadow evaluation should be used."""
        global_config = self.get_global_config()
        return global_config.enable_shadow_evaluation

    def get_config_summary(self) -> dict[str, Any]:
        """Get a summary of all configurations."""
        global_config = self.get_global_config()

        return {
            "global": {
                "advanced_bandits_enabled": global_config.enable_advanced_bandits,
                "shadow_evaluation_enabled": global_config.enable_shadow_evaluation,
                "rollout_percentage": global_config.rollout_percentage,
                "rollout_domains": global_config.rollout_domains,
                "rollout_tenants": global_config.rollout_tenants,
            },
            "doubly_robust_domains": list(self._doubly_robust_configs.keys()),
            "offset_tree_domains": list(self._offset_tree_configs.keys()),
            "cache_size": len(self._config_cache),
        }

    def _get_bool_env(self, name: str, default: bool) -> bool:
        """Get boolean environment variable."""
        value = os.getenv(name, "").lower().strip()
        if value in {"1", "true", "yes", "on"}:
            return True
        elif value in {"0", "false", "no", "off"}:
            return False
        return default

    def _get_int_env(self, name: str, default: int) -> int:
        """Get integer environment variable."""
        try:
            return int(os.getenv(name, str(default)))
        except ValueError:
            logger.warning("Invalid integer value for %s, using default: %d", name, default)
            return default

    def _get_float_env(self, name: str, default: float) -> float:
        """Get float environment variable."""
        try:
            return float(os.getenv(name, str(default)))
        except ValueError:
            logger.warning("Invalid float value for %s, using default: %f", name, default)
            return default

    def _get_str_env(self, name: str, default: str) -> str:
        """Get string environment variable."""
        return os.getenv(name, default)

    def _get_list_env(self, name: str, default: list[str]) -> list[str]:
        """Get list environment variable (comma-separated)."""
        value = os.getenv(name, "").strip()
        if not value:
            return default
        return [item.strip() for item in value.split(",") if item.strip()]


# Global configuration manager instance
config_manager = AdvancedBanditConfigManager()


def get_config_manager() -> AdvancedBanditConfigManager:
    """Get the global configuration manager instance."""
    return config_manager


__all__ = [
    "DoublyRobustConfig",
    "OffsetTreeConfig",
    "AdvancedBanditGlobalConfig",
    "AdvancedBanditConfigManager",
    "get_config_manager",
]
