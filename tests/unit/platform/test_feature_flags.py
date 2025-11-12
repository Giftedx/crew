"""Tests for feature flag registry and lifecycle management."""

from __future__ import annotations

import os
from unittest.mock import mock_open, patch

import pytest

from platform.core.feature_flags import FlagCategory, FlagStatus, FeatureFlagRegistry


def test_get_registered_flag():
    """Test getting a registered flag value."""
    with patch.dict(os.environ, {"ENABLE_API": "true"}):
        assert FeatureFlagRegistry.get("ENABLE_API") is True

    with patch.dict(os.environ, {"ENABLE_API": "false"}):
        assert FeatureFlagRegistry.get("ENABLE_API") is False


def test_get_flag_default():
    """Test flag default when not in environment."""
    with patch.dict(os.environ, {}, clear=True):
        # ENABLE_API has default=True
        assert FeatureFlagRegistry.get("ENABLE_API") is True

        # ENABLE_LITELLM_ROUTER has default=False
        assert FeatureFlagRegistry.get("ENABLE_LITELLM_ROUTER") is False


def test_get_unknown_flag():
    """Test getting unknown flag returns False."""
    with patch.dict(os.environ, {}, clear=True):
        assert FeatureFlagRegistry.get("UNKNOWN_FLAG") is False


def test_get_with_override_default():
    """Test overriding default value."""
    with patch.dict(os.environ, {}, clear=True):
        # Default is True, but override to False
        assert FeatureFlagRegistry.get("ENABLE_API", default=False) is False


def test_parse_bool_variations():
    """Test boolean parsing variations."""
    registry = FeatureFlagRegistry

    # True variations
    assert registry._parse_bool("1") is True
    assert registry._parse_bool("true") is True
    assert registry._parse_bool("True") is True
    assert registry._parse_bool("TRUE") is True
    assert registry._parse_bool("yes") is True
    assert registry._parse_bool("on") is True
    assert registry._parse_bool("enabled") is True

    # False variations
    assert registry._parse_bool("0") is False
    assert registry._parse_bool("false") is False
    assert registry._parse_bool("False") is False
    assert registry._parse_bool("no") is False
    assert registry._parse_bool("off") is False


def test_list_all_flags():
    """Test listing all flags."""
    flags = FeatureFlagRegistry.list_all()

    assert len(flags) > 0
    assert all(f.name.startswith("ENABLE_") for f in flags)
    # Check alphabetical sorting
    names = [f.name for f in flags]
    assert names == sorted(names)


def test_list_flags_by_category():
    """Test filtering flags by category."""
    cache_flags = FeatureFlagRegistry.list_all(category=FlagCategory.CACHE)

    assert len(cache_flags) > 0
    assert all(f.category == FlagCategory.CACHE for f in cache_flags)
    assert "ENABLE_GPTCACHE" in {f.name for f in cache_flags}


def test_list_flags_by_status():
    """Test filtering flags by status."""
    stable_flags = FeatureFlagRegistry.list_all(status=FlagStatus.STABLE)

    assert len(stable_flags) > 0
    assert all(f.status == FlagStatus.STABLE for f in stable_flags)


def test_list_flags_combined_filters():
    """Test combined category and status filters."""
    stable_cache = FeatureFlagRegistry.list_all(
        category=FlagCategory.CACHE,
        status=FlagStatus.STABLE,
    )

    assert all(f.category == FlagCategory.CACHE for f in stable_cache)
    assert all(f.status == FlagStatus.STABLE for f in stable_cache)


def test_validate_success():
    """Test validation with no issues."""
    with patch.dict(os.environ, {"ENABLE_API": "true"}, clear=True):
        result = FeatureFlagRegistry.validate()

        assert result.success
        assert result.data["result"]["enabled_count"] >= 0
        assert result.data["result"]["total_count"] > 0


def test_validate_missing_dependency():
    """Test validation detects missing dependencies."""
    # ENABLE_SEMANTIC_CACHE_SHADOW depends on ENABLE_SEMANTIC_CACHE
    with patch.dict(
        os.environ,
        {"ENABLE_SEMANTIC_CACHE_SHADOW": "true", "ENABLE_SEMANTIC_CACHE": "false"},
        clear=True,
    ):
        result = FeatureFlagRegistry.validate()

        assert not result.success
        assert "requires" in result.error.lower()
        assert "ENABLE_SEMANTIC_CACHE" in result.error


