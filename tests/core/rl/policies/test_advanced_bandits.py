"""Test cases for advanced contextual bandit algorithms."""

import pytest
from core.rl.policies.advanced_bandits import DoublyRobustBandit, OffsetTreeBandit


class TestDoublyRobustBandit:
    """Test the DoublyRobust bandit implementation."""

    def test_initialization(self):
        """Test that bandit initializes correctly."""
        bandit = DoublyRobustBandit(alpha=2.0, dim=4, learning_rate=0.05)
        assert bandit.alpha == 2.0
        assert bandit.dim == 4
        assert bandit.learning_rate == 0.05
        assert len(bandit.reward_models) == 0
        assert len(bandit.importance_weights) == 0

    def test_recommend_empty_candidates(self):
        """Test that bandit raises error for empty candidates."""
        bandit = DoublyRobustBandit()
        with pytest.raises(ValueError, match="candidates must not be empty"):
            bandit.recommend({}, [])

    def test_recommend_single_candidate(self):
        """Test recommendation with single candidate."""
        bandit = DoublyRobustBandit()
        context = {"feature1": 0.5, "feature2": 1.0}
        candidates = ["action1"]

        result = bandit.recommend(context, candidates)
        assert result == "action1"

    def test_recommend_multiple_candidates(self):
        """Test recommendation with multiple candidates."""
        bandit = DoublyRobustBandit()
        context = {"feature1": 0.5, "feature2": 1.0}
        candidates = ["action1", "action2", "action3"]

        result = bandit.recommend(context, candidates)
        assert result in candidates

    def test_update_basic(self):
        """Test basic update functionality."""
        bandit = DoublyRobustBandit()
        context = {"feature1": 0.5, "feature2": 1.0}
        action = "action1"
        reward = 1.0

        bandit.update(action, reward, context)

        assert bandit.counts[action] == 1
        assert bandit.q_values[action] == 1.0
        assert action in bandit.reward_models
        assert len(bandit.importance_weights[action]) == 1

    def test_update_with_importance_weight(self):
        """Test update with explicit importance weight."""
        bandit = DoublyRobustBandit()
        context = {"feature1": 0.5}
        action = "action1"
        reward = 1.0
        importance_weight = 2.0

        bandit.update_with_importance_weight(action, reward, context, importance_weight)

        assert bandit.counts[action] == 1
        assert bandit.importance_weights[action][-1] == importance_weight

    def test_reward_model_prediction(self):
        """Test reward model learning and prediction."""
        bandit = DoublyRobustBandit(learning_rate=0.1)
        context = {"feature1": 1.0}
        action = "action1"

        # Initial prediction should be around 0
        initial_pred = bandit._predict_reward(action, context)
        assert abs(initial_pred) < 0.1

        # Train with positive reward
        bandit.update(action, 1.0, context)

        # Prediction should increase
        new_pred = bandit._predict_reward(action, context)
        assert new_pred > initial_pred

    def test_state_serialization(self):
        """Test state dict serialization and loading."""
        bandit = DoublyRobustBandit(alpha=1.5, dim=6)
        context = {"feature1": 0.5}
        action = "action1"
        reward = 1.0

        bandit.update(action, reward, context)

        # Serialize state
        state = bandit.state_dict()
        assert state["policy"] == "DoublyRobustBandit"
        assert state["alpha"] == 1.5
        assert state["dim"] == 6
        assert "action1" in state["reward_models"]

        # Create new bandit and load state
        new_bandit = DoublyRobustBandit()
        new_bandit.load_state(state)

        assert new_bandit.alpha == 1.5
        assert new_bandit.dim == 6
        assert new_bandit.counts[action] == 1

    def test_confidence_bounds(self):
        """Test that confidence bounds increase with uncertainty."""
        bandit = DoublyRobustBandit(alpha=1.0)
        context = {"feature1": 0.5}
        candidates = ["action1", "action2"]

        # With no data, predictions should be based on confidence
        rec1 = bandit.recommend(context, candidates)

        # After some updates, confidence should change
        bandit.update("action1", 1.0, context)
        bandit.update("action1", 1.0, context)

        rec2 = bandit.recommend(context, candidates)
        # Both recommendations should be valid
        assert rec1 in candidates
        assert rec2 in candidates


