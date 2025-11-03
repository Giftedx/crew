"""Time utilities for the platform package.

Provides UTC-aware helpers used across observability and security modules.
"""

from __future__ import annotations

from datetime import datetime, timezone


__all__ = ["default_utc_now", "ensure_utc"]


def default_utc_now() -> datetime:
    """Return the current time as an aware datetime in UTC.

    Centralized here to avoid scattered imports and to make testing easier.
    """
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """Ensure a datetime has UTC tzinfo.

    If ``dt`` is naive, assume it is already in UTC and attach tzinfo.
    If ``dt`` is aware, convert it to UTC.
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
