"""Unified Configuration System.

This module provides a centralized, type-safe configuration management system
that consolidates all configuration sources into a single interface.
"""

from __future__ import annotations

from .config_cache import ConfigCache
from .config_factory import (
    ConfigFactory,
)
from .config_factory import (
    get_global_config as get_config,
)
from .config_factory import (
    reload_configuration as reload_config,
)
from .config_loader import ConfigLoader
from .config_manager import ConfigManager
from .config_schema import (
    ArchiveConfig,
    ConfigSchema,
    DeprecationsConfig,
    GlobalConfig,
    GroundingConfig,
    IngestConfig,
    MonitoringConfig,
    PolicyConfig,
    PollerConfig,
    ProfilesConfig,
    RoutingConfig,
    SecurityConfig,
    TenantConfig,
)
from .config_validator import ConfigValidator


# Backward compatibility alias: SecureConfig -> GlobalConfig
# Many modules import SecureConfig expecting a settings-like object
SecureConfig = GlobalConfig


__all__ = [
    "ArchiveConfig",
    "ConfigCache",
    "ConfigFactory",
    "ConfigLoader",
    "ConfigManager",
    "ConfigSchema",
    "ConfigValidator",
    "DeprecationsConfig",
    "GlobalConfig",
    "GroundingConfig",
    "IngestConfig",
    "MonitoringConfig",
    "PolicyConfig",
    "PollerConfig",
    "ProfilesConfig",
    "RoutingConfig",
    "SecureConfig",
    "SecurityConfig",
    "TenantConfig",
    "get_config",
    "reload_config",
]
