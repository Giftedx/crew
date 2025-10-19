"""Fallback handlers for when optional dependencies are unavailable.

This module provides fallback implementations for common dependencies
when they are not available in the environment.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class FallbackCache:
    """In-memory fallback cache when Redis is unavailable."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}
        self._ttl: dict[str, float] = {}
        logger.info("Using fallback in-memory cache (Redis unavailable)")

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if key in self._cache:
            # Check TTL
            if key in self._ttl and self._ttl[key] > 0:
                import time

                if time.time() > self._ttl[key]:
                    del self._cache[key]
                    del self._ttl[key]
                    return None
            return self._cache[key]
        return None

    def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        """Set value in cache with optional expiration."""
        self._cache[key] = value
        if ex is not None:
            import time

            self._ttl[key] = time.time() + ex
        return True

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
            if key in self._ttl:
                del self._ttl[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._cache

    def clear(self) -> bool:
        """Clear all cache entries."""
        self._cache.clear()
        self._ttl.clear()
        return True


class FallbackVectorStore:
    """Fallback vector store when Qdrant is unavailable."""

    def __init__(self) -> None:
        self._vectors: dict[str, list[float]] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        logger.info("Using fallback in-memory vector store (Qdrant unavailable)")

    def add_vectors(self, vectors: dict[str, list[float]], metadata: dict[str, dict[str, Any]] | None = None) -> bool:
        """Add vectors to the store."""
        self._vectors.update(vectors)
        if metadata:
            self._metadata.update(metadata)
        return True

    def search(self, query_vector: list[float], top_k: int = 10) -> list[dict[str, Any]]:
        """Search for similar vectors."""
        if not self._vectors:
            return []

        # Simple cosine similarity search
        results: list[dict[str, Any]] = []
        for vector_id, vector in self._vectors.items():
            similarity = self._cosine_similarity(query_vector, vector)
            results.append(
                {
                    "id": vector_id,
                    "score": similarity,
                    "metadata": self._metadata.get(vector_id, {}),
                }
            )

        # Sort by similarity and return top_k
        results.sort(key=lambda x: float(x["score"]), reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))

    def delete_vectors(self, vector_ids: list[str]) -> bool:
        """Delete vectors from the store."""
        for vector_id in vector_ids:
            self._vectors.pop(vector_id, None)
            self._metadata.pop(vector_id, None)
        return True

    def get_vector_count(self) -> int:
        """Get total number of vectors in the store."""
        return len(self._vectors)


class FallbackMetrics:
    """Fallback metrics when Prometheus is unavailable."""

    def __init__(self) -> None:
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
        logger.info("Using fallback in-memory metrics (Prometheus unavailable)")

    def counter(self, name: str, labels: dict[str, str] | None = None) -> FallbackCounter:
        """Create a counter metric."""
        key = self._make_key(name, labels)
        if key not in self._counters:
            self._counters[key] = 0.0
        return FallbackCounter(self._counters, key)

    def gauge(self, name: str, labels: dict[str, str] | None = None) -> FallbackGauge:
        """Create a gauge metric."""
        key = self._make_key(name, labels)
        if key not in self._gauges:
            self._gauges[key] = 0.0
        return FallbackGauge(self._gauges, key)

    def histogram(self, name: str, labels: dict[str, str] | None = None) -> FallbackHistogram:
        """Create a histogram metric."""
        key = self._make_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = []
        return FallbackHistogram(self._histograms, key)

    def _make_key(self, name: str, labels: dict[str, str] | None) -> str:
        """Create a key for the metric."""
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{name}{{{label_str}}}"
        return name

    def get_metrics(self) -> dict[str, Any]:
        """Get all metrics data."""
        return {
            "counters": self._counters.copy(),
            "gauges": self._gauges.copy(),
            "histograms": {k: len(v) for k, v in self._histograms.items()},
        }


