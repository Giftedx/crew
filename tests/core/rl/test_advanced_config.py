"""Test cases for advanced bandit configuration management."""

from unittest.mock import patch

import pytest

from core.rl.advanced_config import (
    AdvancedBanditConfigManager,
    AdvancedBanditGlobalConfig,
    DoublyRobustConfig,
    OffsetTreeConfig,
    get_config_manager,
)


class TestDoublyRobustConfig:
    """Test DoublyRobustConfig validation and functionality."""

    def test_default_initialization(self):
        """Test default configuration values."""
        config = DoublyRobustConfig()
        assert config.alpha == 1.0
        assert config.learning_rate == 0.1
        assert config.dim == 8
        assert config.learning_rate_decay == 0.995
        assert config.min_learning_rate == 0.001
        assert config.adaptive_learning_rate is True
        assert config.max_importance_weight == 10.0
        assert config.min_importance_weight == 0.01

    def test_custom_initialization(self):
        """Test custom configuration values."""
        config = DoublyRobustConfig(
            alpha=2.0,
            learning_rate=0.05,
            dim=16,
            adaptive_learning_rate=False,
        )
        assert config.alpha == 2.0
        assert config.learning_rate == 0.05
        assert config.dim == 16
        assert config.adaptive_learning_rate is False

    def test_validation_positive_alpha(self):
        """Test validation of positive alpha."""
        with pytest.raises(ValueError, match="alpha must be positive"):
            DoublyRobustConfig(alpha=0.0)

        with pytest.raises(ValueError, match="alpha must be positive"):
            DoublyRobustConfig(alpha=-1.0)

    def test_validation_learning_rate_range(self):
        """Test validation of learning rate range."""
        with pytest.raises(ValueError, match="learning_rate must be in"):
            DoublyRobustConfig(learning_rate=0.0)

        with pytest.raises(ValueError, match="learning_rate must be in"):
            DoublyRobustConfig(learning_rate=1.5)

    def test_validation_positive_dim(self):
        """Test validation of positive dimension."""
        with pytest.raises(ValueError, match="dim must be positive"):
            DoublyRobustConfig(dim=0)

    def test_validation_importance_weights(self):
        """Test validation of importance weight bounds."""
        with pytest.raises(ValueError, match="max_importance_weight must be"):
            DoublyRobustConfig(max_importance_weight=0.01, min_importance_weight=0.05)


class TestOffsetTreeConfig:
    """Test OffsetTreeConfig validation and functionality."""

    def test_default_initialization(self):
        """Test default configuration values."""
        config = OffsetTreeConfig()
        assert config.max_depth == 3
        assert config.min_samples_split == 10
        assert config.split_threshold == 0.1
        assert config.split_strategy == "variance"
        assert config.feature_selection == "all"
        assert config.context_history_size == 10000
        assert config.base_bandit_type == "thompson"

    def test_custom_initialization(self):
        """Test custom configuration values."""
        config = OffsetTreeConfig(
            max_depth=5,
            min_samples_split=20,
            split_strategy="information_gain",
            base_bandit_type="epsilon_greedy",
        )
        assert config.max_depth == 5
        assert config.min_samples_split == 20
        assert config.split_strategy == "information_gain"
        assert config.base_bandit_type == "epsilon_greedy"

    def test_validation_positive_max_depth(self):
        """Test validation of positive max depth."""
        with pytest.raises(ValueError, match="max_depth must be positive"):
            OffsetTreeConfig(max_depth=0)

    def test_validation_min_samples_split(self):
        """Test validation of minimum samples for split."""
        with pytest.raises(ValueError, match="min_samples_split must be"):
            OffsetTreeConfig(min_samples_split=1)

    def test_validation_split_strategy(self):
        """Test validation of split strategy."""
        with pytest.raises(ValueError, match="split_strategy must be"):
            OffsetTreeConfig(split_strategy="invalid")

    def test_validation_feature_selection(self):
        """Test validation of feature selection."""
        with pytest.raises(ValueError, match="feature_selection must be"):
            OffsetTreeConfig(feature_selection="invalid")

    def test_validation_history_size(self):
        """Test validation of history size constraints."""
        with pytest.raises(ValueError, match="history_cleanup_size must be"):
            OffsetTreeConfig(context_history_size=100, history_cleanup_size=150)


