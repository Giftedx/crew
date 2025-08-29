"""Input validation utilities.

Provides helpers to validate URLs, file names, MIME types, and file paths
before using them. These helpers raise ``ValueError`` on invalid inputs.
"""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path

from . import net_guard


def validate_url(url: str) -> str:
    """Return ``url`` if safe, else raise ``ValueError``.

    Checks scheme and ensures the host is public using ``net_guard``.
    """
    if not net_guard.is_safe_url(url):
        raise ValueError("unsafe url")
    return url


def validate_filename(name: str) -> str:
    """Return ``name`` if it contains no path separators or traversal parts."""
    if not name or os.path.basename(name) != name or name in {"..", "."}:
        raise ValueError("invalid filename")
    if any(part in {"..", ""} for part in Path(name).parts):
        raise ValueError("invalid filename")
    return name


def validate_path(path: str | Path, base: str | Path) -> Path:
    """Join ``path`` to ``base`` and ensure the result stays within ``base``.

    Returns the resolved ``Path`` on success.
    """
    base_path = Path(base).resolve()
    resolved = (base_path / Path(path)).resolve()
    try:
        resolved.relative_to(base_path)
    except ValueError:
        raise ValueError("path traversal detected")
    return resolved


def validate_mime(filename: str, mime: str | None) -> None:
    """Validate that ``mime`` matches the guessed type for ``filename``.

    Raises ``ValueError`` if ``mime`` is present and mismatched.
    """
    guessed, _ = mimetypes.guess_type(filename)
    if mime and guessed and guessed != mime:
        raise ValueError("mime mismatch")
