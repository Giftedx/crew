"""Cache V2 Tool - CrewAI tool for unified cache facade

This tool provides CrewAI agents with access to the unified cache facade
(ENABLE_CACHE_V2), enabling tenant-aware caching operations through the
consolidated multi-level cache system.

See ADR-0001 for architectural decision rationale.
"""

from __future__ import annotations

import logging
from typing import Any

from crewai.tools import BaseTool  # type: ignore
from pydantic import BaseModel, Field

from ultimate_discord_intelligence_bot.cache import (
    ENABLE_CACHE_V2,
    UnifiedCache,
    get_cache_namespace,
    get_unified_cache,
)
from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)


class CacheV2OperationInput(BaseModel):
    """Input schema for cache V2 operations"""

    operation: str = Field(..., description="Operation: get, set, delete, get_stats")
    cache_name: str = Field(
        ..., description="Logical cache name (e.g., 'llm', 'analysis', 'transcription')"
    )
    key: str = Field(..., description="Cache key")
    value: Any = Field(default=None, description="Value to cache (for set operations)")
    dependencies: list[str] | None = Field(
        default=None, description="Optional dependency keys for invalidation tracking"
    )
    tenant: str = Field(default="default", description="Tenant identifier")
    workspace: str = Field(default="main", description="Workspace identifier")


class CacheV2Tool(BaseTool):
    """CrewAI tool for unified cache facade operations."""

    name: str = "cache_v2_tool"
    description: str = (
        "Unified cache operations using the ENABLE_CACHE_V2 facade. "
        "Provides tenant-aware caching with multi-level cache support. "
        "Operations: get, set, delete, get_stats. "
        "Cache names: llm, analysis, transcription, etc."
    )
    args_schema: type[BaseModel] = CacheV2OperationInput

    def __init__(self) -> None:
        """Initialize the cache V2 tool."""
        super().__init__()
        self._cache: UnifiedCache | None = None

    def _get_cache(self) -> UnifiedCache:
        """Get unified cache instance."""
        if self._cache is None:
            self._cache = get_unified_cache()
        return self._cache

    def _run(
        self,
        operation: str,
        cache_name: str,
        key: str,
        value: Any = None,
        dependencies: list[str] | None = None,
        tenant: str = "default",
        workspace: str = "main",
        **kwargs: Any,
    ) -> str:
        """Execute cache operation using unified facade.

        Args:
            operation: Operation type (get, set, delete, get_stats)
            cache_name: Logical cache name
            key: Cache key
            value: Value for set operations
            dependencies: Dependency keys for invalidation
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            JSON string result of the operation
        """
        try:
            if not ENABLE_CACHE_V2:
                import json

                return json.dumps(
                    StepResult.fail(
                        "ENABLE_CACHE_V2 is disabled. Use legacy cache tools."
                    ).to_dict()
                )

            cache = self._get_cache()
            namespace = get_cache_namespace(tenant, workspace)

            if operation == "get":
                import asyncio

                result = asyncio.run(cache.get(namespace, cache_name, key))
                import json

                return json.dumps(result.to_dict())

            elif operation == "set":
                if value is None:
                    import json

                    return json.dumps(
                        StepResult.fail("Value required for set operation").to_dict()
                    )

                deps_set = set(dependencies) if dependencies else None
                import asyncio

                result = asyncio.run(
                    cache.set(namespace, cache_name, key, value, dependencies=deps_set)
                )
                import json

                return json.dumps(result.to_dict())

            elif operation == "delete":
                # For delete, we'll use set with None value (cache implementation detail)
                import asyncio

                result = asyncio.run(cache.set(namespace, cache_name, key, None))
                import json

                return json.dumps(result.to_dict())

            elif operation == "get_stats":
                # Get cache statistics for the namespace
                cache_instance = cache.get_cache(namespace, cache_name)
                import asyncio

                stats = asyncio.run(cache_instance.get_stats())
                import json

                return json.dumps(StepResult.ok(data=stats).to_dict())

            else:
                import json

                return json.dumps(
                    StepResult.fail(f"Unknown operation: {operation}").to_dict()
                )

        except Exception as exc:
            logger.error(f"Cache V2 operation failed: {exc}", exc_info=True)
            import json

            return json.dumps(
                StepResult.fail(f"Cache operation failed: {exc}").to_dict()
            )
