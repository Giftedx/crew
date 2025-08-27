"""Environment-driven feature flags."""
from __future__ import annotations

import os


def enabled(name: str, default: bool = False) -> bool:
    """Return True if the environment flag ``name`` is enabled."""
    val = os.getenv(name.upper())
    if val is None:
        return default
    return val.lower() in {"1", "true", "yes", "on"}


__all__ = ["enabled"]
