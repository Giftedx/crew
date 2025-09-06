"""Archive package exposing high-level archival helpers.

Previously this module eagerly imported the Discord FastAPI archive implementation
(`archive.discord_store.api`) which pulled in `fastapi` during *any* import of
`archive` (for example through `memory.api`). This caused test collection to fail
early if optional web dependencies were not yet installed. We now lazy-load the
concrete implementation on first access while keeping the public API stable.

Usage:
        from archive import archive_file  # unchanged

If the Discord archive implementation (and its dependencies) are unavailable,
an ImportError is raised only when `archive_file` is first used—not at import time.
This mirrors other optional-subsystem patterns in the codebase.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

_archive_file: Callable[..., Any] | None = None


def __getattr__(name: str):  # pragma: no cover - simple lazy loader
    if name == "archive_file":
        global _archive_file
        if _archive_file is None:
            try:  # local import to avoid mandatory fastapi dependency
                from .discord_store.api import (
                    archive_file as _impl,  # runtime optional import
                )
            except Exception as e:  # broad to surface clear message
                raise ImportError(
                    "archive_file requires the discord_store implementation and its web dependencies (fastapi)."
                ) from e
            _archive_file = _impl
        return _archive_file
    raise AttributeError(name)


def archive_file(*args, **kwargs):
    """Proxy function so static analyzers & type checkers see a symbol.

    The real implementation is imported lazily. Calling this will trigger the
    import if it has not already occurred.
    """
    return __getattr__("archive_file")(*args, **kwargs)


__all__ = ["archive_file"]
