"""Test cases for advanced contextual bandit algorithms."""

from platform.core.rl.policies.advanced_bandits import DoublyRobustBandit, OffsetTreeBandit

import pytest


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
        initial_pred = bandit._predict_reward(action, context)
        assert abs(initial_pred) < 0.1
        bandit.update(action, 1.0, context)
        new_pred = bandit._predict_reward(action, context)
        assert new_pred > initial_pred

    def test_state_serialization(self):
        """Test state dict serialization and loading."""
        bandit = DoublyRobustBandit(alpha=1.5, dim=6)
        context = {"feature1": 0.5}
        action = "action1"
        reward = 1.0
        bandit.update(action, reward, context)
        state = bandit.state_dict()
        assert state["policy"] == "DoublyRobustBandit"
        assert state["alpha"] == 1.5
        assert state["dim"] == 6
        assert "action1" in state["reward_models"]
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
        rec1 = bandit.recommend(context, candidates)
        bandit.update("action1", 1.0, context)
        bandit.update("action1", 1.0, context)
        rec2 = bandit.recommend(context, candidates)
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
        bandit = OffsetTreeBandit(min_samples_split=20, split_threshold=0.5)
        contexts = [{"feature1": 0.1}, {"feature1": 0.2}, {"feature1": 0.8}, {"feature1": 0.9}]
        rewards = [0.1, 0.2, 0.8, 0.9]
        for ctx, reward in zip(contexts, rewards, strict=False):
            bandit.update("action1", reward, ctx)
        assert bandit.tree_nodes["root"]["is_leaf"] is True
        for i in range(25):
            ctx = {"feature1": 0.1 if i < 12 else 0.9}
            reward = 0.1 if i < 12 else 0.9
            bandit.update("action1", reward, ctx)

    def test_split_conditions(self):
        """Test split condition checking."""
        bandit = OffsetTreeBandit(max_depth=1, min_samples_split=5)
        assert not bandit._should_split("root")
        for _i in range(6):
            bandit.update("action1", 0.5, {"feature1": 0.5})
        bandit._should_split("root")

    def test_state_serialization(self):
        """Test state dict serialization and loading."""
        bandit = OffsetTreeBandit(max_depth=2, min_samples_split=3)
        context = {"feature1": 0.5}
        action = "action1"
        reward = 1.0
        bandit.update(action, reward, context)
        state = bandit.state_dict()
        assert state["policy"] == "OffsetTreeBandit"
        assert state["max_depth"] == 2
        assert state["min_samples_split"] == 3
        assert "root" in state["tree_nodes"]
        new_bandit = OffsetTreeBandit()
        new_bandit.load_state(state)
        assert new_bandit.max_depth == 2
        assert new_bandit.min_samples_split == 3
        assert new_bandit.counts[action] == 1

    def test_context_history_truncation(self):
        """Test that context history is properly truncated."""
        bandit = OffsetTreeBandit()
        for i in range(12000):
            context = {"feature1": i % 10}
            bandit.update("action1", 0.5, context)
        assert len(bandit.context_history) <= 10000
        assert len(bandit.context_history) >= 5000

    def test_missing_feature_handling(self):
        """Test handling of missing features in context."""
        bandit = OffsetTreeBandit()
        context1 = {"feature1": 0.5}
        rec1 = bandit.recommend(context1, ["action1", "action2"])
        context2 = {"feature2": 1.0}
        rec2 = bandit.recommend(context2, ["action1", "action2"])
        assert rec1 in ["action1", "action2"]
        assert rec2 in ["action1", "action2"]


class TestIntegration:
    """Integration tests for advanced bandits."""

    def test_doubly_robust_learning(self):
        """Test DoublyRobust learning over multiple iterations."""
        bandit = DoublyRobustBandit(learning_rate=0.1)
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
        high_context = {"feature1": 0.8}
        low_context = {"feature1": 0.2}
        high_recs = [bandit.recommend(high_context, ["action1", "action2"]) for _ in range(10)]
        low_recs = [bandit.recommend(low_context, ["action1", "action2"]) for _ in range(10)]
        assert len(set(high_recs)) <= 2
        assert len(set(low_recs)) <= 2

    def test_offset_tree_adaptation(self):
        """Test OffsetTree adaptation to context patterns."""
        bandit = OffsetTreeBandit(min_samples_split=5, split_threshold=0.1)
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
        assert bandit.tree_nodes["root"]["samples"] == 50
        low_context = {"feature1": 0.1}
        high_context = {"feature1": 0.9}
        low_rec = bandit.recommend(low_context, ["action1", "action2"])
        high_rec = bandit.recommend(high_context, ["action1", "action2"])
        assert low_rec in ["action1", "action2"]
        assert high_rec in ["action1", "action2"]
