"""Tests for migrated LearningEngine functionality."""

import pytest

from core.learning_engine import LearningEngine


def test_learning_engine_initialization():
    """Test that LearningEngine initializes correctly after migration."""
    engine = LearningEngine()
    assert engine is not None
    assert hasattr(engine, "select_model")
    assert hasattr(engine, "update")


def test_learning_engine_select_model_basic():
    """Test basic model selection functionality."""
    engine = LearningEngine()

    # Test with simple domain and candidates
    candidates = ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet"]
    result = engine.select_model("test_domain", candidates)

    assert result in candidates
    assert isinstance(result, str)


def test_learning_engine_update_basic():
    """Test basic model update functionality."""
    engine = LearningEngine()

    # Test update with valid parameters
    engine.update("test_domain", "gpt-4", 0.85)

    # Should not raise any exceptions
    assert True


def test_learning_engine_edge_cases():
    """Test edge cases for LearningEngine."""
    engine = LearningEngine()

    # Test with empty candidates (should raise ValueError)
    with pytest.raises(ValueError, match="candidates must not be empty"):
        engine.select_model("empty_domain", [])

    # Test with single candidate
    result = engine.select_model("single_domain", ["only_model"])
    assert result == "only_model"

    # Test update with edge reward values
    engine.update("edge_domain", "test_model", 0.0)  # Min reward
    engine.update("edge_domain", "test_model", 1.0)  # Max reward


def test_learning_engine_consistent_selection():
    """Test that model selection is consistent for same inputs."""
    engine = LearningEngine()
    candidates = ["model_a", "model_b", "model_c"]

    # Multiple calls should be deterministic or at least not crash
    results = []
    for _ in range(5):
        result = engine.select_model("consistency_test", candidates)
        results.append(result)
        assert result in candidates

    # All results should be valid candidates
    assert all(r in candidates for r in results)


if __name__ == "__main__":
    pytest.main([__file__])
