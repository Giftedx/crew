"""Semantic cache warming utilities for proactive cache population.

This module provides intelligent cache warming strategies that work with
semantic caching to improve hit rates beyond exact matches by pre-populating
caches with semantically similar queries and high-traffic patterns.
"""

from __future__ import annotations

import logging
from platform.cache.multi_level_cache import get_cache
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics


if TYPE_CHECKING:
    from collections.abc import Callable
    from platform.cache.semantic_cache_service import SemanticCacheService

logger = logging.getLogger(__name__)
metrics = get_metrics()


class SemanticCacheWarmer:
    """Intelligent cache warmer that leverages semantic similarity for proactive warming."""

    def __init__(
        self,
        semantic_cache: SemanticCacheService,
        cache_ttl: int = 3600,
        similarity_threshold: float = 0.85,
        max_warm_keys: int = 100,
    ):
        """Initialize semantic cache warmer.

        Args:
            semantic_cache: Semantic cache service instance
            cache_ttl: Default TTL for warmed cache entries
            similarity_threshold: Similarity threshold for semantic matching
            max_warm_keys: Maximum number of keys to warm per operation
        """
        self.semantic_cache = semantic_cache
        self.cache_ttl = cache_ttl
        self.similarity_threshold = similarity_threshold
        self.max_warm_keys = max_warm_keys
        self.cache = get_cache()
        self._warming_stats = {
            "total_warmed": 0,
            "semantic_hits": 0,
            "exact_hits": 0,
            "misses": 0,
        }

    async def warm_from_patterns(
        self,
        operation: str,
        patterns: list[dict[str, Any]],
        data_fetcher: Callable[[dict[str, Any]], Any],
        tenant: str = "",
        workspace: str = "",
    ) -> dict[str, Any]:
        """Warm cache using predefined query patterns.

        Args:
            operation: Cache operation name
            patterns: List of input patterns to warm
            data_fetcher: Function to fetch data for each pattern
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            Warming statistics
        """
        warmed_count = 0
        semantic_count = 0

        for pattern in patterns[: self.max_warm_keys]:
            try:
                # Check if already cached (exact match)
                existing = self.cache.get(operation, pattern, tenant, workspace)
                if existing is not None:
                    self._warming_stats["exact_hits"] += 1
                    continue

                # Check semantic cache for similar queries
                semantic_match = await self.semantic_cache.get_semantic_match(
                    operation, pattern, tenant, workspace, self.similarity_threshold
                )

                if semantic_match:
                    # Use semantically similar result
                    self.cache.set(operation, pattern, semantic_match["value"], self.cache_ttl, tenant, workspace)
                    semantic_count += 1
                    warmed_count += 1
                    self._warming_stats["semantic_hits"] += 1
                else:
                    # Fetch fresh data and cache it
                    try:
                        data = data_fetcher(pattern)
                        if data is not None:
                            self.cache.set(operation, pattern, data, self.cache_ttl, tenant, workspace)
                            # Also store in semantic cache for future similarity matching
                            await self.semantic_cache.store_semantic_entry(operation, pattern, data, tenant, workspace)
                            warmed_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to fetch data for pattern {pattern}: {e}")
                        self._warming_stats["misses"] += 1

            except Exception as e:
                logger.error(f"Error warming pattern {pattern}: {e}")
                continue

        self._warming_stats["total_warmed"] += warmed_count

        stats = {
            "warmed_count": warmed_count,
            "semantic_count": semantic_count,
            "patterns_processed": len(patterns),
            "cache_stats": self.cache.get_stats(),
        }

        metrics.counter(
            "cache_warmer_patterns_warmed",
            labels={"operation": operation, "tenant": tenant or "default", "workspace": workspace or "default"},
        ).inc(warmed_count)

        logger.info(
            f"Semantic cache warming completed: {warmed_count} entries warmed "
            f"({semantic_count} semantic matches) for operation '{operation}'"
        )

        return stats

    async def warm_from_logs(
        self,
        operation: str,
        log_entries: list[dict[str, Any]],
        data_fetcher: Callable[[dict[str, Any]], Any],
        tenant: str = "",
        workspace: str = "",
        min_frequency: int = 2,
    ) -> dict[str, Any]:
        """Warm cache from historical log entries, focusing on frequently accessed patterns.

        Args:
            operation: Cache operation name
            log_entries: List of historical query logs with input patterns
            data_fetcher: Function to fetch data for patterns
            tenant: Tenant identifier
            workspace: Workspace identifier
            min_frequency: Minimum frequency to consider for warming

        Returns:
            Warming statistics
        """
        # Count frequency of each pattern
        pattern_counts = {}
        for entry in log_entries:
            pattern = entry.get("inputs", {})
            pattern_key = str(sorted(pattern.items()))
            pattern_counts[pattern_key] = pattern_counts.get(pattern_key, 0) + 1

        # Filter to frequently accessed patterns
        frequent_patterns = [eval(k) for k, count in pattern_counts.items() if count >= min_frequency][
            : self.max_warm_keys
        ]

        logger.info(f"Found {len(frequent_patterns)} frequent patterns for warming (min_frequency={min_frequency})")

        return await self.warm_from_patterns(operation, frequent_patterns, data_fetcher, tenant, workspace)

    async def warm_related_queries(
        self,
        operation: str,
        seed_queries: list[dict[str, Any]],
        query_generator: Callable[[dict[str, Any]], list[dict[str, Any]]],
        data_fetcher: Callable[[dict[str, Any]], Any],
        tenant: str = "",
        workspace: str = "",
    ) -> dict[str, Any]:
        """Warm cache with related queries generated from seed queries.

        Args:
            operation: Cache operation name
            seed_queries: Initial queries to generate related ones from
            query_generator: Function to generate related queries from a seed
            data_fetcher: Function to fetch data for queries
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            Warming statistics
        """
        all_queries = []
        for seed in seed_queries:
            all_queries.append(seed)
            try:
                related = query_generator(seed)
                all_queries.extend(related)
            except Exception as e:
                logger.warning(f"Failed to generate related queries for {seed}: {e}")

        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for query in all_queries:
            query_key = str(sorted(query.items()))
            if query_key not in seen:
                seen.add(query_key)
                unique_queries.append(query)

        logger.info(f"Generated {len(unique_queries)} unique queries from {len(seed_queries)} seeds")

        return await self.warm_from_patterns(
            operation, unique_queries[: self.max_warm_keys], data_fetcher, tenant, workspace
        )

    def get_warming_stats(self) -> dict[str, Any]:
        """Get comprehensive warming statistics."""
        return {
            **self._warming_stats,
            "cache_stats": self.cache.get_stats(),
            "semantic_cache_stats": self.semantic_cache.get_stats(),
        }

    async def optimize_warming_patterns(
        self,
        operation: str,
        historical_queries: list[dict[str, Any]],
        tenant: str = "",
        workspace: str = "",
    ) -> list[dict[str, Any]]:
        """Analyze historical queries to identify optimal warming patterns.

        Args:
            operation: Cache operation name
            historical_queries: List of historical query inputs
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            List of optimized warming patterns
        """
        if not historical_queries:
            return []

        # Group similar queries using semantic similarity
        pattern_groups = []
        processed = set()

        for i, query in enumerate(historical_queries):
            if i in processed:
                continue

            group = [query]
            processed.add(i)

            # Find semantically similar queries
            for j, other_query in enumerate(historical_queries):
                if j in processed or j == i:
                    continue

                try:
                    similarity = await self.semantic_cache.calculate_similarity(
                        operation, query, other_query, tenant, workspace
                    )
                    if similarity >= self.similarity_threshold:
                        group.append(other_query)
                        processed.add(j)
                except Exception as e:
                    logger.debug(f"Similarity calculation failed for queries {i},{j}: {e}")

            if len(group) > 1:  # Only keep groups with multiple queries
                pattern_groups.append(group)

        # Select representative patterns from each group
        optimized_patterns = []
        for group in pattern_groups[: self.max_warm_keys // 2]:  # Limit total patterns
            # Use the most common pattern in the group as representative
            pattern_counts = {}
            for pattern in group:
                key = str(sorted(pattern.items()))
                pattern_counts[key] = pattern_counts.get(key, 0) + 1

            most_common_key = max(pattern_counts.keys(), key=lambda k: pattern_counts[k])
            optimized_patterns.append(eval(most_common_key))

        logger.info(
            f"Optimized {len(historical_queries)} historical queries into {len(optimized_patterns)} warming patterns"
        )

        return optimized_patterns


class ToolCacheWarmer:
    """Cache warmer specifically designed for tool result caching with semantic support."""

    def __init__(self, semantic_cache: SemanticCacheService):
        """Initialize tool cache warmer.

        Args:
            semantic_cache: Semantic cache service instance
        """
        self.semantic_warmer = SemanticCacheWarmer(semantic_cache)
        self._tool_patterns = {}  # tool_name -> list of common input patterns

    def register_tool_patterns(self, tool_name: str, patterns: list[dict[str, Any]]) -> None:
        """Register common input patterns for a specific tool.

        Args:
            tool_name: Name of the tool
            patterns: List of common input patterns for this tool
        """
        self._tool_patterns[tool_name] = patterns
        logger.info(f"Registered {len(patterns)} patterns for tool '{tool_name}'")

    async def warm_tool_cache(
        self,
        tool_name: str,
        data_fetcher: Callable[[dict[str, Any]], Any],
        tenant: str = "",
        workspace: str = "",
        use_registered_patterns: bool = True,
    ) -> dict[str, Any]:
        """Warm cache for a specific tool using registered patterns or semantic analysis.

        Args:
            tool_name: Name of the tool to warm
            data_fetcher: Function to fetch tool results
            tenant: Tenant identifier
            workspace: Workspace identifier
            use_registered_patterns: Whether to use pre-registered patterns

        Returns:
            Warming statistics
        """
        patterns = []
        if use_registered_patterns and tool_name in self._tool_patterns:
            patterns = self._tool_patterns[tool_name]
            logger.info(f"Using {len(patterns)} registered patterns for tool '{tool_name}'")
        else:
            # Generate basic patterns if none registered
            patterns = self._generate_default_patterns(tool_name)
            logger.info(f"Using {len(patterns)} default patterns for tool '{tool_name}'")

        return await self.semantic_warmer.warm_from_patterns(tool_name, patterns, data_fetcher, tenant, workspace)

    def _generate_default_patterns(self, tool_name: str) -> list[dict[str, Any]]:
        """Generate default warming patterns for tools without registered patterns."""
        # This could be enhanced with tool-specific pattern generation
        # For now, return empty list - tools should register their own patterns
        return []

    def get_tool_warming_stats(self) -> dict[str, Any]:
        """Get warming statistics for all tools."""
        return {
            "registered_tools": list(self._tool_patterns.keys()),
            "warming_stats": self.semantic_warmer.get_warming_stats(),
        }


# Global instances
_semantic_warmer: SemanticCacheWarmer | None = None
_tool_warmer: ToolCacheWarmer | None = None


def get_semantic_cache_warmer() -> SemanticCacheWarmer:
    """Get global semantic cache warmer instance."""
    global _semantic_warmer
    if _semantic_warmer is None:
        from platform.cache.semantic_cache_service import get_semantic_cache

        semantic_cache = get_semantic_cache()
        _semantic_warmer = SemanticCacheWarmer(semantic_cache)
    return _semantic_warmer


def get_tool_cache_warmer() -> ToolCacheWarmer:
    """Get global tool cache warmer instance."""
    global _tool_warmer
    if _tool_warmer is None:
        from platform.cache.semantic_cache_service import get_semantic_cache

        semantic_cache = get_semantic_cache()
        _tool_warmer = ToolCacheWarmer(semantic_cache)
    return _tool_warmer
