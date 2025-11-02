"""Structured analytics logging utilities.

The :class:`AnalyticsStore` persists high level, privacy-safe metrics about
language model usage and learning events. It uses a small SQLite database so
records can be queried for offline analysis or reinforcement learning feedback.
"""
from __future__ import annotations
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any
from core.time import default_utc_now
if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime
    from platform.core.step_result import StepResult

def _as_list(value: Iterable[str] | None) -> StepResult:
    """Return a comma separated list or empty string."""
    if not value:
        return ''
    return ','.join((str(v) for v in value))

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
    db_path: str | Path = 'analytics.db'

    def __post_init__(self) -> StepResult:
        self.path = Path(self.db_path)
        self.conn = sqlite3.connect(self.path)
        self._init_schema()

    def _init_schema(self) -> StepResult:
        cur = self.conn.cursor()
        cur.execute('\n            CREATE TABLE IF NOT EXISTS llm_calls (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                task TEXT,\n                model TEXT,\n                provider TEXT,\n                tokens_in INTEGER,\n                tokens_out INTEGER,\n                cost REAL,\n                latency_ms REAL,\n                ts TEXT,\n                profile_id TEXT,\n                success INTEGER,\n                toolset TEXT\n            )\n            ')
        cur.execute('\n            CREATE TABLE IF NOT EXISTS prompt_variants (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                task TEXT,\n                template_hash TEXT,\n                description TEXT\n            )\n            ')
        cur.execute('\n            CREATE TABLE IF NOT EXISTS bandit_events (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                task TEXT,\n                context TEXT,\n                chosen_arm TEXT,\n                reward REAL,\n                ts TEXT\n            )\n            ')
        cur.execute('\n            CREATE TABLE IF NOT EXISTS human_feedback (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                llm_call_id INTEGER,\n                rating INTEGER,\n                notes TEXT,\n                ts TEXT\n            )\n            ')
        self.conn.commit()

    def log_llm_call(self, task: str, model: str, provider: str, tokens_in: int, tokens_out: int, cost: float, latency_ms: float, profile_id: str | None, success: bool, toolset: Iterable[str] | None=None, ts: datetime | None=None) -> StepResult:
        """Record a language model invocation.

        Only high-level metrics are stored; no prompt or response text is
        persisted to keep the log privacy-safe.
        """
        cur = self.conn.cursor()
        cur.execute('\n            INSERT INTO llm_calls (\n                task, model, provider, tokens_in, tokens_out, cost,\n                latency_ms, ts, profile_id, success, toolset\n            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ', (task, model, provider, tokens_in, tokens_out, cost, latency_ms, (ts or default_utc_now()).isoformat(), profile_id, 1 if success else 0, _as_list(toolset)))
        self.conn.commit()

    def fetch_llm_calls(self) -> StepResult:
        """Yield minimal info about logged calls for tests or dashboards."""
        cur = self.conn.cursor()
        yield from cur.execute('SELECT task, model FROM llm_calls')

    def close(self) -> StepResult:
        self.conn.close()

    def log_bandit_event(self, event: dict[str, Any], ts: datetime | None=None) -> StepResult:
        """Persist adaptive routing or bandit feedback events."""
        payload = {key: value for key, value in event.items() if key not in {'task_type', 'model', 'reward'}}
        context_blob = json.dumps(payload, default=str)
        cur = self.conn.cursor()
        cur.execute('\n            INSERT INTO bandit_events (task, context, chosen_arm, reward, ts)\n            VALUES (?, ?, ?, ?, ?)\n            ', (str(event.get('task_type', 'unknown')), context_blob, str(event.get('model', '')), float(event.get('reward', 0.0) or 0.0), (ts or default_utc_now()).isoformat()))
        self.conn.commit()