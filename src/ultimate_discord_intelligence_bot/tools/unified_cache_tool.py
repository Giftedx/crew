"""Unified Cache Tool - CrewAI tool for unified cache system

This tool provides CrewAI agents with access to the unified three-tier cache
system, enabling intelligent caching, optimization, and performance monitoring
across all cache layers.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Type

from crewai.tools import BaseTool  # type: ignore
from pydantic import BaseModel, Field

from ultimate_discord_intelligence_bot.cache import (
    ENABLE_CACHE_V2,
    CacheNamespace,
    get_cache_namespace,
    get_unified_cache,
)
from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)


class CacheOperationInput(BaseModel):
    """Input schema for cache operations"""

    operation: str = Field(
        ..., description="Operation: get, set, delete, get_metrics, optimize_ttl"
    )
    key: str = Field(..., description="Cache key")
    value: Optional[Any] = Field(
        default=None, description="Value to cache (for set operations)"
    )
    ttl: Optional[int] = Field(default=None, description="Time to live in seconds")
    cache_level: str = Field(
        default="auto", description="Cache level: auto, l1, l2, l3, all"
    )
    tenant_id: str = Field(default="default", description="Tenant identifier")
    workspace_id: str = Field(default="main", description="Workspace identifier")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )


class CacheOptimizationInput(BaseModel):
    """Input schema for cache optimization"""

    operation: str = Field(
        ..., description="Operation: optimize_ttl, get_recommendations, get_metrics"
    )
    key_pattern: str = Field(..., description="Cache key pattern to optimize")
    current_ttl: Optional[int] = Field(default=None, description="Current TTL value")
    access_history: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Access history for optimization"
    )
    tenant_id: str = Field(default="default", description="Tenant identifier")
    workspace_id: str = Field(default="main", description="Workspace identifier")


class UnifiedCacheTool(BaseTool):
    """Unified cache tool for CrewAI agents"""

    name: str = "unified_cache_tool"
    description: str = (
        "Provides intelligent multi-tier caching with memory and Redis layers. "
        "Enables automatic cache operations and performance monitoring across all "
        "caching systems for maximum efficiency and cost optimization."
    )
    args_schema: Type[BaseModel] = CacheOperationInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cache = get_unified_cache()
        logger.info("Unified cache tool initialized with UnifiedCache facade")

    def _run(
        self,
        operation: str,
        key: str,
        value: Optional[Any] = None,
        ttl: Optional[int] = None,
        cache_level: str = "auto",
        tenant_id: str = "default",
        workspace_id: str = "main",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Execute cache operation"""
        try:
            namespace = get_cache_namespace(tenant_id, workspace_id)
            cache_name = (
                metadata.get("cache_name", "default") if metadata else "default"
            )

            if operation == "get":
                return self._get_cache_value(namespace, cache_name, key).to_json()

            elif operation == "set":
                if value is None:
                    return StepResult.fail(
                        "Value is required for set operation"
                    ).to_json()

                return self._set_cache_value(
                    namespace, cache_name, key, value, metadata
                ).to_json()

            elif operation == "delete":
                return StepResult.fail(
                    "Delete operation not yet implemented in UnifiedCache facade"
                ).to_json()

            elif operation == "get_metrics":
                return StepResult.ok(
                    data={"message": "Metrics available via obs.metrics module"}
                ).to_json()

            else:
                return StepResult.fail(f"Unknown operation: {operation}").to_json()

        except Exception as e:
            logger.error(f"Error in unified cache tool: {e}", exc_info=True)
            return StepResult.fail(f"Cache operation failed: {str(e)}").to_json()

    def _get_cache_value(
        self, namespace: CacheNamespace, cache_name: str, key: str
    ) -> StepResult:
        """Get value from cache"""
        try:
            import asyncio

            result = asyncio.run(self._cache.get(namespace, cache_name, key))

            if not result.success:
                return result

            return StepResult.ok(
                data={
                    "hit": result.data.get("hit", False),
                    "value": result.data.get("value"),
                }
            )

        except Exception as e:
            return StepResult.fail(f"Cache get failed: {str(e)}")

    def _set_cache_value(
        self,
        namespace: CacheNamespace,
        cache_name: str,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]],
    ) -> StepResult:
        """Set value in cache"""
        try:
            import asyncio

            dependencies = None
            if metadata and "dependencies" in metadata:
                dependencies = set(metadata["dependencies"])

            result = asyncio.run(
                self._cache.set(namespace, cache_name, key, value, dependencies)
            )

            return result

        except Exception as e:
            return StepResult.fail(f"Cache set failed: {str(e)}")


class CacheOptimizationTool(BaseTool):
    """Cache optimization tool for CrewAI agents"""

    name: str = "cache_optimization_tool"
    description: str = (
        "Provides cache optimization recommendations. Note: RL-based TTL optimization "
        "has been deprecated in favor of unified cache strategies."
    )
    args_schema: Type[BaseModel] = CacheOptimizationInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info("Cache optimization tool initialized (legacy compatibility mode)")

    def _run(
        self,
        operation: str,
        key_pattern: str,
        current_ttl: Optional[int] = None,
        access_history: Optional[List[Dict[str, Any]]] = None,
        tenant_id: str = "default",
        workspace_id: str = "main",
    ) -> str:
        """Execute cache optimization operation"""
        try:
            if operation == "get_recommendations":
                return StepResult.ok(
                    data={
                        "message": "Cache optimization is now handled by unified cache layer",
                        "recommendation": "Use ENABLE_CACHE_V2 flag for enhanced caching",
                    }
                ).to_json()

            elif operation == "get_metrics":
                return StepResult.ok(
                    data={"message": "Metrics available via obs.metrics module"}
                ).to_json()

            else:
                return StepResult.fail(
                    f"Operation {operation} deprecated. Use unified cache instead."
                ).to_json()

        except Exception as e:
            logger.error(f"Error in cache optimization tool: {e}", exc_info=True)
            return StepResult.fail(f"Cache optimization failed: {str(e)}").to_json()


class CacheStatusTool(BaseTool):
    """Cache status tool for CrewAI agents"""

    name: str = "cache_status_tool"
    description: str = (
        "Provides status information about the unified cache system. "
        "Check ENABLE_CACHE_V2 flag status and cache availability."
    )
    args_schema: Type[BaseModel] = BaseModel

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cache = get_unified_cache()
        logger.info("Cache status tool initialized")

    def _run(
        self,
        tenant_id: str = "default",
        workspace_id: str = "main",
    ) -> str:
        """Get cache system status"""
        try:
            status_info = {
                "cache_v2_enabled": ENABLE_CACHE_V2,
                "unified_cache_available": self._cache is not None,
                "message": "Unified cache facade operational. Metrics available via obs.metrics.",
            }

            return StepResult.ok(data=status_info).to_json()

        except Exception as e:
            logger.error(f"Error in cache status tool: {e}", exc_info=True)
            return StepResult.fail(f"Cache status retrieval failed: {str(e)}").to_json()
