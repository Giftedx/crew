"""OpenRouter LLM provider with automatic module forwarding.

This module automatically forwards imports from the openrouter_service subdirectory
for backward compatibility with code that expects a flat module structure.
"""

import sys as _sys
from typing import Any as _Any

from .openrouter_service import OpenRouterService


__all__ = ["OpenRouterService"]


def __getattr__(name: str) -> _Any:
    """Automatically forward module lookups to openrouter_service subdirectory.

    This allows imports like:
        from platform.llm.providers.openrouter.context import ...
    to work even though context.py is actually in openrouter_service/context.py
    """
    # Check if we've already loaded this submodule
    full_module_name = f"platform.llm.providers.openrouter.{name}"
    if full_module_name in _sys.modules:
        return _sys.modules[full_module_name]

    # Try to import from openrouter_service subdirectory
    try:
        from importlib import import_module

        submodule = import_module(f".openrouter_service.{name}", package="platform.llm.providers.openrouter")
        _sys.modules[full_module_name] = submodule
        return submodule
    except (ImportError, ModuleNotFoundError):
        raise AttributeError(f"module 'platform.llm.providers.openrouter' has no attribute '{name}'") from None


def __dir__() -> list[str]:
    """Include openrouter_service submodules in dir() output."""
    from pathlib import Path

    base_dir = Path(__file__).parent / "openrouter_service"
    submodules = [f.stem for f in base_dir.glob("*.py") if f.stem != "__init__"]
    return list(__all__) + submodules
