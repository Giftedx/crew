"""Lazy Loading Configuration.

This module provides configuration for lazy loading behavior, including
feature flags, performance settings, and tool preloading strategies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags


@dataclass
class LazyLoadingConfig:
    """Configuration for lazy loading behavior."""

    # Feature flags
    enabled: bool = True
    preload_critical_tools: bool = True
    cache_tools: bool = True
    enable_metrics: bool = True

    # Performance settings
    max_cache_size: int = 100
    preload_timeout: float = 5.0
    lazy_import_timeout: float = 2.0

    # Tool categories for different loading strategies
    critical_tools: list[str] = None
    optional_tools: list[str] = None
    heavy_tools: list[str] = None

    # Performance thresholds
    slow_tool_threshold: float = 1.0  # seconds
    memory_threshold_mb: int = 100

    def __post_init__(self):
        """Initialize default tool categories."""
        if self.critical_tools is None:
            self.critical_tools = [
                "MultiPlatformDownloadTool",
                "AudioTranscriptionTool",
                "UnifiedMemoryTool",
                "FactCheckTool",
            ]

        if self.optional_tools is None:
            self.optional_tools = [
                "InstagramDownloadTool",
                "TikTokDownloadTool",
                "RedditDownloadTool",
                "TwitterDownloadTool",
            ]

        if self.heavy_tools is None:
            self.heavy_tools = [
                "AdvancedAudioAnalysisTool",
                "VideoFrameAnalysisTool",
                "MultimodalAnalysisTool",
                "SocialGraphAnalysisTool",
            ]


def get_lazy_loading_config() -> LazyLoadingConfig:
    """Get lazy loading configuration from environment and feature flags."""
    feature_flags = FeatureFlags.from_env()

    return LazyLoadingConfig(
        enabled=feature_flags.ENABLE_LAZY_LOADING,
        preload_critical_tools=feature_flags.ENABLE_LAZY_PRELOAD_CRITICAL,
        cache_tools=feature_flags.ENABLE_LAZY_CACHING,
        enable_metrics=feature_flags.ENABLE_LAZY_METRICS,
    )


def get_tool_loading_strategy(tool_name: str) -> str:
    """Get loading strategy for a specific tool."""
    config = get_lazy_loading_config()

    if tool_name in config.critical_tools:
        return "critical"  # Load immediately
    elif tool_name in config.optional_tools:
        return "optional"  # Load on demand
    elif tool_name in config.heavy_tools:
        return "heavy"  # Load with delay
    else:
        return "default"  # Standard lazy loading


def should_preload_tool(tool_name: str) -> bool:
    """Determine if a tool should be preloaded."""
    config = get_lazy_loading_config()

    if not config.enabled:
        return False

    if not config.preload_critical_tools:
        return False

    return tool_name in config.critical_tools


def get_preload_priority(tool_name: str) -> int:
    """Get preload priority for a tool (higher = more important)."""
    config = get_lazy_loading_config()

    if tool_name in config.critical_tools:
        return 10
    elif tool_name in config.optional_tools:
        return 5
    elif tool_name in config.heavy_tools:
        return 1
    else:
        return 3


class LazyLoadingManager:
    """Manager for lazy loading operations and configuration."""

    def __init__(self):
        """Initialize the lazy loading manager."""
        self.config = get_lazy_loading_config()
        self._tool_priorities: dict[str, int] = {}
        self._loading_stats: dict[str, Any] = {}

    def get_tool_priority(self, tool_name: str) -> int:
        """Get priority for a tool."""
        if tool_name not in self._tool_priorities:
            self._tool_priorities[tool_name] = get_preload_priority(tool_name)
        return self._tool_priorities[tool_name]

    def should_preload(self, tool_name: str) -> bool:
        """Check if a tool should be preloaded."""
        return should_preload_tool(tool_name)

    def get_preload_list(self, tool_names: list[str]) -> list[str]:
        """Get list of tools to preload, sorted by priority."""
        preload_candidates = [name for name in tool_names if self.should_preload(name)]

        # Sort by priority (highest first)
        preload_candidates.sort(key=lambda name: self.get_tool_priority(name), reverse=True)

        return preload_candidates

    def update_config(self, **kwargs):
        """Update configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def get_stats(self) -> dict[str, Any]:
        """Get loading statistics."""
        return {
            "config": {
                "enabled": self.config.enabled,
                "preload_critical": self.config.preload_critical_tools,
                "cache_tools": self.config.cache_tools,
                "enable_metrics": self.config.enable_metrics,
            },
            "tool_priorities": self._tool_priorities.copy(),
            "loading_stats": self._loading_stats.copy(),
        }


# Global lazy loading manager
_lazy_manager = LazyLoadingManager()


def get_lazy_manager() -> LazyLoadingManager:
    """Get the global lazy loading manager."""
    return _lazy_manager


def configure_lazy_loading(**kwargs):
    """Configure lazy loading settings."""
    manager = get_lazy_manager()
    manager.update_config(**kwargs)


def get_tool_loading_config(tool_name: str) -> dict[str, Any]:
    """Get loading configuration for a specific tool."""
    manager = get_lazy_manager()

    return {
        "strategy": get_tool_loading_strategy(tool_name),
        "priority": manager.get_tool_priority(tool_name),
        "should_preload": manager.should_preload(tool_name),
        "timeout": manager.config.lazy_import_timeout,
    }
