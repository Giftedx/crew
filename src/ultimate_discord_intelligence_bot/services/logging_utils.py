"""Structured analytics logging utilities.

The :class:`AnalyticsStore` persists high level, privacy-safe metrics about
language model usage and learning events. It uses a small SQLite database so
records can be queried for offline analysis or reinforcement learning feedback.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from core.time import default_utc_now


def _as_list(value: Iterable[str] | None) -> str:
    """Return a comma separated list or empty string."""
    if not value:
        return ""
    # Ensure we only join strings (defensive); convert any non-str via str()
    return ",".join(str(v) for v in value)


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
    def log_llm_call(  # noqa: PLR0913 - arguments map 1:1 to schema columns; grouping preserves explicitness
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
    ) -> None:  # noqa: PLR0913 - arguments mirror fixed analytics schema columns; packing into **kwargs loses type safety
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
                (ts or default_utc_now()).isoformat(),
                profile_id,
                1 if success else 0,
                _as_list(toolset),
            ),
        )
        self.conn.commit()

    def fetch_llm_calls(self) -> Iterable[tuple[str, str]]:
        """Yield minimal info about logged calls for tests or dashboards."""
        cur = self.conn.cursor()
        yield from cur.execute("SELECT task, model FROM llm_calls")

    def close(self) -> None:  # pragma: no cover - trivial
        self.conn.close()

    def log_bandit_event(self, event: dict[str, Any], ts: datetime | None = None) -> None:
        """Persist adaptive routing or bandit feedback events."""

        payload = {key: value for key, value in event.items() if key not in {"task_type", "model", "reward"}}
        context_blob = json.dumps(payload, default=str)
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO bandit_events (task, context, chosen_arm, reward, ts)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(event.get("task_type", "unknown")),
                context_blob,
                str(event.get("model", "")),
                float(event.get("reward", 0.0) or 0.0),
                (ts or default_utc_now()).isoformat(),
            ),
        )
        self.conn.commit()
