"""Shared connection-level locks for sqlite3 connections.

Ensures that any code paths sharing a sqlite3.Connection across threads can
coordinate with a single re-entrant lock. Use this to wrap all DB operations
when check_same_thread=False is enabled.
"""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    import sqlite3


_LOCKS: dict[int, RLock] = {}


def get_lock_for_connection(conn: sqlite3.Connection) -> RLock:
    """Return a process-local RLock for the given sqlite3 connection.

    The lock is keyed by id(conn) and reused wherever requested.
    """
    key = id(conn)
    lock = _LOCKS.get(key)
    if lock is None:
        lock = RLock()
        _LOCKS[key] = lock
    return lock
