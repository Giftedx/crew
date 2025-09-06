"""Retention helpers for deleting expired records.

Docstring precedes future import (Ruff E402 compliance).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta

from policy import policy_engine


def sweep(conn: sqlite3.Connection, *, tenant: str | None = None, now: datetime | None = None) -> int:
    """Delete provenance rows older than the configured max retention."""
    policy = policy_engine.load_policy(tenant)
    days = policy.storage.get("max_retention_days_by_ns", {}).get("default", 30)
    cutoff = (now or datetime.now(UTC)) - timedelta(days=days)
    cur = conn.execute("DELETE FROM provenance WHERE retrieved_at < ?", (cutoff.isoformat(),))
    return cur.rowcount


def export_redacted_dataset(conn: sqlite3.Connection, query: str) -> str:
    cur = conn.execute(query)
    rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]
    return "\n".join(json.dumps(r) for r in rows)


__all__ = ["sweep", "export_redacted_dataset"]
