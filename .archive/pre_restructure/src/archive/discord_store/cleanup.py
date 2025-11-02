"""Safe cleanup helpers for archived files."""

from __future__ import annotations

import contextlib
from pathlib import Path


def delete(path: str | Path) -> None:
    """Remove ``path`` if it exists."""
    p = Path(path)
    with contextlib.suppress(FileNotFoundError):
        p.unlink()


__all__ = ["delete"]
