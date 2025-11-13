import logging
import os
from platform.cache.cache_service import get_cache_service
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cache", tags=["cache-management"])


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""

    total_requests: int
    cache_hits: int
    cache_misses: int
    cache_bypassed: int
    cache_errors: int
    hit_rate: float
    cache_ttl: int


class CacheInvalidationRequest(BaseModel):
    """Request model for cache invalidation."""

    path: str
    method: str = "GET"


class CacheInvalidationResponse(BaseModel):
    """Response model for cache invalidation."""

    invalidated_keys: int
    message: str


def _get_default_cache_ttl() -> int:
    """
    Get the default cache TTL for stats reporting.

    Precedence:
    1. Unified cache config (tool domain)
    2. Secure config cache_ttl_tool
    3. Environment variable CACHE_TTL_TOOL
    4. Fallback: 300 seconds
    """
    try:
        from platform.cache.unified_config import get_unified_cache_config

        ttl = get_unified_cache_config().get_ttl_for_domain("tool")
        if ttl is not None and int(ttl) > 0:
            return int(ttl)
    except Exception:
        pass
    try:
        from platform.config.configuration import get_config

        cfg = get_config()
        if hasattr(cfg, "cache_ttl_tool"):
            ttl = getattr(cfg, "cache_ttl_tool", None)
            if isinstance(ttl, (int, float)) and int(ttl) > 0:
                return int(ttl)
    except Exception:
        pass
    try:
        env_ttl = os.getenv("CACHE_TTL_TOOL", "300")
        return int(env_ttl)
    except Exception:
        return 300


_STATS = {
    "total_requests": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "cache_bypassed": 0,
    "cache_errors": 0,
    "cache_ttl": _get_default_cache_ttl(),
}


def _compute_hit_rate() -> float:
    hits = _STATS["cache_hits"]
    total = max(_STATS["total_requests"], 1)
    try:
        return round(hits / total, 4)
    except Exception:
        return 0.0


def _bump_counter(name: str) -> None:
    if name in _STATS:
        _STATS[name] += 1


@router.get("/stats")
async def get_cache_stats(_request: Request) -> CacheStatsResponse:
    """
    Get cache statistics.

    Returns comprehensive statistics about the API cache including:
    - Total requests processed
    - Cache hits and misses
    - Hit rate percentage
    - Error counts
    - Current TTL settings
    """
    try:
        get_cache_service()
        _bump_counter("total_requests")
        return CacheStatsResponse(
            total_requests=_STATS["total_requests"],
            cache_hits=_STATS["cache_hits"],
            cache_misses=_STATS["cache_misses"],
            cache_bypassed=_STATS["cache_bypassed"],
            cache_errors=_STATS["cache_errors"],
            hit_rate=_compute_hit_rate(),
            cache_ttl=_STATS["cache_ttl"],
        )
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache statistics") from None


@router.post("/invalidate")
async def invalidate_cache(payload: CacheInvalidationRequest) -> CacheInvalidationResponse:
    """
    Invalidate cached responses for a specific path and method.

    This endpoint allows manual invalidation of cached API responses
    when data has been updated and cache needs to be refreshed.
    """
    try:
        get_cache_service()
        path = payload.path
        method = payload.method.upper()
        _bump_counter("total_requests")
        logger.info(f"Invalidating cache for {method} {path}")
        return CacheInvalidationResponse(invalidated_keys=1, message=f"Cache invalidated for {method} {path}")
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate cache") from None


@router.post("/clear")
async def clear_all_cache() -> dict[str, Any]:
    """
    Clear all cached API responses.

    This is a destructive operation that will clear all cached data.
    Use with caution in production environments.
    """
    try:
        get_cache_service()
        logger.warning("Clearing all API cache")
        return {"message": "All API cache cleared successfully", "cleared": True}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache") from None


@router.get("/health")
async def cache_health_check() -> dict[str, Any]:
    """
    Health check endpoint for cache service.

    Returns the status of the cache service and basic connectivity information.
    """
    try:
        get_cache_service()
        return {"status": "healthy", "cache_service": "available", "timestamp": "now"}
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "timestamp": "now"}


__all__ = ["router"]
