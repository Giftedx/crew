"""Test cases for advanced bandit experiment integration."""

import os
from unittest.mock import Mock, patch

from ultimate_discord_intelligence_bot.core.rl.advanced_experiments import (
    AdvancedBanditExperimentManager,
    AdvancedBanditStats,
    create_default_advanced_bandit_experiments,
)
from ultimate_discord_intelligence_bot.core.rl.policies.advanced_bandits import DoublyRobustBandit, OffsetTreeBandit


class TestAdvancedBanditStats:
    """Test the AdvancedBanditStats class."""

    def test_initialization(self):
        """Test that advanced stats initialize correctly."""
        stats = AdvancedBanditStats()
        assert stats.pulls == 0
        assert stats.reward_sum == 0.0
        assert stats.reward_model_mse == 0.0
        assert stats.tree_depth_sum == 0
        assert stats.importance_weight_sum == 0.0
        assert stats.confidence_interval_width == 0.0

    def test_as_dict_includes_advanced_metrics(self):
        """Test that as_dict includes advanced metrics."""
        stats = AdvancedBanditStats(
            pulls=10,
            reward_sum=5.0,
            reward_model_mse=0.1,
            tree_depth_sum=20,
            importance_weight_sum=15.0,
            confidence_interval_width=3.0,
        )

        result = stats.as_dict()

        # Base metrics
        assert result["pulls"] == 10.0
        assert result["reward_sum"] == 5.0
        assert result["reward_mean"] == 0.5

        # Advanced metrics
        assert result["reward_model_mse"] == 0.1
        assert result["tree_depth_avg"] == 2.0  # 20/10
        assert result["importance_weight_avg"] == 1.5  # 15/10
        assert result["confidence_interval_avg"] == 0.3  # 3/10

    def test_as_dict_handles_zero_pulls(self):
        """Test that as_dict handles zero pulls correctly."""
        stats = AdvancedBanditStats()
        result = stats.as_dict()

        assert result["reward_mean"] == 0.0
        assert result["tree_depth_avg"] == 0.0
        assert result["importance_weight_avg"] == 0.0
        assert result["confidence_interval_avg"] == 0.0


