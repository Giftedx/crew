"""
Comprehensive test suite for reinforcement learning algorithms.

Tests Thompson Sampling, UCB bandit, provider preference learning,
and cost-quality optimization components.
"""

from platform.core.rl import (
    CostModel,
    CostQualityOptimizer,
    LearningAlgorithm,
    LearningConfig,
    ModelSpecification,
    OptimizationAlgorithm,
    OptimizationConfig,
    OptimizationObjective,
    PreferenceMetric,
    ProviderPreferenceLearning,
    RewardType,
    ThompsonSamplingBandit,
    ThompsonSamplingConfig,
    UCBBandit,
    UCBConfig,
    UCBStrategy,
)

import pytest


class TestThompsonSamplingBandit:
    """Test Thompson Sampling bandit implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = ThompsonSamplingConfig(alpha_prior=1.0, beta_prior=1.0, min_samples_for_confidence=5)
        self.bandit = ThompsonSamplingBandit(self.config)

    def test_initialization(self):
        """Test bandit initialization."""
        assert self.bandit.config == self.config
        assert len(self.bandit.arms) == 0
        assert self.bandit.metrics.total_selections == 0

    def test_add_arm(self):
        """Test adding arms to the bandit."""
        self.bandit.add_arm("arm1", "Test Arm 1", {"type": "test"})
        assert "arm1" in self.bandit.arms
        assert self.bandit.arms["arm1"].name == "Test Arm 1"
        assert self.bandit.arms["arm1"].metadata["type"] == "test"

    def test_select_arm_no_arms(self):
        """Test arm selection with no arms."""
        result = self.bandit.select_arm()
        assert result is None

    def test_select_arm_single_arm(self):
        """Test arm selection with single arm."""
        self.bandit.add_arm("arm1", "Test Arm 1")
        result = self.bandit.select_arm()
        assert result == "arm1"
        assert self.bandit.metrics.total_selections == 1

    def test_select_arm_multiple_arms(self):
        """Test arm selection with multiple arms."""
        self.bandit.add_arm("arm1", "Test Arm 1")
        self.bandit.add_arm("arm2", "Test Arm 2")
        self.bandit.add_arm("arm3", "Test Arm 3")
        selections = [self.bandit.select_arm() for _ in range(10)]
        assert all(selection in ["arm1", "arm2", "arm3"] for selection in selections)
        assert self.bandit.metrics.total_selections == 10

    def test_update_reward(self):
        """Test reward updates."""
        self.bandit.add_arm("arm1", "Test Arm 1")
        self.bandit.select_arm()
        success = self.bandit.update_reward("arm1", 0.8, RewardType.QUALITY_SCORE)
        assert success
        assert self.bandit.arms["arm1"].total_pulls == 1
        assert self.bandit.arms["arm1"].average_reward == 0.8

    def test_update_reward_nonexistent_arm(self):
        """Test reward update for nonexistent arm."""
        success = self.bandit.update_reward("nonexistent", 0.5)
        assert not success

    def test_arm_statistics(self):
        """Test arm statistics retrieval."""
        self.bandit.add_arm("arm1", "Test Arm 1")
        self.bandit.select_arm()
        self.bandit.update_reward("arm1", 0.7)
        stats = self.bandit.get_arm_statistics("arm1")
        assert stats is not None
        assert stats["arm_id"] == "arm1"
        assert stats["total_pulls"] == 1
        assert stats["average_reward"] == 0.7

    def test_bandit_metrics(self):
        """Test bandit metrics retrieval."""
        self.bandit.add_arm("arm1", "Test Arm 1")
        self.bandit.add_arm("arm2", "Test Arm 2")
        self.bandit.select_arm()
        self.bandit.update_reward("arm1", 0.6)
        metrics = self.bandit.get_bandit_metrics()
        assert metrics["total_arms"] == 2
        assert metrics["total_selections"] == 1
        assert metrics["total_reward"] == 0.6

    def test_reset_arm(self):
        """Test arm reset functionality."""
        self.bandit.add_arm("arm1", "Test Arm 1")
        self.bandit.select_arm()
        self.bandit.update_reward("arm1", 0.8)
        success = self.bandit.reset_arm("arm1")
        assert success
        assert self.bandit.arms["arm1"].total_pulls == 0
        assert self.bandit.arms["arm1"].average_reward == 0.0

    def test_reset_all_arms(self):
        """Test reset all arms functionality."""
        self.bandit.add_arm("arm1", "Test Arm 1")
        self.bandit.add_arm("arm2", "Test Arm 2")
        self.bandit.select_arm()
        self.bandit.update_reward("arm1", 0.7)
        self.bandit.reset_all_arms()
        assert self.bandit.metrics.total_selections == 0
        assert self.bandit.arms["arm1"].total_pulls == 0
        assert self.bandit.arms["arm2"].total_pulls == 0

    def test_best_arms(self):
        """Test getting best arms."""
        self.bandit.add_arm("arm1", "Test Arm 1")
        self.bandit.add_arm("arm2", "Test Arm 2")
        self.bandit.select_arm()
        self.bandit.update_reward("arm1", 0.9)
        self.bandit.select_arm()
        self.bandit.update_reward("arm2", 0.6)
        best_arms = self.bandit.get_best_arms(n=2)
        assert len(best_arms) == 2
        assert best_arms[0]["expected_reward"] >= best_arms[1]["expected_reward"]

    def test_should_explore(self):
        """Test exploration decision logic."""
        assert self.bandit.should_explore()
        self.bandit.add_arm("arm1", "Test Arm 1")
        for _ in range(5):
            self.bandit.select_arm()
            self.bandit.update_reward("arm1", 0.7)
        assert self.bandit.should_explore()


class TestUCBBandit:
    """Test UCB bandit implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = UCBConfig(strategy=UCBStrategy.UCB1, exploration_factor=2.0, min_samples_for_confidence=5)
        self.bandit = UCBBandit(self.config)

    def test_initialization(self):
        """Test bandit initialization."""
        assert self.bandit.config == self.config
        assert len(self.bandit.arms) == 0

    def test_add_arm(self):
        """Test adding arms to the bandit."""
        self.bandit.add_arm("arm1", "Test Arm 1", {"type": "test"})
        assert "arm1" in self.bandit.arms
        assert self.bandit.arms["arm1"].name == "Test Arm 1"

    def test_select_arm_ucb1(self):
        """Test UCB1 arm selection."""
        self.bandit.add_arm("arm1", "Test Arm 1")
        self.bandit.add_arm("arm2", "Test Arm 2")
        result = self.bandit.select_arm()
        assert result in ["arm1", "arm2"]
        assert self.bandit.metrics.total_selections == 1

    def test_update_reward(self):
        """Test reward updates."""
        self.bandit.add_arm("arm1", "Test Arm 1")
        self.bandit.select_arm()
        success = self.bandit.update_reward("arm1", 0.8)
        assert success
        assert self.bandit.arms["arm1"].total_pulls == 1
        assert self.bandit.arms["arm1"].average_reward == 0.8

    def test_ucb_bound_calculation(self):
        """Test UCB bound calculation."""
        self.bandit.add_arm("arm1", "Test Arm 1")
        for _ in range(5):
            self.bandit.select_arm()
            self.bandit.update_reward("arm1", 0.7)
        arm = self.bandit.arms["arm1"]
        arm.update_confidence_bounds(self.bandit.metrics.total_selections, self.config, self.config.strategy)
        assert arm.upper_confidence_bound > arm.expected_reward
        assert arm.confidence_interval[1] >= arm.confidence_interval[0]

    def test_arm_statistics(self):
        """Test arm statistics retrieval."""
        self.bandit.add_arm("arm1", "Test Arm 1")
        self.bandit.select_arm()
        self.bandit.update_reward("arm1", 0.6)
        stats = self.bandit.get_arm_statistics("arm1")
        assert stats is not None
        assert stats["arm_id"] == "arm1"
        assert stats["total_pulls"] == 1
        assert stats["average_reward"] == 0.6

    def test_exploration_analysis(self):
        """Test exploration analysis."""
        self.bandit.add_arm("arm1", "Test Arm 1")
        self.bandit.add_arm("arm2", "Test Arm 2")
        for _ in range(10):
            self.bandit.select_arm()
            self.bandit.update_reward("arm1", 0.7)
        analysis = self.bandit.get_exploration_analysis()
        assert "average_exploration_bonus" in analysis
        assert "most_explored_arm" in analysis

    def test_should_explore_more(self):
        """Test exploration decision logic."""
        assert self.bandit.should_explore_more()
        self.bandit.add_arm("arm1", "Test Arm 1")
        for _ in range(15):
            self.bandit.select_arm()
            self.bandit.update_reward("arm1", 0.7)
        assert self.bandit.should_explore_more()


