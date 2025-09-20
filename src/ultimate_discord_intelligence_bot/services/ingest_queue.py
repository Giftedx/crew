"""Factory for a shared ingest PriorityQueue.

Creates a singleton SQLite-backed PriorityQueue for enqueueing ingest jobs
used by auto-follow backfill and other components. The database path can be
overridden via INGEST_DB_PATH; defaults to data/ingest.db.
"""

from __future__ import annotations

import os
import pathlib
import sqlite3

from ingest.models import connect as connect_models
from scheduler.priority_queue import PriorityQueue

_QUEUE: PriorityQueue | None = None


def _ensure_db_connection(path: str) -> sqlite3.Connection:
    # Ensure parent directory exists
    p = pathlib.Path(path)
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    # Use models.connect to initialize schema
    return connect_models(str(p))


def get_ingest_queue() -> PriorityQueue:
    """Return a process-wide PriorityQueue instance.

    Respects INGEST_DB_PATH environment variable for the SQLite path.
    """
    global _QUEUE
    if _QUEUE is not None:
        return _QUEUE
    db_path = os.getenv("INGEST_DB_PATH", os.path.join("data", "ingest.db"))
    conn = _ensure_db_connection(db_path)
    _QUEUE = PriorityQueue(conn)
    return _QUEUE


__all__ = ["get_ingest_queue"]
