"""Lightweight import-time bootstrap helpers.

This module provides a single function, ensure_platform_proxy(), that augments
Python's stdlib 'platform' module so our repository's 'platform/*' package can
be imported via submodules like 'platform.core.step_result' without conflicting
with the stdlib module name.

Call ensure_platform_proxy() as early as possible in any entrypoint before
importing modules that refer to 'platform.core.*'.
"""

from __future__ import annotations

import importlib.machinery
import sys
from pathlib import Path


def ensure_platform_proxy() -> None:
    """Augment stdlib 'platform' to behave as a package with our submodules.

    Safe to call multiple times; no-ops on failure.
    """
    try:
        import platform as _stdlib_platform
    except Exception:
        _stdlib_platform = None

    if _stdlib_platform is None:
        return

    # Compute the repository 'platform' directory: this file lives at
    # src/ultimate_discord_intelligence_bot/core/bootstrap.py
    # so we go up two levels to src/, then join 'platform'.
    try:
        src_dir = Path(__file__).resolve().parents[2]
    except Exception:
        return

    plat_dir = src_dir / "platform"
    if not plat_dir.joinpath("__init__.py").exists():
        return

    try:
        _stdlib_platform.__package__ = "platform"
        _stdlib_platform.__path__ = [str(plat_dir)]
        _stdlib_platform.__spec__ = importlib.machinery.ModuleSpec(name="platform", loader=None, is_package=True)
        sys.modules["platform"] = _stdlib_platform
    except Exception:
        # Fail silently to avoid breaking process start in unusual environments
        return
