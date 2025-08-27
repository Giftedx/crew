from __future__ import annotations

"""Retention helpers for deleting expired records."""

from datetime import datetime, timedelta, timezone
import sqlite3
from typing import Dict

from policy import policy_engine
import json


def sweep(conn: sqlite3.Connection, *, tenant: str | None = None, now: datetime | None = None) -> int:
    """Delete provenance rows older than the configured max retention."""
    policy = policy_engine.load_policy(tenant)
    days = policy.storage.get("max_retention_days_by_ns", {}).get("default", 30)
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=days)
    cur = conn.execute("DELETE FROM provenance WHERE retrieved_at < ?", (cutoff.isoformat(),))
    return cur.rowcount


def export_redacted_dataset(conn: sqlite3.Connection, query: str) -> str:
    cur = conn.execute(query)
    rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]
    return "\n".join(json.dumps(r) for r in rows)


__all__ = ["sweep", "export_redacted_dataset"]
