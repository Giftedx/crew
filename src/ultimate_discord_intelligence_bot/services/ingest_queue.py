"""Factory for a shared ingest PriorityQueue.

Creates a singleton SQLite-backed PriorityQueue for enqueueing ingest jobs
used by auto-follow backfill and other components. The database path can be
overridden via INGEST_DB_PATH; defaults to data/ingest.db.
"""

from __future__ import annotations

import os
import pathlib
from typing import TYPE_CHECKING

from domains.ingestion.pipeline.models import connect as connect_models
from scheduler.priority_queue import PriorityQueue


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.step_result import StepResult
_QUEUE: PriorityQueue | None = None


def _ensure_db_connection(path: str) -> StepResult:
    p = pathlib.Path(path)
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    return connect_models(str(p))


def get_ingest_queue() -> StepResult:
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