class TestProviderPreferenceLearning:
    """Test provider preference learning system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = LearningConfig(
            algorithm=LearningAlgorithm.EXPONENTIAL_SMOOTHING, alpha=0.3, min_samples_for_learning=5
        )
        self.learner = ProviderPreferenceLearning(self.config)

    def test_initialization(self):
        """Test learner initialization."""
        assert self.learner.config == self.config
        assert len(self.learner.providers) == 0

    def test_add_provider(self):
        """Test adding providers."""
        self.learner.add_provider("provider1", "Test Provider 1", {"region": "us-east"})
        assert "provider1" in self.learner.providers
        assert self.learner.providers["provider1"].provider_name == "Test Provider 1"

    def test_update_provider_request(self):
        """Test updating provider with request data."""
        self.learner.add_provider("provider1", "Test Provider 1")
        success = self.learner.update_provider_request("provider1", True, 1.5, 0.05, 0.8)
        assert success
        assert self.learner.providers["provider1"].total_requests == 1
        assert self.learner.providers["provider1"].successful_requests == 1

    def test_provider_metrics_calculation(self):
        """Test provider metrics calculations."""
        provider = self.learner.providers.get("provider1", None)
        if provider is None:
            self.learner.add_provider("provider1", "Test Provider 1")
            provider = self.learner.providers["provider1"]
        for i in range(10):
            success = i < 8
            response_time = 1.0 + i * 0.1
            cost = 0.05 + i * 0.01
            quality = 0.7 + i * 0.02
            provider.update_request(success, response_time, cost, quality)
        assert provider.success_rate == 0.8
        assert provider.failure_rate == 0.2
        assert provider.reliability_score > 0.0
        assert provider.cost_efficiency_score > 0.0

    def test_preference_learning_update(self):
        """Test preference learning updates."""
        self.learner.add_provider("provider1", "Test Provider 1")
        self.learner.add_provider("provider2", "Test Provider 2")
        for _ in range(10):
            self.learner.update_provider_request("provider1", True, 1.0, 0.03, 0.9)
            self.learner.update_provider_request("provider2", True, 2.0, 0.05, 0.7)
        self.learner._update_preferences()
        provider1 = self.learner.providers["provider1"]
        provider2 = self.learner.providers["provider2"]
        assert len(provider1.learning_history[PreferenceMetric.SUCCESS_RATE]) > 0
        assert len(provider2.learning_history[PreferenceMetric.SUCCESS_RATE]) > 0

    def test_provider_ranking(self):
        """Test provider ranking functionality."""
        self.learner.add_provider("provider1", "Test Provider 1")
        self.learner.add_provider("provider2", "Test Provider 2")
        for _ in range(10):
            self.learner.update_provider_request("provider1", True, 1.0, 0.03, 0.9)
            self.learner.update_provider_request("provider2", True, 2.0, 0.05, 0.7)
        self.learner._update_preferences()
        rankings = self.learner.get_provider_ranking()
        assert len(rankings) == 2
        assert rankings[0]["preference_score"] >= rankings[1]["preference_score"]

    def test_preferred_providers(self):
        """Test getting preferred providers."""
        self.learner.add_provider("provider1", "Test Provider 1")
        self.learner.add_provider("provider2", "Test Provider 2")
        self.learner.add_provider("provider3", "Test Provider 3")
        preferred = self.learner.get_preferred_providers(n=2)
        assert len(preferred) == 2
        assert all(pid in self.learner.providers for pid in preferred)

    def test_provider_recommendation(self):
        """Test provider recommendation."""
        self.learner.add_provider("provider1", "Test Provider 1")
        self.learner.add_provider("provider2", "Test Provider 2")
        for _ in range(10):
            self.learner.update_provider_request("provider1", True, 1.0, 0.03, 0.9)
            self.learner.update_provider_request("provider2", True, 2.0, 0.05, 0.7)
        self.learner._update_preferences()
        recommendation = self.learner.get_provider_recommendation()
        assert recommendation in ["provider1", "provider2"]

    def test_learning_metrics(self):
        """Test learning metrics retrieval."""
        self.learner.add_provider("provider1", "Test Provider 1")
        self.learner.add_provider("provider2", "Test Provider 2")
        for _ in range(5):
            self.learner.update_provider_request("provider1", True, 1.0, 0.03, 0.8)
            self.learner.update_provider_request("provider2", True, 1.5, 0.04, 0.7)
        metrics = self.learner.get_learning_metrics()
        assert metrics["total_providers"] == 2
        assert metrics["total_requests"] == 10
        assert metrics["learning_algorithm"] == self.config.algorithm.value

    def test_reset_provider(self):
        """Test provider reset functionality."""
        self.learner.add_provider("provider1", "Test Provider 1")
        self.learner.update_provider_request("provider1", True, 1.0, 0.03, 0.8)
        success = self.learner.reset_provider("provider1")
        assert success
        assert self.learner.providers["provider1"].total_requests == 0

    def test_reset_all_providers(self):
        """Test reset all providers functionality."""
        self.learner.add_provider("provider1", "Test Provider 1")
        self.learner.add_provider("provider2", "Test Provider 2")
        self.learner.update_provider_request("provider1", True, 1.0, 0.03, 0.8)
        self.learner.update_provider_request("provider2", True, 1.5, 0.04, 0.7)
        self.learner.reset_all_providers()
        assert self.learner.providers["provider1"].total_requests == 0
        assert self.learner.providers["provider2"].total_requests == 0


class TestCostQualityOptimizer:
    """Test cost-quality optimization system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = OptimizationConfig(
            objective=OptimizationObjective.BALANCED,
            algorithm=OptimizationAlgorithm.WEIGHTED_SUM,
            cost_weight=0.3,
            quality_weight=0.7,
            max_cost_per_request=1.0,
            min_quality_threshold=0.6,
        )
        self.optimizer = CostQualityOptimizer(self.config)
        self.model1 = ModelSpecification(
            model_id="model1",
            provider_id="provider1",
            model_name="Fast Model",
            cost_per_token=0.001,
            expected_quality_score=0.7,
            expected_response_time=1.0,
        )
        self.model2 = ModelSpecification(
            model_id="model2",
            provider_id="provider2",
            model_name="Quality Model",
            cost_per_token=0.002,
            expected_quality_score=0.9,
            expected_response_time=2.0,
        )
        self.model3 = ModelSpecification(
            model_id="model3",
            provider_id="provider3",
            model_name="Expensive Model",
            cost_per_token=0.005,
            expected_quality_score=0.8,
            expected_response_time=1.5,
        )

    def test_initialization(self):
        """Test optimizer initialization."""
        assert self.optimizer.config == self.config
        assert len(self.optimizer.models) == 0

    def test_add_model(self):
        """Test adding models to optimizer."""
        self.optimizer.add_model(self.model1)
        assert "model1" in self.optimizer.models
        assert self.optimizer.models["model1"].model_name == "Fast Model"

    def test_model_cost_calculation(self):
        """Test model cost calculation."""
        cost = self.model1.calculate_cost(tokens=1000, requests=1)
        assert cost == 1.0
        model_per_request = ModelSpecification(
            model_id="test",
            provider_id="test",
            model_name="Test",
            cost_per_request=0.1,
            cost_model=CostModel.PER_REQUEST,
        )
        cost = model_per_request.calculate_cost(tokens=1000, requests=5)
        assert cost == 0.5

    def test_model_quality_score(self):
        """Test model quality score calculation."""
        base_score = self.model1.calculate_quality_score()
        assert 0.0 <= base_score <= 1.0
        context = {"task_complexity": 1.2, "time_pressure": 0.5}
        context_score = self.model1.calculate_quality_score(context)
        assert 0.0 <= context_score <= 1.0

    def test_optimize_model_selection_no_models(self):
        """Test optimization with no models."""
        result = self.optimizer.optimize_model_selection(tokens=1000)
        assert result.selected_model is None
        assert not result.is_feasible()

    def test_optimize_model_selection_weighted_sum(self):
        """Test optimization using weighted sum approach."""
        self.optimizer.add_model(self.model1)
        self.optimizer.add_model(self.model2)
        self.optimizer.add_model(self.model3)
        result = self.optimizer.optimize_model_selection(tokens=1000)
        assert result.selected_model is not None
        assert result.is_feasible()
        assert result.optimization_score > 0
        assert result.predicted_cost > 0
        assert result.predicted_quality > 0

    def test_optimize_model_selection_pareto_front(self):
        """Test optimization using Pareto front approach."""
        self.optimizer.config.algorithm = OptimizationAlgorithm.PARETO_FRONT
        self.optimizer.add_model(self.model1)
        self.optimizer.add_model(self.model2)
        self.optimizer.add_model(self.model3)
        result = self.optimizer.optimize_model_selection(tokens=1000)
        assert result.selected_model is not None
        assert result.algorithm_used == OptimizationAlgorithm.PARETO_FRONT
        assert len(result.pareto_front) > 0

    def test_optimize_model_selection_constraint_satisfaction(self):
        """Test optimization using constraint satisfaction."""
        self.optimizer.config.algorithm = OptimizationAlgorithm.CONSTRAINT_SATISFACTION
        self.optimizer.add_model(self.model1)
        self.optimizer.add_model(self.model2)
        result = self.optimizer.optimize_model_selection(tokens=1000)
        assert result.selected_model is not None
        assert result.algorithm_used == OptimizationAlgorithm.CONSTRAINT_SATISFACTION

    def test_constraint_filtering(self):
        """Test constraint-based model filtering."""
        expensive_model = ModelSpecification(
            model_id="expensive",
            provider_id="provider4",
            model_name="Too Expensive",
            cost_per_token=0.01,
            expected_quality_score=0.9,
        )
        self.optimizer.add_model(self.model1)
        self.optimizer.add_model(expensive_model)
        result = self.optimizer.optimize_model_selection(tokens=1000)
        assert result.selected_model is not None and result.selected_model.model_id == "model1"

    def test_optimization_metrics(self):
        """Test optimization metrics retrieval."""
        self.optimizer.add_model(self.model1)
        self.optimizer.add_model(self.model2)
        for _ in range(5):
            self.optimizer.optimize_model_selection(tokens=1000)
        metrics = self.optimizer.get_optimization_metrics()
        assert metrics["total_optimizations"] == 5
        assert metrics["successful_optimizations"] > 0
        assert metrics["current_models_count"] == 2

    def test_update_model_performance(self):
        """Test updating model performance based on actual results."""
        self.optimizer.add_model(self.model1)
        success = self.optimizer.update_model_performance(
            "model1", actual_cost=0.8, actual_quality=0.75, actual_response_time=0.9
        )
        assert success
        updated_model = self.optimizer.models["model1"]
        assert updated_model.expected_quality_score != self.model1.expected_quality_score
        assert updated_model.expected_response_time != self.model1.expected_response_time

    def test_different_objectives(self):
        """Test optimization with different objectives."""
        self.optimizer.add_model(self.model1)
        self.optimizer.add_model(self.model2)
        self.optimizer.config.objective = OptimizationObjective.MINIMIZE_COST
        result_cost = self.optimizer.optimize_model_selection(tokens=1000)
        self.optimizer.config.objective = OptimizationObjective.MAXIMIZE_QUALITY
        result_quality = self.optimizer.optimize_model_selection(tokens=1000)
        assert result_cost.selected_model is not None
        assert result_quality.selected_model is not None

    def test_remove_model(self):
        """Test removing models from optimizer."""
        self.optimizer.add_model(self.model1)
        self.optimizer.add_model(self.model2)
        success = self.optimizer.remove_model("model1")
        assert success
        assert "model1" not in self.optimizer.models
        assert "model2" in self.optimizer.models
        success = self.optimizer.remove_model("nonexistent")
        assert not success