class TestAdvancedBanditGlobalConfig:
    """Test global configuration validation."""

    def test_default_initialization(self):
        """Test default global configuration."""
        config = AdvancedBanditGlobalConfig()
        assert config.enable_advanced_bandits is False
        assert config.enable_shadow_evaluation is False
        assert config.rollout_percentage == 0.0
        assert config.rollout_domains == []
        assert config.rollout_tenants == []

    def test_rollout_percentage_validation(self):
        """Test rollout percentage validation."""
        with pytest.raises(ValueError, match="rollout_percentage must be in"):
            AdvancedBanditGlobalConfig(rollout_percentage=-0.1)

        with pytest.raises(ValueError, match="rollout_percentage must be in"):
            AdvancedBanditGlobalConfig(rollout_percentage=1.1)

    def test_threshold_validation(self):
        """Test performance threshold validation."""
        with pytest.raises(ValueError, match="shadow_sample_threshold must be positive"):
            AdvancedBanditGlobalConfig(shadow_sample_threshold=0)

        with pytest.raises(ValueError, match="performance_improvement_threshold must be non-negative"):
            AdvancedBanditGlobalConfig(performance_improvement_threshold=-0.1)

        with pytest.raises(ValueError, match="degradation_threshold must be negative"):
            AdvancedBanditGlobalConfig(degradation_threshold=0.1)


