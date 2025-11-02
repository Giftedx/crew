"""Retention helpers for deleting expired records.

Docstring precedes future import (Ruff E402 compliance).
"""
from __future__ import annotations
import json
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from platform.time import default_utc_now
from policy import policy_engine
if TYPE_CHECKING:
    import sqlite3

def sweep(conn: sqlite3.Connection, *, tenant: str | None=None, now: datetime | None=None) -> int:
    """Delete provenance rows older than the configured max retention."""
    policy = policy_engine.load_policy(tenant)
    days = policy.storage.get('max_retention_days_by_ns', {}).get('default', 30)
    cutoff = (now or default_utc_now()) - timedelta(days=days)
    cur = conn.execute('DELETE FROM provenance WHERE retrieved_at < ?', (cutoff.isoformat(),))
    return cur.rowcount

def export_redacted_dataset(conn: sqlite3.Connection, query: str) -> str:
    cur = conn.execute(query)
    rows = [dict(zip([c[0] for c in cur.description], r, strict=False)) for r in cur.fetchall()]
    return '\n'.join((json.dumps(r) for r in rows))
__all__ = ['export_redacted_dataset', 'sweep']