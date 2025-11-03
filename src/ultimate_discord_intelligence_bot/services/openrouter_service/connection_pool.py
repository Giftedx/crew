"""HTTP connection pooling for OpenRouter API requests.

This module provides connection pooling capabilities to reduce latency
and improve performance for concurrent OpenRouter API requests.

Note: This module creates Sessions that are passed as request_fn to
http_utils wrappers, which is compliant with HTTP wrapper policy.
"""

from __future__ import annotations

import logging
import threading
from platform import http_utils
from platform.observability.metrics import get_metrics
from typing import Any

from app.config.feature_flags import FeatureFlags
from requests import RequestException  # http-compliance: allow-direct-requests (exception type import only)


log = logging.getLogger(__name__)


class ConnectionPool:
    """Manages HTTP connection pool for OpenRouter API requests.

    This class provides connection pooling, retry strategies, and
    performance monitoring for HTTP requests to the OpenRouter API.
    """

    def __init__(
        self,
        pool_size: int = 10,
        max_retries: int = 3,
        backoff_factor: float = 0.3,
        status_forcelist: tuple[int, ...] = (500, 502, 504),
        keepalive: int = 30,
    ) -> None:
        """Initialize connection pool.

        Args:
            pool_size: Maximum number of connections in the pool
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retry delays
            status_forcelist: HTTP status codes that should trigger retries
            keepalive: Keep-alive timeout in seconds
        """
        self._pool_size = pool_size
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor
        self._status_forcelist = status_forcelist
        self._keepalive = keepalive
        self._session: http_utils.requests.Session | None = None
        self._lock = threading.RLock()
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retry_attempts": 0,
            "connection_reuses": 0,
        }
        self._metrics = get_metrics()

    def _create_session(self) -> http_utils.requests.Session:
        """Create a new session with connection pooling."""
        session = http_utils.requests.Session()
        retry_strategy = http_utils.requests.packages.urllib3.util.retry.Retry(
            total=self._max_retries,
            backoff_factor=self._backoff_factor,
            status_forcelist=self._status_forcelist,
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"],
        )
        adapter = http_utils.requests.adapters.HTTPAdapter(
            pool_connections=self._pool_size, pool_maxsize=self._pool_size, pool_block=False, max_retries=retry_strategy
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({"Connection": "keep-alive", "Keep-Alive": f"timeout={self._keepalive}, max=1000"})
        return session

    def _record_request_metric(self, method: str, status: str) -> None:
        """Record request metrics to Prometheus.

        Args:
            method: HTTP method (get/post)
            status: Request status (success/failed/exception)
        """
        if self._metrics:
            self._metrics.counter(
                "openrouter_connection_pool_requests_total",
                labels={"method": method, "pool_size": str(self._pool_size), "status": status},
            ).inc()

    def _record_connection_reuse_metric(self) -> None:
        """Record connection reuse metric to Prometheus."""
        if self._metrics:
            self._metrics.counter(
                "openrouter_connection_pool_reuses_total", labels={"pool_size": str(self._pool_size)}
            ).inc()

    def get_session(self) -> http_utils.requests.Session:
        """Get or create a session with connection pooling."""
        with self._lock:
            if self._session is None:
                self._session = self._create_session()
                log.debug("Created new HTTP session with connection pooling")
            return self._session

    def post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json_payload: dict[str, Any] | None = None,
        timeout: int = 30,
        **kwargs: Any,
    ) -> http_utils.requests.Response | None:
        """Make a POST request using the connection pool.

        Args:
            url: The URL to make the request to
            headers: HTTP headers
            json_payload: JSON payload for the request
            timeout: Request timeout in seconds
            **kwargs: Additional request parameters

        Returns:
            Response object or None if request failed
        """
        session = self.get_session()
        try:
            self._stats["total_requests"] += 1
            self._record_request_metric("post", "attempted")
            response = http_utils.retrying_post(
                url,
                json_payload=json_payload,
                headers=headers,
                timeout_seconds=timeout,
                request_callable=lambda u, **_: http_utils.resilient_post(
                    u, json_payload=json_payload, headers=headers, timeout_seconds=timeout, request_fn=session.post
                ),
            )
            if response and getattr(response, "status_code", 500) < 400:
                self._stats["successful_requests"] += 1
                self._record_request_metric("post", "success")
                log.debug("Request successful: %s", response.status_code)
            else:
                self._stats["failed_requests"] += 1
                self._record_request_metric("post", "failed")
                log.warning("Request failed: %s", getattr(response, "status_code", "No response"))
            return response
        except RequestException as e:
            self._stats["failed_requests"] += 1
            self._record_request_metric("post", "exception")
            log.error("Request exception: %s", e)
            return None

    def get(
        self, url: str, headers: dict[str, str] | None = None, timeout: int = 30, **kwargs: Any
    ) -> http_utils.requests.Response | None:
        """Make a GET request using the connection pool.

        Args:
            url: The URL to make the request to
            headers: HTTP headers
            timeout: Request timeout in seconds
            **kwargs: Additional request parameters

        Returns:
            Response object or None if request failed
        """
        session = self.get_session()
        try:
            self._stats["total_requests"] += 1
            response = http_utils.retrying_get(
                url,
                headers=headers,
                timeout_seconds=timeout,
                request_callable=lambda u, **_: http_utils.resilient_get(
                    u, headers=headers, timeout_seconds=timeout, request_fn=session.get
                ),
            )
            if response and getattr(response, "status_code", 500) < 400:
                self._stats["successful_requests"] += 1
                log.debug("Request successful: %s", response.status_code)
            else:
                self._stats["failed_requests"] += 1
                log.warning("Request failed: %s", getattr(response, "status_code", "No response"))
            return response
        except RequestException as e:
            self._stats["failed_requests"] += 1
            log.error("Request exception: %s", e)
            return None

    def close(self) -> None:
        """Close the connection pool and cleanup resources."""
        with self._lock:
            if self._session:
                self._session.close()
                self._session = None
                log.debug("Closed HTTP session and connection pool")

    def get_stats(self) -> dict[str, Any]:
        """Get connection pool statistics.

        Returns:
            Dictionary containing pool statistics
        """
        with self._lock:
            total = self._stats["total_requests"]
            success_rate = self._stats["successful_requests"] / total * 100 if total > 0 else 0
            return {
                **self._stats,
                "success_rate_percent": round(success_rate, 2),
                "pool_size": self._pool_size,
                "max_retries": self._max_retries,
            }

    def reset_stats(self) -> None:
        """Reset connection pool statistics."""
        with self._lock:
            self._stats = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "retry_attempts": 0,
                "connection_reuses": 0,
            }


