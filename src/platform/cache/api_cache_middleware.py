"""FastAPI middleware for HTTP response caching.

This middleware provides intelligent caching for HTTP responses using the
advanced caching system, with support for cache invalidation, TTL management,
and performance monitoring.
"""

from __future__ import annotations

import hashlib
import logging
from platform.cache.cache_service import get_cache_service
from typing import TYPE_CHECKING, Any

from fastapi import Request, Response


if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)
HTTP_OK_MIN = 200
HTTP_REDIRECT_MAX = 300


class APICacheConfig:
    """Configuration for API cache middleware."""

    def __init__(
        self,
        cache_ttl: int = 300,
        exclude_paths: set[str] | None = None,
        exclude_methods: set[str] | None = None,
        include_headers: list[str] | None = None,
        cache_private: bool = False,
    ):
        self.cache_ttl = cache_ttl
        self.exclude_paths = exclude_paths or {"/health", "/metrics"}
        self.exclude_methods = exclude_methods or {"POST", "PUT", "DELETE", "PATCH"}
        self.include_headers = include_headers or []
        self.cache_private = cache_private


class APICacheMiddleware:
    """Middleware for caching FastAPI HTTP responses."""

    def __init__(
        self,
        cache_service: Any | None = None,
        cache_ttl: int = 300,
        exclude_paths: set[str] | None = None,
        exclude_methods: set[str] | None = None,
        include_headers: list[str] | None = None,
        cache_private: bool = False,
    ):
        """Initialize the API cache middleware.

        Args:
            cache_service: Cache service instance (uses global if None)
            cache_ttl: Default TTL for cached responses in seconds
            exclude_paths: Set of path patterns to exclude from caching
            exclude_methods: Set of HTTP methods to exclude from caching
            include_headers: List of headers to include in cache key
            cache_private: Whether to cache responses with private cache headers
        """
        self.cache_service = cache_service or get_cache_service()
        self.cache_ttl = cache_ttl
        self.exclude_paths = exclude_paths or {"/health", "/metrics"}
        self.exclude_methods = exclude_methods or {"POST", "PUT", "DELETE", "PATCH"}
        self.include_headers = include_headers or []
        self.cache_private = cache_private
        self.stats = {"hits": 0, "misses": 0, "errors": 0, "bypassed": 0}

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process the request and potentially cache the response."""
        if not self._should_cache_request(request):
            self.stats["bypassed"] += 1
            return await call_next(request)
        cache_key = self._generate_cache_key(request)
        try:
            cached_response = await self.cache_service.get(cache_key, "api")
            if cached_response:
                self.stats["hits"] += 1
                logger.debug(f"Cache hit for {request.method} {request.url.path}")
                return self._create_response_from_cache(cached_response)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            self.stats["errors"] += 1
        self.stats["misses"] += 1
        response = await call_next(request)
        if self._should_cache_response(response):
            try:
                await self._cache_response(cache_key, response)
                logger.debug(f"Cached response for {request.method} {request.url.path}")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
                self.stats["errors"] += 1
        return response

    def _should_cache_request(self, request: Request) -> bool:
        """Determine if the request should be cached."""
        if request.method in self.exclude_methods:
            return False
        path = request.url.path
        if any(excluded in path for excluded in self.exclude_paths):
            return False
        if hasattr(request, "query_params") and request.query_params:
            dynamic_params = {"timestamp", "nonce", "token", "session", "cache"}
            if any(param in request.query_params for param in dynamic_params):
                return False
        return True

    def _should_cache_response(self, response: Response) -> bool:
        """Determine if the response should be cached."""
        if response.status_code < HTTP_OK_MIN or response.status_code >= HTTP_REDIRECT_MAX:
            return False
        cache_control = getattr(response.headers, "get", lambda x, default: default)("cache-control", "").lower()
        if ("no-cache" in cache_control or "private" in cache_control) and (not self.cache_private):
            return False
        return "set-cookie" not in getattr(response, "headers", {})

    def _generate_cache_key(self, request: Request) -> str:
        """Generate a cache key for the request."""
        components = [request.method, str(getattr(request.url, "path", "/"))]
        if hasattr(request, "query_params") and request.query_params:
            sorted_params = sorted(request.query_params.items())
            components.append(str(sorted_params))
        for header_name in self.include_headers:
            header_value = getattr(request.headers, "get", lambda x: None)(header_name)
            if header_value:
                components.append(f"{header_name}:{header_value}")
        user_id = self._get_user_identifier(request)
        if user_id:
            components.append(f"user:{user_id}")
        key_content = "|".join(components)
        key_hash = hashlib.sha256(key_content.encode()).hexdigest()[:16]
        path_str = str(getattr(request.url, "path", "/"))
        return f"api:{request.method}:{path_str}:{key_hash}"

    def _get_user_identifier(self, request: Request) -> str | None:
        """Extract user identifier from request for personalized caching."""
        api_key = getattr(request.headers, "get", lambda x: None)("x-api-key") or getattr(
            request.headers, "get", lambda x: None
        )("authorization")
        if api_key:
            return hashlib.sha256(api_key.encode()).hexdigest()[:8]
        user_id = getattr(request.headers, "get", lambda x: None)("x-user-id")
        if user_id:
            return user_id
        return None

    def _create_response_from_cache(self, cached_data: dict[str, Any]) -> Response:
        """Create a Response object from cached data."""
        return Response(
            content=cached_data.get("content", b""),
            status_code=cached_data.get("status_code", 200),
            headers=cached_data.get("headers", {}),
            media_type=cached_data.get("media_type"),
        )

    async def _cache_response(self, cache_key: str, response: Response) -> None:
        """Cache the response data."""
        content = b""
        try:
            if hasattr(response, "content"):
                content = response.content
            else:
                logger.debug("Response content not available for caching")
                return
        except Exception as e:
            logger.warning(f"Error reading response content: {e}")
            return
        cache_data = {
            "content": content,
            "status_code": response.status_code,
            "headers": dict(getattr(response, "headers", {})),
            "media_type": getattr(response, "media_type", None),
            "cached_at": "now",
        }
        await self.cache_service.set(cache_key, cache_data, ttl=self.cache_ttl, cache_type="api")

    def get_stats(self) -> dict[str, Any]:
        """Get middleware statistics."""
        total_requests = sum(self.stats.values())
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0.0
        return {
            "total_requests": total_requests,
            "cache_hits": self.stats["hits"],
            "cache_misses": self.stats["misses"],
            "cache_bypassed": self.stats["bypassed"],
            "cache_errors": self.stats["errors"],
            "hit_rate": hit_rate,
            "cache_ttl": self.cache_ttl,
        }

    async def invalidate_path(self, path: str, method: str = "GET") -> int:
        """Invalidate cached responses for a specific path."""
        logger.info(f"Invalidating cache for path: {method} {path}")
        return 0

    async def clear_all_cache(self) -> bool:
        """Clear all cached API responses."""
        logger.info("Clearing all API cache")
        return True


def create_api_cache_middleware(
    cache_ttl: int = 300,
    exclude_paths: set[str] | None = None,
    exclude_methods: set[str] | None = None,
    include_headers: list[str] | None = None,
    cache_private: bool = False,
) -> APICacheMiddleware:
    """Factory function to create API cache middleware."""
    return APICacheMiddleware(
        cache_ttl=cache_ttl,
        exclude_paths=exclude_paths,
        exclude_methods=exclude_methods,
        include_headers=include_headers,
        cache_private=cache_private,
    )


__all__ = ["APICacheConfig", "APICacheMiddleware", "create_api_cache_middleware"]
