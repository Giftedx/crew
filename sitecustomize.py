"""Test-friendly site customizations for this repository.

This module is automatically imported by Python's site module if present
on sys.path. We use it to:
- Ensure the src/ directory is importable without setting PYTHONPATH
- Prevent third-party pytest plugin auto-loading that often breaks
  hermetic test runs (e.g., chromadb/lancedb exporting pytest plugins)

Both behaviors are safe for local development and CI, and can be overridden
via environment variables.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import sys
import sysconfig
import types
from pathlib import Path


# 1) Make sure src/ is importable (so `import ultimate_discord_intelligence_bot` works)
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if SRC.exists():
    src_path = str(SRC)
    # Capture stdlib 'platform' BEFORE adding src to path
    std_platform = None
    # Prefer robust load from stdlib path to avoid accidentally grabbing the local package
    try:
        stdlib_dir = Path(sysconfig.get_paths().get("stdlib", Path(os.__file__).resolve().parent))
        platform_py = stdlib_dir / "platform.py"
        if platform_py.exists():
            loader = importlib.machinery.SourceFileLoader("platform", str(platform_py))
            spec = importlib.util.spec_from_loader("platform", loader)
            if spec is not None:
                module = importlib.util.module_from_spec(spec)
                assert module is not None
                loader.exec_module(module)  # type: ignore[arg-type]
                std_platform = module
    except Exception:  # pragma: no cover - best-effort bootstrap
        std_platform = None
    # Fallbacks only if robust load failed
    if std_platform is None:
        if "platform" in sys.modules and hasattr(sys.modules["platform"], "system"):
            # If a valid stdlib-like platform is already loaded, use it
            std_platform = sys.modules["platform"]
        else:
            try:
                import platform as _std_platform  # type: ignore

                std_platform = _std_platform if hasattr(_std_platform, "system") else None
            except Exception:
                std_platform = None

    # Ensure stdlib platform is registered early so subsequent imports see it
    if std_platform is not None:
        sys.modules["platform"] = std_platform

    # Now add src/ to path
    if src_path not in sys.path:
        # Ensure our 'src/' takes precedence over stdlib lookups
        sys.path.insert(0, src_path)

    # Build or augment a 'platform' package that exposes stdlib attributes while
    # acting as a package for our repo's 'platform/*' submodules.
    plat_dir = SRC / "platform"
    plat_init = plat_dir / "__init__.py"
    if plat_init.exists() and std_platform is not None:
        try:
            # Create a proxy module that inherits from stdlib platform
            class PlatformProxy(types.ModuleType):
                def __init__(self, std_platform, plat_dir):
                    super().__init__("platform")
                    self._std_platform = std_platform
                    self.__path__ = [str(plat_dir)]
                    self.__package__ = "platform"
                    self.__spec__ = importlib.machinery.ModuleSpec(name="platform", loader=None, is_package=True)

                    # Copy all stdlib attributes
                    for name in dir(std_platform):
                        if not name.startswith("_"):
                            setattr(self, name, getattr(std_platform, name))

                    # Copy critical private attrs
                    for attr in ["__file__", "__name__", "__doc__", "__loader__"]:
                        if hasattr(std_platform, attr):
                            setattr(self, attr, getattr(std_platform, attr))

                def __getattr__(self, name):
                    # First check if it's a local submodule
                    local_submodules = ["core", "config", "http", "time", "cache", "optimization", "settings"]
                    if name in local_submodules:
                        try:
                            return importlib.import_module(f"platform.{name}")
                        except ImportError:
                            pass
                    # Then check stdlib
                    if hasattr(self._std_platform, name):
                        return getattr(self._std_platform, name)
                    raise AttributeError(f"module 'platform' has no attribute '{name}'")

            proxy = PlatformProxy(std_platform, plat_dir)
            sys.modules["platform"] = proxy

            # Directly import and register local submodules
            try:
                import platform.core

                sys.modules["platform.core"] = platform.core
            except ImportError:
                pass
            try:
                import platform.config

                sys.modules["platform.config"] = platform.config
            except ImportError:
                pass

        except Exception as e:  # Fallback to simple proxy creation if class fails
            try:
                proxy = types.ModuleType("platform")
                # Copy ALL stdlib attributes so dependencies like urllib3/zstandard/pydantic work
                for name in dir(std_platform):
                    if not name.startswith("_"):
                        from contextlib import suppress

                        with suppress(Exception):
                            setattr(proxy, name, getattr(std_platform, name))
                # Also copy critical private/dunder attrs that libs may use
                for attr in [
                    "__file__",
                    "__name__",
                    "__doc__",
                    "__package__",
                    "__loader__",
                    "__spec__",
                ]:
                    if hasattr(std_platform, attr):
                        from contextlib import suppress

                        with suppress(Exception):
                            setattr(proxy, attr, getattr(std_platform, attr))
                # Override package traits for submodule imports
                proxy.__package__ = "platform"
                proxy.__path__ = [str(plat_dir)]
                proxy.__spec__ = importlib.machinery.ModuleSpec(name="platform", loader=None, is_package=True)
                # Bind the proxy into sys.modules
                sys.modules["platform"] = proxy
            except Exception as e2:
                # Log the error for debugging but continue
                import warnings

                warnings.warn(
                    f"Failed to create platform proxy: {e} / fallback error: {e2}",
                    stacklevel=2,
                )

# 2) Disable auto-loading of external pytest plugins by default.
# This avoids ImportPathMismatch and binary-dep import errors during collection.
# You can re-enable plugin autoload by setting PYTEST_DISABLE_PLUGIN_AUTOLOAD=0.
if os.getenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD") is None:
    # Only set the guard if not explicitly configured by the environment
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
