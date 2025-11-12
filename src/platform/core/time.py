"""Compatibility shim for platform.core.time."""

import time as stdlib_time
from datetime import datetime, timezone


def default_utc_now():
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


def ensure_utc(dt):
    """Ensure datetime is in UTC timezone."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


__all__ = ["datetime", "default_utc_now", "ensure_utc", "stdlib_time", "timezone"]
