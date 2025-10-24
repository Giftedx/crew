"""Import cache for lazy loading optimization.

This module provides caching capabilities for imports to improve
performance and reduce redundant module loading.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any


logger = logging.getLogger(__name__)


class ImportCache:
    """Cache for imported modules to improve performance."""

    def __init__(self, max_size: int = 1000):
        """Initialize the import cache."""
        self._cache: dict[str, Any] = {}
        self._max_size = max_size
        self._access_count: dict[str, int] = {}
        self._import_errors: set[str] = set()

    def get_module(self, module_path: str) -> Any | None:
        """Get a module from cache or import it."""
        if module_path in self._import_errors:
            return None

        if module_path in self._cache:
            self._access_count[module_path] = self._access_count.get(module_path, 0) + 1
            return self._cache[module_path]

        try:
            module = importlib.import_module(module_path)
            self._cache[module_path] = module
            self._access_count[module_path] = 1

            # Evict least recently used modules if cache is full
            if len(self._cache) > self._max_size:
                self._evict_lru()

            return module
        except ImportError as e:
            logger.warning(f"Failed to import module {module_path}: {e}")
            self._import_errors.add(module_path)
            return None

    def _evict_lru(self) -> None:
        """Evict least recently used modules from cache."""
        if not self._access_count:
            return

        # Find module with lowest access count
        lru_module = min(self._access_count.items(), key=lambda x: x[1])[0]

        # Remove from cache
        if lru_module in self._cache:
            del self._cache[lru_module]
        if lru_module in self._access_count:
            del self._access_count[lru_module]

    def preload_module(self, module_path: str) -> bool:
        """Preload a module into cache."""
        module = self.get_module(module_path)
        return module is not None

    def preload_modules(self, module_paths: list[str]) -> dict[str, bool]:
        """Preload multiple modules into cache."""
        results = {}
        for module_path in module_paths:
            results[module_path] = self.preload_module(module_path)
        return results

    def clear_cache(self) -> None:
        """Clear all cached modules."""
        self._cache.clear()
        self._access_count.clear()
        self._import_errors.clear()

    def remove_module(self, module_path: str) -> None:
        """Remove a specific module from cache."""
        if module_path in self._cache:
            del self._cache[module_path]
        if module_path in self._access_count:
            del self._access_count[module_path]
        if module_path in self._import_errors:
            self._import_errors.remove(module_path)

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._cache),
            "max_size": self._max_size,
            "import_errors": len(self._import_errors),
            "total_accesses": sum(self._access_count.values()),
            "most_accessed": max(self._access_count.items(), key=lambda x: x[1])[0] if self._access_count else None,
        }

    def get_module_info(self, module_path: str) -> dict[str, Any]:
        """Get information about a specific module."""
        return {
            "cached": module_path in self._cache,
            "access_count": self._access_count.get(module_path, 0),
            "import_error": module_path in self._import_errors,
            "module": self._cache.get(module_path),
        }

    def warmup_cache(self, critical_modules: list[str]) -> dict[str, bool]:
        """Warm up cache with critical modules."""
        results = {}
        for module_path in critical_modules:
            results[module_path] = self.preload_module(module_path)
        return results


# Global import cache instance
_import_cache = ImportCache()


def get_import_cache() -> ImportCache:
    """Get the global import cache instance."""
    return _import_cache


def get_module(module_path: str) -> Any | None:
    """Get a module from the global cache."""
    return _import_cache.get_module(module_path)


def preload_module(module_path: str) -> bool:
    """Preload a module into the global cache."""
    return _import_cache.preload_module(module_path)


def preload_modules(module_paths: list[str]) -> dict[str, bool]:
    """Preload multiple modules into the global cache."""
    return _import_cache.preload_modules(module_paths)
