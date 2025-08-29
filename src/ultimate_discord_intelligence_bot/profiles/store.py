"""SQLite-backed storage for creator profiles."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from .schema import CreatorProfile


class ProfileStore:
    """Persist and retrieve :class:`CreatorProfile` records."""

    def __init__(self, db_path: str | Path = "profiles.db") -> None:
        self.path = Path(db_path)
        self.conn = sqlite3.connect(self.path)
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                name TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cross_profile_links (
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                count INTEGER NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                PRIMARY KEY (source, target)
            )
            """
        )
        self.conn.commit()

    def upsert_profile(self, profile: CreatorProfile) -> None:
        data = json.dumps(profile.to_dict())
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO profiles (name, data) VALUES (?, ?)",
            (profile.name, data),
        )
        self.conn.commit()

    def get_profile(self, name: str) -> CreatorProfile | None:
        cur = self.conn.cursor()
        row = cur.execute("SELECT data FROM profiles WHERE name = ?", (name,)).fetchone()
        if not row:
            return None
        data = json.loads(row[0])
        return CreatorProfile.from_dict(data)

    def all_profiles(self) -> Iterable[CreatorProfile]:
        cur = self.conn.cursor()
        for (data,) in cur.execute("SELECT data FROM profiles"):
            yield CreatorProfile.from_dict(json.loads(data))

    # -- Cross profile links -------------------------------------------------

    def record_link(self, source: str, target: str, timestamp: datetime) -> None:
        """Record that ``source`` appeared with ``target`` at ``timestamp``."""
        cur = self.conn.cursor()
        row = cur.execute(
            "SELECT count, first_seen FROM cross_profile_links WHERE source = ? AND target = ?",
            (source, target),
        ).fetchone()
        if row:
            count, first_seen = row
            cur.execute(
                "UPDATE cross_profile_links SET count = ?, last_seen = ? WHERE source = ? AND target = ?",
                (count + 1, timestamp.isoformat(), source, target),
            )
        else:
            cur.execute(
                "INSERT INTO cross_profile_links (source, target, count, first_seen, last_seen) VALUES (?, ?, ?, ?, ?)",
                (source, target, 1, timestamp.isoformat(), timestamp.isoformat()),
            )
        self.conn.commit()

    def get_collaborators(self, creator: str, limit: int = 10) -> list[tuple[str, int]]:
        """Return collaborators for ``creator`` ordered by appearance count."""
        cur = self.conn.cursor()
        rows = cur.execute(
            "SELECT target, count FROM cross_profile_links WHERE source = ? ORDER BY count DESC LIMIT ?",
            (creator, limit),
        ).fetchall()
        return [(r[0], r[1]) for r in rows]

    def close(self) -> None:
        self.conn.close()
