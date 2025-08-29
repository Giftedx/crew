"""SQLite storage for marketplace metadata."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .models import Signer


class MarketplaceStore:
    """Persist marketplace records in a small SQLite database."""

    def __init__(self, db_path: str | Path = "marketplace.db") -> None:
        self.path = Path(db_path)
        self.conn = sqlite3.connect(self.path)
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        # repositories
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS mp_repos (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
            """
        )
        # plugins
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS mp_plugins (
                id TEXT PRIMARY KEY,
                repo_id TEXT NOT NULL,
                data TEXT NOT NULL
            )
            """
        )
        # signers
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS mp_signers (
                fingerprint TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
            """
        )
        # releases
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS mp_releases (
                plugin_id TEXT NOT NULL,
                version TEXT NOT NULL,
                data TEXT NOT NULL,
                PRIMARY KEY (plugin_id, version)
            )
            """
        )
        # advisories
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS mp_advisories (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
            """
        )
        # installs
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS mp_installs (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
            """
        )
        # rollouts
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS mp_rollouts (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    # signer helpers -------------------------------------------------
    def upsert_signer(self, signer: Signer) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO mp_signers(fingerprint, data) VALUES(?, ?)
            ON CONFLICT(fingerprint) DO UPDATE SET data=excluded.data
            """,
            (signer.fingerprint, json.dumps(asdict(signer), default=str)),
        )
        self.conn.commit()

    def get_signer(self, fingerprint: str) -> Signer | None:
        cur = self.conn.cursor()
        cur.execute("SELECT data FROM mp_signers WHERE fingerprint=?", (fingerprint,))
        row = cur.fetchone()
        if not row:
            return None
        data = json.loads(row[0])
        return Signer(
            fingerprint=data["fingerprint"],
            issuer=data["issuer"],
            subject=data["subject"],
            trust_tier=data["trust_tier"],
            revoked=data["revoked"],
            not_before=datetime.fromisoformat(data["not_before"]),
            not_after=datetime.fromisoformat(data["not_after"]),
        )
