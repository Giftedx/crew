"""Compatibility shim for platform.secure_config imports.

Re-exports from platform.core.secure_config for backward compatibility.
"""

# Re-export everything from the actual secure_config module
from platform.core import secure_config as _sc
from platform.core.secure_config import *  # noqa: F403


__all__ = getattr(_sc, "__all__", [])
