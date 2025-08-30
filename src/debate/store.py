"""SQLite storage for debate sessions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass
class Debate:
    id: int | None
    tenant: str
    workspace: str
    query: str
    panel_config_json: str
    n_rounds: int
    final_output: str
    created_at: str


@dataclass
class DebateAgent:
    id: int | None
    debate_id: int
    role: str
    model: str
    output: str
    cost_usd: float
    latency_ms: float
    round: int
    confidence: float


@dataclass
class DebateCritique:
    id: int | None
    debate_id: int
    from_role: str
    target_role: str
    content: str
    round: int


@dataclass
class DebateVote:
    id: int | None
    debate_id: int
    voter_role: str
    chosen_role: str
    reason: str
    round: int


class DebateStore:
    """Lightweight SQLite-backed debate store."""

    def __init__(self, path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS debates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant TEXT NOT NULL,
                workspace TEXT NOT NULL,
                query TEXT NOT NULL,
                panel_config_json TEXT NOT NULL,
                n_rounds INTEGER NOT NULL,
                final_output TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS debate_agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                debate_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                model TEXT NOT NULL,
                output TEXT NOT NULL,
                cost_usd REAL DEFAULT 0,
                latency_ms REAL DEFAULT 0,
                round INTEGER NOT NULL,
                confidence REAL DEFAULT 0,
                FOREIGN KEY(debate_id) REFERENCES debates(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS debate_critiques (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                debate_id INTEGER NOT NULL,
                from_role TEXT NOT NULL,
                target_role TEXT NOT NULL,
                content TEXT NOT NULL,
                round INTEGER NOT NULL,
                FOREIGN KEY(debate_id) REFERENCES debates(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS debate_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                debate_id INTEGER NOT NULL,
                voter_role TEXT NOT NULL,
                chosen_role TEXT NOT NULL,
                reason TEXT,
                round INTEGER NOT NULL,
                FOREIGN KEY(debate_id) REFERENCES debates(id)
            )
            """
        )
        self.conn.commit()

    def add_debate(self, debate: Debate) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO debates (tenant, workspace, query, panel_config_json, n_rounds, final_output, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                debate.tenant,
                debate.workspace,
                debate.query,
                debate.panel_config_json,
                debate.n_rounds,
                debate.final_output,
                debate.created_at,
            ),
        )
        self.conn.commit()
        row_id = cur.lastrowid
        if row_id is None:
            raise RuntimeError("Expected lastrowid after inserting debate")
        return int(row_id)

    def list_debates(self, tenant: str, workspace: str) -> list[Debate]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM debates WHERE tenant = ? AND workspace = ? ORDER BY id DESC",
            (tenant, workspace),
        )
        return [Debate(**row) for row in cur.fetchall()]


__all__ = [
    "Debate",
    "DebateAgent",
    "DebateCritique",
    "DebateVote",
    "DebateStore",
]
