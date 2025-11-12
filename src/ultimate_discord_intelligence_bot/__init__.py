"""Primary package for ultimate_discord_intelligence_bot.

Presence of this module plus an inline ``py.typed`` marker in the directory
ensures type checkers (mypy, pyright) treat the code as typed application
code rather than an untyped third-party dependency.
"""

# Ensure src directory is in path for absolute imports from domains/
import sys
from typing import Any


_src_path = "/home/crew/src"
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)


__all__: list[str] = []


# Backward-compat re-exports for moved features (import lazily)
def __getattr__(name: str) -> Any:  # pragma: no cover
    if name == "features":
        import importlib

        return importlib.import_module("ultimate_discord_intelligence_bot.features")
    raise AttributeError(name)
