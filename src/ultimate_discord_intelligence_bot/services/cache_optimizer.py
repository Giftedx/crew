"""Cache optimization service.

This module provides comprehensive cache optimization strategies and management
for improving system performance through intelligent caching mechanisms.
"""
from __future__ import annotations
import logging
import time
from typing import TYPE_CHECKING, Any
from platform.core.step_result import StepResult
if TYPE_CHECKING:
    from ..tenancy.context import TenantContext
logger = logging.getLogger(__name__)

class CacheOptimizer:
    """Cache optimization service for performance improvement."""

    def __init__(self, tenant_context: TenantContext):
        """Initialize cache optimizer with tenant context.

        Args:
            tenant_context: Tenant context for data isolation
        """
        self.tenant_context = tenant_context
        self.cache_stats: dict[str, Any] = {}
        self.optimization_rules: list[dict[str, Any]] = []
        self._initialize_optimization_rules()

    def _initialize_optimization_rules(self) -> None:
        """Initialize cache optimization rules."""
        self.optimization_rules = [{'name': 'frequent_access_boost', 'description': 'Boost cache priority for frequently accessed items', 'enabled': True, 'threshold': 5, 'boost_factor': 1.5}, {'name': 'size_based_eviction', 'description': 'Evict large items when cache is full', 'enabled': True, 'size_threshold': 1024 * 1024, 'priority': 'low'}, {'name': 'time_based_eviction', 'description': 'Evict items based on access time', 'enabled': True, 'max_age_seconds': 3600, 'priority': 'medium'}, {'name': 'pattern_based_prefetch', 'description': 'Prefetch items based on access patterns', 'enabled': True, 'pattern_window': 100, 'prefetch_count': 5}]

    def optimize_cache(self, cache_data: dict[str, Any], optimization_strategy: str='balanced') -> StepResult:
        """Optimize cache based on strategy.

        Args:
            cache_data: Current cache data
            optimization_strategy: Optimization strategy (aggressive, balanced, conservative)

        Returns:
            StepResult with optimization results
        """
        try:
            optimization_results = {'strategy': optimization_strategy, 'original_size': len(cache_data), 'optimizations_applied': [], 'performance_metrics': {}}
            if optimization_strategy == 'aggressive':
                optimized_data = self._apply_aggressive_optimization(cache_data)
            elif optimization_strategy == 'conservative':
                optimized_data = self._apply_conservative_optimization(cache_data)
            else:
                optimized_data = self._apply_balanced_optimization(cache_data)
            original_size = len(cache_data)
            optimized_size = len(optimized_data)
            size_reduction = original_size - optimized_size
            reduction_percentage = size_reduction / original_size * 100 if original_size > 0 else 0
            optimization_results['optimized_size'] = optimized_size
            optimization_results['size_reduction'] = size_reduction
            optimization_results['reduction_percentage'] = reduction_percentage
            optimization_results['performance_metrics'] = self._calculate_performance_metrics(cache_data, optimized_data)
            return StepResult.ok(data={'optimized_cache': optimized_data, 'optimization_results': optimization_results, 'tenant': self.tenant_context.tenant, 'workspace': self.tenant_context.workspace})
        except Exception as e:
            logger.error(f'Cache optimization failed: {e}')
            return StepResult.fail(f'Cache optimization failed: {e!s}')

    def _apply_aggressive_optimization(self, cache_data: dict[str, Any]) -> dict[str, Any]:
        """Apply aggressive cache optimization.

        Args:
            cache_data: Cache data to optimize

        Returns:
            Aggressively optimized cache data
        """
        optimized = {}
        optimizations_applied = []
        for key, value in cache_data.items():
            if self._should_keep_item_aggressive(key, value, cache_data):
                optimized[key] = self._optimize_item_value(value)
            else:
                optimizations_applied.append(f'Removed {key} (aggressive eviction)')
        return optimized

    def _apply_balanced_optimization(self, cache_data: dict[str, Any]) -> dict[str, Any]:
        """Apply balanced cache optimization.

        Args:
            cache_data: Cache data to optimize

        Returns:
            Balanced optimized cache data
        """
        optimized = {}
        optimizations_applied = []
        for key, value in cache_data.items():
            if self._should_keep_item_balanced(key, value, cache_data):
                optimized[key] = self._optimize_item_value(value)
            else:
                optimizations_applied.append(f'Removed {key} (balanced eviction)')
        return optimized

    def _apply_conservative_optimization(self, cache_data: dict[str, Any]) -> dict[str, Any]:
        """Apply conservative cache optimization.

        Args:
            cache_data: Cache data to optimize

        Returns:
            Conservatively optimized cache data
        """
        optimized = {}
        optimizations_applied = []
        for key, value in cache_data.items():
            if self._should_keep_item_conservative(key, value, cache_data):
                optimized[key] = self._optimize_item_value(value)
            else:
                optimizations_applied.append(f'Removed {key} (conservative eviction)')
        return optimized

    def _should_keep_item_aggressive(self, key: str, value: Any, cache_data: dict[str, Any]) -> bool:
        """Check if item should be kept with aggressive optimization.

        Args:
            key: Cache key
            value: Cache value
            cache_data: Full cache data

        Returns:
            True if item should be kept
        """
        if not self._is_frequently_accessed(key, value):
            return False
        if self._is_large_item(value):
            return False
        return not self._is_old_item(value)

    def _should_keep_item_balanced(self, key: str, value: Any, cache_data: dict[str, Any]) -> bool:
        """Check if item should be kept with balanced optimization.

        Args:
            key: Cache key
            value: Cache value
            cache_data: Full cache data

        Returns:
            True if item should be kept
        """
        score = 0
        if self._is_frequently_accessed(key, value):
            score += 2
        if not self._is_large_item(value):
            score += 1
        if not self._is_old_item(value):
            score += 1
        return score >= 2

    def _should_keep_item_conservative(self, key: str, value: Any, cache_data: dict[str, Any]) -> bool:
        """Check if item should be kept with conservative optimization.

        Args:
            key: Cache key
            value: Cache value
            cache_data: Full cache data

        Returns:
            True if item should be kept
        """
        if self._is_very_old_item(value):
            return False
        return not self._is_very_large_item(value)

    def _is_frequently_accessed(self, key: str, value: Any) -> bool:
        """Check if item is frequently accessed.

        Args:
            key: Cache key
            value: Cache value

        Returns:
            True if frequently accessed
        """
        if isinstance(value, dict) and 'access_count' in value:
            return value['access_count'] >= 5
        return True

    def _is_large_item(self, value: Any) -> bool:
        """Check if item is large.

        Args:
            value: Cache value

        Returns:
            True if item is large
        """
        try:
            import sys
            size = sys.getsizeof(value)
            return size > 1024 * 1024
        except Exception:
            return False

    def _is_very_large_item(self, value: Any) -> bool:
        """Check if item is very large.

        Args:
            value: Cache value

        Returns:
            True if item is very large
        """
        try:
            import sys
            size = sys.getsizeof(value)
            return size > 10 * 1024 * 1024
        except Exception:
            return False

    def _is_old_item(self, value: Any) -> bool:
        """Check if item is old.

        Args:
            value: Cache value

        Returns:
            True if item is old
        """
        if isinstance(value, dict) and 'created_at' in value:
            try:
                created_time = float(value['created_at'])
                current_time = time.time()
                return current_time - created_time > 3600
            except Exception:
                pass
        return False

    def _is_very_old_item(self, value: Any) -> bool:
        """Check if item is very old.

        Args:
            value: Cache value

        Returns:
            True if item is very old
        """
        if isinstance(value, dict) and 'created_at' in value:
            try:
                created_time = float(value['created_at'])
                current_time = time.time()
                return current_time - created_time > 86400
            except Exception:
                pass
        return False

    def _optimize_item_value(self, value: Any) -> Any:
        """Optimize individual cache item value.

        Args:
            value: Cache value to optimize

        Returns:
            Optimized value
        """
        if isinstance(value, dict):
            optimized = value.copy()
            unnecessary_keys = ['debug_info', 'temp_data', 'internal_notes']
            for key in unnecessary_keys:
                optimized.pop(key, None)
            if 'content' in optimized and isinstance(optimized['content'], str) and (len(optimized['content']) > 10000):
                optimized['content'] = optimized['content'][:10000] + '... [truncated]'
                optimized['content_truncated'] = True
            return optimized
        return value

    def _calculate_performance_metrics(self, original_data: dict[str, Any], optimized_data: dict[str, Any]) -> dict[str, Any]:
        """Calculate performance metrics for optimization.

        Args:
            original_data: Original cache data
            optimized_data: Optimized cache data

        Returns:
            Performance metrics
        """
        try:
            import sys
            original_size = sys.getsizeof(original_data)
            optimized_size = sys.getsizeof(optimized_data)
            return {'original_memory_bytes': original_size, 'optimized_memory_bytes': optimized_size, 'memory_saved_bytes': original_size - optimized_size, 'memory_saved_percentage': (original_size - optimized_size) / original_size * 100 if original_size > 0 else 0, 'item_count_reduction': len(original_data) - len(optimized_data), 'compression_ratio': optimized_size / original_size if original_size > 0 else 1.0}
        except Exception as e:
            logger.warning(f'Could not calculate performance metrics: {e}')
            return {'original_memory_bytes': 0, 'optimized_memory_bytes': 0, 'memory_saved_bytes': 0, 'memory_saved_percentage': 0, 'item_count_reduction': len(original_data) - len(optimized_data), 'compression_ratio': 1.0}

    def get_cache_statistics(self) -> StepResult:
        """Get cache statistics and metrics.

        Returns:
            StepResult with cache statistics
        """
        try:
            stats = {'optimization_rules': self.optimization_rules, 'cache_stats': self.cache_stats, 'tenant': self.tenant_context.tenant, 'workspace': self.tenant_context.workspace, 'timestamp': time.time()}
            return StepResult.ok(data=stats)
        except Exception as e:
            logger.error(f'Failed to get cache statistics: {e}')
            return StepResult.fail(f'Cache statistics retrieval failed: {e!s}')

    def update_optimization_rules(self, rules: list[dict[str, Any]]) -> StepResult:
        """Update cache optimization rules.

        Args:
            rules: New optimization rules

        Returns:
            StepResult with update result
        """
        try:
            self.optimization_rules = rules
            return StepResult.ok(data={'updated_rules': rules, 'rule_count': len(rules), 'tenant': self.tenant_context.tenant, 'workspace': self.tenant_context.workspace})
        except Exception as e:
            logger.error(f'Failed to update optimization rules: {e}')
            return StepResult.fail(f'Optimization rules update failed: {e!s}')

