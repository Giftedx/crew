"""Lightweight SQLite-backed data models for ingestion metadata."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from core.time import default_utc_now


@dataclass
class CreatorProfile:
    id: int | None
    slug: str
    youtube_id: str | None = None
    twitch_id: str | None = None
    verified: bool = False
    last_checked_at: str | None = None


@dataclass
class Episode:
    id: int | None
    creator_id: int
    platform: str
    external_id: str
    url: str
    title: str
    published_at: str | None
    duration: float | None
    visibility: str


@dataclass
class TranscriptSegment:
    id: int | None
    episode_id: int
    start: float
    end: float
    text: str
    speaker: str | None = None


@dataclass
class IngestLog:
    id: int | None
    episode_id: int
    status: str
    details: str
    created_at: str


@dataclass
class Provenance:
    id: int | None
    content_id: str
    source_url: str
    source_type: str
    retrieved_at: str
    license: str
    terms_url: str | None
    consent_flags: str | None
    checksum_sha256: str
    creator_id: int | None = None
    episode_id: int | None = None


@dataclass
class UsageLog:
    id: int | None
    call_id: str
    content_ids: str
    policy_version: str
    decisions: str
    redactions: str
    output_hash: str
    user_cmd: str
    channel_id: str
    ts: str


@dataclass
class Watchlist:
    id: int | None
    tenant: str
    workspace: str
    source_type: str
    handle: str
    label: str | None
    enabled: bool = True
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class IngestState:
    id: int | None
    watchlist_id: int
    cursor: str | None
    last_seen_at: str | None
    etag: str | None
    failure_count: int = 0
    backoff_until: str | None = None


@dataclass
class IngestJobRecord:
    id: int | None
    tenant: str
    workspace: str
    source_type: str
    external_id: str
    url: str
    tags: str
    visibility: str
    priority: int
    status: str
    attempts: int
    scheduled_at: str
    picked_at: str | None = None
    finished_at: str | None = None
    error: str | None = None


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
CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant TEXT,
    workspace TEXT,
    source_type TEXT,
    handle TEXT,
    label TEXT,
    enabled INTEGER,
    created_at TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS ingest_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watchlist_id INTEGER,
    cursor TEXT,
    last_seen_at TEXT,
    etag TEXT,
    failure_count INTEGER,
    backoff_until TEXT
);
CREATE TABLE IF NOT EXISTS ingest_job (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant TEXT,
    workspace TEXT,
    source_type TEXT,
    external_id TEXT,
    url TEXT,
    tags TEXT,
    visibility TEXT,
    priority INTEGER,
    status TEXT,
    attempts INTEGER,
    scheduled_at TEXT,
    picked_at TEXT,
    finished_at TEXT,
    error TEXT
);

-- Performance indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_creator_profile_slug ON creator_profile(slug);
CREATE INDEX IF NOT EXISTS idx_creator_profile_youtube_id ON creator_profile(youtube_id);
CREATE INDEX IF NOT EXISTS idx_creator_profile_twitch_id ON creator_profile(twitch_id);

CREATE INDEX IF NOT EXISTS idx_episode_creator_id ON episode(creator_id);
CREATE INDEX IF NOT EXISTS idx_episode_external_id ON episode(external_id);
CREATE INDEX IF NOT EXISTS idx_episode_platform ON episode(platform);
CREATE INDEX IF NOT EXISTS idx_episode_published_at ON episode(published_at);

CREATE INDEX IF NOT EXISTS idx_transcript_segment_episode_id ON transcript_segment(episode_id);
CREATE INDEX IF NOT EXISTS idx_transcript_segment_start ON transcript_segment(start);

CREATE INDEX IF NOT EXISTS idx_ingest_log_episode_id ON ingest_log(episode_id);
CREATE INDEX IF NOT EXISTS idx_ingest_log_status ON ingest_log(status);

CREATE INDEX IF NOT EXISTS idx_provenance_content_id ON provenance(content_id);
CREATE INDEX IF NOT EXISTS idx_provenance_source_type ON provenance(source_type);
CREATE INDEX IF NOT EXISTS idx_provenance_checksum ON provenance(checksum_sha256);

CREATE INDEX IF NOT EXISTS idx_usage_log_call_id ON usage_log(call_id);
CREATE INDEX IF NOT EXISTS idx_usage_log_ts ON usage_log(ts);
CREATE INDEX IF NOT EXISTS idx_usage_log_channel_id ON usage_log(channel_id);

CREATE INDEX IF NOT EXISTS idx_watchlist_tenant_workspace ON watchlist(tenant, workspace);
CREATE INDEX IF NOT EXISTS idx_watchlist_source_type ON watchlist(source_type);
CREATE INDEX IF NOT EXISTS idx_watchlist_enabled ON watchlist(enabled);

CREATE INDEX IF NOT EXISTS idx_ingest_state_watchlist_id ON ingest_state(watchlist_id);
CREATE INDEX IF NOT EXISTS idx_ingest_state_failure_count ON ingest_state(failure_count);

CREATE INDEX IF NOT EXISTS idx_ingest_job_tenant_workspace ON ingest_job(tenant, workspace);
CREATE INDEX IF NOT EXISTS idx_ingest_job_status ON ingest_job(status);
CREATE INDEX IF NOT EXISTS idx_ingest_job_priority ON ingest_job(priority);
CREATE INDEX IF NOT EXISTS idx_ingest_job_scheduled_at ON ingest_job(scheduled_at);
"""


