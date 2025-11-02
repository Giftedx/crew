"""Feature flag management with dependency-aware toggles.

This module provides a feature flag system that integrates with
the dependency management system to enable/disable features based
on both configuration and dependency availability.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any, TypeVar

from .dependency_manager import get_dependency_manager


if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)


class FeatureFlag:
    """Individual feature flag with dependency checking."""

    def __init__(
        self,
        name: str,
        default_value: bool = False,
        required_deps: set[str] | None = None,
        description: str | None = None,
        env_var: str | None = None,
    ):
        self.name = name
        self.default_value = default_value
        self.required_deps = required_deps or set()
        self.description = description
        self.env_var = env_var or f"ENABLE_{name.upper()}"
        self._dependency_manager = get_dependency_manager()

    def is_enabled(self) -> bool:
        """Check if the feature flag is enabled."""
        # Check environment variable first
        env_value = os.getenv(self.env_var, "").lower()
        if env_value in {"0", "false", "no", "off"}:
            return False
        elif env_value in {"1", "true", "yes", "on"}:
            env_enabled = True
        else:
            env_enabled = self.default_value

        # Check dependencies
        deps_available = all(self._dependency_manager.check_dependency(dep) for dep in self.required_deps)

        # Feature is enabled only if environment allows it AND dependencies are available
        return env_enabled and deps_available

    def get_status(self) -> dict[str, Any]:
        """Get detailed status of the feature flag."""
        env_value = os.getenv(self.env_var, "")
        deps_status = {dep: self._dependency_manager.check_dependency(dep) for dep in self.required_deps}

        return {
            "name": self.name,
            "enabled": self.is_enabled(),
            "default_value": self.default_value,
            "env_var": self.env_var,
            "env_value": env_value,
            "required_dependencies": self.required_deps,
            "dependencies_available": deps_status,
            "description": self.description,
        }

    def __bool__(self) -> bool:
        """Boolean evaluation of the feature flag."""
        return self.is_enabled()


class FeatureFlagManager:
    """Manages feature flags with dependency integration."""

    def __init__(self):
        self._flags: dict[str, FeatureFlag] = {}
        self._dependency_manager = get_dependency_manager()
        self._register_builtin_flags()

    def _register_builtin_flags(self) -> None:
        """Register built-in feature flags."""
        builtin_flags = [
            # Caching features
            FeatureFlag(
                "redis_cache",
                default_value=True,
                required_deps={"redis"},
                description="Enable Redis-based caching",
            ),
            FeatureFlag(
                "memory_cache",
                default_value=True,
                description="Enable in-memory caching fallback",
            ),
            # Vector storage features
            FeatureFlag(
                "qdrant_vector",
                default_value=True,
                required_deps={"qdrant_client"},
                description="Enable Qdrant vector storage",
            ),
            FeatureFlag(
                "vector_search",
                default_value=True,
                description="Enable vector search capabilities",
            ),
            # Database features
            FeatureFlag(
                "postgres_database",
                default_value=False,
                required_deps={"psycopg2", "sqlalchemy"},
                description="Enable PostgreSQL database support",
            ),
            FeatureFlag(
                "sqlite_database",
                default_value=True,
                description="Enable SQLite database support",
            ),
            # AI/ML features
            FeatureFlag(
                "ai_models",
                default_value=True,
                required_deps={"transformers"},
                description="Enable AI model capabilities",
            ),
            FeatureFlag(
                "torch_acceleration",
                default_value=True,
                required_deps={"torch"},
                description="Enable PyTorch acceleration",
            ),
            # Monitoring features
            FeatureFlag(
                "prometheus_metrics",
                default_value=False,
                required_deps={"prometheus_client"},
                description="Enable Prometheus metrics collection",
            ),
            FeatureFlag(
                "advanced_monitoring",
                default_value=False,
                required_deps={"prometheus_client"},
                description="Enable advanced monitoring features",
            ),
            # Development features
            FeatureFlag(
                "debug_mode",
                default_value=False,
                description="Enable debug mode with additional logging",
            ),
            FeatureFlag(
                "profiling",
                default_value=False,
                description="Enable performance profiling",
            ),
            # Router features
            FeatureFlag(
                "bandit_routing",
                default_value=False,
                description="Enable bandit-based model routing",
            ),
            FeatureFlag(
                "cost_aware_routing",
                default_value=True,
                description="Enable cost-aware model routing",
            ),
        ]

        for flag in builtin_flags:
            self.register_flag(flag)

    def register_flag(self, flag: FeatureFlag) -> None:
        """Register a feature flag."""
        self._flags[flag.name] = flag
        logger.debug(f"Registered feature flag: {flag.name}")

    def get_flag(self, name: str) -> FeatureFlag | None:
        """Get a feature flag by name."""
        return self._flags.get(name)

    def is_enabled(self, name: str) -> bool:
        """Check if a feature flag is enabled."""
        flag = self.get_flag(name)
        if flag is None:
            logger.warning(f"Unknown feature flag: {name}")
            return False
        return flag.is_enabled()

    def enable(self, name: str) -> None:
        """Enable a feature flag via environment variable."""
        flag = self.get_flag(name)
        if flag:
            os.environ[flag.env_var] = "1"
            logger.info(f"Enabled feature flag: {name}")

    def disable(self, name: str) -> None:
        """Disable a feature flag via environment variable."""
        flag = self.get_flag(name)
        if flag:
            os.environ[flag.env_var] = "0"
            logger.info(f"Disabled feature flag: {name}")

    def get_all_flags(self) -> dict[str, FeatureFlag]:
        """Get all registered feature flags."""
        return self._flags.copy()

    def get_enabled_flags(self) -> set[str]:
        """Get names of all enabled feature flags."""
        return {name for name, flag in self._flags.items() if flag.is_enabled()}

    def get_disabled_flags(self) -> set[str]:
        """Get names of all disabled feature flags."""
        return {name for name, flag in self._flags.items() if not flag.is_enabled()}

    def get_flags_by_dependency(self, dep_name: str) -> set[str]:
        """Get feature flags that require a specific dependency."""
        flags = set()
        for name, flag in self._flags.items():
            if dep_name in flag.required_deps:
                flags.add(name)
        return flags

    def get_dependency_impact(self, dep_name: str) -> dict[str, Any]:
        """Get the impact of a dependency on feature flags."""
        affected_flags = self.get_flags_by_dependency(dep_name)
        dep_available = self._dependency_manager.check_dependency(dep_name)

        return {
            "dependency": dep_name,
            "available": dep_available,
            "affected_flags": list(affected_flags),
            "enabled_flags": [name for name in affected_flags if self.is_enabled(name)],
            "disabled_flags": [name for name in affected_flags if not self.is_enabled(name)],
        }

    def get_status_report(self) -> dict[str, Any]:
        """Get a comprehensive status report of all feature flags."""
        report = {
            "total_flags": len(self._flags),
            "enabled_flags": len(self.get_enabled_flags()),
            "disabled_flags": len(self.get_disabled_flags()),
            "flags": {},
            "dependency_impact": {},
        }

        # Individual flag status
        for name, flag in self._flags.items():
            report["flags"][name] = flag.get_status()

        # Dependency impact
        all_deps = set()
        for flag in self._flags.values():
            all_deps.update(flag.required_deps)

        for dep in all_deps:
            report["dependency_impact"][dep] = self.get_dependency_impact(dep)

        return report

    def create_flag(
        self,
        name: str,
        default_value: bool = False,
        required_deps: set[str] | None = None,
        description: str | None = None,
        env_var: str | None = None,
    ) -> FeatureFlag:
        """Create and register a new feature flag."""
        flag = FeatureFlag(name, default_value, required_deps, description, env_var)
        self.register_flag(flag)
        return flag


# Global feature flag manager instance
_feature_flag_manager = FeatureFlagManager()


def get_feature_flag_manager() -> FeatureFlagManager:
    """Get the global feature flag manager instance."""
    return _feature_flag_manager


def is_feature_enabled(name: str) -> bool:
    """Check if a feature flag is enabled."""
    return _feature_flag_manager.is_enabled(name)


def enable_feature(name: str) -> None:
    """Enable a feature flag."""
    _feature_flag_manager.enable(name)


def disable_feature(name: str) -> None:
    """Disable a feature flag."""
    _feature_flag_manager.disable(name)


def create_feature_flag(
    name: str,
    default_value: bool = False,
    required_deps: set[str] | None = None,
    description: str | None = None,
    env_var: str | None = None,
) -> FeatureFlag:
    """Create and register a new feature flag."""
    return _feature_flag_manager.create_flag(name, default_value, required_deps, description, env_var)


def get_feature_flag(name: str) -> FeatureFlag | None:
    """Get a feature flag by name."""
    return _feature_flag_manager.get_flag(name)


def get_feature_status() -> dict[str, Any]:
    """Get comprehensive feature flag status."""
    return _feature_flag_manager.get_status_report()


# Convenience functions for common patterns
T = TypeVar("T")


def with_feature_flag(flag_name: str, fallback_func: Callable[[], Any] | None = None):
    """Decorator to enable/disable functionality based on feature flags."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if is_feature_enabled(flag_name):
                return func(*args, **kwargs)
            elif fallback_func:
                logger.debug(f"Using fallback for {func.__name__} (feature {flag_name} disabled)")
                return fallback_func(*args, **kwargs)
            else:
                raise RuntimeError(f"Feature {flag_name} is disabled and no fallback provided")

        return wrapper

    return decorator


def require_feature(flag_name: str):
    """Decorator to require a feature flag to be enabled."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if not is_feature_enabled(flag_name):
                raise RuntimeError(f"Feature {flag_name} is required but not enabled")
            return func(*args, **kwargs)

        return wrapper

    return decorator
