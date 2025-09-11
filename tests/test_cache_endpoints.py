"""
Tests for cache management endpoints.
"""

import pytest
from core.cache.cache_endpoints import router
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def test_app():
    """Create a test FastAPI app with cache endpoints."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


class TestCacheEndpoints:
    """Test cases for cache management endpoints."""

    def test_get_cache_stats(self, client):
        """Test getting cache statistics."""
        response = client.get("/api/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "cache_hits" in data
        assert "hit_rate" in data

    def test_invalidate_cache(self, client):
        """Test cache invalidation endpoint."""
        request_data = {"path": "/api/data", "method": "GET"}
        response = client.post("/api/cache/invalidate", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "invalidated_keys" in data
        assert "message" in data

    def test_clear_cache(self, client):
        """Test clearing all cache."""
        response = client.post("/api/cache/clear")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "cleared" in data

    def test_cache_health_check(self, client):
        """Test cache health check endpoint."""
        response = client.get("/api/cache/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "cache_service" in data


if __name__ == "__main__":
    pytest.main([__file__])
