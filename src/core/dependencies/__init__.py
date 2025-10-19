"""Dependency management system with optional dependencies and graceful fallbacks.

This module provides a unified system for managing optional dependencies,
feature flags, and graceful fallbacks when dependencies are unavailable.

Usage:
    from src.core.dependencies import (
        check_dependency,
        require_dependency,
        get_with_fallback,
        is_feature_enabled,
        redis,
        qdrant_client,
    )

    # Check if a dependency is available
    if check_dependency("redis"):
        # Use Redis
        pass
    else:
        # Use fallback
        pass

    # Use optional imports with fallbacks
    cache = get_with_fallback("redis", fallback_func=get_fallback_cache)

    # Check feature flags
    if is_feature_enabled("redis_cache"):
        # Enable Redis caching
        pass
"""

from __future__ import annotations

from .dependency_checker import (
    check_module_available,
    check_version_requirement,
    generate_dependency_report,
    get_dependency_checker,
    get_module_version,
    validate_requirements_file,
)
from .dependency_manager import (
    DependencyError,
    check_dependency,
    get_dependency_manager,
    get_with_fallback,
    is_feature_available,
    register_fallback,
    require_dependency,
    require_dependency_group,
)
from .fallback_handlers import (
    FallbackCache,
    FallbackDatabase,
    FallbackHistogram,
    FallbackMetrics,
    FallbackVectorStore,
    get_fallback_cache,
    get_fallback_database,
    get_fallback_metrics,
    get_fallback_vector_store,
)
from .feature_flags import (
    FeatureFlag,
    FeatureFlagManager,
    create_feature_flag,
    disable_feature,
    enable_feature,
    get_feature_flag,
    get_feature_flag_manager,
    get_feature_status,
    is_feature_enabled,
    require_feature,
    with_feature_flag,
)
from .optional_deps import (
    FeatureGate,
    OptionalClass,
    OptionalImport,
    advanced_monitoring_gate,
    ai_models_gate,
    check_dependencies,
    create_feature_gate,
    get_optional_class,
    get_optional_module,
    numpy,
    pandas,
    postgres_database_gate,
    prometheus_client,
    prometheus_metrics_gate,
    psycopg2,
    qdrant_client,
    qdrant_vector_gate,
    redis,
    redis_cache_gate,
    require_dependencies,
    torch,
    transformers,
    with_fallback,
)

# Public API
__all__ = [
    # Core dependency management
    "DependencyError",
    "check_dependency",
    "require_dependency",
    "require_dependency_group",
    "get_with_fallback",
    "register_fallback",
    "is_feature_available",
    "get_dependency_manager",
    # Optional imports
    "OptionalImport",
    "OptionalClass",
    "FeatureGate",
    "get_optional_module",
    "get_optional_class",
    "create_feature_gate",
    # Feature flags
    "FeatureFlag",
    "FeatureFlagManager",
    "is_feature_enabled",
    "enable_feature",
    "disable_feature",
    "create_feature_flag",
    "get_feature_flag",
    "get_feature_status",
    "get_feature_flag_manager",
    "require_feature",
    "with_feature_flag",
    # Fallback handlers
    "FallbackCache",
    "FallbackVectorStore",
    "FallbackMetrics",
    "FallbackDatabase",
    "get_fallback_cache",
    "get_fallback_vector_store",
    "get_fallback_metrics",
    "get_fallback_database",
    # Dependency checking
    "check_module_available",
    "get_module_version",
    "check_version_requirement",
    "generate_dependency_report",
    "validate_requirements_file",
    "get_dependency_checker",
    # Common optional imports
    "redis",
    "qdrant_client",
    "prometheus_client",
    "psycopg2",
    "transformers",
    "torch",
    "pandas",
    "numpy",
    # Feature gates
    "redis_cache_gate",
    "qdrant_vector_gate",
    "prometheus_metrics_gate",
    "postgres_database_gate",
    "ai_models_gate",
    "advanced_monitoring_gate",
    # Utility functions
    "with_fallback",
    "require_dependencies",
    "check_dependencies",
]


# Initialize the dependency system
def _initialize_dependency_system() -> None:
    """Initialize the dependency management system."""
    import logging

    logger = logging.getLogger(__name__)

    # Register fallback handlers
    from .fallback_handlers import register_fallback_handlers

    register_fallback_handlers()

    # Log initialization
    logger.info("Dependency management system initialized")

    # Generate initial dependency report in debug mode
    if logger.isEnabledFor(logging.DEBUG):
        report = generate_dependency_report()
        logger.debug(f"Dependency system status: {report}")


# Auto-initialize when module is imported
_initialize_dependency_system()