class CacheOptimizationManager:
    """Manager for cache optimization across tenants."""

    def __init__(self):
        """Initialize cache optimization manager."""
        self.optimizers: dict[str, CacheOptimizer] = {}

    def get_optimizer(self, tenant_context: TenantContext) -> CacheOptimizer:
        """Get or create cache optimizer for tenant.

        Args:
            tenant_context: Tenant context

        Returns:
            Cache optimizer for the tenant
        """
        key = f'{tenant_context.tenant}:{tenant_context.workspace}'
        if key not in self.optimizers:
            self.optimizers[key] = CacheOptimizer(tenant_context)
        return self.optimizers[key]

    def optimize_tenant_cache(self, tenant_context: TenantContext, cache_data: dict[str, Any], optimization_strategy: str='balanced') -> StepResult:
        """Optimize cache for tenant.

        Args:
            tenant_context: Tenant context
            cache_data: Cache data to optimize
            optimization_strategy: Optimization strategy

        Returns:
            StepResult with optimization results
        """
        optimizer = self.get_optimizer(tenant_context)
        return optimizer.optimize_cache(cache_data, optimization_strategy)
_cache_optimization_manager = CacheOptimizationManager()

def get_cache_optimizer(tenant_context: TenantContext) -> CacheOptimizer:
    """Get cache optimizer for tenant.

    Args:
        tenant_context: Tenant context

    Returns:
        Cache optimizer for the tenant
    """
    return _cache_optimization_manager.get_optimizer(tenant_context)

def optimize_cache(tenant_context: TenantContext, cache_data: dict[str, Any], optimization_strategy: str='balanced') -> StepResult:
    """Optimize cache for tenant.

    Args:
        tenant_context: Tenant context
        cache_data: Cache data to optimize
        optimization_strategy: Optimization strategy

    Returns:
        StepResult with optimization results
    """
    return _cache_optimization_manager.optimize_tenant_cache(tenant_context, cache_data, optimization_strategy)