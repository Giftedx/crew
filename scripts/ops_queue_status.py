#!/usr/bin/env python3
"""Print scheduler queue backlog by tenant/workspace.

Usage:
  python scripts/ops_queue_status.py --db path/to/sched.db

Outputs a simple table of pending job counts grouped by tenant/workspace and a total.
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="Path to scheduler sqlite database (ingest_job table)")
    args = ap.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"DB not found: {db_path}")
        return 2
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT tenant, workspace, COUNT(*) FROM ingest_job WHERE status='pending' GROUP BY tenant, workspace"
    ).fetchall()
    total = cur.execute("SELECT COUNT(*) FROM ingest_job WHERE status='pending'").fetchone()[0]
    print("tenant\tworkspace\tpending")
    for tenant, workspace, count in rows:
        print(f"{tenant}\t{workspace}\t{count}")
    print(f"TOTAL\t-\t{total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

