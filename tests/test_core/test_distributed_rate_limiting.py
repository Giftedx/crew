"""Tests for distributed rate limiting functionality."""

from __future__ import annotations

import time
from unittest.mock import Mock, patch

import pytest

from core.rate_limiting import DistributedRateLimiter, RedisBackend


class TestDistributedRateLimiter:
    """Test distributed rate limiter functionality."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client for testing."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.eval.return_value = [1, 50]  # allowed=True, remaining=50
        return mock_client

    @pytest.fixture
    def limiter(self, mock_redis):
        """Create rate limiter with mocked Redis."""
        with patch("redis.from_url", return_value=mock_redis):
            return DistributedRateLimiter(
                redis_url="redis://localhost:6379",
                default_capacity=60,
                default_refill_per_sec=1.0,
                fallback_to_local=True,
            )

    def test_initialization_success(self, mock_redis):
        """Test successful initialization."""
        with patch("redis.from_url", return_value=mock_redis):
            limiter = DistributedRateLimiter("redis://localhost:6379")
            assert limiter.redis_available
            assert limiter.redis_client is not None

    def test_initialization_failure(self):
        """Test initialization with Redis connection failure."""
        with patch("redis.from_url", side_effect=Exception("Connection failed")):
            limiter = DistributedRateLimiter("redis://localhost:6379")
            assert not limiter.redis_available
            assert limiter.redis_client is None

    def test_allowed_request(self, limiter):
        """Test allowed request."""
        result = limiter.is_allowed("test_key", cost=1)

        assert result.success
        assert result.data["allowed"] is True
        assert "remaining" in result.data

    def test_rate_limit_exceeded(self, limiter):
        """Test rate limit exceeded scenario."""
        # Mock Redis to return rate limit exceeded
        limiter.redis_client.eval.return_value = [0, 0]  # allowed=False, remaining=0

        result = limiter.is_allowed("test_key", cost=100)  # High cost

        assert not result.success
        assert result.data["allowed"] is False
        assert result.data["remaining"] == 0

    def test_local_fallback(self):
        """Test local fallback when Redis is unavailable."""
        limiter = DistributedRateLimiter(
            redis_url="redis://localhost:6379",
            default_capacity=10,
            default_refill_per_sec=1.0,
            fallback_to_local=True,
        )
        limiter.redis_available = False

        # First request should be allowed
        result1 = limiter.is_allowed("test_key", cost=1)
        assert result1.success
        assert result1.data["allowed"] is True

        # Second request should also be allowed (local bucket refills)
        result2 = limiter.is_allowed("test_key", cost=1)
        assert result2.success

    def test_local_fallback_disabled(self):
        """Test behavior when local fallback is disabled."""
        limiter = DistributedRateLimiter(
            redis_url="redis://localhost:6379",
            fallback_to_local=False,
        )
        limiter.redis_available = False

        # Request should be allowed when no fallback
        result = limiter.is_allowed("test_key")
        assert result.success
        assert result.data["allowed"] is True

    def test_custom_capacity_and_refill(self, limiter):
        """Test custom capacity and refill rate."""
        result = limiter.is_allowed(
            "test_key",
            cost=1,
            capacity=100,
            refill_per_sec=10.0,
        )

        assert result.success
        # Verify custom parameters were passed to Redis
        limiter.redis_client.eval.assert_called_once()
        call_args = limiter.redis_client.eval.call_args
        assert call_args[0][2] == 100  # capacity
        assert call_args[0][3] == 10.0  # refill_per_sec

    def test_get_remaining_tokens(self, limiter):
        """Test getting remaining tokens."""
        # Mock Redis response
        limiter.redis_client.hmget.return_value = ["45"]

        remaining = limiter.get_remaining_tokens("test_key")
        assert remaining == 45

    def test_get_remaining_tokens_fallback(self):
        """Test getting remaining tokens with local fallback."""
        limiter = DistributedRateLimiter("redis://localhost:6379")
        limiter.redis_available = False

        # Should return default capacity
        remaining = limiter.get_remaining_tokens("test_key")
        assert remaining == limiter.default_capacity

    def test_reset_bucket(self, limiter):
        """Test resetting a rate limit bucket."""
        # Mock Redis delete operation
        limiter.redis_client.delete.return_value = 1

        result = limiter.reset_bucket("test_key")
        assert result is True
        limiter.redis_client.delete.assert_called_once_with("rl:test_key")

    def test_reset_bucket_fallback(self):
        """Test resetting bucket with local fallback."""
        limiter = DistributedRateLimiter("redis://localhost:6379")
        limiter.redis_available = False

        # Add a local limiter
        limiter.local_limiters["test_key"] = {"tokens": 10, "last_refill": time.time()}

        result = limiter.reset_bucket("test_key")
        assert result is True
        assert "test_key" not in limiter.local_limiters

    def test_health_check_healthy(self, limiter):
        """Test health check when Redis is healthy."""
        result = limiter.health_check()

        assert result.success
        assert result.data["status"] == "healthy"
        assert result.data["backend"] == "redis"

    def test_health_check_degraded(self):
        """Test health check when Redis is unavailable."""
        limiter = DistributedRateLimiter("redis://localhost:6379")
        limiter.redis_available = False

        result = limiter.health_check()

        assert result.success
        assert result.data["status"] == "degraded"
        assert result.data["backend"] == "local"

    def test_redis_connection_error_handling(self, limiter):
        """Test handling of Redis connection errors."""
        # Mock Redis to raise connection error
        limiter.redis_client.eval.side_effect = Exception("Connection failed")

        # Should fallback to local
        result = limiter.is_allowed("test_key")
        assert result.success  # Should succeed with local fallback

    def test_concurrent_requests(self, limiter):
        """Test handling of concurrent requests."""
        import queue
        import threading

        results = queue.Queue()

        def worker():
            result = limiter.is_allowed("concurrent_test", cost=1)
            results.put(result)

        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All requests should succeed
        assert results.qsize() == 5
        while not results.empty():
            result = results.get()
            assert result.success


class TestRedisBackend:
    """Test Redis backend functionality."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for testing."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.hget.return_value = "50"
        mock_client.hset.return_value = True
        mock_client.hincrby.return_value = 45
        mock_client.delete.return_value = 1
        mock_client.keys.return_value = ["rl:key1", "rl:key2"]
        mock_client.hmget.return_value = ["50", "1234567890"]
        mock_client.info.return_value = {
            "connected_clients": 10,
            "used_memory": 1024000,
            "keyspace": {"db0": "keys=100,expires=10"},
        }
        return mock_client

    @pytest.fixture
    def redis_backend(self, mock_redis_client):
        """Create Redis backend with mocked client."""
        with patch("redis.from_url", return_value=mock_redis_client):
            return RedisBackend("redis://localhost:6379")

    def test_initialization_success(self, mock_redis_client):
        """Test successful initialization."""
        with patch("redis.from_url", return_value=mock_redis_client):
            backend = RedisBackend("redis://localhost:6379")
            assert backend.available
            assert backend.client is not None

    def test_initialization_failure(self):
        """Test initialization with connection failure."""
        with patch("redis.from_url", side_effect=Exception("Connection failed")):
            backend = RedisBackend("redis://localhost:6379")
            assert not backend.available
            assert backend.client is None

    def test_get_tokens(self, redis_backend):
        """Test getting tokens."""
        tokens = redis_backend.get_tokens("test_key")
        assert tokens == 50
        redis_backend.client.hget.assert_called_once_with("rl:test_key", "tokens")

    def test_set_tokens(self, redis_backend):
        """Test setting tokens."""
        result = redis_backend.set_tokens("test_key", 100)
        assert result is True
        redis_backend.client.hset.assert_called_once_with("rl:test_key", "tokens", 100)
        redis_backend.client.expire.assert_called_once_with("rl:test_key", 3600)

    def test_increment_tokens(self, redis_backend):
        """Test incrementing tokens."""
        result = redis_backend.increment_tokens("test_key", 10)
        assert result == 45
        redis_backend.client.hincrby.assert_called_once_with("rl:test_key", "tokens", 10)

    def test_decrement_tokens(self, redis_backend):
        """Test decrementing tokens."""
        result = redis_backend.decrement_tokens("test_key", 5)
        assert result == 45
        redis_backend.client.hincrby.assert_called_once_with("rl:test_key", "tokens", -5)

    def test_health_check(self, redis_backend):
        """Test health check."""
        result = redis_backend.health_check()
        assert result is True
        redis_backend.client.ping.assert_called_once()

    def test_get_stats(self, redis_backend):
        """Test getting statistics."""
        stats = redis_backend.get_stats()
        assert stats["status"] == "available"
        assert "connected_clients" in stats
        assert "used_memory" in stats

    def test_error_handling(self):
        """Test error handling when Redis is unavailable."""
        backend = RedisBackend("redis://localhost:6379")
        backend.available = False

        # All operations should return None or False
        assert backend.get_tokens("test_key") is None
        assert backend.set_tokens("test_key", 100) is False
        assert backend.increment_tokens("test_key", 10) is None
        assert backend.health_check() is False
