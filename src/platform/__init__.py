"""
Local "platform" package that safely coexists with the Python stdlib module "platform".

This module exposes the project's platform subpackages (analytics, discovery, etc.) while
forwarding unknown attributes to the real stdlib platform module. This design prevents
stdlib breakages (e.g., uuid importing platform.system()) when our local package name
collides with the stdlib module name.

Implementation notes:
- We dynamically load the stdlib platform module by file path to avoid recursive import
  of this package.
- We implement module-level __getattr__/__dir__ per PEP 562 to forward attribute lookups.
"""

from __future__ import annotations

import importlib
import os as _os
import sys as _sys
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from sysconfig import get_paths


# Ensure our platform package is loaded before stdlib platform
_this_dir = _os.path.dirname(__file__)
_parent_dir = _os.path.dirname(_this_dir)
if _parent_dir not in _sys.path:
    _sys.path.insert(0, _parent_dir)


# --- Load the real stdlib platform module under a private name ---
_STDLIB_PLATFORM: object | None = None
try:
    _stdlib_dir = get_paths().get("stdlib")
    if _stdlib_dir:
        _stdlib_platform_path = _os.path.join(_stdlib_dir, "platform.py")
        if _os.path.exists(_stdlib_platform_path):
            _loader = SourceFileLoader("_py_stdlib_platform", _stdlib_platform_path)
            _spec = spec_from_loader("_py_stdlib_platform", _loader)
            if _spec is not None:
                _module = module_from_spec(_spec)
                assert _spec.loader is not None
                _spec.loader.exec_module(_module)
                _STDLIB_PLATFORM = _module
except Exception:
    # As a last resort, try to reuse any already-imported stdlib platform
    _STDLIB_PLATFORM = _sys.modules.get("platform")

# --- Import local subpackages and symbols ---
# --- Import local subpackages and symbols ---
from . import config as _config  # noqa: E402
from . import core as _core  # noqa: E402
from .content_discovery import (  # noqa: E402
    AggregationMode,
    ContentCluster,
    ContentDiscovery,
    ContentRankingMethod,
    DiscoveryQuery,
    DiscoveryResult,
    DiscoveryStrategy,
)
from .cross_platform_analytics import (  # noqa: E402
    AnalyticsDataPoint,
    AnalyticsDimension,
    AnalyticsMetric,
    AnalyticsQuery,
    AnalyticsResult,
    CrossPlatformAnalytics,
    CrossPlatformInsight,
    TimeGranularity,
    VisualizationType,
)
from .platform_integration import (  # noqa: E402
    AuthType,
    IntegrationMetrics,
    IntegrationStatus,
    PlatformConfig,
    PlatformIntegration,
    SyncMode,
    SyncResult,
)
from .social_monitor import (  # noqa: E402
    ContentType,
    MonitoringRule,
    PlatformType,
    SentimentType,
    SocialContent,
    SocialMonitor,
    TrendData,
)


# Make platform.core available for imports
_sys.modules["platform.core"] = _core
_sys.modules["platform.config"] = _config


__all__ = [
    "AggregationMode",
    "AnalyticsDataPoint",
    "AnalyticsDimension",
    # Cross-platform analytics
    "AnalyticsMetric",
    "AnalyticsQuery",
    "AnalyticsResult",
    "AuthType",
    "ContentCluster",
    "ContentDiscovery",
    "ContentRankingMethod",
    "ContentType",
    "CrossPlatformAnalytics",
    "CrossPlatformInsight",
    "DiscoveryQuery",
    "DiscoveryResult",
    # Content discovery
    "DiscoveryStrategy",
    "ErrorCategory",
    # Core
    "IntegrationMetrics",
    # Platform integration
    "IntegrationStatus",
    "MonitoringRule",
    "PlatformConfig",
    "PlatformIntegration",
    "PlatformType",
    "SentimentType",
    # Social monitoring
    "SocialContent",
    "SocialMonitor",
    "StepResult",
    # Core
    "SyncMode",
    "SyncResult",
    "TimeGranularity",
    "TrendData",
    "VisualizationType",
]


def __getattr__(name: str):
    """Forward unknown attributes to the stdlib platform module, if available."""
    if name in globals():
        return globals()[name]
    if name == "core":
        return _core
    if name == "config":
        return _config
    # Handle other local submodules
    local_submodules = ["http", "time", "cache", "optimization", "settings"]
    if name in local_submodules:
        try:
            return importlib.import_module(f"platform.{name}")
        except ImportError:
            pass
    if _STDLIB_PLATFORM is not None and hasattr(_STDLIB_PLATFORM, name):
        return getattr(_STDLIB_PLATFORM, name)
    raise AttributeError(f"module 'platform' has no attribute '{name}'")


def __dir__() -> list[str]:  # pragma: no cover - cosmetic
    std_attrs = []
    if _STDLIB_PLATFORM is not None:
        try:
            std_attrs = dir(_STDLIB_PLATFORM)
        except Exception:
            std_attrs = []
    return sorted(set(globals().keys()).union(std_attrs))
