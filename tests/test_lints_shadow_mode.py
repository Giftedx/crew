"""Tests for LinTS shadow mode implementation."""

import os
from unittest.mock import MagicMock, patch

from core.learning_engine import LearningEngine
from core.rl.policies.lints import LinTSDiagBandit
from core.rl.shadow_regret import ShadowRegretTracker, get_shadow_tracker


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

    # Test basic functionality
    candidates = ["model_a", "model_b", "model_c"]
    context = {"task": "analysis", "complexity": 0.7}

    choice = policy.recommend(context, candidates)
    assert choice in candidates

    # Test update
    policy.update(choice, 0.85, context)
    assert policy.counts[choice] == 1
    assert abs(policy.q_values[choice] - 0.85) < 0.001


def test_shadow_regret_tracker():
    """Test the shadow regret tracking functionality."""
    tracker = ShadowRegretTracker()

    # Update baseline performance
    tracker.update_baseline(0.8)
    tracker.update_baseline(0.85)
    tracker.update_baseline(0.9)

    assert tracker.baseline_count == 3
    assert abs(tracker.baseline_reward - 0.85) < 0.01  # Average of the three

    # Record shadow results
    tracker.record_shadow_result("lints", 0.82, True)
    tracker.record_shadow_result("lints", 0.88, False)
    tracker.record_shadow_result("lints", 0.86, True)

    # Check summary
    summary = tracker.get_summary()
    assert "lints" in summary["policies"]
    lints_stats = summary["policies"]["lints"]
    assert lints_stats["pulls"] == 3
    assert abs(lints_stats["avg_reward"] - 0.853) < 0.01

    # Performance ratio should be close to 1.0 (similar performance)
    assert abs(lints_stats["performance_ratio"] - 1.0) < 0.1


def test_lints_shadow_mode_integration():
    """Test LinTS shadow mode integration in LearningEngine."""
    enable_flags()

    with patch("core.learning_engine.metrics") as mock_metrics:
        # Mock the metrics
        mock_llm_selected = MagicMock()
        mock_metrics.LLM_MODEL_SELECTED = mock_llm_selected
        mock_metrics.label_ctx.return_value = {"tenant": "test", "workspace": "main"}

        engine = LearningEngine()

        # Register a non-LinTS policy as active
        engine.register_domain("test_domain")

        candidates = ["gpt-3.5", "gpt-4", "claude"]

        # Should include LinTS in shadow evaluation
        choice = engine.select_model("analysis", candidates)
        assert choice in candidates

        # Verify shadow metrics were recorded (LinTS should be included)
        assert mock_llm_selected.labels.called

        # Check if lints shadow was included in calls
        calls = mock_llm_selected.labels.call_args_list
        shadow_calls = [call for call in calls if "shadow::lints" in str(call)]
        assert len(shadow_calls) > 0


def test_regret_tracking_with_updates():
    """Test regret tracking when updates are made."""
    enable_flags()

    # Clear any existing tracker state
    tracker = get_shadow_tracker()
    tracker.cumulative_regret.clear()
    tracker.total_pulls.clear()
    tracker.total_rewards.clear()
    tracker.baseline_count = 0
    tracker.baseline_reward = 0.0

    engine = LearningEngine()

    # Simulate some model selections and updates
    for i in range(10):
        choice = engine.select_model("analysis", ["gpt-3.5", "gpt-4"])
        reward = 0.8 + (i % 3) * 0.05  # Varying rewards
        engine.update("analysis", choice, reward)

    # Check that baseline was updated
    assert tracker.baseline_count == 10
    assert tracker.baseline_reward > 0.0


def test_lints_policy_state_serialization():
    """Test LinTS policy state dict and load state functionality."""
    policy = LinTSDiagBandit(dim=4, sigma=0.3)

    # Make some updates to create state
    candidates = ["a", "b", "c"]
    for i in range(5):
        context = {"feature1": i * 0.1, "feature2": (i % 2) * 0.5}
        choice = policy.recommend(context, candidates)
        policy.update(choice, 0.7 + i * 0.05, context)

    # Get state dict
    state = policy.state_dict()
    assert state["policy"] == "LinTSDiagBandit"
    assert state["version"] == 1
    assert state["dim"] == 4
    assert state["sigma"] == 0.3
    assert len(state["q_values"]) > 0
    assert len(state["counts"]) > 0

    # Create new policy and load state
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

        # No shadow metrics should be recorded
        calls = mock_llm_selected.labels.call_args_list
        shadow_calls = [call for call in calls if "shadow" in str(call)]
        assert len(shadow_calls) == 0


def test_lints_flag_disabled():
    """Test that LinTS is not included in shadow when its flag is disabled."""
    os.environ["ENABLE_RL_SHADOW"] = "1"
    os.environ.pop("ENABLE_RL_LINTS", None)  # Disable LinTS specifically

    with patch("core.learning_engine.metrics") as mock_metrics:
        mock_llm_selected = MagicMock()
        mock_metrics.LLM_MODEL_SELECTED = mock_llm_selected
        mock_metrics.label_ctx.return_value = {"tenant": "test", "workspace": "main"}

        engine = LearningEngine()
        candidates = ["gpt-3.5", "gpt-4"]

        choice = engine.select_model("analysis", candidates)
        assert choice in candidates

        # Should have shadow calls, but not for LinTS
        calls = mock_llm_selected.labels.call_args_list
        shadow_calls = [call for call in calls if "shadow" in str(call)]
        lints_calls = [call for call in calls if "shadow::lints" in str(call)]

        assert len(shadow_calls) > 0  # Other shadow policies
        assert len(lints_calls) == 0  # No LinTS


def test_regret_percentage_calculation():
    """Test regret percentage calculation."""
    tracker = ShadowRegretTracker()

    # Set up baseline
    tracker.baseline_reward = 0.8
    tracker.baseline_count = 10

    # Record some results with different performance
    tracker.record_shadow_result("policy_a", 0.75, False)  # 5% worse
    tracker.record_shadow_result("policy_a", 0.77, False)  # 3% worse
    tracker.record_shadow_result("policy_a", 0.82, True)  # 2% better

    regret_pct = tracker.get_regret_percentage("policy_a")
    # Should be positive since there was some regret
    assert regret_pct >= 0.0

    performance_ratio = tracker.get_performance_ratio("policy_a")
    # Should be close to 1.0 with slight underperformance
    assert abs(performance_ratio - 0.975) < 0.02  # (0.75+0.77+0.82)/3 / 0.8


if __name__ == "__main__":
    # Run all tests
    test_lints_policy_creation()
    test_shadow_regret_tracker()
    test_lints_shadow_mode_integration()
    test_regret_tracking_with_updates()
    test_lints_policy_state_serialization()
    test_shadow_mode_disabled()
    test_lints_flag_disabled()
    test_regret_percentage_calculation()
    print("All LinTS shadow mode tests passed!")
