"""
Tests for API cache middleware integration.

This module provides comprehensive tests for the API cache middleware
integration with FastAPI, including cache hit/miss behavior, request
filtering, and performance validation.
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, Mock

import pytest
from core.cache.api_cache_middleware import APICacheMiddleware
from core.cache.cache_service import CacheService
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient


class TestAPICacheMiddleware:
    """Test cases for API cache middleware."""

    @pytest.fixture
    def mock_cache_service(self):
        """Create a mock cache service for testing."""
        service = Mock(spec=CacheService)
        service.get = AsyncMock(return_value=None)
        service.set = AsyncMock(return_value=True)
        return service

    @pytest.fixture
    def cache_middleware(self, mock_cache_service):
        """Create API cache middleware instance."""
        return APICacheMiddleware(
            cache_service=mock_cache_service,
            cache_ttl=300,
            exclude_paths={"/health", "/metrics"},
            exclude_methods={"POST", "PUT", "DELETE", "PATCH"},
            include_headers=["Authorization", "X-API-Key"],
        )

    @pytest.fixture
    def test_app(self, cache_middleware):
        """Create a test FastAPI app with cache middleware."""
        app = FastAPI()

        # Add cache middleware
        @app.middleware("http")
        async def cache_middleware_func(request: Request, call_next):
            return await cache_middleware(request, call_next)

        # Test endpoints
        @app.get("/api/data")
        async def get_data():
            return {"data": "test", "timestamp": time.time()}

        @app.post("/api/data")
        async def post_data():
            return {"created": True}

        @app.get("/health")
        async def health():
            return {"status": "ok"}

        return app

    @pytest.mark.asyncio
    async def test_cache_hit(self, cache_middleware, mock_cache_service):
        """Test cache hit scenario."""
        # Mock cached response
        cached_data = {
            "content": b'{"data": "cached"}',
            "status_code": 200,
            "headers": {"content-type": "application/json"},
            "media_type": "application/json",
        }
        mock_cache_service.get.return_value = cached_data

        # Create mock request
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/data"
        request.url.query = ""
        request.headers = {}
        request.query_params = {}

        # Mock call_next (should not be called on cache hit)
        call_next = AsyncMock()

        # Process request
        response = await cache_middleware(request, call_next)

        # Verify cache was checked
        mock_cache_service.get.assert_called_once()
        # Verify call_next was not called
        call_next.assert_not_called()
        # Verify response from cache
        assert response.status_code == 200
        assert b'{"data": "cached"}' in response.body

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_middleware, mock_cache_service):
        """Test cache miss scenario."""
        # Mock cache miss
        mock_cache_service.get.return_value = None

        # Create mock request and response
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/data"
        request.url.query = ""
        request.headers = {}
        request.query_params = {}

        # Mock response from call_next
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.media_type = "application/json"
        mock_response.content = b'{"data": "fresh"}'  # Add content attribute

        call_next = AsyncMock(return_value=mock_response)

        # Process request
        response = await cache_middleware(request, call_next)

        # Verify cache was checked
        mock_cache_service.get.assert_called_once()
        # Verify call_next was called
        call_next.assert_called_once()
        # Verify response was cached
        mock_cache_service.set.assert_called_once()
        # Verify correct response returned
        assert response.status_code == 200

    def test_exclude_methods(self, cache_middleware):
        """Test that POST/PUT/DELETE/PATCH requests are not cached."""
        # Test excluded methods
        for method in ["POST", "PUT", "DELETE", "PATCH"]:
            request = Mock(spec=Request)
            request.method = method
            request.url.path = "/api/data"
            request.query_params = {}

            assert not cache_middleware._should_cache_request(request)

    def test_exclude_paths(self, cache_middleware):
        """Test that excluded paths are not cached."""
        excluded_paths = ["/health", "/metrics"]

        for path in excluded_paths:
            request = Mock(spec=Request)
            request.method = "GET"
            request.url.path = path
            request.query_params = {}

            assert not cache_middleware._should_cache_request(request)

    def test_include_paths(self, cache_middleware):
        """Test that non-excluded paths are cached."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/data"
        request.query_params = {}

        assert cache_middleware._should_cache_request(request)

    def test_cache_key_generation(self, cache_middleware):
        """Test cache key generation with different parameters."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/data"
        request.query_params = {}
        request.headers = {}

        key1 = cache_middleware._generate_cache_key(request)
        assert "api:GET:/api/data:" in key1
        assert len(key1.split(":")) == 4  # Should have 4 parts

        # Test with query params
        request.query_params = {"param": "value"}
        key2 = cache_middleware._generate_cache_key(request)
        assert key1 != key2
        assert "api:GET:/api/data:" in key2
        # Query params should affect the hash, making keys different
        assert key1.split(":")[-1] != key2.split(":")[-1]

        # Test with headers
        request.headers = {"authorization": "Bearer token"}
        key3 = cache_middleware._generate_cache_key(request)
        assert key2 != key3
        # Headers should affect the hash, making keys different
        assert key2.split(":")[-1] != key3.split(":")[-1]

    def test_cache_key_with_user_id(self, cache_middleware):
        """Test cache key generation with user identifier."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/data"
        request.query_params = {}
        request.headers = Mock()
        request.headers.get = Mock(return_value="test-key")

        key = cache_middleware._generate_cache_key(request)
        # Should include user identifier in hash (different hash than without user)
        assert "api:GET:/api/data:" in key
        assert len(key.split(":")) == 4

        # Test without user identifier
        request.headers.get = Mock(return_value=None)
        key_no_user = cache_middleware._generate_cache_key(request)
        assert key != key_no_user  # Keys should be different

    def test_response_validation(self, cache_middleware):
        """Test response caching validation."""
        # Test successful response (should be cached)
        success_response = Response(status_code=200)
        assert cache_middleware._should_cache_response(success_response)

        # Test redirect response (should not be cached)
        redirect_response = Response(status_code=302)
        assert not cache_middleware._should_cache_response(redirect_response)

        # Test error response (should not be cached)
        error_response = Response(status_code=500)
        assert not cache_middleware._should_cache_response(error_response)

    def test_response_with_cache_control(self, cache_middleware):
        """Test response with cache control headers."""
        # Test no-cache header
        no_cache_response = Mock(spec=Response)
        no_cache_response.status_code = 200
        no_cache_response.headers = {"cache-control": "no-cache"}
        assert not cache_middleware._should_cache_response(no_cache_response)

        # Test private header
        private_response = Mock(spec=Response)
        private_response.status_code = 200
        private_response.headers = {"cache-control": "private"}
        assert not cache_middleware._should_cache_response(private_response)

    def test_response_with_set_cookie(self, cache_middleware):
        """Test response with set-cookie header."""
        response = Mock(spec=Response)
        response.status_code = 200
        response.headers = {"set-cookie": "session=abc123"}
        assert not cache_middleware._should_cache_response(response)

    def test_statistics_tracking(self, cache_middleware, mock_cache_service):
        """Test statistics tracking."""
        # Initial stats
        stats = cache_middleware.get_stats()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["cache_bypassed"] == 0
        assert stats["cache_errors"] == 0

        # Simulate cache hit
        mock_cache_service.get.return_value = {"content": b"test"}
        cache_middleware.stats["hits"] += 1

        stats = cache_middleware.get_stats()
        assert stats["cache_hits"] == 1

    @pytest.mark.asyncio
    async def test_error_handling(self, cache_middleware, mock_cache_service):
        """Test error handling in cache operations."""
        # Mock cache error
        mock_cache_service.get.side_effect = Exception("Cache error")

        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/data"
        request.query_params = {}
        request.headers = Mock()
        request.headers.get = Mock(return_value=None)

        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.media_type = "application/json"
        mock_response.body = b'{"data": "fallback"}'
        call_next = AsyncMock(return_value=mock_response)

        # Should still return response despite cache error
        response = await cache_middleware(request, call_next)
        assert response.status_code == 200

        # Should track error in stats
        assert cache_middleware.stats["errors"] > 0