class TestAdvancedBanditExperimentManager:
    """Test the AdvancedBanditExperimentManager class."""

    def test_initialization(self):
        """Test that manager initializes correctly."""
        manager = AdvancedBanditExperimentManager()
        assert len(manager._experiments) == 0
        assert len(manager._advanced_experiments) == 0

    def test_register_advanced_bandit_experiment(self):
        """Test registering an advanced bandit experiment."""
        manager = AdvancedBanditExperimentManager()

        manager.register_advanced_bandit_experiment(
            domain="test_domain",
            baseline_policy="epsilon_greedy",
            advanced_policies={"doubly_robust": 0.5},
            shadow_samples=100,
        )

        exp_id = "advanced_bandits::test_domain"
        assert exp_id in manager._experiments
        assert exp_id in manager._advanced_experiments

        exp = manager._experiments[exp_id]
        assert exp.control == "epsilon_greedy"
        assert "doubly_robust" in exp.variants
        assert exp.auto_activate_after == 100
        assert isinstance(exp.stats["epsilon_greedy"], AdvancedBanditStats)
        assert isinstance(exp.stats["doubly_robust"], AdvancedBanditStats)

    def test_register_advanced_bandit_experiment_defaults(self):
        """Test registering experiment with default parameters."""
        manager = AdvancedBanditExperimentManager()

        manager.register_advanced_bandit_experiment(domain="test_domain")

        exp_id = "advanced_bandits::test_domain"
        exp = manager._experiments[exp_id]

        assert exp.control == "epsilon_greedy"
        assert "doubly_robust" in exp.variants
        assert "offset_tree" in exp.variants
        assert exp.variants["doubly_robust"] == 0.3
        assert exp.variants["offset_tree"] == 0.3

    @patch("core.rl.advanced_experiments.current_tenant")
    @patch("core.rl.advanced_experiments.os.getenv")
    def test_record_advanced_metrics_doubly_robust(self, mock_getenv, mock_tenant):
        """Test recording metrics for DoublyRobust bandit."""
        mock_tenant.return_value = Mock(tenant_id="test", workspace_id="ws")
        mock_getenv.return_value = "true"  # Enable experiment harness

        manager = AdvancedBanditExperimentManager()
        manager.register_advanced_bandit_experiment(domain="test")

        # Create a mock DoublyRobust bandit
        bandit = DoublyRobustBandit()
        bandit.reward_models["doubly_robust"] = {"weights": [0.1, 0.2], "bias": 0.5, "variance": 0.25}
        bandit.importance_weights["doubly_robust"] = [1.5]

        context = {"feature1": 0.5}

        # Mock the predict method to return a specific value
        with patch.object(bandit, "_predict_reward", return_value=0.7):
            manager.record_advanced_metrics(
                "advanced_bandits::test",
                "doubly_robust",
                0.8,  # actual reward
                context,
                bandit,
            )

        exp = manager._experiments["advanced_bandits::test"]
        stats = exp.stats["doubly_robust"]

        assert stats.pulls == 1
        assert stats.reward_sum == 0.8
        assert stats.importance_weight_sum == 1.5
        assert abs(stats.reward_model_mse - 0.01) < 1e-10  # (0.7 - 0.8)^2 = 0.01
        assert stats.confidence_interval_width > 0

    @patch("core.rl.advanced_experiments.current_tenant")
    @patch.dict(os.environ, {"ENABLE_EXPERIMENT_HARNESS": "true"})
    def test_record_advanced_metrics_offset_tree(self, mock_tenant):
        """Test recording metrics for OffsetTree bandit."""
        mock_tenant.return_value = Mock(tenant_id="test", workspace_id="ws")

        manager = AdvancedBanditExperimentManager()
        manager.register_advanced_bandit_experiment(domain="test")

        # Create a mock OffsetTree bandit
        bandit = OffsetTreeBandit()
        bandit.tree_nodes["root"] = {"depth": 2}

        context = {"feature1": 0.5}

        # Record the reward and advanced metrics
        with patch.object(bandit, "_get_node_id", return_value="root"):
            manager.record_advanced_metrics("advanced_bandits::test", "offset_tree", 0.6, context, bandit)

        exp = manager._experiments["advanced_bandits::test"]
        stats = exp.stats["offset_tree"]

        assert stats.pulls == 1
        assert stats.reward_sum == 0.6
        assert stats.tree_depth_sum == 2
        assert stats.reward_sum == 0.6
        assert stats.tree_depth_sum == 2

    @patch.dict(os.environ, {"ENABLE_EXPERIMENT_HARNESS": "true"})
    def test_get_advanced_experiment_summary(self):
        """Test getting experiment summary."""
        manager = AdvancedBanditExperimentManager()
        manager.register_advanced_bandit_experiment(domain="test")

        # Record some data - need to set up the experiment first
        manager.record("advanced_bandits::test", "epsilon_greedy", 0.5)
        manager.record("advanced_bandits::test", "doubly_robust", 0.7)

        summary = manager.get_advanced_experiment_summary("test")

        assert summary["experiment_id"] == "advanced_bandits::test"
        assert summary["control"] == "epsilon_greedy"
        assert "advanced_analysis" in summary

        analysis = summary["advanced_analysis"]
        assert analysis["baseline_policy"] == "epsilon_greedy"
        assert analysis["baseline_reward_mean"] == 0.5
        assert "variant_comparisons" in analysis

    def test_get_advanced_experiment_summary_nonexistent(self):
        """Test getting summary for nonexistent experiment."""
        manager = AdvancedBanditExperimentManager()

        summary = manager.get_advanced_experiment_summary("nonexistent")
        assert "error" in summary

    @patch.dict(os.environ, {"ENABLE_EXPERIMENT_HARNESS": "true"})
    def test_analyze_advanced_performance(self):
        """Test advanced performance analysis."""
        manager = AdvancedBanditExperimentManager()
        manager.register_advanced_bandit_experiment(domain="test")

        exp = manager._experiments["advanced_bandits::test"]

        # Simulate baseline performance - record multiple rewards for epsilon_greedy
        for i in range(20):
            manager.record("advanced_bandits::test", "epsilon_greedy", 0.5)

        # Add consistent doubly_robust data
        for i in range(30):
            manager.record("advanced_bandits::test", "doubly_robust", 0.6)

        analysis = manager._analyze_advanced_performance(exp)

        assert analysis["baseline_reward_mean"] == 0.5
        assert "doubly_robust" in analysis["variant_comparisons"]

        dr_comparison = analysis["variant_comparisons"]["doubly_robust"]
        assert dr_comparison["reward_mean"] == 0.6
        assert abs(dr_comparison["reward_improvement_pct"] - 20.0) < 0.01  # 20% improvement

        # Should have recommendation for good performance
        assert len(analysis["recommendations"]) > 0
        assert "Consider activating doubly_robust" in analysis["recommendations"][0]

    @patch.dict(os.environ, {"ENABLE_EXPERIMENT_HARNESS": "true"})
    def test_analyze_advanced_performance_insufficient_data(self):
        """Test analysis with insufficient data."""
        manager = AdvancedBanditExperimentManager()
        manager.register_advanced_bandit_experiment(domain="test")

        exp = manager._experiments["advanced_bandits::test"]

        # Add minimal data
        manager.record("advanced_bandits::test", "epsilon_greedy", 0.5)
        manager.record("advanced_bandits::test", "doubly_robust", 0.6)

        analysis = manager._analyze_advanced_performance(exp)

        dr_comparison = analysis["variant_comparisons"]["doubly_robust"]
        assert dr_comparison["status"] == "insufficient_data"
        assert dr_comparison["pulls"] == 1


