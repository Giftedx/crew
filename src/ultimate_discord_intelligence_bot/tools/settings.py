"""Tool-specific settings and configuration.

This module provides tool-specific configuration settings that don't belong
in the main settings module but are needed by various tools.
"""

from __future__ import annotations

import contextlib
import os
import warnings
from pathlib import Path
from typing import Any


try:
    # Prefer unified cache configuration for TTLs when available
    from core.cache.unified_config import get_cache_ttl as _unified_get_cache_ttl  # type: ignore
except Exception:  # pragma: no cover - optional dependency path
    _unified_get_cache_ttl = None  # type: ignore

# Project base directory for tool storage paths
try:  # Prefer main application BASE_DIR if available
    from ultimate_discord_intelligence_bot.settings import BASE_DIR as _BASE_DIR  # type: ignore
except Exception:  # pragma: no cover - optional in minimal envs
    _BASE_DIR = Path.cwd()

# Public constant for tools to consume
BASE_DIR: Path = _BASE_DIR


def get_tool_setting(key: str, default: Any = None) -> Any:
    """Get a tool-specific setting from environment variables.

    Args:
        key: The setting key to retrieve
        default: Default value if setting is not found

    Returns:
        The setting value or default
    """
    return os.getenv(f"TOOL_{key.upper()}", default)


def get_download_timeout() -> int:
    """Get the default download timeout in seconds."""
    return int(get_tool_setting("DOWNLOAD_TIMEOUT", "300"))


def get_transcription_timeout() -> int:
    """Get the default transcription timeout in seconds."""
    return int(get_tool_setting("TRANSCRIPTION_TIMEOUT", "600"))


def get_analysis_timeout() -> int:
    """Get the default analysis timeout in seconds."""
    return int(get_tool_setting("ANALYSIS_TIMEOUT", "120"))


def get_max_file_size() -> int:
    """Get the maximum file size in bytes."""
    return int(get_tool_setting("MAX_FILE_SIZE", "104857600"))  # 100MB


def get_enable_caching() -> bool:
    """Get whether caching is enabled for tools."""
    return get_tool_setting("ENABLE_CACHING", "true").lower() in ("true", "1", "yes")


def get_cache_ttl() -> int:
    """Get the cache TTL in seconds.

    Deprecated: Use core.cache.unified_config.get_cache_ttl("tool") instead.
    """
    warnings.warn(
        ("tools.settings.get_cache_ttl() is deprecated. Use core.cache.unified_config.get_cache_ttl('tool') instead."),
        DeprecationWarning,
        stacklevel=2,
    )
    if _unified_get_cache_ttl:
        with contextlib.suppress(Exception):
            return int(_unified_get_cache_ttl("tool"))
    return int(get_tool_setting("CACHE_TTL", "3600"))  # 1 hour


# Tool-specific configuration
TOOL_CONFIG = {
    "download_timeout": get_download_timeout(),
    "transcription_timeout": get_transcription_timeout(),
    "analysis_timeout": get_analysis_timeout(),
    "max_file_size": get_max_file_size(),
    "enable_caching": get_enable_caching(),
    "cache_ttl": get_cache_ttl(),
}