def connect(path: str) -> sqlite3.Connection:
    # Allow use across threads; we serialize access at higher layers with locks
    conn = sqlite3.connect(path, check_same_thread=False)
    # Improve concurrency characteristics for multiple writers/readers
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
    except Exception:
        pass
    conn.executescript(SCHEMA)
    return conn


# ------------------------------------------------------------ uploader tracking helpers
def _slug_namespace(tenant: str, workspace: str, raw: str) -> str:
    return f"{tenant}:{workspace}:{raw}"


def upsert_creator_by_youtube_channel(conn: sqlite3.Connection, *, tenant: str, workspace: str, channel_id: str) -> int:
    """Upsert a creator_profile row keyed by namespaced slug for a YouTube channel id.

    Returns the creator_profile.id.
    """
    slug = _slug_namespace(tenant, workspace, f"yt:{channel_id}")
    cur = conn.execute("SELECT id FROM creator_profile WHERE slug=?", (slug,))
    row = cur.fetchone()
    if row:
        cid = int(row[0])
        conn.execute(
            "UPDATE creator_profile SET youtube_id=?, last_checked_at=datetime('now') WHERE id=?",
            (channel_id, cid),
        )
        conn.commit()
        return cid
    cur2 = conn.execute(
        "INSERT INTO creator_profile (slug, youtube_id, verified, last_checked_at) VALUES (?,?,?,datetime('now'))",
        (slug, channel_id, 0),
    )
    conn.commit()
    rid = cur2.lastrowid
    return int(rid) if rid is not None else 0


def ensure_watchlist(
    conn: sqlite3.Connection,
    *,
    tenant: str,
    workspace: str,
    source_type: str,
    handle: str,
    label: str | None = None,
) -> int:
    """Ensure a watchlist entry exists; returns its id.

    Adds a corresponding ingest_state row if inserting.
    """
    cur = conn.execute(
        "SELECT id FROM watchlist WHERE tenant=? AND workspace=? AND source_type=? AND handle=?",
        (tenant, workspace, source_type, handle),
    )
    row = cur.fetchone()
    if row:
        return int(row[0])
    now = default_utc_now().isoformat()
    cur2 = conn.execute(
        "INSERT INTO watchlist (tenant, workspace, source_type, handle, label, enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
        (tenant, workspace, source_type, handle, label, 1, now, now),
    )
    wid = int(cur2.lastrowid) if cur2.lastrowid is not None else 0
    conn.execute(
        "INSERT INTO ingest_state (watchlist_id, cursor, last_seen_at, etag, failure_count, backoff_until) VALUES (?,?,?,?,?,?)",
        (wid, None, None, None, 0, None),
    )
    conn.commit()
    return wid


