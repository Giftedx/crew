"""SQLite-backed manifest mapping content hashes to Discord attachments."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

# Backward-compatible path resolution:
# 1. Explicit env var ARCHIVE_DB_PATH wins.
# 2. If legacy root-level file exists (archive_manifest.db) and no data/ version yet, reuse it.
# 3. Otherwise place the DB under data/archive_manifest.db (creating the directory) to keep root tidy.
_LEGACY_DB = Path("archive_manifest.db")
_DATA_DIR = Path("data")
_PREFERRED_DB = _DATA_DIR / "archive_manifest.db"

def _resolve_db_path() -> Path:
    env_path = os.environ.get("ARCHIVE_DB_PATH")
    if env_path:
        return Path(env_path)
    # Legacy file kept if already present and new location absent
    if _LEGACY_DB.exists() and not _PREFERRED_DB.exists():
        return _LEGACY_DB
    # default new location
    if not _DATA_DIR.exists():
        try:
            _DATA_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as exc:  # pragma: no cover - extremely unlikely / non-critical
            logging.getLogger(__name__).debug("Failed creating data dir for archive DB: %s", exc)
    return _PREFERRED_DB

_DB_PATH = _resolve_db_path()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS attachments (
    content_hash TEXT PRIMARY KEY,
    message_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    attachment_ids TEXT NOT NULL,
    filename TEXT NOT NULL,
    size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    tenant TEXT,
    workspace TEXT,
    media_type TEXT,
    visibility TEXT,
    tags TEXT,
    compression TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(_SCHEMA)
    return conn


def record(content_hash: str, meta: dict[str, Any]) -> None:
    """Store ``meta`` under ``content_hash``.

    ``meta`` must contain ``attachment_ids`` as a list of strings and may include
    ``compression`` stats which will be JSON‑encoded for persistence.
    """
    conn = _connect()
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO attachments (
                content_hash, message_id, channel_id, attachment_ids, filename, size, sha256,
                tenant, workspace, media_type, visibility, tags, compression
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                content_hash,
                meta["message_id"],
                meta["channel_id"],
                ",".join(meta["attachment_ids"]),
                meta["filename"],
                meta["size"],
                meta["sha256"],
                meta.get("tenant"),
                meta.get("workspace"),
                meta.get("media_type"),
                meta.get("visibility"),
                ",".join(meta.get("tags", [])),
                json.dumps(meta.get("compression", {})),
            ),
        )
    conn.close()


def lookup(content_hash: str) -> dict[str, Any] | None:
    conn = _connect()
    cur = conn.execute("SELECT * FROM attachments WHERE content_hash = ?", (content_hash,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    columns = [c[0] for c in cur.description]
    rec = dict(zip(columns, row))
    rec["attachment_ids"] = (
        rec.get("attachment_ids", "").split(",") if rec.get("attachment_ids") else []
    )
    if rec.get("tags"):
        rec["tags"] = rec["tags"].split(",")
    if rec.get("compression"):
        try:
            rec["compression"] = json.loads(rec["compression"])
        except json.JSONDecodeError:
            rec["compression"] = {}
    else:
        rec["compression"] = {}
    return rec


def search_tag(tag: str, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
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
