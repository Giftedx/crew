"""Cache V2 Shadow Harness for Hit Rate Comparison

This service implements dual-write shadow mode to compare cache hit rates
between ENABLE_CACHE_V2=true (unified cache) and legacy cache implementations.

See ADR-0001 for architectural decision rationale.
"""

from __future__ import annotations

import logging
from typing import Any

from core.cache.bounded_cache import BoundedLRUCache
from ultimate_discord_intelligence_bot.cache import (
    ENABLE_CACHE_V2,
    UnifiedCache,
    get_cache_namespace,
    get_unified_cache,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class CacheShadowHarness:
    """Shadow harness for comparing cache V2 vs legacy hit rates."""

    def __init__(self) -> StepResult:
        """Initialize the shadow harness."""
        self.unified_cache: UnifiedCache | None = None
        self.legacy_cache: BoundedLRUCache | None = None
        self._shadow_metrics = {
            "unified_hits": 0,
            "unified_misses": 0,
            "legacy_hits": 0,
            "legacy_misses": 0,
        }

    def _get_unified_cache(self) -> StepResult:
        """Get unified cache instance."""
        if self.unified_cache is None:
            self.unified_cache = get_unified_cache()
        return self.unified_cache

    def _get_legacy_cache(self) -> StepResult:
        """Get legacy cache instance."""
        if self.legacy_cache is None:
            self.legacy_cache = BoundedLRUCache(max_size=1000)
        return self.legacy_cache

    async def shadow_get(
        self,
        cache_name: str,
        key: str,
        tenant: str = "default",
        workspace: str = "main",
    ) -> StepResult:
        """Get value from both unified and legacy cache (shadow mode).

        Args:
            cache_name: Logical cache name
            key: Cache key
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            Tuple of (unified_value, metrics_dict)
        """
        metrics = {
            "unified_hit": False,
            "legacy_hit": False,
            "cache_name": cache_name,
            "key": key,
        }

        # Try unified cache (V2)
        unified_value = None
        if ENABLE_CACHE_V2:
            try:
                cache = self._get_unified_cache()
                namespace = get_cache_namespace(tenant, workspace)
                result = await cache.get(namespace, cache_name, key)
                if result.success and result.data.get("hit", False):
                    unified_value = result.data.get("value")
                    metrics["unified_hit"] = True
                    self._shadow_metrics["unified_hits"] += 1
                else:
                    self._shadow_metrics["unified_misses"] += 1
            except Exception as exc:
                logger.warning(f"Unified cache get failed: {exc}")
                self._shadow_metrics["unified_misses"] += 1

        # Try legacy cache
        try:
            legacy_cache = self._get_legacy_cache()
            legacy_key = f"{cache_name}:{key}"
            legacy_value = legacy_cache.get(legacy_key)
            if legacy_value is not None:
                metrics["legacy_hit"] = True
                self._shadow_metrics["legacy_hits"] += 1
            else:
                self._shadow_metrics["legacy_misses"] += 1
        except Exception as exc:
            logger.warning(f"Legacy cache get failed: {exc}")
            self._shadow_metrics["legacy_misses"] += 1

        return unified_value, metrics

    async def shadow_set(
        self,
        cache_name: str,
        key: str,
        value: Any,
        tenant: str = "default",
        workspace: str = "main",
        dependencies: set[str] | None = None,
    ) -> StepResult:
        """Set value in both unified and legacy cache (dual-write).

        Args:
            cache_name: Logical cache name
            key: Cache key
            value: Value to cache
            tenant: Tenant identifier
            workspace: Workspace identifier
            dependencies: Optional dependency keys

        Returns:
            StepResult indicating success/failure
        """
        errors = []

        # Set in unified cache (V2)
        if ENABLE_CACHE_V2:
            try:
                cache = self._get_unified_cache()
                namespace = get_cache_namespace(tenant, workspace)
                result = await cache.set(namespace, cache_name, key, value, dependencies=dependencies)
                if not result.success:
                    errors.append(f"Unified cache set failed: {result.error}")
            except Exception as exc:
                errors.append(f"Unified cache set error: {exc}")

        # Set in legacy cache
        try:
            legacy_cache = self._get_legacy_cache()
            legacy_key = f"{cache_name}:{key}"
            legacy_cache.set(legacy_key, value)
        except Exception as exc:
            errors.append(f"Legacy cache set error: {exc}")

        if errors:
            return StepResult.fail(f"Shadow set errors: {'; '.join(errors)}")
        return StepResult.ok()

    def get_shadow_metrics(self) -> StepResult:
        """Get shadow mode hit rate metrics.

        Returns:
            Dictionary with hit rates and raw counts
        """
        total_unified = self._shadow_metrics["unified_hits"] + self._shadow_metrics["unified_misses"]
        total_legacy = self._shadow_metrics["legacy_hits"] + self._shadow_metrics["legacy_misses"]

        unified_hit_rate = self._shadow_metrics["unified_hits"] / total_unified if total_unified > 0 else 0.0
        legacy_hit_rate = self._shadow_metrics["legacy_hits"] / total_legacy if total_legacy > 0 else 0.0

        return {
            "unified_hit_rate": unified_hit_rate,
            "legacy_hit_rate": legacy_hit_rate,
            "hit_rate_delta": unified_hit_rate - legacy_hit_rate,
            "unified_hits": self._shadow_metrics["unified_hits"],
            "unified_misses": self._shadow_metrics["unified_misses"],
            "legacy_hits": self._shadow_metrics["legacy_hits"],
            "legacy_misses": self._shadow_metrics["legacy_misses"],
            "total_requests": total_unified + total_legacy,
        }

    def reset_metrics(self) -> StepResult:
        """Reset shadow metrics counters."""
        self._shadow_metrics = {
            "unified_hits": 0,
            "unified_misses": 0,
            "legacy_hits": 0,
            "legacy_misses": 0,
        }


# Global shadow harness instance
_shadow_harness: CacheShadowHarness | None = None


def get_cache_shadow_harness() -> StepResult:
    """Get global cache shadow harness instance."""
    global _shadow_harness
    if _shadow_harness is None:
        _shadow_harness = CacheShadowHarness()
    return _shadow_harness
