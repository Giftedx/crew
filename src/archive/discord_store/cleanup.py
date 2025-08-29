"""Safe cleanup helpers for archived files."""

from __future__ import annotations

from pathlib import Path


def delete(path: str | Path) -> None:
    """Remove ``path`` if it exists."""
    p = Path(path)
    try:
        p.unlink()
    except FileNotFoundError:
        pass


__all__ = ["delete"]
