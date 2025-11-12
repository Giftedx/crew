"""Database locking utilities for thread-safe database operations."""

import threading
from typing import Any


def get_lock_for_connection(connection: Any = None) -> threading.Lock:  # noqa: ARG001
    """Get a thread lock for database connection operations."""
    return threading.Lock()


__all__ = ["get_lock_for_connection"]
