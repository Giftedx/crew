"""Primary package for ultimate_discord_intelligence_bot.

Presence of this module plus an inline ``py.typed`` marker in the directory
ensures type checkers (mypy, pyright) treat the code as typed application
code rather than an untyped third-party dependency.
"""

from typing import Any


__all__: list[str] = []


# Backward-compat re-exports for moved features (import lazily)
def __getattr__(name: str) -> Any:  # pragma: no cover
    if name == "features":
        import importlib

        return importlib.import_module("ultimate_discord_intelligence_bot.features")
    raise AttributeError(name)
