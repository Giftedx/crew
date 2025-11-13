"""Internal Discord package for test helpers and observability modules.

This shim exposes lightweight, internal modules under ``src/discord`` used by
our tests (e.g., ``src.discord.observability``). To maintain backward
compatibility with tests that do ``from discord import commands as dc``, we
expose ``commands`` from the local submodule when available. In production,
code paths that require the real ``discord.py`` gateway should import through
``app.discord.discord_env`` which safely resolves the real dependency or falls
back to a lightweight shim.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Optional


if TYPE_CHECKING:  # for type checkers only; annotations are postponed
    from types import ModuleType


__all__: list[str] = [
    # Intentionally minimal; tests use attribute access rather than * imports.
    "commands",
]

# Provide ``discord.commands`` as an attribute resolving to our local module so
# that ``from discord import commands as dc`` works consistently across
# environments, without requiring the external discord.py package.
commands: ModuleType | None
try:  # pragma: no cover - import-time shim logic
    commands = import_module("discord.commands")
except Exception:  # Circular during first import; load relative
    try:
        commands = import_module(".commands", package=__name__)
    except Exception:
        commands = None
