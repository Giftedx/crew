"""Unified Cache Tool - CrewAI tool for unified cache system

This tool provides CrewAI agents with access to the unified three-tier cache
system, enabling intelligent caching, optimization, and performance monitoring
across all cache layers.
"""
from __future__ import annotations
import logging
from typing import Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from ultimate_discord_intelligence_bot.cache import ENABLE_CACHE_V2, CacheNamespace, get_cache_namespace, get_unified_cache
from platform.core.step_result import StepResult
logger = logging.getLogger(__name__)

class CacheOperationInput(BaseModel):
    """Input schema for cache operations"""
    operation: str = Field(..., description='Operation: get, set, delete, get_metrics, optimize_ttl')
    key: str = Field(..., description='Cache key')
    value: Any | None = Field(default=None, description='Value to cache (for set operations)')
    ttl: int | None = Field(default=None, description='Time to live in seconds')
    cache_level: str = Field(default='auto', description='Cache level: auto, l1, l2, l3, all')
    tenant_id: str = Field(default='default', description='Tenant identifier')
    workspace_id: str = Field(default='main', description='Workspace identifier')
    metadata: dict[str, Any] | None = Field(default=None, description='Additional metadata')

class CacheOptimizationInput(BaseModel):
    """Input schema for cache optimization"""
    operation: str = Field(..., description='Operation: optimize_ttl, get_recommendations, get_metrics')
    key_pattern: str = Field(..., description='Cache key pattern to optimize')
    current_ttl: int | None = Field(default=None, description='Current TTL value')
    access_history: list[dict[str, Any]] | None = Field(default=None, description='Access history for optimization')
    tenant_id: str = Field(default='default', description='Tenant identifier')
    workspace_id: str = Field(default='main', description='Workspace identifier')

class UnifiedCacheTool(BaseTool):
    """Unified cache tool for CrewAI agents"""
    name: str = 'unified_cache_tool'
    description: str = 'Provides intelligent multi-tier caching with memory and Redis layers. Enables automatic cache operations and performance monitoring across all caching systems for maximum efficiency and cost optimization.'
    args_schema: type[BaseModel] = CacheOperationInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cache = get_unified_cache()
        logger.info('Unified cache tool initialized with UnifiedCache facade')

    def _run(self, operation: str, key: str, value: Any | None=None, ttl: int | None=None, cache_level: str='auto', tenant_id: str='default', workspace_id: str='main', metadata: dict[str, Any] | None=None) -> StepResult:
        """Execute cache operation"""
        try:
            namespace = get_cache_namespace(tenant_id, workspace_id)
            cache_name = metadata.get('cache_name', 'default') if metadata else 'default'
            if operation == 'get':
                return self._get_cache_value(namespace, cache_name, key)
            elif operation == 'set':
                if value is None:
                    return StepResult.fail('Value is required for set operation')
                return self._set_cache_value(namespace, cache_name, key, value, metadata)
            elif operation == 'delete':
                return StepResult.fail('Delete operation not yet implemented in UnifiedCache facade')
            elif operation == 'get_metrics':
                return StepResult.ok(data={'message': 'Metrics available via obs.metrics module'})
            else:
                return StepResult.fail(f'Unknown operation: {operation}')
        except Exception as e:
            logger.error(f'Error in unified cache tool: {e}', exc_info=True)
            return StepResult.fail(f'Cache operation failed: {e!s}', error_context={'exception': str(e)})

    def _get_cache_value(self, namespace: CacheNamespace, cache_name: str, key: str) -> StepResult:
        """Get value from cache"""
        try:
            import asyncio
            result = asyncio.run(self._cache.get(namespace, cache_name, key))
            if not result.success:
                return result
            return StepResult.ok(data={'hit': result.data.get('hit', False), 'value': result.data.get('value')})
        except Exception as e:
            return StepResult.fail(f'Cache get failed: {e!s}')

    def _set_cache_value(self, namespace: CacheNamespace, cache_name: str, key: str, value: Any, metadata: dict[str, Any] | None) -> StepResult:
        """Set value in cache"""
        try:
            import asyncio
            dependencies = None
            if metadata and 'dependencies' in metadata:
                dependencies = set(metadata['dependencies'])
            result = asyncio.run(self._cache.set(namespace, cache_name, key, value, dependencies))
            return result
        except Exception as e:
            return StepResult.fail(f'Cache set failed: {e!s}')

class CacheOptimizationTool(BaseTool):
    """Cache optimization tool for CrewAI agents"""
    name: str = 'cache_optimization_tool'
    description: str = 'Provides cache optimization recommendations. Note: RL-based TTL optimization has been deprecated in favor of unified cache strategies.'
    args_schema: type[BaseModel] = CacheOptimizationInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info('Cache optimization tool initialized (legacy compatibility mode)')

    def _run(self, operation: str, key_pattern: str, current_ttl: int | None=None, access_history: list[dict[str, Any]] | None=None, tenant_id: str='default', workspace_id: str='main') -> StepResult:
        """Execute cache optimization operation"""
        try:
            if operation == 'get_recommendations':
                return StepResult.ok(data={'message': 'Cache optimization is now handled by unified cache layer', 'recommendation': 'Use ENABLE_CACHE_V2 flag for enhanced caching'})
            elif operation == 'get_metrics':
                return StepResult.ok(data={'message': 'Metrics available via obs.metrics module'})
            else:
                return StepResult.fail(f'Operation {operation} deprecated. Use unified cache instead.')
        except Exception as e:
            logger.error(f'Error in cache optimization tool: {e}', exc_info=True)
            return StepResult.fail(f'Cache optimization failed: {e!s}', error_context={'exception': str(e)})

class CacheStatusTool(BaseTool):
    """Cache status tool for CrewAI agents"""
    name: str = 'cache_status_tool'
    description: str = 'Provides status information about the unified cache system. Check ENABLE_CACHE_V2 flag status and cache availability.'
    args_schema: type[BaseModel] = BaseModel

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cache = get_unified_cache()
        logger.info('Cache status tool initialized')

    def _run(self, tenant_id: str='default', workspace_id: str='main') -> StepResult:
        """Get cache system status"""
        try:
            status_info = {'cache_v2_enabled': ENABLE_CACHE_V2, 'unified_cache_available': self._cache is not None, 'message': 'Unified cache facade operational. Metrics available via obs.metrics.'}
            return StepResult.ok(data=status_info)
        except Exception as e:
            logger.error(f'Error in cache status tool: {e}', exc_info=True)
            return StepResult.fail(f'Cache status retrieval failed: {e!s}', error_context={'exception': str(e)})