class TestIntegration:
    """Integration tests for RL algorithms working together."""

    def test_bandit_with_optimizer_integration(self):
        """Test integration between bandit and optimizer."""
        bandit = ThompsonSamplingBandit(ThompsonSamplingConfig())
        bandit.add_arm("model1", "Fast Model")
        bandit.add_arm("model2", "Quality Model")
        optimizer = CostQualityOptimizer(OptimizationConfig())
        model1 = ModelSpecification("model1", "provider1", "Fast Model", 0.001, 0.7)
        model2 = ModelSpecification("model2", "provider2", "Quality Model", 0.002, 0.9)
        optimizer.add_model(model1)
        optimizer.add_model(model2)
        selected_arm = bandit.select_arm()
        assert selected_arm in ["model1", "model2"]
        result = optimizer.optimize_model_selection(tokens=1000)
        assert result.selected_model is not None
        if result.selected_model.model_id == selected_arm:
            bandit.update_reward(selected_arm, result.predicted_quality)

    def test_provider_learning_with_optimizer(self):
        """Test integration between provider learning and optimizer."""
        learner = ProviderPreferenceLearning(LearningConfig())
        learner.add_provider("provider1", "Fast Provider")
        learner.add_provider("provider2", "Quality Provider")
        optimizer = CostQualityOptimizer(OptimizationConfig())
        model1 = ModelSpecification("model1", "provider1", "Fast Model", 0.001, 0.7)
        model2 = ModelSpecification("model2", "provider2", "Quality Model", 0.002, 0.9)
        optimizer.add_model(model1)
        optimizer.add_model(model2)
        for _ in range(10):
            result = optimizer.optimize_model_selection(tokens=1000)
            learner.update_provider_request(
                result.selected_model.provider_id,
                True,
                result.predicted_response_time,
                result.predicted_cost,
                result.predicted_quality,
            )
        metrics = learner.get_learning_metrics()
        assert metrics["total_requests"] == 10


if __name__ == "__main__":
    pytest.main([__file__])