class TestAdvancedBanditConfigManager:
    """Test the configuration manager."""

    def test_initialization(self):
        """Test manager initialization."""
        manager = AdvancedBanditConfigManager()
        assert manager._global_config is None
        assert len(manager._doubly_robust_configs) == 0
        assert len(manager._offset_tree_configs) == 0

    @patch.dict(
        "os.environ",
        {
            "ENABLE_RL_ADVANCED": "true",
            "ENABLE_RL_SHADOW_EVAL": "true",
            "RL_ROLLOUT_PERCENTAGE": "0.25",
            "RL_DR_ALPHA": "2.0",
            "RL_DR_LEARNING_RATE": "0.05",
            "RL_OT_MAX_DEPTH": "4",
        },
    )
    def test_load_from_environment(self):
        """Test loading configuration from environment variables."""
        manager = AdvancedBanditConfigManager()
        manager.load_from_environment()

        global_config = manager.get_global_config()
        assert global_config.enable_advanced_bandits is True
        assert global_config.enable_shadow_evaluation is True
        assert global_config.rollout_percentage == 0.25

        dr_config = manager.get_doubly_robust_config()
        assert dr_config.alpha == 2.0
        assert dr_config.learning_rate == 0.05

        ot_config = manager.get_offset_tree_config()
        assert ot_config.max_depth == 4

    @patch.dict(
        "os.environ",
        {
            "RL_ROLLOUT_DOMAINS": "model_routing,content_analysis",
            "RL_ROLLOUT_TENANTS": "tenant1,tenant2",
        },
    )
    def test_load_list_environment_variables(self):
        """Test loading list-type environment variables."""
        manager = AdvancedBanditConfigManager()
        manager.load_from_environment()

        global_config = manager.get_global_config()
        assert global_config.rollout_domains == ["model_routing", "content_analysis"]
        assert global_config.rollout_tenants == ["tenant1", "tenant2"]

    def test_set_domain_config(self):
        """Test setting domain-specific configurations."""
        manager = AdvancedBanditConfigManager()

        dr_config = DoublyRobustConfig(alpha=3.0, learning_rate=0.02)
        ot_config = OffsetTreeConfig(max_depth=6)

        manager.set_domain_config(
            "test_domain",
            doubly_robust_config=dr_config,
            offset_tree_config=ot_config,
        )

        retrieved_dr = manager.get_doubly_robust_config("test_domain")
        retrieved_ot = manager.get_offset_tree_config("test_domain")

        assert retrieved_dr.alpha == 3.0
        assert retrieved_dr.learning_rate == 0.02
        assert retrieved_ot.max_depth == 6

    def test_is_enabled_for_domain(self):
        """Test domain-specific enablement checking."""
        manager = AdvancedBanditConfigManager()

        # Test with disabled global config
        global_config = AdvancedBanditGlobalConfig(enable_advanced_bandits=False)
        manager._global_config = global_config
        assert not manager.is_enabled_for_domain("test_domain")

        # Test with enabled but specific domains
        global_config = AdvancedBanditGlobalConfig(
            enable_advanced_bandits=True,
            rollout_domains=["allowed_domain"],
        )
        manager._global_config = global_config
        assert manager.is_enabled_for_domain("allowed_domain")
        assert not manager.is_enabled_for_domain("other_domain")

    def test_is_enabled_for_tenant(self):
        """Test tenant-specific enablement checking."""
        manager = AdvancedBanditConfigManager()

        # Test with disabled global config
        global_config = AdvancedBanditGlobalConfig(enable_advanced_bandits=False)
        manager._global_config = global_config
        assert not manager.is_enabled_for_tenant("test_tenant")

        # Test with enabled but specific tenants
        global_config = AdvancedBanditGlobalConfig(
            enable_advanced_bandits=True,
            rollout_tenants=["allowed_tenant"],
        )
        manager._global_config = global_config
        assert manager.is_enabled_for_tenant("allowed_tenant")
        assert not manager.is_enabled_for_tenant("other_tenant")

    def test_rollout_percentage_hash_based_routing(self):
        """Test hash-based routing for rollout percentage."""
        manager = AdvancedBanditConfigManager()

        # Test with 50% rollout
        global_config = AdvancedBanditGlobalConfig(
            enable_advanced_bandits=True,
            rollout_percentage=0.5,
        )
        manager._global_config = global_config

        # Test multiple domains - some should be enabled, some not
        domains = [f"domain_{i}" for i in range(20)]
        enabled_count = sum(1 for domain in domains if manager.is_enabled_for_domain(domain))

        # Should be roughly 50% (allowing for hash distribution variation)
        assert 6 <= enabled_count <= 14  # Reasonable range for 50% of 20

    def test_should_use_shadow_evaluation(self):
        """Test shadow evaluation enablement."""
        manager = AdvancedBanditConfigManager()

        global_config = AdvancedBanditGlobalConfig(enable_shadow_evaluation=True)
        manager._global_config = global_config
        assert manager.should_use_shadow_evaluation()

        global_config = AdvancedBanditGlobalConfig(enable_shadow_evaluation=False)
        manager._global_config = global_config
        assert not manager.should_use_shadow_evaluation()

    def test_get_config_summary(self):
        """Test configuration summary generation."""
        manager = AdvancedBanditConfigManager()
        manager.load_from_environment()

        summary = manager.get_config_summary()

        assert "global" in summary
        assert "doubly_robust_domains" in summary
        assert "offset_tree_domains" in summary
        assert "cache_size" in summary

        global_summary = summary["global"]
        assert "advanced_bandits_enabled" in global_summary
        assert "shadow_evaluation_enabled" in global_summary
        assert "rollout_percentage" in global_summary

    @patch.dict("os.environ", {"INVALID_INT": "not_a_number"})
    def test_environment_parsing_error_handling(self):
        """Test handling of invalid environment variable values."""
        manager = AdvancedBanditConfigManager()

        # Should handle invalid integer gracefully
        result = manager._get_int_env("INVALID_INT", 42)
        assert result == 42  # Should return default

        # Should handle invalid float gracefully
        result = manager._get_float_env("INVALID_INT", 3.14)
        assert result == 3.14  # Should return default

    def test_list_environment_parsing(self):
        """Test parsing of list environment variables."""
        manager = AdvancedBanditConfigManager()

        # Test empty string
        result = manager._get_list_env("EMPTY_LIST", ["default"])
        assert result == ["default"]

        # Test with mock environment
        with patch.dict("os.environ", {"TEST_LIST": "item1, item2 , item3"}):
            result = manager._get_list_env("TEST_LIST", [])
            assert result == ["item1", "item2", "item3"]


class TestGlobalConfigManager:
    """Test the global config manager instance."""

    def test_get_config_manager_singleton(self):
        """Test that get_config_manager returns same instance."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        assert manager1 is manager2

    def test_config_manager_type(self):
        """Test that config manager is correct type."""
        manager = get_config_manager()
        assert isinstance(manager, AdvancedBanditConfigManager)
