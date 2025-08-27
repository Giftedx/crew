"""Structured analytics logging utilities.

The :class:`AnalyticsStore` persists high level, privacy-safe metrics about
language model usage and learning events. It uses a small SQLite database so
records can be queried for offline analysis or reinforcement learning feedback.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence
from datetime import datetime


def _as_list(value: Optional[Sequence[str]]) -> str:
    """Return a comma separated list or empty string."""
    if not value:
        return ""
    return ",".join(value)


@dataclass
class AnalyticsStore:
    """Light-weight SQLite store for structured logs.

    Parameters
    ----------
    db_path:
        Location of the SQLite database file. The schema is created on first
        use and contains four tables: ``llm_calls``, ``prompt_variants``,
        ``bandit_events`` and ``human_feedback``. Only ``llm_calls`` is exposed
        via helper methods initially; the remaining tables are placeholders for
        future expansion.
    """

    db_path: str | Path = "analytics.db"

    def __post_init__(self) -> None:  # pragma: no cover - simple setup
        self.path = Path(self.db_path)
        self.conn = sqlite3.connect(self.path)
        self._init_schema()

    # -- schema -----------------------------------------------------------------
    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS llm_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT,
                model TEXT,
                provider TEXT,
                tokens_in INTEGER,
                tokens_out INTEGER,
                cost REAL,
                latency_ms REAL,
                ts TEXT,
                profile_id TEXT,
                success INTEGER,
                toolset TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS prompt_variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT,
                template_hash TEXT,
                description TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS bandit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT,
                context TEXT,
                chosen_arm TEXT,
                reward REAL,
                ts TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS human_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                llm_call_id INTEGER,
                rating INTEGER,
                notes TEXT,
                ts TEXT
            )
            """
        )
        self.conn.commit()

    # -- logging helpers --------------------------------------------------------
    def log_llm_call(
        self,
        task: str,
        model: str,
        provider: str,
        tokens_in: int,
        tokens_out: int,
        cost: float,
        latency_ms: float,
        profile_id: str | None,
        success: bool,
        toolset: Iterable[str] | None = None,
        ts: datetime | None = None,
    ) -> None:
        """Record a language model invocation.

        Only high-level metrics are stored; no prompt or response text is
        persisted to keep the log privacy-safe.
        """

        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO llm_calls (
                task, model, provider, tokens_in, tokens_out, cost,
                latency_ms, ts, profile_id, success, toolset
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task,
                model,
                provider,
                tokens_in,
                tokens_out,
                cost,
                latency_ms,
                (ts or datetime.utcnow()).isoformat(),
                profile_id,
                1 if success else 0,
                _as_list(toolset),
            ),
        )
        self.conn.commit()

    def fetch_llm_calls(self) -> Iterable[tuple[str, str]]:
        """Yield minimal info about logged calls for tests or dashboards."""
        cur = self.conn.cursor()
        for row in cur.execute("SELECT task, model FROM llm_calls"):
            yield row

    def close(self) -> None:  # pragma: no cover - trivial
        self.conn.close()
