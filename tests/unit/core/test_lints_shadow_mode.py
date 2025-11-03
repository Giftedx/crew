"""Tests for LinTS shadow mode implementation."""

import os
from platform.core.learning_engine import LearningEngine
from platform.core.rl.policies.lints import LinTSDiagBandit
from platform.core.rl.shadow_regret import ShadowRegretTracker, get_shadow_tracker
from unittest.mock import MagicMock, patch


def enable_flags():
    """Enable required flags for LinTS shadow mode."""
    os.environ["ENABLE_RL_LINTS"] = "1"
    os.environ["ENABLE_RL_SHADOW"] = "1"


def disable_flags():
    """Disable flags to test default behavior."""
    os.environ.pop("ENABLE_RL_LINTS", None)
    os.environ.pop("ENABLE_RL_SHADOW", None)


def test_lints_policy_creation():
    """Test that LinTS policy can be created and used."""
    policy = LinTSDiagBandit()
    candidates = ["model_a", "model_b", "model_c"]
    context = {"task": "analysis", "complexity": 0.7}
    choice = policy.recommend(context, candidates)
    assert choice in candidates
    policy.update(choice, 0.85, context)
    assert policy.counts[choice] == 1
    assert abs(policy.q_values[choice] - 0.85) < 0.001


def test_shadow_regret_tracker():
    """Test the shadow regret tracking functionality."""
    tracker = ShadowRegretTracker()
    tracker.update_baseline(0.8)
    tracker.update_baseline(0.85)
    tracker.update_baseline(0.9)
    assert tracker.baseline_count == 3
    assert abs(tracker.baseline_reward - 0.85) < 0.01
    tracker.record_shadow_result("lints", 0.82, True)
    tracker.record_shadow_result("lints", 0.88, False)
    tracker.record_shadow_result("lints", 0.86, True)
    summary = tracker.get_summary()
    assert "lints" in summary["policies"]
    lints_stats = summary["policies"]["lints"]
    assert lints_stats["pulls"] == 3
    assert abs(lints_stats["avg_reward"] - 0.853) < 0.01
    assert abs(lints_stats["performance_ratio"] - 1.0) < 0.1


def test_lints_shadow_mode_integration():
    """Test LinTS shadow mode integration in LearningEngine."""
    enable_flags()
    with patch("core.learning_engine.metrics") as mock_metrics:
        mock_llm_selected = MagicMock()
        mock_metrics.LLM_MODEL_SELECTED = mock_llm_selected
        mock_metrics.label_ctx.return_value = {"tenant": "test", "workspace": "main"}
        engine = LearningEngine()
        engine.register_domain("test_domain")
        candidates = ["gpt-3.5", "gpt-4", "claude"]
        choice = engine.select_model("analysis", candidates)
        assert choice in candidates
        assert mock_llm_selected.labels.called
        calls = mock_llm_selected.labels.call_args_list
        shadow_calls = [call for call in calls if "shadow::lints" in str(call)]
        assert len(shadow_calls) > 0


def test_regret_tracking_with_updates():
    """Test regret tracking when updates are made."""
    enable_flags()
    tracker = get_shadow_tracker()
    tracker.cumulative_regret.clear()
    tracker.total_pulls.clear()
    tracker.total_rewards.clear()
    tracker.baseline_count = 0
    tracker.baseline_reward = 0.0
    engine = LearningEngine()
    for i in range(10):
        choice = engine.select_model("analysis", ["gpt-3.5", "gpt-4"])
        reward = 0.8 + i % 3 * 0.05
        engine.update("analysis", choice, reward)
    assert tracker.baseline_count == 10
    assert tracker.baseline_reward > 0.0


def test_lints_policy_state_serialization():
    """Test LinTS policy state dict and load state functionality."""
    policy = LinTSDiagBandit(dim=4, sigma=0.3)
    candidates = ["a", "b", "c"]
    for i in range(5):
        context = {"feature1": i * 0.1, "feature2": i % 2 * 0.5}
        choice = policy.recommend(context, candidates)
        policy.update(choice, 0.7 + i * 0.05, context)
    state = policy.state_dict()
    assert state["policy"] == "LinTSDiagBandit"
    assert state["version"] == 1
    assert state["dim"] == 4
    assert state["sigma"] == 0.3
    assert len(state["q_values"]) > 0
    assert len(state["counts"]) > 0
    new_policy = LinTSDiagBandit()
    new_policy.load_state(state)
    assert new_policy.dim == 4
    assert new_policy.sigma == 0.3
    assert new_policy.q_values == policy.q_values
    assert new_policy.counts == policy.counts


def test_shadow_mode_disabled():
    """Test that shadow mode is properly disabled when flags are off."""
    disable_flags()
    with patch("core.learning_engine.metrics") as mock_metrics:
        mock_llm_selected = MagicMock()
        mock_metrics.LLM_MODEL_SELECTED = mock_llm_selected
        mock_metrics.label_ctx.return_value = {"tenant": "test", "workspace": "main"}
        engine = LearningEngine()
        candidates = ["gpt-3.5", "gpt-4"]
        choice = engine.select_model("analysis", candidates)
        assert choice in candidates
        calls = mock_llm_selected.labels.call_args_list
        shadow_calls = [call for call in calls if "shadow" in str(call)]
        assert len(shadow_calls) == 0


def test_lints_flag_disabled():
    """Test that LinTS is not included in shadow when its flag is disabled."""
    os.environ["ENABLE_RL_SHADOW"] = "1"
    os.environ.pop("ENABLE_RL_LINTS", None)
    with patch("core.learning_engine.metrics") as mock_metrics:
        mock_llm_selected = MagicMock()
        mock_metrics.LLM_MODEL_SELECTED = mock_llm_selected
        mock_metrics.label_ctx.return_value = {"tenant": "test", "workspace": "main"}
        engine = LearningEngine()
        candidates = ["gpt-3.5", "gpt-4"]
        choice = engine.select_model("analysis", candidates)
        assert choice in candidates
        calls = mock_llm_selected.labels.call_args_list
        shadow_calls = [call for call in calls if "shadow" in str(call)]
        lints_calls = [call for call in calls if "shadow::lints" in str(call)]
        assert len(shadow_calls) > 0
        assert len(lints_calls) == 0


def test_regret_percentage_calculation():
    """Test regret percentage calculation."""
    tracker = ShadowRegretTracker()
    tracker.baseline_reward = 0.8
    tracker.baseline_count = 10
    tracker.record_shadow_result("policy_a", 0.75, False)
    tracker.record_shadow_result("policy_a", 0.77, False)
    tracker.record_shadow_result("policy_a", 0.82, True)
    regret_pct = tracker.get_regret_percentage("policy_a")
    assert regret_pct >= 0.0
    performance_ratio = tracker.get_performance_ratio("policy_a")
    assert abs(performance_ratio - 0.975) < 0.02


if __name__ == "__main__":
    test_lints_policy_creation()
    test_shadow_regret_tracker()
    test_lints_shadow_mode_integration()
    test_regret_tracking_with_updates()
    test_lints_policy_state_serialization()
    test_shadow_mode_disabled()
    test_lints_flag_disabled()
    test_regret_percentage_calculation()
    print("All LinTS shadow mode tests passed!")
