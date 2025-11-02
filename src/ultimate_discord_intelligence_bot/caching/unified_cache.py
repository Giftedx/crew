"""Unified Cache Service - Three-tier cache system with intelligent optimization

This service provides a unified three-tier cache system that consolidates
all caching implementations into a single, intelligent caching layer with
L1 (memory), L2 (Redis), and L3 (Semantic) caching with RL-based optimization.
"""

from __future__ import annotations
import logging
import pickle
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from platform.cache.unified_config import get_unified_cache_config
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant

try:
    import redis
    from redis import Redis
except ImportError:
    Redis = None
try:
    from platform.cache import Cache as CoreCache
except ImportError:
    CoreCache = None
try:
    from ultimate_discord_intelligence_bot.services.semantic_cache_service import SemanticCacheService
except ImportError:
    SemanticCacheService = None
logger = logging.getLogger(__name__)


@dataclass
class CacheRequest:
    """Request for cache operations"""

    key: str
    value: Any = None
    ttl: int | None = None
    cache_level: str = "auto"
    tenant_id: str | None = None
    workspace_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheResult:
    """Result from cache operations"""

    hit: bool
    value: Any = None
    cache_level: str = "none"
    ttl: int | None = None
    cost: float = 0.0
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CacheMetrics:
    """Cache performance metrics"""

    total_requests: int = 0
    total_hits: int = 0
    total_misses: int = 0
    l1_hits: int = 0
    l2_hits: int = 0
    l3_hits: int = 0
    avg_latency_ms: float = 0.0
    total_cost: float = 0.0
    hit_rate: float = 0.0
    last_reset: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class UnifiedCacheConfig:
    """Configuration for unified cache service"""

    enable_l1_cache: bool = True
    enable_l2_cache: bool = True
    enable_l3_cache: bool = True
    enable_rl_optimization: bool = True
    enable_metrics: bool = True
    l1_max_size: int = 10000
    l1_default_ttl: int = 300
    l2_host: str = "localhost"
    l2_port: int = 6379
    l2_db: int = 0
    l2_default_ttl: int = 3600
    l3_default_ttl: int = 86400
    l3_similarity_threshold: float = 0.8
    optimization_interval: int = 300
    metrics_reset_interval: int = 3600


