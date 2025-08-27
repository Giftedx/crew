from __future__ import annotations

"""Lightweight SQLite-backed data models for ingestion metadata."""

from dataclasses import dataclass
from typing import Optional
import sqlite3


@dataclass
class CreatorProfile:
    id: Optional[int]
    slug: str
    youtube_id: Optional[str] = None
    twitch_id: Optional[str] = None
    verified: bool = False
    last_checked_at: Optional[str] = None


@dataclass
class Episode:
    id: Optional[int]
    creator_id: int
    platform: str
    external_id: str
    url: str
    title: str
    published_at: Optional[str]
    duration: Optional[float]
    visibility: str


@dataclass
class TranscriptSegment:
    id: Optional[int]
    episode_id: int
    start: float
    end: float
    text: str
    speaker: Optional[str] = None


@dataclass
class IngestLog:
    id: Optional[int]
    episode_id: int
    status: str
    details: str
    created_at: str


@dataclass
class Provenance:
    id: Optional[int]
    content_id: str
    source_url: str
    source_type: str
    retrieved_at: str
    license: str
    terms_url: Optional[str]
    consent_flags: Optional[str]
    checksum_sha256: str
    creator_id: Optional[int] = None
    episode_id: Optional[int] = None


@dataclass
class UsageLog:
    id: Optional[int]
    call_id: str
    content_ids: str
    policy_version: str
    decisions: str
    redactions: str
    output_hash: str
    user_cmd: str
    channel_id: str
    ts: str


SCHEMA = """
CREATE TABLE IF NOT EXISTS creator_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE,
    youtube_id TEXT,
    twitch_id TEXT,
    verified INTEGER,
    last_checked_at TEXT
);
CREATE TABLE IF NOT EXISTS episode (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER,
    platform TEXT,
    external_id TEXT,
    url TEXT,
    title TEXT,
    published_at TEXT,
    duration REAL,
    visibility TEXT
);
CREATE TABLE IF NOT EXISTS transcript_segment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER,
    start REAL,
    end REAL,
    text TEXT,
    speaker TEXT
);
CREATE TABLE IF NOT EXISTS ingest_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER,
    status TEXT,
    details TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id TEXT,
    source_url TEXT,
    source_type TEXT,
    retrieved_at TEXT,
    license TEXT,
    terms_url TEXT,
    consent_flags TEXT,
    checksum_sha256 TEXT,
    creator_id INTEGER,
    episode_id INTEGER
);
CREATE TABLE IF NOT EXISTS usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id TEXT,
    content_ids TEXT,
    policy_version TEXT,
    decisions TEXT,
    redactions TEXT,
    output_hash TEXT,
    user_cmd TEXT,
    channel_id TEXT,
    ts TEXT
);
"""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def record_provenance(conn: sqlite3.Connection, prov: Provenance) -> None:
    conn.execute(
        "INSERT INTO provenance (content_id, source_url, source_type, retrieved_at, license, terms_url, consent_flags, checksum_sha256, creator_id, episode_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            prov.content_id,
            prov.source_url,
            prov.source_type,
            prov.retrieved_at,
            prov.license,
            prov.terms_url,
            prov.consent_flags,
            prov.checksum_sha256,
            prov.creator_id,
            prov.episode_id,
        ),
    )
    conn.commit()


def record_usage(conn: sqlite3.Connection, usage: UsageLog) -> None:
    conn.execute(
        "INSERT INTO usage_log (call_id, content_ids, policy_version, decisions, redactions, output_hash, user_cmd, channel_id, ts) VALUES (?,?,?,?,?,?,?,?,?)",
        (
            usage.call_id,
            usage.content_ids,
            usage.policy_version,
            usage.decisions,
            usage.redactions,
            usage.output_hash,
            usage.user_cmd,
            usage.channel_id,
            usage.ts,
        ),
    )
    conn.commit()
