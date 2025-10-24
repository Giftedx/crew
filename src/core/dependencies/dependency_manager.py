"""Dependency management system with optional dependencies and graceful fallbacks.

This module provides a unified system for managing optional dependencies,
feature flags, and graceful fallbacks when dependencies are unavailable.
"""

from __future__ import annotations

import importlib
import logging
import os
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)


class DependencyError(Exception):
    """Raised when a required dependency is unavailable."""


class DependencyManager:
    """Manages optional dependencies and provides graceful fallbacks."""

    def __init__(self) -> None:
        self._available_deps: set[str] = set()
        self._fallback_handlers: dict[str, Callable[[], Any]] = {}
        self._dependency_groups: dict[str, set[str]] = {}
        self._checked_deps: set[str] = set()
        self._init_builtin_groups()

    def _init_builtin_groups(self) -> None:
        """Initialize built-in dependency groups."""
        self._dependency_groups = {
            "core": {
                "requests",
                "pydantic",
                "structlog",
                "asyncio",
            },
            "ai": {
                "openai",
                "anthropic",
                "transformers",
                "torch",
                "numpy",
            },
            "database": {
                "sqlalchemy",
                "alembic",
                "psycopg2",
                "sqlite3",
            },
            "vector": {
                "qdrant_client",
                "chromadb",
                "pinecone",
                "faiss",
            },
            "cache": {
                "redis",
                "memcached",
            },
            "monitoring": {
                "prometheus_client",
                "grafana_api",
                "datadog",
            },
            "ml": {
                "scikit-learn",
                "pandas",
                "matplotlib",
                "seaborn",
            },
            "dev": {
                "pytest",
                "black",
                "ruff",
                "mypy",
            },
        }

    def check_dependency(self, name: str) -> bool:
        """Check if a dependency is available."""
        if name in self._checked_deps:
            return name in self._available_deps

        try:
            importlib.import_module(name)
            self._available_deps.add(name)
            self._checked_deps.add(name)
            logger.debug(f"Dependency '{name}' is available")
            return True
        except ImportError:
            self._checked_deps.add(name)
            logger.debug(f"Dependency '{name}' is not available")
            return False

    def check_dependency_group(self, group_name: str) -> dict[str, bool]:
        """Check availability of all dependencies in a group."""
        if group_name not in self._dependency_groups:
            logger.warning(f"Unknown dependency group: {group_name}")
            return {}

        group_deps = self._dependency_groups[group_name]
        results = {}
        for dep in group_deps:
            results[dep] = self.check_dependency(dep)
        return results

    def require_dependency(self, name: str) -> None:
        """Require a dependency, raising DependencyError if unavailable."""
        if not self.check_dependency(name):
            raise DependencyError(f"Required dependency '{name}' is not available")

    def require_dependency_group(self, group_name: str, min_available: int | None = None) -> None:
        """Require a dependency group with optional minimum availability."""
        results = self.check_dependency_group(group_name)
        available_count = sum(1 for available in results.values() if available)

        if min_available is None:
            min_available = len(results)  # Require all by default

        if available_count < min_available:
            missing = [name for name, available in results.items() if not available]
            raise DependencyError(
                f"Dependency group '{group_name}' has insufficient availability: "
                f"{available_count}/{len(results)} available, need {min_available}. "
                f"Missing: {missing}"
            )

    def register_fallback(self, name: str, fallback_func: Callable[[], Any]) -> None:
        """Register a fallback function for a dependency."""
        self._fallback_handlers[name] = fallback_func
        logger.debug(f"Registered fallback for dependency '{name}'")

    def get_with_fallback(self, name: str, fallback_func: Callable[[], Any] | None = None) -> Any:
        """Get a dependency with fallback support."""
        if self.check_dependency(name):
            return importlib.import_module(name)

        if fallback_func:
            logger.info(f"Using fallback for dependency '{name}'")
            return fallback_func()

        if name in self._fallback_handlers:
            logger.info(f"Using registered fallback for dependency '{name}'")
            return self._fallback_handlers[name]()

        raise DependencyError(f"Dependency '{name}' is not available and no fallback provided")

    def add_dependency_group(self, name: str, dependencies: set[str]) -> None:
        """Add a custom dependency group."""
        self._dependency_groups[name] = dependencies.copy()
        logger.debug(f"Added dependency group '{name}' with {len(dependencies)} dependencies")

    def get_available_dependencies(self) -> set[str]:
        """Get set of all available dependencies."""
        return self._available_deps.copy()

    def get_unavailable_dependencies(self, group_name: str | None = None) -> set[str]:
        """Get set of unavailable dependencies."""
        if group_name:
            if group_name not in self._dependency_groups:
                return set()
            deps_to_check = self._dependency_groups[group_name]
        else:
            deps_to_check = set()
            for group_deps in self._dependency_groups.values():
                deps_to_check.update(group_deps)

        unavailable = set()
        for dep in deps_to_check:
            if dep in self._checked_deps and dep not in self._available_deps:
                unavailable.add(dep)
        return unavailable

    def is_feature_available(self, feature_name: str) -> bool:
        """Check if a feature is available based on dependencies and feature flags."""
        # Check feature flag first
        flag_name = f"ENABLE_{feature_name.upper()}"
        if os.getenv(flag_name, "1").lower() not in {"1", "true", "yes", "on"}:
            return False

        # Check if feature has dependency requirements
        feature_deps = self._get_feature_dependencies(feature_name)
        return all(self.check_dependency(dep) for dep in feature_deps)

    def _get_feature_dependencies(self, feature_name: str) -> set[str]:
        """Get dependencies required for a feature."""
        # This could be extended to read from a configuration file
        feature_deps_map = {
            "redis_cache": {"redis"},
            "qdrant_vector": {"qdrant_client"},
            "prometheus_metrics": {"prometheus_client"},
            "postgres_database": {"psycopg2", "sqlalchemy"},
            "ai_models": {"transformers", "torch"},
            "advanced_monitoring": {"prometheus_client", "grafana_api"},
        }
        return feature_deps_map.get(feature_name, set())

    def get_dependency_status(self) -> dict[str, Any]:
        """Get comprehensive dependency status."""
        status: dict[str, Any] = {
            "available": list(self._available_deps),
            "unavailable": list(self.get_unavailable_dependencies()),
            "groups": {},
            "features": {},
        }

        # Group status
        for group_name in self._dependency_groups:
            group_results = self.check_dependency_group(group_name)
            available_count = sum(1 for available in group_results.values() if available)
            status["groups"][group_name] = {
                "available": available_count,
                "total": len(group_results),
                "dependencies": group_results,
            }

        # Feature status
        common_features = [
            "redis_cache",
            "qdrant_vector",
            "prometheus_metrics",
            "postgres_database",
            "ai_models",
            "advanced_monitoring",
        ]
        for feature in common_features:
            status["features"][feature] = self.is_feature_available(feature)

        return status


# Global dependency manager instance
_dependency_manager = DependencyManager()


def get_dependency_manager() -> DependencyManager:
    """Get the global dependency manager instance."""
    return _dependency_manager


def check_dependency(name: str) -> bool:
    """Check if a dependency is available."""
    return _dependency_manager.check_dependency(name)


def require_dependency(name: str) -> None:
    """Require a dependency, raising DependencyError if unavailable."""
    _dependency_manager.require_dependency(name)


def require_dependency_group(group_name: str, min_available: int | None = None) -> None:
    """Require a dependency group with optional minimum availability."""
    _dependency_manager.require_dependency_group(group_name, min_available)


def get_with_fallback(name: str, fallback_func: Callable[[], Any] | None = None) -> Any:
    """Get a dependency with fallback support."""
    return _dependency_manager.get_with_fallback(name, fallback_func)


def is_feature_available(feature_name: str) -> bool:
    """Check if a feature is available based on dependencies and feature flags."""
    return _dependency_manager.is_feature_available(feature_name)


def register_fallback(name: str, fallback_func: Callable[[], Any]) -> None:
    """Register a fallback function for a dependency."""
    _dependency_manager.register_fallback(name, fallback_func)