def record_provenance(conn: sqlite3.Connection, prov: Provenance) -> None:
    conn.execute(
        (
            "INSERT INTO provenance (content_id, source_url, source_type, retrieved_at, license, "
            "terms_url, consent_flags, checksum_sha256, creator_id, episode_id) VALUES (?,?,?,?,?,?,?,?,?,?)"
        ),
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
        (
            "INSERT INTO usage_log (call_id, content_ids, policy_version, decisions, redactions, "
            "output_hash, user_cmd, channel_id, ts) VALUES (?,?,?,?,?,?,?,?,?)"
        ),
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


# Optimized query functions using indexes


def get_creator_by_slug(conn: sqlite3.Connection, slug: str) -> CreatorProfile | None:
    """Get creator profile by slug (uses index)."""
    cursor = conn.execute("SELECT * FROM creator_profile WHERE slug = ?", (slug,))
    row = cursor.fetchone()
    if row:
        return CreatorProfile(*row)
    return None


def get_episodes_by_creator(conn: sqlite3.Connection, creator_id: int, limit: int = 50) -> list[Episode]:
    """Get episodes by creator ID with pagination (uses index)."""
    cursor = conn.execute(
        "SELECT * FROM episode WHERE creator_id = ? ORDER BY published_at DESC LIMIT ?",
        (creator_id, limit),
    )
    return [Episode(*row) for row in cursor.fetchall()]


def get_transcript_segments(conn: sqlite3.Connection, episode_id: int) -> list[TranscriptSegment]:
    """Get transcript segments for an episode (uses index)."""
    cursor = conn.execute(
        "SELECT * FROM transcript_segment WHERE episode_id = ? ORDER BY start",
        (episode_id,),
    )
    return [TranscriptSegment(*row) for row in cursor.fetchall()]


def get_provenance_by_content_id(conn: sqlite3.Connection, content_id: str) -> Provenance | None:
    """Get provenance record by content ID (uses index)."""
    cursor = conn.execute("SELECT * FROM provenance WHERE content_id = ?", (content_id,))
    row = cursor.fetchone()
    if row:
        return Provenance(*row)
    return None


def get_usage_by_call_id(conn: sqlite3.Connection, call_id: str) -> UsageLog | None:
    """Get usage log by call ID (uses index)."""
    cursor = conn.execute("SELECT * FROM usage_log WHERE call_id = ?", (call_id,))
    row = cursor.fetchone()
    if row:
        return UsageLog(*row)
    return None


def get_watchlist_by_tenant_workspace(conn: sqlite3.Connection, tenant: str, workspace: str) -> list[Watchlist]:
    """Get watchlist entries by tenant and workspace (uses index)."""
    cursor = conn.execute(
        "SELECT * FROM watchlist WHERE tenant = ? AND workspace = ? AND enabled = 1",
        (tenant, workspace),
    )
    return [Watchlist(*row) for row in cursor.fetchall()]


def get_pending_ingest_jobs(
    conn: sqlite3.Connection, tenant: str, workspace: str, limit: int = 10
) -> list[IngestJobRecord]:
    """Get pending ingest jobs ordered by priority (uses indexes)."""
    cursor = conn.execute(
        """
        SELECT * FROM ingest_job
        WHERE tenant = ? AND workspace = ? AND status = 'pending'
        ORDER BY priority DESC, scheduled_at ASC
        LIMIT ?
        """,
        (tenant, workspace, limit),
    )
    return [IngestJobRecord(*row) for row in cursor.fetchall()]


def get_ingest_jobs_by_status(conn: sqlite3.Connection, status: str, limit: int = 100) -> list[IngestJobRecord]:
    """Get ingest jobs by status (uses index)."""
    cursor = conn.execute(
        "SELECT * FROM ingest_job WHERE status = ? ORDER BY scheduled_at DESC LIMIT ?",
        (status, limit),
    )
    return [IngestJobRecord(*row) for row in cursor.fetchall()]


def get_recent_usage_logs(conn: sqlite3.Connection, channel_id: str, limit: int = 50) -> list[UsageLog]:
    """Get recent usage logs for a channel (uses indexes)."""
    cursor = conn.execute(
        "SELECT * FROM usage_log WHERE channel_id = ? ORDER BY ts DESC LIMIT ?",
        (channel_id, limit),
    )
    return [UsageLog(*row) for row in cursor.fetchall()]


def bulk_insert_provenance(conn: sqlite3.Connection, provenance_records: list[Provenance]) -> None:
    """Bulk insert multiple provenance records efficiently."""
    if not provenance_records:
        return

    with conn:
        conn.executemany(
            """
            INSERT INTO provenance (
                content_id, source_url, source_type, retrieved_at, license,
                terms_url, consent_flags, checksum_sha256, creator_id, episode_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    p.content_id,
                    p.source_url,
                    p.source_type,
                    p.retrieved_at,
                    p.license,
                    p.terms_url,
                    p.consent_flags,
                    p.checksum_sha256,
                    p.creator_id,
                    p.episode_id,
                )
                for p in provenance_records
            ],
        )


def bulk_insert_usage_logs(conn: sqlite3.Connection, usage_records: list[UsageLog]) -> None:
    """Bulk insert multiple usage log records efficiently."""
    if not usage_records:
        return

    with conn:
        conn.executemany(
            """
            INSERT INTO usage_log (
                call_id, content_ids, policy_version, decisions, redactions,
                output_hash, user_cmd, channel_id, ts
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    u.call_id,
                    u.content_ids,
                    u.policy_version,
                    u.decisions,
                    u.redactions,
                    u.output_hash,
                    u.user_cmd,
                    u.channel_id,
                    u.ts,
                )
                for u in usage_records
            ],
        )