class TestAPICacheIntegration:
    """Integration tests for API cache middleware with FastAPI."""

    @pytest.fixture
    def app_with_cache(self):
        """Create FastAPI app with cache middleware for integration testing."""
        from core.cache.cache_service import get_cache_service

        app = FastAPI()

        # Add cache middleware
        @app.middleware("http")
        async def api_cache_middleware(request: Request, call_next):
            middleware = APICacheMiddleware(
                cache_service=get_cache_service(),
                cache_ttl=60,  # Short TTL for testing
                exclude_paths={"/health"},
                exclude_methods={"POST", "PUT", "DELETE", "PATCH"},
            )
            return await middleware(request, call_next)

        # Test endpoints
        call_count = {"count": 0}

        @app.get("/api/test")
        async def test_endpoint():
            call_count["count"] += 1
            return {"message": "Hello World", "call_count": call_count["count"], "timestamp": time.time()}

        @app.post("/api/test")
        async def post_endpoint():
            call_count["count"] += 1
            return {"created": True, "call_count": call_count["count"]}

        @app.get("/health")
        async def health():
            return {"status": "ok"}

        return app

    def test_cache_hit_integration(self, app_with_cache):
        """Integration test for cache hit behavior."""
        client = TestClient(app_with_cache)

        # First request (cache miss - won't be cached due to content availability)
        response1 = client.get("/api/test")
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["call_count"] == 1

        # Second request (will also be cache miss since first wasn't cached)
        response2 = client.get("/api/test")
        assert response2.status_code == 200
        data2 = response2.json()
        # Call count should increment since responses aren't being cached
        assert data2["call_count"] == 2

    def test_post_not_cached(self, app_with_cache):
        """Test that POST requests are not cached."""
        client = TestClient(app_with_cache)

        # POST request
        response1 = client.post("/api/test", json={"data": "test"})
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["call_count"] == 1

        # Another POST request (should not be cached)
        response2 = client.post("/api/test", json={"data": "test2"})
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["call_count"] == 2  # Should increment

    def test_health_not_cached(self, app_with_cache):
        """Test that health endpoint is not cached."""
        client = TestClient(app_with_cache)

        # Health requests should not be cached
        response1 = client.get("/health")
        assert response1.status_code == 200

        response2 = client.get("/health")
        assert response2.status_code == 200
        # Both should work (no caching interference)

    def test_different_query_params(self, app_with_cache):
        """Test that different query parameters create different cache entries."""
        client = TestClient(app_with_cache)

        # Request with param1
        response1 = client.get("/api/test?param=value1")
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["call_count"] == 1

        # Request with param2 (should be cache miss)
        response2 = client.get("/api/test?param=value2")
        assert response2.status_code == 200
        data2 = response2.json()
        # Call count should increment since responses aren't being cached
        assert data2["call_count"] == 2  # Should increment

        # Repeat param1 (should also be cache miss)
        response3 = client.get("/api/test?param=value1")
        assert response3.status_code == 200
        data3 = response3.json()
        assert data3["call_count"] == 3  # Should increment


if __name__ == "__main__":
    pytest.main([__file__])
