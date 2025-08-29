from __future__ import annotations

"""SQLite-backed knowledge graph store with tenant isolation."""

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass
class KGNode:
    id: int | None
    tenant: str
    type: str
    name: str
    attrs_json: str
    created_at: str


@dataclass
class KGEdge:
    id: int | None
    src_id: int
    dst_id: int
    type: str
    weight: float
    provenance_id: int | None
    created_at: str


class KGStore:
    """Lightweight store for knowledge graph nodes and edges."""

    def __init__(self, path: str = ":memory:"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS kg_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant TEXT NOT NULL,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                attrs_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS kg_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                src_id INTEGER NOT NULL,
                dst_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                provenance_id INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY(src_id) REFERENCES kg_nodes(id),
                FOREIGN KEY(dst_id) REFERENCES kg_nodes(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS kg_provenance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER NOT NULL,
                source_url TEXT,
                episode_id TEXT,
                transcript_span TEXT,
                speaker TEXT,
                retrieved_at TEXT,
                license TEXT,
                checksum_sha256 TEXT,
                FOREIGN KEY(node_id) REFERENCES kg_nodes(id)
            )
            """
        )
        self.conn.commit()

    # Node operations
    def add_node(
        self, tenant: str, type: str, name: str, attrs: dict | None = None, created_at: str = ""
    ) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO kg_nodes (tenant, type, name, attrs_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (tenant, type, name, json.dumps(attrs or {}), created_at),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def query_nodes(
        self, tenant: str, *, type: str | None = None, name: str | None = None
    ) -> list[KGNode]:
        cur = self.conn.cursor()
        conditions = ["tenant = ?"]
        params: list[Any] = [tenant]
        if type:
            conditions.append("type = ?")
            params.append(type)
        if name:
            conditions.append("name = ?")
            params.append(name)
        cur.execute(f"SELECT * FROM kg_nodes WHERE {' AND '.join(conditions)}", params)
        rows = cur.fetchall()
        return [KGNode(**row) for row in rows]

    def get_node(self, node_id: int) -> KGNode | None:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM kg_nodes WHERE id = ?", (node_id,))
        row = cur.fetchone()
        return KGNode(**row) if row else None

    # Edge operations
    def add_edge(
        self,
        src_id: int,
        dst_id: int,
        type: str,
        *,
        weight: float = 1.0,
        provenance_id: int | None = None,
        created_at: str = "",
    ) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO kg_edges (src_id, dst_id, type, weight, provenance_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (src_id, dst_id, type, weight, provenance_id, created_at),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def query_edges(
        self, *, src_id: int | None = None, dst_id: int | None = None, type: str | None = None
    ) -> list[KGEdge]:
        cur = self.conn.cursor()
        conditions: list[str] = []
        params: list[Any] = []
        if src_id is not None:
            conditions.append("src_id = ?")
            params.append(src_id)
        if dst_id is not None:
            conditions.append("dst_id = ?")
            params.append(dst_id)
        if type is not None:
            conditions.append("type = ?")
            params.append(type)
        clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        cur.execute(f"SELECT * FROM kg_edges{clause}", params)
        rows = cur.fetchall()
        return [KGEdge(**row) for row in rows]

    def neighbors(self, node_id: int, depth: int = 1) -> Iterable[int]:
        """Return node IDs reachable within ``depth`` hops."""
        seen = {node_id}
        frontier = {node_id}
        for _ in range(depth):
            if not frontier:
                break
            cur = self.conn.cursor()
            q_marks = ",".join(["?"] * len(frontier))
            cur.execute(f"SELECT dst_id FROM kg_edges WHERE src_id IN ({q_marks})", list(frontier))
            rows = {r[0] for r in cur.fetchall()}
            rows -= seen
            seen |= rows
            frontier = rows
        return seen - {node_id}
