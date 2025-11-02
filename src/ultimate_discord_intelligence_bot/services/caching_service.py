"""Caching service for ML/AI operations."""

from __future__ import annotations
import logging
from typing import Any
from ultimate_discord_intelligence_bot.settings import get_settings
from platform.core.step_result import StepResult
from ...platform.cache.multi_level_cache import MultiLevelCache

logger = logging.getLogger(__name__)


class CachingService:
    """Service for managing ML/AI operation caching."""

    def __init__(self):
        """Initialize caching service."""
        self.settings = get_settings()
        self.cache: MultiLevelCache | None = None
        self._initialize_cache()

    def _initialize_cache(self) -> None:
        """Initialize cache with settings."""
        try:
            redis_url = getattr(self.settings, "RATE_LIMIT_REDIS_URL", None)
            if not redis_url:
                redis_url = getattr(self.settings, "REDIS_URL", None)
            self.cache = MultiLevelCache(
                redis_url=redis_url,
                max_memory_size=getattr(self.settings, "CACHE_MEMORY_SIZE", 1000),
                default_ttl=getattr(self.settings, "CACHE_DEFAULT_TTL", 3600),
                enable_disk_cache=getattr(self.settings, "CACHE_ENABLE_DISK", False),
                disk_cache_path=getattr(self.settings, "CACHE_DISK_PATH", "/tmp/cache"),
            )
            logger.info("Caching service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize caching service: {e}")
            self.cache = None

    def get_cache(self) -> MultiLevelCache | None:
        """Get cache instance."""
        return self.cache

    def cache_transcription(
        self, url: str, transcript: str, tenant: str, workspace: str, ttl: int | None = None
    ) -> bool:
        """Cache transcription result."""
        if not self.cache:
            return False
        try:
            return self.cache.set("transcription", {"url": url}, transcript, ttl or 86400, tenant, workspace)
        except Exception as e:
            logger.error(f"Failed to cache transcription: {e}")
            return False

    def get_cached_transcription(self, url: str, tenant: str, workspace: str) -> str | None:
        """Get cached transcription."""
        if not self.cache:
            return None
        try:
            return self.cache.get("transcription", {"url": url}, tenant, workspace)
        except Exception as e:
            logger.error(f"Failed to get cached transcription: {e}")
            return None

    def cache_embedding(
        self, text: str, embedding: list[float], tenant: str, workspace: str, ttl: int | None = None
    ) -> bool:
        """Cache embedding result."""
        if not self.cache:
            return False
        try:
            return self.cache.set("embedding", {"text": text}, embedding, ttl or 3600, tenant, workspace)
        except Exception as e:
            logger.error(f"Failed to cache embedding: {e}")
            return False

    def get_cached_embedding(self, text: str, tenant: str, workspace: str) -> list[float] | None:
        """Get cached embedding."""
        if not self.cache:
            return None
        try:
            return self.cache.get("embedding", {"text": text}, tenant, workspace)
        except Exception as e:
            logger.error(f"Failed to get cached embedding: {e}")
            return None

    def cache_analysis(
        self, content: str, analysis: dict[str, Any], tenant: str, workspace: str, ttl: int | None = None
    ) -> bool:
        """Cache analysis result."""
        if not self.cache:
            return False
        try:
            return self.cache.set("analysis", {"content": content}, analysis, ttl or 1800, tenant, workspace)
        except Exception as e:
            logger.error(f"Failed to cache analysis: {e}")
            return False

    def get_cached_analysis(self, content: str, tenant: str, workspace: str) -> dict[str, Any] | None:
        """Get cached analysis."""
        if not self.cache:
            return None
        try:
            return self.cache.get("analysis", {"content": content}, tenant, workspace)
        except Exception as e:
            logger.error(f"Failed to get cached analysis: {e}")
            return None

    def cache_fact_check(
        self, claim: str, fact_check: dict[str, Any], tenant: str, workspace: str, ttl: int | None = None
    ) -> bool:
        """Cache fact check result."""
        if not self.cache:
            return False
        try:
            return self.cache.set("fact_check", {"claim": claim}, fact_check, ttl or 3600, tenant, workspace)
        except Exception as e:
            logger.error(f"Failed to cache fact check: {e}")
            return False

    def get_cached_fact_check(self, claim: str, tenant: str, workspace: str) -> dict[str, Any] | None:
        """Get cached fact check."""
        if not self.cache:
            return None
        try:
            return self.cache.get("fact_check", {"claim": claim}, tenant, workspace)
        except Exception as e:
            logger.error(f"Failed to get cached fact check: {e}")
            return None

    def clear_tenant_cache(self, tenant: str, workspace: str = "") -> bool:
        """Clear cache for specific tenant/workspace."""
        if not self.cache:
            return False
        try:
            return self.cache.clear(tenant, workspace)
        except Exception as e:
            logger.error(f"Failed to clear tenant cache: {e}")
            return False

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        if not self.cache:
            return {"status": "disabled"}
        try:
            return self.cache.get_stats()
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

    def health_check(self) -> StepResult:
        """Check cache health."""
        if not self.cache:
            return StepResult.fail("Cache not initialized")
        try:
            return self.cache.health_check()
        except Exception as e:
            return StepResult.fail(f"Cache health check failed: {e}")


_caching_service: CachingService | None = None


def get_caching_service() -> CachingService:
    """Get global caching service instance."""
    global _caching_service
    if _caching_service is None:
        _caching_service = CachingService()
    return _caching_service
