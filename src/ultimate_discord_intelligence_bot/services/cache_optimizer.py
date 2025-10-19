#!/usr/bin/env python3
"""
Cache Optimization Service.

This service implements intelligent caching strategies to maximize cache hit rates,
reduce latency, and optimize memory usage across the platform.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Tuple

from ..step_result import StepResult


class CacheOptimizer:
    """Intelligent cache optimization service."""

    def __init__(self):
        """Initialize the cache optimizer."""
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "compressions": 0,
            "total_requests": 0,
        }
        self.cache_policies = {
            "ttl_strategies": {
                "frequent": 3600,  # 1 hour for frequently accessed data
                "moderate": 1800,  # 30 minutes for moderate access
                "rare": 300,  # 5 minutes for rarely accessed data
            },
            "compression_threshold": 1024,  # Compress data larger than 1KB
            "eviction_policy": "lru",  # Least Recently Used
            "max_cache_size": 1000,  # Maximum number of cache entries
        }

    def generate_cache_key(
        self,
        operation: str,
        params: Dict[str, Any],
        tenant: str,
        workspace: str,
    ) -> str:
        """
        Generate an optimized cache key.

        Args:
            operation: The operation being performed
            params: Parameters for the operation
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            A unique cache key
        """
        # Create a normalized representation of the parameters
        normalized_params = self._normalize_params(params)

        # Create a hash of the operation and parameters
        key_data = {
            "operation": operation,
            "params": normalized_params,
            "tenant": tenant,
            "workspace": workspace,
        }

        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()

        return f"cache:{operation}:{key_hash[:16]}"

    def _normalize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize parameters for consistent cache key generation.

        Args:
            params: Raw parameters

        Returns:
            Normalized parameters
        """
        normalized = {}

        for key, value in params.items():
            if isinstance(value, (str, int, float, bool)):
                normalized[key] = value
            elif isinstance(value, (list, tuple)):
                # Sort lists for consistent ordering
                normalized[key] = sorted(value) if value else []
            elif isinstance(value, dict):
                # Recursively normalize nested dictionaries
                normalized[key] = self._normalize_params(value)
            else:
                # Convert other types to string representation
                normalized[key] = str(value)

        return normalized

    def determine_cache_strategy(
        self,
        operation: str,
        data_size: int,
        access_frequency: str = "moderate",
    ) -> Dict[str, Any]:
        """
        Determine the optimal caching strategy for an operation.

        Args:
            operation: The operation being performed
            data_size: Size of the data to be cached
            access_frequency: Expected access frequency

        Returns:
            Cache strategy configuration
        """
        strategy = {
            "ttl": self.cache_policies["ttl_strategies"].get(access_frequency, 1800),
            "compress": data_size > self.cache_policies["compression_threshold"],
            "priority": self._calculate_priority(
                operation, data_size, access_frequency
            ),
            "eviction_policy": self.cache_policies["eviction_policy"],
        }

        return strategy

    def _calculate_priority(
        self,
        operation: str,
        data_size: int,
        access_frequency: str,
    ) -> int:
        """
        Calculate cache priority based on operation characteristics.

        Args:
            operation: The operation being performed
            data_size: Size of the data
            access_frequency: Expected access frequency

        Returns:
            Priority score (higher = more important)
        """
        # Base priority from access frequency
        frequency_scores = {"frequent": 100, "moderate": 50, "rare": 10}
        priority = frequency_scores.get(access_frequency, 50)

        # Adjust for operation type
        operation_weights = {
            "content_analysis": 80,
            "fact_checking": 90,
            "debate_scoring": 85,
            "memory_retrieval": 70,
            "oauth_token": 95,
            "user_preferences": 60,
        }
        priority += operation_weights.get(operation, 50)

        # Adjust for data size (smaller data gets higher priority)
        if data_size < 1024:  # Less than 1KB
            priority += 20
        elif data_size > 10240:  # More than 10KB
            priority -= 10

        return max(0, min(100, priority))

    def optimize_cache_entry(
        self,
        key: str,
        data: Any,
        strategy: Dict[str, Any],
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Optimize a cache entry based on the determined strategy.

        Args:
            key: Cache key
            data: Data to be cached
            strategy: Caching strategy

        Returns:
            Optimized data and metadata
        """
        optimized_data = data
        metadata = {
            "created_at": time.time(),
            "ttl": strategy["ttl"],
            "priority": strategy["priority"],
            "compressed": False,
            "size": len(str(data)),
        }

        # Apply compression if needed
        if strategy["compress"]:
            optimized_data, compression_ratio = self._compress_data(data)
            metadata["compressed"] = True
            metadata["compression_ratio"] = compression_ratio
            metadata["original_size"] = len(str(data))
            metadata["compressed_size"] = len(str(optimized_data))
            self.cache_stats["compressions"] += 1

        return optimized_data, metadata

    def _compress_data(self, data: Any) -> Tuple[Any, float]:
        """
        Compress data for efficient storage.

        Args:
            data: Data to compress

        Returns:
            Compressed data and compression ratio
        """
        # Simple compression simulation
        # In production, use actual compression libraries like gzip or lz4
        original_size = len(str(data))

        # Simulate compression (in real implementation, use actual compression)
        compressed_data = data  # Placeholder for actual compression
        compressed_size = original_size * 0.7  # Simulate 30% compression

        compression_ratio = (
            compressed_size / original_size if original_size > 0 else 1.0
        )

        return compressed_data, compression_ratio

    def should_cache(
        self,
        operation: str,
        data_size: int,
        access_frequency: str,
    ) -> bool:
        """
        Determine if data should be cached based on optimization criteria.

        Args:
            operation: The operation being performed
            data_size: Size of the data
            access_frequency: Expected access frequency

        Returns:
            True if data should be cached
        """
        # Don't cache very small data (overhead not worth it)
        if data_size < 100:
            return False

        # Don't cache very large data (memory constraints)
        if data_size > 1024 * 1024:  # 1MB
            return False

        # Always cache high-frequency operations
        if access_frequency == "frequent":
            return True

        # Cache moderate operations if they're not too large
        if access_frequency == "moderate" and data_size < 10000:
            return True

        # Only cache rare operations if they're small
        if access_frequency == "rare" and data_size < 1000:
            return True

        return False

    def get_cache_analytics(self) -> Dict[str, Any]:
        """
        Get cache performance analytics.

        Returns:
            Cache analytics data
        """
        total_requests = self.cache_stats["total_requests"]
        hit_rate = (
            self.cache_stats["hits"] / total_requests if total_requests > 0 else 0.0
        )

        return {
            "hit_rate": hit_rate,
            "miss_rate": 1.0 - hit_rate,
            "total_requests": total_requests,
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "evictions": self.cache_stats["evictions"],
            "compressions": self.cache_stats["compressions"],
            "compression_savings": self._calculate_compression_savings(),
        }

    def _calculate_compression_savings(self) -> float:
        """
        Calculate total compression savings.

        Returns:
            Compression savings ratio
        """
        # Simulate compression savings calculation
        # In production, track actual compression ratios
        return 0.3  # 30% average compression

    def optimize_cache_policies(self) -> StepResult:
        """
        Optimize cache policies based on current performance.

        Returns:
            StepResult with optimization results
        """
        try:
            analytics = self.get_cache_analytics()

            # Adjust TTL strategies based on hit rates
            if analytics["hit_rate"] < 0.6:  # Low hit rate
                # Increase TTL for better hit rates
                self.cache_policies["ttl_strategies"]["frequent"] = 7200  # 2 hours
                self.cache_policies["ttl_strategies"]["moderate"] = 3600  # 1 hour
            elif analytics["hit_rate"] > 0.9:  # High hit rate
                # Decrease TTL to reduce memory usage
                self.cache_policies["ttl_strategies"]["frequent"] = 1800  # 30 minutes
                self.cache_policies["ttl_strategies"]["moderate"] = 900  # 15 minutes

            # Adjust compression threshold based on compression savings
            if analytics["compression_savings"] > 0.4:  # Good compression
                self.cache_policies["compression_threshold"] = 512  # Lower threshold
            elif analytics["compression_savings"] < 0.2:  # Poor compression
                self.cache_policies["compression_threshold"] = 2048  # Higher threshold

            return StepResult.ok(
                data={
                    "optimization_applied": True,
                    "new_policies": self.cache_policies,
                    "analytics": analytics,
                }
            )

        except Exception as e:
            return StepResult.fail(f"Cache optimization failed: {str(e)}")

    def record_cache_operation(
        self,
        operation: str,
        hit: bool,
        data_size: int,
    ) -> None:
        """
        Record a cache operation for analytics.

        Args:
            operation: The operation performed
            hit: Whether it was a cache hit
            data_size: Size of the data
        """
        self.cache_stats["total_requests"] += 1

        if hit:
            self.cache_stats["hits"] += 1
        else:
            self.cache_stats["misses"] += 1

    def get_optimization_recommendations(self) -> List[str]:
        """
        Get cache optimization recommendations.

        Returns:
            List of optimization recommendations
        """
        recommendations = []
        analytics = self.get_cache_analytics()

        if analytics["hit_rate"] < 0.6:
            recommendations.append("Consider increasing cache TTL for better hit rates")

        if analytics["compression_savings"] < 0.2:
            recommendations.append(
                "Consider adjusting compression threshold for better efficiency"
            )

        if analytics["evictions"] > analytics["hits"] * 0.1:
            recommendations.append("Consider increasing cache size to reduce evictions")

        if not recommendations:
            recommendations.append("Cache performance is optimal")

        return recommendations
