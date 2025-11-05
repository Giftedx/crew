"""Tests for cold-start priors service with cross-tenant retrieval."""

import json
from unittest.mock import Mock, patch

import pytest

from platform.llm.routing.bandits.cold_start_priors import (
    ColdStartPriorService,
    ModelPrior,
)


class TestColdStartPriorService:
    """Test suite for ColdStartPriorService."""

    def test_initialization_without_redis(self):
        """Test service initialization when Redis is not available."""
        with patch("platform.llm.routing.bandits.cold_start_priors.REDIS_AVAILABLE", False):
            service = ColdStartPriorService()
            assert service._redis_client is None
            assert service._enabled is True

    def test_initialization_with_redis_enabled(self):
        """Test service initialization with Redis enabled."""
        with patch("platform.llm.routing.bandits.cold_start_priors.REDIS_AVAILABLE", True):
            mock_redis = Mock()
            mock_redis.ping.return_value = True
            with patch("platform.llm.routing.bandits.cold_start_priors.redis.from_url", return_value=mock_redis):
                service = ColdStartPriorService(enable_cross_tenant=True)
                assert service._redis_client is not None

    def test_cross_tenant_prior_without_redis(self):
        """Test cross-tenant prior falls back to uniform when Redis unavailable."""
        service = ColdStartPriorService()
        service._redis_client = None
        service._enable_cross_tenant = True

        prior = service._cross_tenant_prior("test-model", "tenant1")

        assert prior.source == "uniform"
        assert prior.confidence == 0.0

    def test_cross_tenant_prior_with_redis_no_data(self):
        """Test cross-tenant prior when no data exists in Redis."""
        mock_redis = Mock()
        mock_redis.get.return_value = None

        service = ColdStartPriorService()
        service._redis_client = mock_redis
        service._enable_cross_tenant = True

        prior = service._cross_tenant_prior("test-model", "tenant1")

        assert prior.source == "uniform"
        assert prior.confidence == 0.0
        mock_redis.get.assert_called_once_with("bandit:cross_tenant:test-model")

    def test_cross_tenant_prior_with_valid_data(self):
        """Test cross-tenant prior with valid Redis data."""
        mock_redis = Mock()
        aggregate_data = {
            "mean_reward": 0.85,
            "variance": 0.02,
            "sample_count": 100,
            "updated_at": "2025-01-05T12:00:00Z",
        }
        mock_redis.get.return_value = json.dumps(aggregate_data)

        service = ColdStartPriorService(prior_confidence=0.5)
        service._redis_client = mock_redis
        service._enable_cross_tenant = True

        prior = service._cross_tenant_prior("test-model", "tenant1")

        assert prior.source == "cross_tenant"
        assert prior.mean_reward == 0.85
        assert prior.variance == 0.02
        assert prior.sample_count == 100
        assert prior.confidence == 0.5

    def test_cross_tenant_prior_insufficient_samples(self):
        """Test cross-tenant prior rejects data with insufficient samples."""
        mock_redis = Mock()
        aggregate_data = {
            "mean_reward": 0.85,
            "variance": 0.02,
            "sample_count": 5,  # Less than minimum of 10
            "updated_at": "2025-01-05T12:00:00Z",
        }
        mock_redis.get.return_value = json.dumps(aggregate_data)

        service = ColdStartPriorService()
        service._redis_client = mock_redis
        service._enable_cross_tenant = True

        prior = service._cross_tenant_prior("test-model", "tenant1")

        assert prior.source == "uniform"
        assert prior.confidence == 0.0

    def test_cross_tenant_prior_caching(self):
        """Test that cross-tenant priors are cached."""
        mock_redis = Mock()
        aggregate_data = {
            "mean_reward": 0.85,
            "variance": 0.02,
            "sample_count": 100,
            "updated_at": "2025-01-05T12:00:00Z",
        }
        mock_redis.get.return_value = json.dumps(aggregate_data)

        service = ColdStartPriorService()
        service._redis_client = mock_redis
        service._enable_cross_tenant = True

        # First call
        prior1 = service._cross_tenant_prior("test-model", "tenant1")
        # Second call should use cache
        prior2 = service._cross_tenant_prior("test-model", "tenant1")

        assert prior1.source == "cross_tenant"
        assert prior2.source == "cross_tenant"
        # Redis should only be called once
        mock_redis.get.assert_called_once()

    def test_cross_tenant_prior_invalid_json(self):
        """Test cross-tenant prior handles invalid JSON gracefully."""
        mock_redis = Mock()
        mock_redis.get.return_value = "invalid json data"

        service = ColdStartPriorService()
        service._redis_client = mock_redis
        service._enable_cross_tenant = True

        prior = service._cross_tenant_prior("test-model", "tenant1")

        assert prior.source == "uniform"
        assert prior.confidence == 0.0

    def test_store_cross_tenant_aggregate_success(self):
        """Test storing cross-tenant aggregate to Redis."""
        mock_redis = Mock()
        mock_redis.setex.return_value = True

        service = ColdStartPriorService()
        service._redis_client = mock_redis
        service._enable_cross_tenant = True

        result = service.store_cross_tenant_aggregate(
            model_name="test-model",
            mean_reward=0.85,
            variance=0.02,
            sample_count=100,
            ttl_seconds=3600,
        )

        assert result is True
        mock_redis.setex.assert_called_once()
        # Verify the key format
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "bandit:cross_tenant:test-model"
        assert call_args[0][1] == 3600

    def test_store_cross_tenant_aggregate_without_redis(self):
        """Test storing cross-tenant aggregate fails gracefully without Redis."""
        service = ColdStartPriorService()
        service._redis_client = None
        service._enable_cross_tenant = True

        result = service.store_cross_tenant_aggregate(
            model_name="test-model",
            mean_reward=0.85,
            variance=0.02,
            sample_count=100,
        )

        assert result is False

    def test_store_cross_tenant_aggregate_disabled(self):
        """Test storing cross-tenant aggregate when feature is disabled."""
        mock_redis = Mock()

        service = ColdStartPriorService(enable_cross_tenant=False)
        service._redis_client = mock_redis

        result = service.store_cross_tenant_aggregate(
            model_name="test-model",
            mean_reward=0.85,
            variance=0.02,
            sample_count=100,
        )

        assert result is False
        mock_redis.setex.assert_not_called()

    def test_get_prior_for_model_uses_cross_tenant(self):
        """Test that get_prior_for_model uses cross-tenant data when available."""
        mock_redis = Mock()
        aggregate_data = {
            "mean_reward": 0.85,
            "variance": 0.02,
            "sample_count": 100,
            "updated_at": "2025-01-05T12:00:00Z",
        }
        mock_redis.get.return_value = json.dumps(aggregate_data)

        service = ColdStartPriorService(prior_confidence=0.8)
        service._redis_client = mock_redis
        service._enable_cross_tenant = True

        alpha, beta = service.get_prior_for_model("unknown-model", tenant="tenant1")

        # Should use cross-tenant data and convert to beta params
        # With confidence=0.8 and mean=0.85, alpha should be ~68, beta ~12
        assert alpha > 1.0  # Should be informative prior
        assert beta > 1.0
        # Mean of beta distribution should be close to 0.85
        mean = alpha / (alpha + beta)
        assert abs(mean - 0.85) < 0.05

    def test_priority_order_benchmark_over_cross_tenant(self):
        """Test that benchmark data takes priority over cross-tenant data."""
        # Create a mock benchmark file
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "test-model": {
                    "mean_reward": 0.9,
                    "variance": 0.01,
                    "sample_count": 500,
                }
            }, f)
            benchmark_path = f.name

        mock_redis = Mock()
        aggregate_data = {
            "mean_reward": 0.7,  # Different from benchmark
            "variance": 0.03,
            "sample_count": 100,
        }
        mock_redis.get.return_value = json.dumps(aggregate_data)

        service = ColdStartPriorService(
            benchmark_path=benchmark_path,
            enable_cross_tenant=True,
            prior_confidence=0.5,
        )
        service._redis_client = mock_redis

        prior = service._compute_prior("test-model", None, "tenant1")

        # Should use benchmark data, not cross-tenant
        assert prior.source == "benchmark"
        assert prior.mean_reward == 0.9

        # Cleanup
        import os
        os.unlink(benchmark_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
