"""Optional dependency handling with lazy loading and feature detection.

This module provides utilities for handling optional dependencies
with lazy loading and feature detection capabilities.
"""

from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING, Any, TypeVar

from .dependency_manager import DependencyError, get_dependency_manager


if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)

T = TypeVar("T")


class OptionalImport:
    """Lazy import wrapper for optional dependencies."""

    def __init__(
        self,
        module_name: str,
        fallback: Any | None = None,
        install_hint: str | None = None,
    ) -> None:
        self.module_name = module_name
        self.fallback = fallback
        self.install_hint = install_hint
        self._module: Any | None = None
        self._imported = False

    def __getattr__(self, name: str) -> Any:
        """Lazy import on attribute access."""
        if not self._imported:
            self._import_module()
        return getattr(self._module, name)

    def _import_module(self) -> None:
        """Import the module or use fallback."""
        try:
            self._module = importlib.import_module(self.module_name)
            self._imported = True
            logger.debug(f"Successfully imported optional module: {self.module_name}")
        except ImportError as e:
            self._imported = True
            if self.fallback is not None:
                self._module = self.fallback
                logger.info(f"Using fallback for optional module: {self.module_name}")
            else:
                error_msg = f"Optional module '{self.module_name}' is not available"
                if self.install_hint:
                    error_msg += f". {self.install_hint}"
                raise DependencyError(error_msg) from e

    @property
    def is_available(self) -> bool:
        """Check if the module is available without importing it."""
        return get_dependency_manager().check_dependency(self.module_name)

    def __bool__(self) -> bool:
        """Boolean evaluation based on availability."""
        return self.is_available


class OptionalClass:
    """Lazy class import wrapper for optional dependencies."""

    def __init__(
        self,
        module_name: str,
        class_name: str,
        fallback_class: type[T] | None = None,
        install_hint: str | None = None,
    ) -> None:
        self.module_name = module_name
        self.class_name = class_name
        self.fallback_class = fallback_class
        self.install_hint = install_hint
        self._class: type[T] | None = None
        self._imported = False

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Create an instance of the class."""
        if not self._imported:
            self._import_class()
        if self._class is None:
            raise DependencyError(f"Class {self.module_name}.{self.class_name} not available")
        return self._class(*args, **kwargs)

    def _import_class(self) -> None:
        """Import the class or use fallback."""
        try:
            module = importlib.import_module(self.module_name)
            self._class = getattr(module, self.class_name)
            self._imported = True
            logger.debug(f"Successfully imported optional class: {self.module_name}.{self.class_name}")
        except (ImportError, AttributeError) as e:
            self._imported = True
            if self.fallback_class is not None:
                self._class = self.fallback_class
                logger.info(f"Using fallback class for: {self.module_name}.{self.class_name}")
            else:
                error_msg = f"Optional class '{self.module_name}.{self.class_name}' is not available"
                if self.install_hint:
                    error_msg += f". {self.install_hint}"
                raise DependencyError(error_msg) from e

    @property
    def is_available(self) -> bool:
        """Check if the class is available without importing it."""
        return get_dependency_manager().check_dependency(self.module_name)

    def __bool__(self) -> bool:
        """Boolean evaluation based on availability."""
        return self.is_available


class FeatureGate:
    """Feature gate with dependency checking."""

    def __init__(self, feature_name: str, required_deps: list[str] | None = None) -> None:
        self.feature_name = feature_name
        self.required_deps = required_deps or []
        self._dependency_manager = get_dependency_manager()

    def is_enabled(self) -> bool:
        """Check if the feature is enabled and dependencies are available."""
        return self._dependency_manager.is_feature_available(self.feature_name)

    def require(self) -> None:
        """Require the feature to be enabled."""
        if not self.is_enabled():
            missing_deps = []
            for dep in self.required_deps:
                if not self._dependency_manager.check_dependency(dep):
                    missing_deps.append(dep)

            error_msg = f"Feature '{self.feature_name}' is not available"
            if missing_deps:
                error_msg += f". Missing dependencies: {missing_deps}"
            raise DependencyError(error_msg)

    def __bool__(self) -> bool:
        """Boolean evaluation based on availability."""
        return self.is_enabled()


# Common optional imports
redis = OptionalImport(
    "redis",
    install_hint="Install with: pip install redis",
)

qdrant_client = OptionalImport(
    "qdrant_client",
    install_hint="Install with: pip install qdrant-client",
)

prometheus_client = OptionalImport(
    "prometheus_client",
    install_hint="Install with: pip install prometheus-client",
)

psycopg2 = OptionalImport(
    "psycopg2",
    install_hint="Install with: pip install psycopg2-binary",
)

transformers = OptionalImport(
    "transformers",
    install_hint="Install with: pip install transformers",
)

torch = OptionalImport(
    "torch",
    install_hint="Install with: pip install torch",
)

pandas = OptionalImport(
    "pandas",
    install_hint="Install with: pip install pandas",
)

numpy = OptionalImport(
    "numpy",
    install_hint="Install with: pip install numpy",
)

# Feature gates
redis_cache_gate = FeatureGate("redis_cache", ["redis"])
qdrant_vector_gate = FeatureGate("qdrant_vector", ["qdrant_client"])
prometheus_metrics_gate = FeatureGate("prometheus_metrics", ["prometheus_client"])
postgres_database_gate = FeatureGate("postgres_database", ["psycopg2", "sqlalchemy"])
ai_models_gate = FeatureGate("ai_models", ["transformers", "torch"])
advanced_monitoring_gate = FeatureGate("advanced_monitoring", ["prometheus_client", "grafana_api"])


def get_optional_module(
    module_name: str, fallback: Any | None = None, install_hint: str | None = None
) -> OptionalImport:
    """Get an optional module with fallback support."""
    return OptionalImport(module_name, fallback, install_hint)


def get_optional_class(
    module_name: str,
    class_name: str,
    fallback_class: type[T] | None = None,
    install_hint: str | None = None,
) -> OptionalClass:
    """Get an optional class with fallback support."""
    return OptionalClass(module_name, class_name, fallback_class, install_hint)


def create_feature_gate(feature_name: str, required_deps: list[str] | None = None) -> FeatureGate:
    """Create a feature gate with dependency checking."""
    return FeatureGate(feature_name, required_deps)


# Utility functions for common patterns
def with_fallback(
    fallback_func: Callable[[], Any],
) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
    """Decorator to provide fallback functionality when dependencies are unavailable."""

    def decorator(import_func: Callable[[], Any]) -> Callable[[], Any]:
        def wrapper() -> Any:
            try:
                return import_func()
            except (ImportError, DependencyError):
                logger.info(f"Using fallback for {import_func.__name__}")
                return fallback_func()

        return wrapper

    return decorator


def require_dependencies(*deps: str) -> Callable[[Any], Any]:
    """Decorator to require dependencies before function execution."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            dependency_manager = get_dependency_manager()
            for dep in deps:
                dependency_manager.require_dependency(dep)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def check_dependencies(*deps: str) -> bool:
    """Check if all specified dependencies are available."""
    dependency_manager = get_dependency_manager()
    return all(dependency_manager.check_dependency(dep) for dep in deps)
