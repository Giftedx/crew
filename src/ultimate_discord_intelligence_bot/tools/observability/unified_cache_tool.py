"""Unified Cache Tool - CrewAI tool for unified cache system

This tool provides CrewAI agents with access to the unified three-tier cache
system, enabling intelligent caching, optimization, and performance monitoring
across all cache layers.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from pydantic import BaseModel, Field

from crewai.tools import BaseTool
from platform.cache.unified_cache import UnifiedCacheService, get_unified_cache_config
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics


logger = logging.getLogger(__name__)


class CacheOperationInput(BaseModel):
    """Input schema for cache operations"""

    operation: str = Field(..., description="Operation: get, set, delete, get_metrics")
    key: str = Field(..., description="Cache key")
    value: Any | None = Field(default=None, description="Value to cache (for set operations)")
    ttl: int | None = Field(default=None, description="Time to live in seconds")
    cache_level: str = Field(default="auto", description="Cache level: auto, l1, l2, l3, all")
    tenant_id: str = Field(default="default", description="Tenant identifier")
    workspace_id: str = Field(default="main", description="Workspace identifier")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")


class UnifiedCacheTool(BaseTool):
    """Unified cache tool for CrewAI agents"""

    name: str = "unified_cache_tool"
    description: str = "Provides intelligent multi-tier caching with memory and Redis layers. Enables automatic cache operations and performance monitoring across all caching systems for maximum efficiency and cost optimization."
    args_schema: type[BaseModel] = CacheOperationInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cache = UnifiedCacheService(use_new_config=True)
        logger.info("Unified cache tool initialized with UnifiedCacheService")

    def _run(
        self,
        operation: str,
        key: str,
        value: Any | None = None,
        ttl: int | None = None,
        cache_level: str = "auto",
        tenant_id: str = "default",
        workspace_id: str = "main",
        metadata: dict[str, Any] | None = None,
    ) -> StepResult:
        """Execute cache operation"""
        get_metrics().counter("tool_runs_total", labels={"tool": self.name}).inc()
        try:
            if operation == "get":
                return self._run_async(self._cache.get(key, tenant_id, workspace_id))
            elif operation == "set":
                if value is None:
                    return StepResult.fail("Value is required for set operation")
                return self._run_async(self._cache.set(key, value, ttl, cache_level, tenant_id, workspace_id, metadata))
            elif operation == "delete":
                return self._run_async(self._cache.delete(key, tenant_id, workspace_id))
            elif operation == "get_metrics":
                 metrics = self._cache.get_metrics(tenant_id, workspace_id)
                 return StepResult.ok(data=metrics)
            else:
                return StepResult.fail(f"Unknown operation: {operation}")
        except Exception as e:
            logger.error(f"Error in unified cache tool: {e}", exc_info=True)
            return StepResult.fail(f"Cache operation failed: {e!s}", error_context={"exception": str(e)})

    def _run_async(self, coroutine):
        """Helper to run async methods synchronously."""
        try:
            return asyncio.run(coroutine)
        except RuntimeError:
             # Handle case where event loop is already running
             loop = asyncio.get_event_loop()
             return loop.run_until_complete(coroutine)


class CacheOptimizationTool(BaseTool):
    """Cache optimization tool for CrewAI agents. Deprecated."""

    name: str = "cache_optimization_tool"
    description: str = "DEPRECATED. Use UnifiedCacheTool instead."
    args_schema: type[BaseModel] = BaseModel

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.warning("CacheOptimizationTool is deprecated.")

    def _run(self, **kwargs) -> StepResult:
        get_metrics().counter("tool_runs_total", labels={"tool": self.name}).inc()
        return StepResult.ok(
            data={
                "message": "Cache optimization is now handled automatically by UnifiedCacheService.",
                "recommendation": "Use UnifiedCacheTool for all cache operations.",
            }
        )


class CacheStatusTool(BaseTool):
    """Cache status tool for CrewAI agents"""

    name: str = "cache_status_tool"
    description: str = "Provides status information about the unified cache system."
    args_schema: type[BaseModel] = BaseModel

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cache = UnifiedCacheService(use_new_config=True)

    def _run(self, tenant_id: str = "default", workspace_id: str = "main") -> StepResult:
        get_metrics().counter("tool_runs_total", labels={"tool": self.name}).inc()
        try:
            metrics = self._cache.get_metrics(tenant_id, workspace_id)
            return StepResult.ok(
                data={
                    "status": "operational",
                    "metrics": metrics,
                    "config": str(self._cache.config)
                }
            )
        except Exception as e:
            return StepResult.fail(f"Cache status failed: {e}")

__all__ = ["UnifiedCacheTool", "CacheOptimizationTool", "CacheStatusTool"]
