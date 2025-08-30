"""SQLite-backed storage for unified memory items and retention policies."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class MemoryItem:
    id: int | None
    tenant: str
    workspace: str
    type: str
    content_json: str
    embedding_json: str
    ts_created: str
    ts_last_used: str
    retention_policy: str
    decay_score: float
    pinned: int
    archived: int


@dataclass
class RetentionPolicy:
    name: str
    tenant: str
    ttl_days: int


class MemoryStore:
    """Lightweight memory store with TTL pruning and pin/archive flags."""

    def __init__(self, path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_tables()

    # ------------------------------------------------------------------ schema
    def _ensure_tables(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant TEXT NOT NULL,
                workspace TEXT NOT NULL,
                type TEXT NOT NULL,
                content_json TEXT NOT NULL,
                embedding_json TEXT NOT NULL,
                ts_created TEXT NOT NULL,
                ts_last_used TEXT NOT NULL,
                retention_policy TEXT NOT NULL,
                decay_score REAL DEFAULT 1.0,
                pinned INTEGER DEFAULT 0,
                archived INTEGER DEFAULT 0
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS retention_policies (
                name TEXT NOT NULL,
                tenant TEXT NOT NULL,
                ttl_days INTEGER NOT NULL,
                PRIMARY KEY(name, tenant)
            )
            """
        )
        self.conn.commit()

    # ------------------------------------------------------------------ items
    def add_item(self, item: MemoryItem) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO memory_items (
                tenant, workspace, type, content_json, embedding_json,
                ts_created, ts_last_used, retention_policy, decay_score, pinned, archived
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.tenant,
                item.workspace,
                item.type,
                item.content_json,
                item.embedding_json,
                item.ts_created,
                item.ts_last_used,
                item.retention_policy,
                item.decay_score,
                item.pinned,
                item.archived,
            ),
        )
        self.conn.commit()
        row_id = cur.lastrowid  # Optional[int] per stub
        if row_id is None:  # Extremely unlikely after successful INSERT
            raise RuntimeError("sqlite cursor.lastrowid was None after INSERT")
        return int(row_id)

    def get_item(self, item_id: int) -> MemoryItem | None:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM memory_items WHERE id = ?", (item_id,))
        row = cur.fetchone()
        return MemoryItem(**row) if row else None

    def update_last_used(self, item_id: int, ts: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE memory_items SET ts_last_used = ? WHERE id = ?",
            (ts, item_id),
        )
        self.conn.commit()

    def pin_item(self, item_id: int, pinned: bool = True) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE memory_items SET pinned = ? WHERE id = ?",
            (1 if pinned else 0, item_id),
        )
        self.conn.commit()

    def mark_archived(self, item_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE memory_items SET archived = 1 WHERE id = ?",
            (item_id,),
        )
        self.conn.commit()

    # ------------------------------------------------------------------ policies
    def upsert_policy(self, policy: RetentionPolicy) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO retention_policies(name, tenant, ttl_days)
            VALUES (?, ?, ?)
            ON CONFLICT(name, tenant) DO UPDATE SET ttl_days = excluded.ttl_days
            """,
            (policy.name, policy.tenant, policy.ttl_days),
        )
        self.conn.commit()

    def get_policy(self, tenant: str, name: str) -> RetentionPolicy | None:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM retention_policies WHERE tenant = ? AND name = ?",
            (tenant, name),
        )
        row = cur.fetchone()
        return RetentionPolicy(**row) if row else None

    # ------------------------------------------------------------------ search
    def search_keyword(
        self, tenant: str, workspace: str, text: str, limit: int = 5
    ) -> list[MemoryItem]:
        cur = self.conn.cursor()
        like = f"%{text}%"
        cur.execute(
            """
            SELECT * FROM memory_items
            WHERE tenant = ? AND workspace = ? AND content_json LIKE ?
            ORDER BY ts_last_used DESC
            LIMIT ?
            """,
            (tenant, workspace, like, limit),
        )
        return [MemoryItem(**row) for row in cur.fetchall()]

    # ------------------------------------------------------------------ pruning
    def prune(self, tenant: str, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        cur = self.conn.cursor()
        cur.execute(
            "SELECT name, ttl_days FROM retention_policies WHERE tenant = ?",
            (tenant,),
        )
        policies = {r["name"]: r["ttl_days"] for r in cur.fetchall()}
        deleted_total = 0
        for name, ttl in policies.items():
            cutoff = now - timedelta(days=ttl)
            cur.execute(
                """
                DELETE FROM memory_items
                WHERE tenant = ? AND retention_policy = ? AND pinned = 0
                AND archived = 0 AND ts_last_used < ?
                """,
                (tenant, name, cutoff.isoformat()),
            )
            deleted_total += cur.rowcount
        self.conn.commit()
        return deleted_total


__all__ = ["MemoryItem", "RetentionPolicy", "MemoryStore"]
