"""Compatibility settings facade.

This module provides a stable import surface ``core.settings`` that proxies to
``core.secure_config``. It preserves the historical API used across the codebase
and tests:

- ``get_settings()`` → returns a settings object (SecureConfig)
- ``reload_settings()`` → reloads settings from environment
- Attribute access on the module (e.g. ``settings.qdrant_url``) transparently
  forwards to the underlying configuration instance for convenience.

This thin shim eliminates ImportError issues in modules and tests that expect
``core.settings`` to exist, while centralizing the true configuration logic in
``core.secure_config``.
"""

from __future__ import annotations

from typing import Any

from core.secure_config import SecureConfig, get_config, reload_config


def get_settings() -> SecureConfig:
    """Return the global settings object.

    Returns:
        SecureConfig: The singleton configuration instance.
    """
    return get_config()


def reload_settings() -> SecureConfig:
    """Reload settings from the environment and return the new instance."""
    return reload_config()


def __getattr__(name: str) -> Any:  # pragma: no cover - thin delegation
    """Dynamic attribute delegation to the SecureConfig instance.

    Allows idioms like ``from core import settings; settings.qdrant_url`` to
    keep working while the true values live in ``SecureConfig``.
    """
    return getattr(get_config(), name)


__all__ = ["SecureConfig", "get_settings", "reload_settings"]