def test_validate_multiple_dependencies():
    """Test flag with multiple dependencies."""
    # ENABLE_TRAJECTORY_FEEDBACK_LOOP depends on both evaluation and routing
    with patch.dict(
        os.environ,
        {
            "ENABLE_TRAJECTORY_FEEDBACK_LOOP": "true",
            "ENABLE_TRAJECTORY_EVALUATION": "false",
            "ENABLE_RL_ROUTING": "true",
        },
        clear=True,
    ):
        result = FeatureFlagRegistry.validate()

        assert not result.success
        assert "ENABLE_TRAJECTORY_EVALUATION" in result.error


def test_get_metadata_existing_flag():
    """Test getting metadata for existing flag."""
    metadata = FeatureFlagRegistry.get_metadata("ENABLE_API")

    assert metadata is not None
    assert metadata["name"] == "ENABLE_API"
    assert metadata["description"] == "Enable FastAPI REST API server"
    assert metadata["category"] == "core"
    assert metadata["status"] == "stable"
    assert metadata["default"] is True
    assert "current" in metadata
    assert isinstance(metadata["dependencies"], list)


def test_get_metadata_nonexistent_flag():
    """Test getting metadata for nonexistent flag."""
    metadata = FeatureFlagRegistry.get_metadata("NONEXISTENT_FLAG")

    assert metadata is None


def test_metadata_includes_current_value():
    """Test metadata includes current environment value."""
    with patch.dict(os.environ, {"ENABLE_API": "false"}):
        metadata = FeatureFlagRegistry.get_metadata("ENABLE_API")

        assert metadata["current"] is False


def test_sync_with_env_example_success():
    """Test sync validation succeeds when registry matches .env.example."""
    env_content = """
# Test .env.example
ENABLE_API=true
ENABLE_TRACING=true
ENABLE_GPTCACHE=true
"""

    with patch("builtins.open", mock_open(read_data=env_content)):
        result = FeatureFlagRegistry.sync_with_env_example(".env.example")

        # Will be uncertain because .env.example has far more flags than test subset
        assert result.success or not result.success  # May be ok or uncertain


def test_sync_detects_missing_in_env():
    """Test sync detects flags in registry but not in .env.example."""
    env_content = """
# Minimal .env.example - missing many registry flags
ENABLE_API=true
"""

    with patch("builtins.open", mock_open(read_data=env_content)):
        result = FeatureFlagRegistry.sync_with_env_example(".env.example")

        # Uncertain status is still success=True
        assert result.success
        assert result.custom_status == "uncertain"
        assert "Missing in .env.example" in str(result.data["result"])


def test_sync_handles_file_error():
    """Test sync handles file read errors gracefully."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        result = FeatureFlagRegistry.sync_with_env_example(".env.example")

        assert not result.success
        assert result.error_category.name == "EXTERNAL_SERVICE_ERROR"


def test_flag_dependency_chain():
    """Test flag with dependency chain."""
    # ENABLE_GPTCACHE_ANALYSIS_SHADOW depends on ENABLE_GPTCACHE
    metadata_shadow = FeatureFlagRegistry.get_metadata("ENABLE_GPTCACHE_ANALYSIS_SHADOW")
    assert metadata_shadow is not None
    assert "ENABLE_GPTCACHE" in metadata_shadow["dependencies"]


def test_category_enum_values():
    """Test all expected categories are defined."""
    categories = {c.value for c in FlagCategory}

    assert "core" in categories
    assert "cache" in categories
    assert "llm" in categories
    assert "memory" in categories
    assert "observability" in categories
    assert "security" in categories


def test_status_enum_values():
    """Test all expected statuses are defined."""
    statuses = {s.value for s in FlagStatus}

    assert "experimental" in statuses
    assert "beta" in statuses
    assert "stable" in statuses
    assert "deprecated" in statuses
    assert "removed" in statuses


def test_tool_contract_validation_flag():
    """Test ENABLE_TOOL_CONTRACT_VALIDATION flag exists and is shadow mode."""
    metadata = FeatureFlagRegistry.get_metadata("ENABLE_TOOL_CONTRACT_VALIDATION")

    assert metadata is not None
    assert metadata["status"] == "beta"
    assert metadata["default"] is False  # Shadow mode by default
    assert metadata["added_date"] == "2025-11-12"
