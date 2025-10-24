"""Dependency manager for optional dependencies.

This module provides dependency management capabilities to handle
optional dependencies gracefully and provide fallbacks when needed.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any


logger = logging.getLogger(__name__)


class DependencyManager:
    """Manages optional dependencies and provides fallbacks."""

    def __init__(self):
        """Initialize the dependency manager."""
        self._dependency_cache: dict[str, bool] = {}
        self._dependency_versions: dict[str, str] = {}
        self._fallback_modules: dict[str, Any] = {}

    def check_dependency(self, dependency: str) -> bool:
        """Check if a dependency is available."""
        if dependency in self._dependency_cache:
            return self._dependency_cache[dependency]

        try:
            module = importlib.import_module(dependency)
            self._dependency_cache[dependency] = True

            # Try to get version if available
            try:
                version = getattr(module, "__version__", "unknown")
                self._dependency_versions[dependency] = version
            except AttributeError:
                self._dependency_versions[dependency] = "unknown"

            return True
        except ImportError:
            self._dependency_cache[dependency] = False
            return False

    def check_dependencies(self, dependencies: list[str]) -> tuple[bool, list[str]]:
        """Check multiple dependencies and return status."""
        missing = []
        for dep in dependencies:
            if not self.check_dependency(dep):
                missing.append(dep)

        return len(missing) == 0, missing

    def get_dependency_version(self, dependency: str) -> str | None:
        """Get the version of a dependency if available."""
        if dependency in self._dependency_versions:
            return self._dependency_versions[dependency]
        return None

    def get_available_dependencies(self) -> list[str]:
        """Get list of available dependencies."""
        return [dep for dep, available in self._dependency_cache.items() if available]

    def get_missing_dependencies(self) -> list[str]:
        """Get list of missing dependencies."""
        return [dep for dep, available in self._dependency_cache.items() if not available]

    def register_fallback(self, dependency: str, fallback_module: Any) -> None:
        """Register a fallback module for a dependency."""
        self._fallback_modules[dependency] = fallback_module

    def get_fallback(self, dependency: str) -> Any | None:
        """Get fallback module for a dependency."""
        return self._fallback_modules.get(dependency)

    def create_fallback_module(self, dependency: str, error_message: str) -> Any:
        """Create a fallback module for a missing dependency."""

        class FallbackModule:
            def __init__(self, name: str, error: str):
                self.__name__ = name
                self.__version__ = "fallback"
                self.error = error

            def __getattr__(self, name: str) -> Any:
                raise ImportError(f"{self.__name__} is unavailable: {self.error}")

        return FallbackModule(dependency, error_message)

    def get_dependency_info(self) -> dict[str, dict[str, Any]]:
        """Get comprehensive dependency information."""
        info = {}
        for dep in self._dependency_cache:
            info[dep] = {
                "available": self._dependency_cache[dep],
                "version": self._dependency_versions.get(dep, "unknown"),
                "fallback": dep in self._fallback_modules,
            }
        return info

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._dependency_cache.clear()
        self._dependency_versions.clear()
        self._fallback_modules.clear()

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        return {
            "dependency_cache_size": len(self._dependency_cache),
            "version_cache_size": len(self._dependency_versions),
            "fallback_cache_size": len(self._fallback_modules),
        }


# Global dependency manager instance
_dependency_manager = DependencyManager()


def get_dependency_manager() -> DependencyManager:
    """Get the global dependency manager instance."""
    return _dependency_manager


def check_dependency(dependency: str) -> bool:
    """Check if a dependency is available."""
    return _dependency_manager.check_dependency(dependency)


def check_dependencies(dependencies: list[str]) -> tuple[bool, list[str]]:
    """Check multiple dependencies and return status."""
    return _dependency_manager.check_dependencies(dependencies)