class UnifiedCacheService:
    """Unified three-tier cache service with intelligent optimization"""

    def __init__(self, config: UnifiedCacheConfig | None = None, use_new_config: bool = True):
        """Initialize unified cache service.

        Args:
            config: Legacy UnifiedCacheConfig for backward compatibility
            use_new_config: If True, use new unified cache configuration (default)
        """
        if use_new_config:
            new_config = get_unified_cache_config()
            self.config = UnifiedCacheConfig(
                enable_l1_cache=new_config.memory.enabled,
                enable_l2_cache=new_config.redis.enabled,
                enable_l3_cache=new_config.semantic.enabled,
                enable_rl_optimization=new_config.auto_tier_selection,
                enable_metrics=new_config.metrics.enabled,
                l1_max_size=new_config.memory.max_size,
                l1_default_ttl=new_config.domain.tool.ttl if new_config.domain.tool.enabled else 300,
                l2_host=new_config.redis.host,
                l2_port=new_config.redis.port,
                l2_db=new_config.redis.db,
                l2_default_ttl=new_config.redis.default_ttl,
                l3_default_ttl=new_config.semantic.ttl,
                l3_similarity_threshold=new_config.semantic.similarity_threshold,
                optimization_interval=300,
                metrics_reset_interval=3600,
            )
        else:
            self.config = config or UnifiedCacheConfig()
        self._initialized = False
        self._l1_cache: dict[str, Any] = {}
        self._l2_client: Redis | None = None
        self._l3_service: Any | None = None
        self._core_cache: Any | None = None
        self._metrics: dict[str, CacheMetrics] = {}
        self._last_optimization: dict[str, datetime] = {}
        self._initialize_cache_layers()

    def _initialize_cache_layers(self) -> None:
        """Initialize all configured cache layers"""
        try:
            if self.config.enable_l1_cache:
                self._l1_cache = {}
                logger.info("L1 Cache (Memory) initialized")
            if self.config.enable_l2_cache and Redis:
                try:
                    self._l2_client = redis.Redis(
                        host=self.config.l2_host, port=self.config.l2_port, db=self.config.l2_db, decode_responses=False
                    )
                    self._l2_client.ping()
                    logger.info("L2 Cache (Redis) initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize L2 Cache (Redis): {e}")
                    self._l2_client = None
            if self.config.enable_l3_cache and SemanticCacheService:
                try:
                    self._l3_service = SemanticCacheService()
                    logger.info("L3 Cache (Semantic) initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize L3 Cache (Semantic): {e}")
                    self._l3_service = None
            if CoreCache:
                try:
                    self._core_cache = CoreCache()
                    logger.info("Core Cache initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Core Cache: {e}")
                    self._core_cache = None
            self._initialized = True
            logger.info(f"Unified cache service initialized with {self._get_active_layers()} layers")
        except Exception as e:
            logger.error(f"Failed to initialize unified cache service: {e}")
            self._initialized = False

    def _get_active_layers(self) -> int:
        """Get count of active cache layers"""
        count = 0
        if self._l1_cache is not None:
            count += 1
        if self._l2_client is not None:
            count += 1
        if self._l3_service is not None:
            count += 1
        if self._core_cache is not None:
            count += 1
        return count

    async def get(self, key: str, tenant_id: str | None = None, workspace_id: str | None = None) -> StepResult:
        """Get value from cache with intelligent tier selection"""
        try:
            if not self._initialized:
                return StepResult.fail("Unified cache service not initialized")
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"
            namespaced_key = self._create_namespaced_key(key, tenant_id, workspace_id)
            start_time = time.time()
            metrics_key = f"{tenant_id}:{workspace_id}"
            if self.config.enable_l1_cache and self._l1_cache is not None:
                l1_result = await self._get_l1(namespaced_key)
                if l1_result.success and l1_result.data is not None:
                    latency = (time.time() - start_time) * 1000
                    self._record_metrics(metrics_key, True, "l1", latency, 0.0)
                    return StepResult.ok(
                        data=CacheResult(
                            hit=True,
                            value=l1_result.data,
                            cache_level="l1",
                            latency_ms=latency,
                            metadata={"source": "l1_memory"},
                        )
                    )
            if self.config.enable_l2_cache and self._l2_client is not None:
                l2_result = await self._get_l2(namespaced_key)
                if l2_result.success and l2_result.data is not None:
                    latency = (time.time() - start_time) * 1000
                    self._record_metrics(metrics_key, True, "l2", latency, 0.001)
                    if self.config.enable_l1_cache:
                        await self._set_l1(namespaced_key, l2_result.data, self.config.l1_default_ttl)
                    return StepResult.ok(
                        data=CacheResult(
                            hit=True,
                            value=l2_result.data,
                            cache_level="l2",
                            latency_ms=latency,
                            cost=0.001,
                            metadata={"source": "l2_redis"},
                        )
                    )
            if self.config.enable_l3_cache and self._l3_service is not None:
                l3_result = await self._get_l3(key, tenant_id, workspace_id)
                if l3_result.success and l3_result.data is not None:
                    latency = (time.time() - start_time) * 1000
                    self._record_metrics(metrics_key, True, "l3", latency, 0.01)
                    if self.config.enable_l1_cache:
                        await self._set_l1(namespaced_key, l3_result.data, self.config.l1_default_ttl)
                    if self.config.enable_l2_cache:
                        await self._set_l2(namespaced_key, l3_result.data, self.config.l2_default_ttl)
                    return StepResult.ok(
                        data=CacheResult(
                            hit=True,
                            value=l3_result.data,
                            cache_level="l3",
                            latency_ms=latency,
                            cost=0.01,
                            metadata={"source": "l3_semantic"},
                        )
                    )
            if self._core_cache is not None:
                core_result = await self._get_core(namespaced_key)
                if core_result.success and core_result.data is not None:
                    latency = (time.time() - start_time) * 1000
                    self._record_metrics(metrics_key, True, "core", latency, 0.005)
                    if self.config.enable_l1_cache:
                        await self._set_l1(namespaced_key, core_result.data, self.config.l1_default_ttl)
                    if self.config.enable_l2_cache:
                        await self._set_l2(namespaced_key, core_result.data, self.config.l2_default_ttl)
                    return StepResult.ok(
                        data=CacheResult(
                            hit=True,
                            value=core_result.data,
                            cache_level="core",
                            latency_ms=latency,
                            cost=0.005,
                            metadata={"source": "core_cache"},
                        )
                    )
            latency = (time.time() - start_time) * 1000
            self._record_metrics(metrics_key, False, "none", latency, 0.0)
            return StepResult.ok(
                data=CacheResult(hit=False, cache_level="none", latency_ms=latency, metadata={"source": "cache_miss"})
            )
        except Exception as e:
            logger.error(f"Error in cache get operation: {e}", exc_info=True)
            return StepResult.fail(f"Cache get failed: {e!s}")

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        cache_level: str = "auto",
        tenant_id: str | None = None,
        workspace_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StepResult:
        """Set value in cache with intelligent tier selection"""
        try:
            if not self._initialized:
                return StepResult.fail("Unified cache service not initialized")
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"
            namespaced_key = self._create_namespaced_key(key, tenant_id, workspace_id)
            if cache_level == "auto":
                levels = self._determine_cache_levels(value, ttl)
            elif cache_level == "all":
                levels = ["l1", "l2", "l3"]
            else:
                levels = [cache_level]
            results = []
            if "l1" in levels and self.config.enable_l1_cache and (self._l1_cache is not None):
                l1_ttl = ttl or self.config.l1_default_ttl
                l1_result = await self._set_l1(namespaced_key, value, l1_ttl)
                results.append(("l1", l1_result.success))
            if "l2" in levels and self.config.enable_l2_cache and (self._l2_client is not None):
                l2_ttl = ttl or self.config.l2_default_ttl
                l2_result = await self._set_l2(namespaced_key, value, l2_ttl)
                results.append(("l2", l2_result.success))
            if "l3" in levels and self.config.enable_l3_cache and (self._l3_service is not None):
                l3_ttl = ttl or self.config.l3_default_ttl
                l3_result = await self._set_l3(key, value, l3_ttl, tenant_id, workspace_id, metadata)
                results.append(("l3", l3_result.success))
            if self._core_cache is not None:
                core_ttl = ttl or self.config.l2_default_ttl
                core_result = await self._set_core(namespaced_key, value, core_ttl)
                results.append(("core", core_result.success))
            success_count = sum((1 for _, success in results if success))
            return StepResult.ok(
                data={
                    "set_in_layers": [level for level, success in results if success],
                    "total_layers": len(results),
                    "success_count": success_count,
                    "metadata": metadata or {},
                }
            )
        except Exception as e:
            logger.error(f"Error in cache set operation: {e}", exc_info=True)
            return StepResult.fail(f"Cache set failed: {e!s}")

    async def delete(self, key: str, tenant_id: str | None = None, workspace_id: str | None = None) -> StepResult:
        """Delete value from all cache layers"""
        try:
            if not self._initialized:
                return StepResult.fail("Unified cache service not initialized")
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"
            namespaced_key = self._create_namespaced_key(key, tenant_id, workspace_id)
            results = []
            if self.config.enable_l1_cache and self._l1_cache is not None:
                l1_result = await self._delete_l1(namespaced_key)
                results.append(("l1", l1_result.success))
            if self.config.enable_l2_cache and self._l2_client is not None:
                l2_result = await self._delete_l2(namespaced_key)
                results.append(("l2", l2_result.success))
            if self.config.enable_l3_cache and self._l3_service is not None:
                l3_result = await self._delete_l3(key, tenant_id, workspace_id)
                results.append(("l3", l3_result.success))
            if self._core_cache is not None:
                core_result = await self._delete_core(namespaced_key)
                results.append(("core", core_result.success))
            success_count = sum((1 for _, success in results if success))
            return StepResult.ok(
                data={
                    "deleted_from_layers": [level for level, success in results if success],
                    "total_layers": len(results),
                    "success_count": success_count,
                }
            )
        except Exception as e:
            logger.error(f"Error in cache delete operation: {e}", exc_info=True)
            return StepResult.fail(f"Cache delete failed: {e!s}")

    def get_metrics(self, tenant_id: str | None = None, workspace_id: str | None = None) -> dict[str, Any]:
        """Get cache performance metrics"""
        try:
            if tenant_id and workspace_id:
                key = f"{tenant_id}:{workspace_id}"
                metrics = self._metrics.get(key, CacheMetrics())
            else:
                metrics = CacheMetrics()
                for key_metrics in self._metrics.values():
                    metrics.total_requests += key_metrics.total_requests
                    metrics.total_hits += key_metrics.total_hits
                    metrics.total_misses += key_metrics.total_misses
                    metrics.l1_hits += key_metrics.l1_hits
                    metrics.l2_hits += key_metrics.l2_hits
                    metrics.l3_hits += key_metrics.l3_hits
                    metrics.total_cost += key_metrics.total_cost
            if metrics.total_requests > 0:
                metrics.hit_rate = metrics.total_hits / metrics.total_requests
            if metrics.total_requests > 0:
                metrics.avg_latency_ms = (
                    sum(
                        (
                            getattr(metrics, f"{level}_hits", 0)
                            * (1.0 if level == "l1" else 2.0 if level == "l2" else 5.0)
                            for level in ["l1", "l2", "l3"]
                        )
                    )
                    / metrics.total_requests
                )
            return {
                "total_requests": metrics.total_requests,
                "total_hits": metrics.total_hits,
                "total_misses": metrics.total_misses,
                "hit_rate": metrics.hit_rate,
                "l1_hits": metrics.l1_hits,
                "l2_hits": metrics.l2_hits,
                "l3_hits": metrics.l3_hits,
                "avg_latency_ms": metrics.avg_latency_ms,
                "total_cost": metrics.total_cost,
                "last_reset": metrics.last_reset.isoformat(),
                "active_layers": self._get_active_layers(),
            }
        except Exception as e:
            logger.error(f"Failed to get cache metrics: {e}")
            return {"error": str(e)}

    def _create_namespaced_key(self, key: str, tenant_id: str, workspace_id: str) -> str:
        """Create tenant/workspace namespaced cache key"""
        return f"{tenant_id}:{workspace_id}:{key}"

    def _determine_cache_levels(self, value: Any, ttl: int | None) -> list[str]:
        """Determine which cache levels to use based on value and TTL"""
        levels = []
        if self._is_small_value(value):
            levels.append("l1")
        if ttl is None or ttl <= self.config.l2_default_ttl:
            levels.append("l2")
        if ttl is None or ttl >= self.config.l3_default_ttl:
            levels.append("l3")
        return levels if levels else ["l1", "l2"]

    def _is_small_value(self, value: Any) -> bool:
        """Check if value is small enough for L1 cache"""
        try:
            serialized = pickle.dumps(value)
            return len(serialized) < 1024 * 1024
        except Exception:
            return False

    def _record_metrics(self, metrics_key: str, hit: bool, cache_level: str, latency_ms: float, cost: float) -> None:
        """Record cache operation metrics"""
        try:
            if metrics_key not in self._metrics:
                self._metrics[metrics_key] = CacheMetrics()
            metrics = self._metrics[metrics_key]
            metrics.total_requests += 1
            if hit:
                metrics.total_hits += 1
                if cache_level == "l1":
                    metrics.l1_hits += 1
                elif cache_level == "l2":
                    metrics.l2_hits += 1
                elif cache_level == "l3":
                    metrics.l3_hits += 1
            else:
                metrics.total_misses += 1
            metrics.total_cost += cost
            now = datetime.now(timezone.utc)
            if (now - metrics.last_reset).total_seconds() > self.config.metrics_reset_interval:
                metrics.total_requests = 0
                metrics.total_hits = 0
                metrics.total_misses = 0
                metrics.l1_hits = 0
                metrics.l2_hits = 0
                metrics.l3_hits = 0
                metrics.total_cost = 0.0
                metrics.last_reset = now
        except Exception as e:
            logger.warning(f"Failed to record cache metrics: {e}")

    async def _get_l1(self, key: str) -> StepResult:
        """Get from L1 cache (memory)"""
        try:
            if key in self._l1_cache:
                return StepResult.ok(data=self._l1_cache[key])
            return StepResult.ok(data=None)
        except Exception as e:
            return StepResult.fail(str(e))

    async def _set_l1(self, key: str, value: Any, ttl: int) -> StepResult:
        """Set in L1 cache (memory)"""
        try:
            expire_time = time.time() + ttl
            self._l1_cache[key] = {"value": value, "expire_time": expire_time}
            await self._cleanup_l1()
            return StepResult.ok(data=True)
        except Exception as e:
            return StepResult.fail(str(e))

    async def _delete_l1(self, key: str) -> StepResult:
        """Delete from L1 cache (memory)"""
        try:
            if key in self._l1_cache:
                del self._l1_cache[key]
            return StepResult.ok(data=True)
        except Exception as e:
            return StepResult.fail(str(e))

    async def _cleanup_l1(self) -> None:
        """Cleanup expired entries from L1 cache"""
        try:
            current_time = time.time()
            expired_keys = [
                key
                for key, data in self._l1_cache.items()
                if isinstance(data, dict) and data.get("expire_time", 0) < current_time
            ]
            for key in expired_keys:
                del self._l1_cache[key]
        except Exception as e:
            logger.warning(f"Failed to cleanup L1 cache: {e}")

    async def _get_l2(self, key: str) -> StepResult:
        """Get from L2 cache (Redis)"""
        try:
            if not self._l2_client:
                return StepResult.fail("L2 cache not available")
            result = self._l2_client.get(key)
            if result:
                value = pickle.loads(result)
                return StepResult.ok(data=value)
            return StepResult.ok(data=None)
        except Exception as e:
            return StepResult.fail(str(e))

    async def _set_l2(self, key: str, value: Any, ttl: int) -> StepResult:
        """Set in L2 cache (Redis)"""
        try:
            if not self._l2_client:
                return StepResult.fail("L2 cache not available")
            serialized = pickle.dumps(value)
            self._l2_client.setex(key, ttl, serialized)
            return StepResult.ok(data=True)
        except Exception as e:
            return StepResult.fail(str(e))

    async def _delete_l2(self, key: str) -> StepResult:
        """Delete from L2 cache (Redis)"""
        try:
            if not self._l2_client:
                return StepResult.fail("L2 cache not available")
            self._l2_client.delete(key)
            return StepResult.ok(data=True)
        except Exception as e:
            return StepResult.fail(str(e))

    async def _get_l3(self, key: str, tenant_id: str, workspace_id: str) -> StepResult:
        """Get from L3 cache (Semantic)"""
        try:
            if not self._l3_service:
                return StepResult.fail("L3 cache not available")
            if hasattr(self._l3_service, "get"):
                result = await self._l3_service.get(key, tenant_id, workspace_id)
                return result
            return StepResult.ok(data=None)
        except Exception as e:
            return StepResult.fail(str(e))

    async def _set_l3(
        self, key: str, value: Any, ttl: int, tenant_id: str, workspace_id: str, metadata: dict[str, Any] | None
    ) -> StepResult:
        """Set in L3 cache (Semantic)"""
        try:
            if not self._l3_service:
                return StepResult.fail("L3 cache not available")
            if hasattr(self._l3_service, "set"):
                result = await self._l3_service.set(key, value, ttl, tenant_id, workspace_id, metadata)
                return result
            return StepResult.ok(data=True)
        except Exception as e:
            return StepResult.fail(str(e))

    async def _delete_l3(self, key: str, tenant_id: str, workspace_id: str) -> StepResult:
        """Delete from L3 cache (Semantic)"""
        try:
            if not self._l3_service:
                return StepResult.fail("L3 cache not available")
            if hasattr(self._l3_service, "delete"):
                result = await self._l3_service.delete(key, tenant_id, workspace_id)
                return result
            return StepResult.ok(data=True)
        except Exception as e:
            return StepResult.fail(str(e))

    async def _get_core(self, key: str) -> StepResult:
        """Get from core cache"""
        try:
            if not self._core_cache:
                return StepResult.fail("Core cache not available")
            if hasattr(self._core_cache, "get"):
                result = await self._core_cache.get(key)
                return result
            return StepResult.ok(data=None)
        except Exception as e:
            return StepResult.fail(str(e))

    async def _set_core(self, key: str, value: Any, ttl: int) -> StepResult:
        """Set in core cache"""
        try:
            if not self._core_cache:
                return StepResult.fail("Core cache not available")
            if hasattr(self._core_cache, "set"):
                result = await self._core_cache.set(key, value, ttl)
                return result
            return StepResult.ok(data=True)
        except Exception as e:
            return StepResult.fail(str(e))

    async def _delete_core(self, key: str) -> StepResult:
        """Delete from core cache"""
        try:
            if not self._core_cache:
                return StepResult.fail("Core cache not available")
            if hasattr(self._core_cache, "delete"):
                result = await self._core_cache.delete(key)
                return result
            return StepResult.ok(data=True)
        except Exception as e:
            return StepResult.fail(str(e))
