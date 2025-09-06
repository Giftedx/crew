"""Timezone utilities.

Central place for enforcing UTC normalization so we avoid repeating
"assume naive datetimes are UTC" logic scattered across the codebase.

This is intentionally tiny; expand only if a *clear* second use-case
materialises (keep surface area small to preserve clarity).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

__all__ = ["ensure_utc", "UtcNowProvider", "default_utc_now"]


class UtcNowProvider(Protocol):  # pragma: no cover - structural protocol
    def __call__(self) -> datetime: ...


def ensure_utc(dt: datetime) -> datetime:
    """Return a UTC-aware datetime.

    If ``dt`` is naive, we *assume* it represents a UTC instant (the only
    acceptable naive form in this codebase) and attach the UTC tzinfo.
    """
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def default_utc_now() -> datetime:
    """Wrapper to allow patching in tests if needed."""
    return datetime.now(UTC)