class FallbackCounter:
    """Fallback counter implementation."""

    def __init__(self, counters: dict[str, float], key: str) -> None:
        self._counters = counters
        self._key = key

    def inc(self, amount: float = 1.0) -> None:
        """Increment the counter."""
        self._counters[self._key] += amount


class FallbackGauge:
    """Fallback gauge implementation."""

    def __init__(self, gauges: dict[str, float], key: str) -> None:
        self._gauges = gauges
        self._key = key

    def set(self, value: float) -> None:
        """Set the gauge value."""
        self._gauges[self._key] = value

    def inc(self, amount: float = 1.0) -> None:
        """Increment the gauge."""
        self._gauges[self._key] += amount

    def dec(self, amount: float = 1.0) -> None:
        """Decrement the gauge."""
        self._gauges[self._key] -= amount


class FallbackHistogram:
    """Fallback histogram implementation."""

    def __init__(self, histograms: dict[str, list[float]], key: str) -> None:
        self._histograms = histograms
        self._key = key

    def observe(self, value: float) -> None:
        """Observe a value in the histogram."""
        self._histograms[self._key].append(value)


class FallbackDatabase:
    """Fallback database when PostgreSQL is unavailable."""

    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {}
        logger.info("Using fallback in-memory database (PostgreSQL unavailable)")

    def execute(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute a query (simplified implementation)."""
        # This is a very simplified implementation
        # In practice, you'd want a more sophisticated query parser
        query_lower = query.lower().strip()

        if query_lower.startswith("select"):
            return self._handle_select(query, params)
        elif query_lower.startswith("insert"):
            return self._handle_insert(query, params)
        elif query_lower.startswith("update"):
            return self._handle_update(query, params)
        elif query_lower.startswith("delete"):
            return self._handle_delete(query, params)
        else:
            logger.warning(f"Unsupported query type: {query}")
            return []

    def _handle_select(self, query: str, params: dict[str, Any] | None) -> list[dict[str, Any]]:
        """Handle SELECT queries."""
        # Simplified SELECT implementation
        return []

    def _handle_insert(self, query: str, params: dict[str, Any] | None) -> list[dict[str, Any]]:
        """Handle INSERT queries."""
        # Simplified INSERT implementation
        return []

    def _handle_update(self, query: str, params: dict[str, Any] | None) -> list[dict[str, Any]]:
        """Handle UPDATE queries."""
        # Simplified UPDATE implementation
        return []

    def _handle_delete(self, query: str, params: dict[str, Any] | None) -> list[dict[str, Any]]:
        """Handle DELETE queries."""
        # Simplified DELETE implementation
        return []


# Fallback handler functions
def get_fallback_cache() -> FallbackCache:
    """Get fallback cache implementation."""
    return FallbackCache()


def get_fallback_vector_store() -> FallbackVectorStore:
    """Get fallback vector store implementation."""
    return FallbackVectorStore()


def get_fallback_metrics() -> FallbackMetrics:
    """Get fallback metrics implementation."""
    return FallbackMetrics()


def get_fallback_database() -> FallbackDatabase:
    """Get fallback database implementation."""
    return FallbackDatabase()


# Register fallback handlers with dependency manager
def register_fallback_handlers() -> None:
    """Register all fallback handlers with the dependency manager."""
    from .dependency_manager import get_dependency_manager

    dependency_manager = get_dependency_manager()

    # Register Redis fallback
    dependency_manager.register_fallback("redis", get_fallback_cache)

    # Register Qdrant fallback
    dependency_manager.register_fallback("qdrant_client", get_fallback_vector_store)

    # Register Prometheus fallback
    dependency_manager.register_fallback("prometheus_client", get_fallback_metrics)

    # Register PostgreSQL fallback
    dependency_manager.register_fallback("psycopg2", get_fallback_database)

    logger.info("Registered fallback handlers for optional dependencies")


# Auto-register fallback handlers when module is imported
register_fallback_handlers()
