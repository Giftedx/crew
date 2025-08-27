"""SQLite-backed manifest mapping content hashes to Discord attachments."""
from __future__ import annotations
import hashlib
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

_DB_PATH = Path(os.environ.get("ARCHIVE_DB_PATH", "archive_manifest.db"))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS attachments (
    content_hash TEXT PRIMARY KEY,
    message_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    attachment_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    tenant TEXT,
    workspace TEXT,
    media_type TEXT,
    visibility TEXT,
    tags TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""


def _connect():
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(_SCHEMA)
    return conn


def record(content_hash: str, meta: Dict[str, Any]) -> None:
    conn = _connect()
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO attachments (
                content_hash, message_id, channel_id, attachment_id, filename, size, sha256,
                tenant, workspace, media_type, visibility, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                content_hash,
                meta["message_id"],
                meta["channel_id"],
                meta["attachment_id"],
                meta["filename"],
                meta["size"],
                meta["sha256"],
                meta.get("tenant"),
                meta.get("workspace"),
                meta.get("media_type"),
                meta.get("visibility"),
                ",".join(meta.get("tags", [])),
            ),
        )
    conn.close()


def lookup(content_hash: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    cur = conn.execute("SELECT * FROM attachments WHERE content_hash = ?", (content_hash,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    columns = [c[0] for c in cur.description]
    return dict(zip(columns, row))


def search_tag(tag: str, limit: int = 20, offset: int = 0) -> list[Dict[str, Any]]:
    conn = _connect()
    cur = conn.execute(
        "SELECT content_hash, filename, tags FROM attachments WHERE tags LIKE ? LIMIT ? OFFSET ?",
        (f"%{tag}%", limit, offset),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(zip([c[0] for c in cur.description], r)) for r in rows]


def compute_hash(path: str | Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(8192)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()

__all__ = ["record", "lookup", "compute_hash", "search_tag"]
