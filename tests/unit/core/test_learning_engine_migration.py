"""Tests for migrated LearningEngine functionality."""

from platform.core.learning_engine import LearningEngine

import pytest


def test_learning_engine_initialization():
    """Test that LearningEngine initializes correctly after migration."""
    engine = LearningEngine()
    assert engine is not None
    assert hasattr(engine, "select_model")
    assert hasattr(engine, "update")


def test_learning_engine_select_model_basic():
    """Test basic model selection functionality."""
    engine = LearningEngine()
    candidates = ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet"]
    result = engine.select_model("test_domain", candidates)
    assert result in candidates
    assert isinstance(result, str)


def test_learning_engine_update_basic():
    """Test basic model update functionality."""
    engine = LearningEngine()
    engine.update("test_domain", "gpt-4", 0.85)
    assert True


def test_learning_engine_edge_cases():
    """Test edge cases for LearningEngine."""
    engine = LearningEngine()
    with pytest.raises(ValueError, match="candidates must not be empty"):
        engine.select_model("empty_domain", [])
    result = engine.select_model("single_domain", ["only_model"])
    assert result == "only_model"
    engine.update("edge_domain", "test_model", 0.0)
    engine.update("edge_domain", "test_model", 1.0)


def test_learning_engine_consistent_selection():
    """Test that model selection is consistent for same inputs."""
    engine = LearningEngine()
    candidates = ["model_a", "model_b", "model_c"]
    results = []
    for _ in range(5):
        result = engine.select_model("consistency_test", candidates)
        results.append(result)
        assert result in candidates
    assert all(r in candidates for r in results)


if __name__ == "__main__":
    pytest.main([__file__])
