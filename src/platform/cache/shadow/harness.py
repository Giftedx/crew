"""Cache shadow harness for comparing legacy vs. unified cache results.

This module provides infrastructure for running both legacy and unified cache
implementations in parallel (shadow mode) to verify correctness and performance
before full migration.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from platform.cache.unified_cache import UnifiedCacheService
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


@dataclass
class ShadowComparison:
    """Result of a shadow comparison between legacy and unified cache."""
    operation: str
    key: str
    legacy_success: bool
    unified_success: bool
    legacy_value_hash: str | None
    unified_value_hash: str | None
    match: bool
    legacy_latency_ms: float
    unified_latency_ms: float
    timestamp: float = field(default_factory=time.time)


class LegacyCacheProtocol(Protocol):
    """Protocol for legacy cache implementations."""
    async def get(self, key: str) -> Any: ...
    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool: ...
    async def delete(self, key: str) -> bool: ...


class CacheShadowHarness:
    """Harness for running cache operations in shadow mode."""

    def __init__(self, legacy_cache: LegacyCacheProtocol, unified_cache: UnifiedCacheService | None = None):
        self.legacy_cache = legacy_cache
        self.unified_cache = unified_cache or UnifiedCacheService()
        self.comparisons: list[ShadowComparison] = []
        logger.info("CacheShadowHarness initialized")

    async def get(self, key: str, tenant_id: str = "default", workspace_id: str = "main") -> Any:
        """Perform get operation on both caches and compare."""

        # Legacy execution
        start_legacy = time.time()
        try:
            legacy_result = await self.legacy_cache.get(key)
            legacy_success = True
        except Exception as e:
            logger.warning(f"Legacy cache get failed: {e}")
            legacy_result = None
            legacy_success = False
        legacy_latency = (time.time() - start_legacy) * 1000

        # Unified execution (shadow)
        start_unified = time.time()
        try:
            # Note: UnifiedCacheService returns StepResult
            unified_step_result = await self.unified_cache.get(key, tenant_id, workspace_id)
            if unified_step_result.success and unified_step_result.data:
                unified_result = unified_step_result.data.value if hasattr(unified_step_result.data, "value") else unified_step_result.data
                unified_success = True
            else:
                unified_result = None
                unified_success = unified_step_result.success
        except Exception as e:
            logger.warning(f"Unified cache get failed: {e}")
            unified_result = None
            unified_success = False
        unified_latency = (time.time() - start_unified) * 1000

        # Comparison
        match = self._compare_values(legacy_result, unified_result)

        comparison = ShadowComparison(
            operation="get",
            key=key,
            legacy_success=legacy_success,
            unified_success=unified_success,
            legacy_value_hash=str(hash(str(legacy_result))) if legacy_result is not None else None,
            unified_value_hash=str(hash(str(unified_result))) if unified_result is not None else None,
            match=match,
            legacy_latency_ms=legacy_latency,
            unified_latency_ms=unified_latency
        )
        self.comparisons.append(comparison)

        if not match:
             logger.info(f"Cache shadow mismatch for key '{key}': legacy={legacy_result}, unified={unified_result}")

        return legacy_result

    async def set(self, key: str, value: Any, ttl: int | None = None, tenant_id: str = "default", workspace_id: str = "main") -> bool:
        """Perform set operation on both caches."""

        # Legacy execution
        start_legacy = time.time()
        try:
            legacy_success = await self.legacy_cache.set(key, value, ttl)
        except Exception as e:
            logger.warning(f"Legacy cache set failed: {e}")
            legacy_success = False
        legacy_latency = (time.time() - start_legacy) * 1000

        # Unified execution (shadow)
        start_unified = time.time()
        try:
            unified_step_result = await self.unified_cache.set(key, value, ttl, tenant_id=tenant_id, workspace_id=workspace_id)
            unified_success = unified_step_result.success
        except Exception as e:
            logger.warning(f"Unified cache set failed: {e}")
            unified_success = False
        unified_latency = (time.time() - start_unified) * 1000

        # Comparison (success status)
        match = (bool(legacy_success) == bool(unified_success))

        comparison = ShadowComparison(
            operation="set",
            key=key,
            legacy_success=bool(legacy_success),
            unified_success=unified_success,
            legacy_value_hash=None,
            unified_value_hash=None,
            match=match,
            legacy_latency_ms=legacy_latency,
            unified_latency_ms=unified_latency
        )
        self.comparisons.append(comparison)

        return legacy_success

    def _compare_values(self, v1: Any, v2: Any) -> bool:
        """Compare two values for equality."""
        if v1 is None and v2 is None:
            return True
        if v1 is None or v2 is None:
            return False
        try:
            return v1 == v2
        except Exception:
            # Fallback to string comparison if direct comparison fails
            return str(v1) == str(v2)

    def get_stats(self) -> dict[str, Any]:
        """Return statistics about comparisons."""
        total = len(self.comparisons)
        if total == 0:
            return {"total": 0, "match_rate": 0.0}

        matches = sum(1 for c in self.comparisons if c.match)
        return {
            "total": total,
            "matches": matches,
            "mismatches": total - matches,
            "match_rate": matches / total,
            "avg_legacy_latency": sum(c.legacy_latency_ms for c in self.comparisons) / total,
            "avg_unified_latency": sum(c.unified_latency_ms for c in self.comparisons) / total,
        }
