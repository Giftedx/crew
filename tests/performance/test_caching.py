"""Tests for multi-level caching system."""

import tempfile
from platform.core.cache.multi_level_cache import MultiLevelCache
from unittest.mock import Mock, patch

from src.ultimate_discord_intelligence_bot.services.caching_service import CachingService
from src.ultimate_discord_intelligence_bot.step_result import StepResult


class TestMultiLevelCache:
    """Test multi-level cache functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cache = MultiLevelCache(redis_url=None, max_memory_size=10, default_ttl=3600, enable_disk_cache=False)

    def test_memory_cache_basic_operations(self):
        """Test basic memory cache operations."""
        result = self.cache.set("test", {"key": "value"}, "test_value", ttl=3600)
        assert result is True
        cached_value = self.cache.get("test", {"key": "value"})
        assert cached_value == "test_value"

    def test_memory_cache_expiration(self):
        """Test cache expiration."""
        self.cache.set("test", {"key": "value"}, "test_value", ttl=1)
        cached_value = self.cache.get("test", {"key": "value"})
        assert cached_value == "test_value"
        import time

        time.sleep(1.1)
        cached_value = self.cache.get("test", {"key": "value"})
        assert cached_value is None

    def test_memory_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        for i in range(15):
            self.cache.set("test", {"key": f"value_{i}"}, f"test_value_{i}")
        assert self.cache.get("test", {"key": "value_0"}) is None
        assert self.cache.get("test", {"key": "value_1"}) is None
        assert self.cache.get("test", {"key": "value_14"}) == "test_value_14"

    def test_tenant_workspace_isolation(self):
        """Test tenant and workspace isolation."""
        self.cache.set("test", {"key": "value"}, "tenant1_value", tenant="tenant1", workspace="ws1")
        self.cache.set("test", {"key": "value"}, "tenant2_value", tenant="tenant2", workspace="ws1")
        value1 = self.cache.get("test", {"key": "value"}, tenant="tenant1", workspace="ws1")
        value2 = self.cache.get("test", {"key": "value"}, tenant="tenant2", workspace="ws1")
        assert value1 == "tenant1_value"
        assert value2 == "tenant2_value"
        assert value1 != value2

    def test_cache_delete(self):
        """Test cache deletion."""
        self.cache.set("test", {"key": "value"}, "test_value")
        assert self.cache.get("test", {"key": "value"}) == "test_value"
        result = self.cache.delete("test", {"key": "value"})
        assert result is True
        assert self.cache.get("test", {"key": "value"}) is None

    def test_cache_clear(self):
        """Test cache clearing."""
        self.cache.set("test1", {"key": "value1"}, "value1")
        self.cache.set("test2", {"key": "value2"}, "value2")
        assert self.cache.get("test1", {"key": "value1"}) == "value1"
        assert self.cache.get("test2", {"key": "value2"}) == "value2"
        result = self.cache.clear()
        assert result is True
        assert self.cache.get("test1", {"key": "value1"}) is None
        assert self.cache.get("test2", {"key": "value2"}) is None

    def test_cache_stats(self):
        """Test cache statistics."""
        self.cache.set("test1", {"key": "value1"}, "value1")
        self.cache.set("test2", {"key": "value2"}, "value2")
        stats = self.cache.get_stats()
        assert "memory_cache_size" in stats
        assert stats["memory_cache_size"] == 2
        assert "redis_available" in stats
        assert "disk_cache_enabled" in stats

    def test_health_check(self):
        """Test cache health check."""
        result = self.cache.health_check()
        assert result.success
        assert "status" in result.data
        assert result.data["status"] == "healthy"

    def test_serialization_complex_types(self):
        """Test serialization of complex types."""
        complex_value = {"list": [1, 2, 3], "dict": {"nested": "value"}, "tuple": (1, 2, 3)}
        self.cache.set("complex", {"key": "value"}, complex_value)
        cached_value = self.cache.get("complex", {"key": "value"})
        assert cached_value == complex_value

    @patch("redis.from_url")
    def test_redis_integration(self, mock_redis):
        """Test Redis integration when available."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_client.setex.return_value = True
        mock_redis.return_value = mock_client
        cache = MultiLevelCache(redis_url="redis://localhost:6379")
        result = cache.set("test", {"key": "value"}, "test_value")
        assert result is True
        cached_value = cache.get("test", {"key": "value"})
        assert cached_value is None

    def test_disk_cache_integration(self):
        """Test disk cache integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = MultiLevelCache(redis_url=None, enable_disk_cache=True, disk_cache_path=temp_dir)
            result = cache.set("test", {"key": "value"}, "test_value")
            assert result is True
            cached_value = cache.get("test", {"key": "value"})
            assert cached_value == "test_value"


class TestCachingService:
    """Test caching service functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("src.ultimate_discord_intelligence_bot.services.caching_service.get_settings"):
            self.service = CachingService()

    def test_transcription_caching(self):
        """Test transcription caching."""
        self.service.cache = Mock()
        self.service.cache.set.return_value = True
        self.service.cache.get.return_value = "cached_transcript"
        result = self.service.cache_transcription(
            "https://example.com/video", "transcript text", "tenant1", "workspace1"
        )
        assert result is True
        cached = self.service.get_cached_transcription("https://example.com/video", "tenant1", "workspace1")
        assert cached == "cached_transcript"

    def test_embedding_caching(self):
        """Test embedding caching."""
        self.service.cache = Mock()
        self.service.cache.set.return_value = True
        self.service.cache.get.return_value = [0.1, 0.2, 0.3]
        result = self.service.cache_embedding("test text", [0.1, 0.2, 0.3], "tenant1", "workspace1")
        assert result is True
        cached = self.service.get_cached_embedding("test text", "tenant1", "workspace1")
        assert cached == [0.1, 0.2, 0.3]

    def test_analysis_caching(self):
        """Test analysis caching."""
        self.service.cache = Mock()
        self.service.cache.set.return_value = True
        self.service.cache.get.return_value = {"score": 0.8, "sentiment": "positive"}
        analysis = {"score": 0.8, "sentiment": "positive"}
        result = self.service.cache_analysis("test content", analysis, "tenant1", "workspace1")
        assert result is True
        cached = self.service.get_cached_analysis("test content", "tenant1", "workspace1")
        assert cached == analysis

    def test_fact_check_caching(self):
        """Test fact check caching."""
        self.service.cache = Mock()
        self.service.cache.set.return_value = True
        self.service.cache.get.return_value = {"verified": True, "confidence": 0.9}
        fact_check = {"verified": True, "confidence": 0.9}
        result = self.service.cache_fact_check("test claim", fact_check, "tenant1", "workspace1")
        assert result is True
        cached = self.service.get_cached_fact_check("test claim", "tenant1", "workspace1")
        assert cached == fact_check

    def test_tenant_cache_clearing(self):
        """Test tenant cache clearing."""
        self.service.cache = Mock()
        self.service.cache.clear.return_value = True
        result = self.service.clear_tenant_cache("tenant1", "workspace1")
        assert result is True
        self.service.cache.clear.assert_called_once_with("tenant1", "workspace1")

    def test_cache_stats(self):
        """Test cache statistics."""
        self.service.cache = Mock()
        self.service.cache.get_stats.return_value = {"memory_cache_size": 10}
        stats = self.service.get_cache_stats()
        assert stats == {"memory_cache_size": 10}

    def test_health_check(self):
        """Test cache health check."""
        self.service.cache = Mock()
        self.service.cache.health_check.return_value = StepResult.ok(data={"status": "healthy"})
        result = self.service.health_check()
        assert result.success
        assert result.data["status"] == "healthy"

    def test_cache_not_initialized(self):
        """Test behavior when cache is not initialized."""
        self.service.cache = None
        assert self.service.cache_transcription("url", "transcript", "tenant", "workspace") is False
        assert self.service.get_cached_transcription("url", "tenant", "workspace") is None
        assert self.service.clear_tenant_cache("tenant", "workspace") is False
        assert self.service.get_cache_stats() == {"status": "disabled"}
        result = self.service.health_check()
        assert not result.success
        assert "not initialized" in result.error