class ConnectionPoolManager:
    """Manages connection pools for different services and endpoints."""

    def __init__(self) -> None:
        """Initialize connection pool manager."""
        self._pools: dict[str, ConnectionPool] = {}
        self._lock = threading.RLock()
        self._feature_flags = FeatureFlags()

    def get_pool(self, service_name: str = "openrouter", pool_size: int | None = None, **kwargs: Any) -> ConnectionPool:
        """Get or create a connection pool for a service.

        Args:
            service_name: Name of the service (used as pool key)
            pool_size: Override default pool size
            **kwargs: Additional pool configuration

        Returns:
            ConnectionPool instance for the service
        """
        with self._lock:
            if service_name not in self._pools:
                if not self._feature_flags.ENABLE_OPENROUTER_CONNECTION_POOLING:
                    self._pools[service_name] = MockConnectionPool()
                else:
                    pool_config = {"pool_size": pool_size or 10, **kwargs}
                    self._pools[service_name] = ConnectionPool(**pool_config)
                log.debug("Created connection pool for service: %s", service_name)
            return self._pools[service_name]

    def close_all(self) -> None:
        """Close all connection pools."""
        with self._lock:
            for pool in self._pools.values():
                pool.close()
            self._pools.clear()
            log.debug("Closed all connection pools")

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all connection pools.

        Returns:
            Dictionary mapping service names to their pool statistics
        """
        with self._lock:
            return {service_name: pool.get_stats() for service_name, pool in self._pools.items()}


class MockConnectionPool:
    """Mock connection pool for when pooling is disabled.

    This class provides the same interface as ConnectionPool but
    doesn't actually pool connections, maintaining backward compatibility.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize mock connection pool."""
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retry_attempts": 0,
            "connection_reuses": 0,
        }

    def post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json_payload: dict[str, Any] | None = None,
        timeout: int = 30,
        **kwargs: Any,
    ) -> http_utils.requests.Response | None:
        """Make a POST request without connection pooling."""
        try:
            self._stats["total_requests"] += 1
            response = http_utils.retrying_post(
                url, json_payload=json_payload, headers=headers, timeout_seconds=timeout
            )
            if getattr(response, "status_code", 500) < 400:
                self._stats["successful_requests"] += 1
            else:
                self._stats["failed_requests"] += 1
            return response
        except RequestException as e:
            self._stats["failed_requests"] += 1
            log.error("Mock pool request exception: %s", e)
            return None

    def get(
        self, url: str, headers: dict[str, str] | None = None, timeout: int = 30, **kwargs: Any
    ) -> http_utils.requests.Response | None:
        """Make a GET request without connection pooling."""
        try:
            self._stats["total_requests"] += 1
            response = http_utils.retrying_get(url, headers=headers, timeout_seconds=timeout)
            if getattr(response, "status_code", 500) < 400:
                self._stats["successful_requests"] += 1
            else:
                self._stats["failed_requests"] += 1
            return response
        except RequestException as e:
            self._stats["failed_requests"] += 1
            log.error("Mock pool request exception: %s", e)
            return None

    def close(self) -> None:
        """Mock close method."""

    def get_stats(self) -> dict[str, Any]:
        """Get mock pool statistics."""
        total = self._stats["total_requests"]
        success_rate = self._stats["successful_requests"] / total * 100 if total > 0 else 0
        return {**self._stats, "success_rate_percent": round(success_rate, 2), "pool_type": "mock"}

    def reset_stats(self) -> None:
        """Reset mock pool statistics."""
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retry_attempts": 0,
            "connection_reuses": 0,
        }


_connection_pool_manager = ConnectionPoolManager()


def get_connection_pool(service_name: str = "openrouter", **kwargs: Any) -> ConnectionPool:
    """Get a connection pool for the specified service.

    Args:
        service_name: Name of the service
        **kwargs: Additional pool configuration

    Returns:
        ConnectionPool instance
    """
    return _connection_pool_manager.get_pool(service_name, **kwargs)


def close_all_connection_pools() -> None:
    """Close all connection pools."""
    _connection_pool_manager.close_all()


def get_connection_pool_stats() -> dict[str, dict[str, Any]]:
    """Get statistics for all connection pools.

    Returns:
        Dictionary mapping service names to their pool statistics
    """
    return _connection_pool_manager.get_all_stats()