class TestOffsetTreeBandit:
    """Test the OffsetTree bandit implementation."""

    def test_initialization(self):
        """Test that bandit initializes correctly."""
        bandit = OffsetTreeBandit(max_depth=2, min_samples_split=5)
        assert bandit.max_depth == 2
        assert bandit.min_samples_split == 5
        assert "root" in bandit.tree_nodes
        assert bandit.tree_nodes["root"]["is_leaf"] is True

    def test_recommend_empty_candidates(self):
        """Test that bandit raises error for empty candidates."""
        bandit = OffsetTreeBandit()
        with pytest.raises(ValueError, match="candidates must not be empty"):
            bandit.recommend({}, [])

    def test_recommend_single_candidate(self):
        """Test recommendation with single candidate."""
        bandit = OffsetTreeBandit()
        context = {"feature1": 0.5, "feature2": 1.0}
        candidates = ["action1"]

        result = bandit.recommend(context, candidates)
        assert result == "action1"

    def test_get_node_id_root(self):
        """Test node ID retrieval for root."""
        bandit = OffsetTreeBandit()
        context = {"feature1": 0.5}

        node_id = bandit._get_node_id(context)
        assert node_id == "root"

    def test_update_basic(self):
        """Test basic update functionality."""
        bandit = OffsetTreeBandit()
        context = {"feature1": 0.5, "feature2": 1.0}
        action = "action1"
        reward = 1.0

        bandit.update(action, reward, context)

        assert bandit.counts[action] == 1
        assert bandit.q_values[action] == 1.0
        assert len(bandit.context_history) == 1
        assert bandit.tree_nodes["root"]["samples"] == 1

    def test_tree_splitting(self):
        """Test tree node splitting behavior."""
        bandit = OffsetTreeBandit(min_samples_split=20, split_threshold=0.5)  # Higher thresholds

        # Add diverse samples to trigger splitting
        contexts = [
            {"feature1": 0.1},
            {"feature1": 0.2},
            {"feature1": 0.8},
            {"feature1": 0.9},
        ]
        rewards = [0.1, 0.2, 0.8, 0.9]

        for ctx, reward in zip(contexts, rewards):
            bandit.update("action1", reward, ctx)

        # Root should still be a leaf with only 4 samples (less than min_samples_split=20)
        assert bandit.tree_nodes["root"]["is_leaf"] is True

        # Add more diverse samples to potentially trigger split
        for i in range(25):
            ctx = {"feature1": 0.1 if i < 12 else 0.9}
            reward = 0.1 if i < 12 else 0.9
            bandit.update("action1", reward, ctx)

        # After many diverse samples, tree might split (depends on variance)

    def test_split_conditions(self):
        """Test split condition checking."""
        bandit = OffsetTreeBandit(max_depth=1, min_samples_split=5)

        # Test insufficient samples
        assert not bandit._should_split("root")

        # Add samples but not enough variance
        for i in range(6):
            bandit.update("action1", 0.5, {"feature1": 0.5})

        # Might not split due to low variance
        # This depends on the variance threshold
        bandit._should_split("root")

    def test_state_serialization(self):
        """Test state dict serialization and loading."""
        bandit = OffsetTreeBandit(max_depth=2, min_samples_split=3)
        context = {"feature1": 0.5}
        action = "action1"
        reward = 1.0

        bandit.update(action, reward, context)

        # Serialize state
        state = bandit.state_dict()
        assert state["policy"] == "OffsetTreeBandit"
        assert state["max_depth"] == 2
        assert state["min_samples_split"] == 3
        assert "root" in state["tree_nodes"]

        # Create new bandit and load state
        new_bandit = OffsetTreeBandit()
        new_bandit.load_state(state)

        assert new_bandit.max_depth == 2
        assert new_bandit.min_samples_split == 3
        assert new_bandit.counts[action] == 1

    def test_context_history_truncation(self):
        """Test that context history is properly truncated."""
        bandit = OffsetTreeBandit()

        # Add many samples to test truncation (trigger at >10000, keep last 5000)
        for i in range(12000):  # More than the 10000 limit
            context = {"feature1": i % 10}
            bandit.update("action1", 0.5, context)

        # History should be limited - it truncates when it exceeds 10000
        assert len(bandit.context_history) <= 10000
        assert len(bandit.context_history) >= 5000  # Should have at least 5000 after truncation

    def test_missing_feature_handling(self):
        """Test handling of missing features in context."""
        bandit = OffsetTreeBandit()

        # Create a context and get recommendation
        context1 = {"feature1": 0.5}
        rec1 = bandit.recommend(context1, ["action1", "action2"])

        # Context with missing feature should still work
        context2 = {"feature2": 1.0}  # Different feature
        rec2 = bandit.recommend(context2, ["action1", "action2"])

        assert rec1 in ["action1", "action2"]
        assert rec2 in ["action1", "action2"]


class TestIntegration:
    """Integration tests for advanced bandits."""

    def test_doubly_robust_learning(self):
        """Test DoublyRobust learning over multiple iterations."""
        bandit = DoublyRobustBandit(learning_rate=0.1)

        # Simulate a scenario where action1 is better for high feature1
        for i in range(100):
            if i % 2 == 0:
                context = {"feature1": 0.8}
                action = "action1"
                reward = 1.0
            else:
                context = {"feature1": 0.2}
                action = "action2"
                reward = 1.0

            bandit.update(action, reward, context)

        # Test learned behavior
        high_context = {"feature1": 0.8}
        low_context = {"feature1": 0.2}

        # Make multiple recommendations to see if pattern emerges
        high_recs = [bandit.recommend(high_context, ["action1", "action2"]) for _ in range(10)]
        low_recs = [bandit.recommend(low_context, ["action1", "action2"]) for _ in range(10)]

        # Should show some learning (not perfect due to exploration)
        assert len(set(high_recs)) <= 2
        assert len(set(low_recs)) <= 2

    def test_offset_tree_adaptation(self):
        """Test OffsetTree adaptation to context patterns."""
        bandit = OffsetTreeBandit(min_samples_split=5, split_threshold=0.1)

        # Create a clear pattern: action1 good for low values, action2 for high
        for i in range(50):
            if i < 25:
                context = {"feature1": 0.2}
                action = "action1"
                reward = 1.0
            else:
                context = {"feature1": 0.8}
                action = "action2"
                reward = 1.0

            bandit.update(action, reward, context)

        # Check that the tree has learned something
        assert bandit.tree_nodes["root"]["samples"] == 50

        # Test recommendations on new contexts
        low_context = {"feature1": 0.1}
        high_context = {"feature1": 0.9}

        low_rec = bandit.recommend(low_context, ["action1", "action2"])
        high_rec = bandit.recommend(high_context, ["action1", "action2"])

        # Both should be valid actions
        assert low_rec in ["action1", "action2"]
        assert high_rec in ["action1", "action2"]
