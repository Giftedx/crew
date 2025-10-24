"""Caching System for the Ultimate Discord Intelligence Bot.

This package provides comprehensive caching capabilities including:
- Result caching for expensive operations
- Smart caching with adaptive strategies
- Cache configuration and management
- Performance monitoring and optimization
"""

from __future__ import annotations

from ultimate_discord_intelligence_bot.caching.result_cache import (
    CacheEntry,
    ResultCache,
    cache_result,
    cache_tool_result,
    clear_result_cache,
    get_cache_stats,
    get_result_cache,
    invalidate_cache_pattern,
)
from ultimate_discord_intelligence_bot.caching.smart_cache import (
    CachingStrategy,
    SmartCache,
    ToolUsagePattern,
    analyze_cache_performance,
    auto_optimize_cache,
    get_cache_recommendations,
    get_smart_cache,
    smart_cache_tool_result,
)


__all__ = [
    # Result cache
    "ResultCache",
    "CacheEntry",
    "get_result_cache",
    "cache_result",
    "cache_tool_result",
    "clear_result_cache",
    "get_cache_stats",
    "invalidate_cache_pattern",
    # Smart cache
    "SmartCache",
    "ToolUsagePattern",
    "CachingStrategy",
    "get_smart_cache",
    "smart_cache_tool_result",
    "analyze_cache_performance",
    "auto_optimize_cache",
    "get_cache_recommendations",
]
