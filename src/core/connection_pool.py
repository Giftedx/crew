"""HTTP connection pooling implementation using aiohttp.

This module provides a centralized HTTP connection pool manager that can be used
across the application to improve performance by reusing HTTP connections.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any
from urllib.parse import urlparse

import aiohttp
from aiohttp import ClientSession, TCPConnector


class ConnectionPoolManager:
    """Manages HTTP connection pools for different hosts.

    This class provides a centralized way to manage HTTP connection pools
    using aiohttp, with configurable pool sizes and timeouts.
    """

    def __init__(self) -> None:
        """Initialize the connection pool manager."""
        self._sessions: dict[str, ClientSession] = {}
        self._connectors: dict[str, TCPConnector] = {}
        self._lock = asyncio.Lock()

        # Configuration from environment variables
        self.pool_size = int(os.getenv("HTTP_POOL_SIZE", "100"))
        self.max_connections_per_host = int(os.getenv("HTTP_MAX_CONNECTIONS_PER_HOST", "30"))
        self.keepalive_timeout = int(os.getenv("HTTP_KEEPALIVE_TIMEOUT", "30"))
        self.enable_cleanup_closed = os.getenv("HTTP_ENABLE_CLEANUP_CLOSED", "true").lower() == "true"

    async def get_session(self, url: str) -> ClientSession:
        """Get or create a ClientSession for the given URL.

        Args:
            url: The URL to create a session for

        Returns:
            ClientSession configured for the URL's host
        """
        parsed = urlparse(url)
        host_key = f"{parsed.scheme}://{parsed.netloc}"

        async with self._lock:
            if host_key not in self._sessions:
                # Create a new connector for this host
                connector = TCPConnector(
                    limit=self.pool_size,
                    limit_per_host=self.max_connections_per_host,
                    keepalive_timeout=self.keepalive_timeout,
                    enable_cleanup_closed=self.enable_cleanup_closed,
                    ttl_dns_cache=300,  # 5 minutes DNS cache
                    use_dns_cache=True,
                )

                # Create timeout configuration
                timeout = aiohttp.ClientTimeout(
                    total=30,  # Total timeout
                    connect=10,  # Connection timeout
                    sock_read=30,  # Socket read timeout
                )

                # Create session with connector and timeout
                session = ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={
                        "User-Agent": "UltimateDiscordIntelligenceBot/1.0",
                        "Connection": "keep-alive",
                    },
                )

                self._connectors[host_key] = connector
                self._sessions[host_key] = session

            return self._sessions[host_key]

    async def close_all(self) -> None:
        """Close all active sessions and connectors."""
        async with self._lock:
            # Close all sessions
            for session in self._sessions.values():
                if not session.closed:
                    await session.close()

            # Close all connectors
            for connector in self._connectors.values():
                if not connector.closed:
                    await connector.close()

            self._sessions.clear()
            self._connectors.clear()

    async def __aenter__(self) -> ConnectionPoolManager:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close_all()


# Global connection pool manager instance
_connection_pool_manager: ConnectionPoolManager | None = None


async def get_connection_pool_manager() -> ConnectionPoolManager:
    """Get the global connection pool manager instance.

    Returns:
        ConnectionPoolManager: The global connection pool manager
    """
    global _connection_pool_manager
    if _connection_pool_manager is None:
        _connection_pool_manager = ConnectionPoolManager()
    return _connection_pool_manager


async def get_http_session(url: str) -> ClientSession:
    """Get an HTTP session for the given URL using the global connection pool.

    Args:
        url: The URL to get a session for

    Returns:
        ClientSession: Configured session for the URL
    """
    manager = await get_connection_pool_manager()
    return await manager.get_session(url)


async def close_all_connections() -> None:
    """Close all HTTP connections in the global connection pool."""
    global _connection_pool_manager
    if _connection_pool_manager is not None:
        await _connection_pool_manager.close_all()
        _connection_pool_manager = None


# Convenience functions for common HTTP operations
async def http_get(url: str, **kwargs: Any) -> aiohttp.ClientResponse:
    """Perform an HTTP GET request using the connection pool.

    Args:
        url: The URL to GET
        **kwargs: Additional arguments for the request

    Returns:
        ClientResponse: The HTTP response
    """
    session = await get_http_session(url)
    return await session.get(url, **kwargs)


async def http_post(url: str, **kwargs: Any) -> aiohttp.ClientResponse:
    """Perform an HTTP POST request using the connection pool.

    Args:
        url: The URL to POST to
        **kwargs: Additional arguments for the request

    Returns:
        ClientResponse: The HTTP response
    """
    session = await get_http_session(url)
    return await session.post(url, **kwargs)


async def http_put(url: str, **kwargs: Any) -> aiohttp.ClientResponse:
    """Perform an HTTP PUT request using the connection pool.

    Args:
        url: The URL to PUT to
        **kwargs: Additional arguments for the request

    Returns:
        ClientResponse: The HTTP response
    """
    session = await get_http_session(url)
    return await session.put(url, **kwargs)


async def http_delete(url: str, **kwargs: Any) -> aiohttp.ClientResponse:
    """Perform an HTTP DELETE request using the connection pool.

    Args:
        url: The URL to DELETE
        **kwargs: Additional arguments for the request

    Returns:
        ClientResponse: The HTTP response
    """
    session = await get_http_session(url)
    return await session.delete(url, **kwargs)


__all__ = [
    "ConnectionPoolManager",
    "close_all_connections",
    "get_connection_pool_manager",
    "get_http_session",
    "http_delete",
    "http_get",
    "http_post",
    "http_put",
]
