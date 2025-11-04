"""Repository-specific Python startup customizations.

This module is imported automatically by Python's site module if present on
sys.path, after sitecustomize. We use it to make the repository's 'platform/*'
package coexist with the stdlib 'platform' module by augmenting the stdlib
module to behave as a package that exposes our submodules (platform.core, ...).

It is intentionally tiny and side-effect free beyond the augmentation so that
import order remains stable and safe across environments.
"""

from __future__ import annotations

import importlib.machinery
import os as _os
import sys
from pathlib import Path


try:
    import platform as _stdlib_platform
except Exception:  # pragma: no cover - extremely early import failure
    _stdlib_platform = None

# Determine the repo's 'platform' directory relative to this file (which lives in src/)
SRC_DIR = Path(__file__).resolve().parent
PLATFORM_DIR = SRC_DIR / "platform"

if _stdlib_platform is not None and PLATFORM_DIR.joinpath("__init__.py").exists():
    try:
        # Augment the stdlib module in-place to behave as a package so that
        # 'import platform.core.step_result' resolves our submodules.
        _stdlib_platform.__package__ = "platform"
        _stdlib_platform.__path__ = [str(PLATFORM_DIR)]
        _stdlib_platform.__spec__ = importlib.machinery.ModuleSpec(name="platform", loader=None, is_package=True)
        sys.modules["platform"] = _stdlib_platform
    except Exception:
        # Last-resort fallback: if anything goes wrong, silently continue
        # without raising to avoid breaking Python startup.
        pass

# Prevent third-party pytest plugin auto-loading unless explicitly enabled.
# This avoids flaky test collection due to environment-provided plugins.
if _os.getenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD") is None:
    _os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