class TestUtilityFunctions:
    """Test utility functions."""

    @patch("core.rl.advanced_experiments.os.getenv")
    def test_create_default_experiments_enabled(self, mock_getenv):
        """Test creating default experiments when enabled."""
        mock_getenv.return_value = "true"

        manager = AdvancedBanditExperimentManager()
        create_default_advanced_bandit_experiments(manager)

        # Should create experiments for default domains
        expected_domains = [
            "model_routing",
            "content_analysis",
            "transcription_service",
            "memory_retrieval",
        ]

        for domain in expected_domains:
            exp_id = f"advanced_bandits::{domain}"
            assert exp_id in manager._experiments

    @patch("core.rl.advanced_experiments.os.getenv")
    def test_create_default_experiments_disabled(self, mock_getenv):
        """Test not creating experiments when disabled."""
        mock_getenv.return_value = "false"

        manager = AdvancedBanditExperimentManager()
        create_default_advanced_bandit_experiments(manager)

        # Should not create any experiments
        assert len(manager._experiments) == 0

    @patch("core.rl.advanced_experiments.os.getenv")
    def test_create_default_experiments_with_errors(self, mock_getenv):
        """Test handling errors during experiment creation."""
        mock_getenv.return_value = "true"

        manager = AdvancedBanditExperimentManager()

        # Mock register method to raise an error
        with patch.object(manager, "register_advanced_bandit_experiment", side_effect=Exception("Test error")):
            # Should not raise an exception
            create_default_advanced_bandit_experiments(manager)

        # Should still have empty experiments (all failed)
        assert len(manager._experiments) == 0


class TestIntegration:
    """Integration tests for advanced experiment functionality."""

    @patch.dict(os.environ, {"ENABLE_EXPERIMENT_HARNESS": "true"})
    def test_full_experiment_lifecycle(self):
        """Test a complete experiment lifecycle."""
        manager = AdvancedBanditExperimentManager()

        # Register experiment
        manager.register_advanced_bandit_experiment(
            domain="integration_test",
            shadow_samples=5,  # Low threshold for quick test
        )

        exp_id = "advanced_bandits::integration_test"
        exp = manager._experiments[exp_id]

        # Verify initial state
        assert exp.phase == "shadow"
        assert exp.auto_activate_after == 5

        # Record some shadow data - need enough for epsilon_greedy (control) to trigger activation
        for i in range(6):  # 6 > 5 threshold
            manager.record(exp_id, "epsilon_greedy", 0.5)
            if i < 4:  # Only some doubly_robust data
                manager.record(exp_id, "doubly_robust", 0.6)

        # Should now be active after reaching the threshold
        assert exp.phase == "active"

        # Get summary
        summary = manager.get_advanced_experiment_summary("integration_test")
        assert summary["phase"] == "active"

        analysis = summary["advanced_analysis"]
        assert "doubly_robust" in analysis["variant_comparisons"]
