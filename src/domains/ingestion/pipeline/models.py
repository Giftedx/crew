"""Lightweight SQLite-backed data models for ingestion metadata."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from platform.time import default_utc_now


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


SCHEMA = "\nCREATE TABLE IF NOT EXISTS creator_profile (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    slug TEXT UNIQUE,\n    youtube_id TEXT,\n    twitch_id TEXT,\n    verified INTEGER,\n    last_checked_at TEXT\n);\nCREATE TABLE IF NOT EXISTS episode (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    creator_id INTEGER,\n    platform TEXT,\n    external_id TEXT,\n    url TEXT,\n    title TEXT,\n    published_at TEXT,\n    duration REAL,\n    visibility TEXT\n);\nCREATE TABLE IF NOT EXISTS transcript_segment (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    episode_id INTEGER,\n    start REAL,\n    end REAL,\n    text TEXT,\n    speaker TEXT\n);\nCREATE TABLE IF NOT EXISTS ingest_log (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    episode_id INTEGER,\n    status TEXT,\n    details TEXT,\n    created_at TEXT\n);\nCREATE TABLE IF NOT EXISTS provenance (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    content_id TEXT,\n    source_url TEXT,\n    source_type TEXT,\n    retrieved_at TEXT,\n    license TEXT,\n    terms_url TEXT,\n    consent_flags TEXT,\n    checksum_sha256 TEXT,\n    creator_id INTEGER,\n    episode_id INTEGER\n);\nCREATE TABLE IF NOT EXISTS usage_log (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    call_id TEXT,\n    content_ids TEXT,\n    policy_version TEXT,\n    decisions TEXT,\n    redactions TEXT,\n    output_hash TEXT,\n    user_cmd TEXT,\n    channel_id TEXT,\n    ts TEXT\n);\nCREATE TABLE IF NOT EXISTS watchlist (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    tenant TEXT,\n    workspace TEXT,\n    source_type TEXT,\n    handle TEXT,\n    label TEXT,\n    enabled INTEGER,\n    created_at TEXT,\n    updated_at TEXT\n);\nCREATE TABLE IF NOT EXISTS ingest_state (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    watchlist_id INTEGER,\n    cursor TEXT,\n    last_seen_at TEXT,\n    etag TEXT,\n    failure_count INTEGER,\n    backoff_until TEXT\n);\nCREATE TABLE IF NOT EXISTS ingest_job (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    tenant TEXT,\n    workspace TEXT,\n    source_type TEXT,\n    external_id TEXT,\n    url TEXT,\n    tags TEXT,\n    visibility TEXT,\n    priority INTEGER,\n    status TEXT,\n    attempts INTEGER,\n    scheduled_at TEXT,\n    picked_at TEXT,\n    finished_at TEXT,\n    error TEXT\n);\n\n-- Performance indexes for frequently queried columns\nCREATE INDEX IF NOT EXISTS idx_creator_profile_slug ON creator_profile(slug);\nCREATE INDEX IF NOT EXISTS idx_creator_profile_youtube_id ON creator_profile(youtube_id);\nCREATE INDEX IF NOT EXISTS idx_creator_profile_twitch_id ON creator_profile(twitch_id);\n\nCREATE INDEX IF NOT EXISTS idx_episode_creator_id ON episode(creator_id);\nCREATE INDEX IF NOT EXISTS idx_episode_external_id ON episode(external_id);\nCREATE INDEX IF NOT EXISTS idx_episode_platform ON episode(platform);\nCREATE INDEX IF NOT EXISTS idx_episode_published_at ON episode(published_at);\n\nCREATE INDEX IF NOT EXISTS idx_transcript_segment_episode_id ON transcript_segment(episode_id);\nCREATE INDEX IF NOT EXISTS idx_transcript_segment_start ON transcript_segment(start);\n\nCREATE INDEX IF NOT EXISTS idx_ingest_log_episode_id ON ingest_log(episode_id);\nCREATE INDEX IF NOT EXISTS idx_ingest_log_status ON ingest_log(status);\n\nCREATE INDEX IF NOT EXISTS idx_provenance_content_id ON provenance(content_id);\nCREATE INDEX IF NOT EXISTS idx_provenance_source_type ON provenance(source_type);\nCREATE INDEX IF NOT EXISTS idx_provenance_checksum ON provenance(checksum_sha256);\n\nCREATE INDEX IF NOT EXISTS idx_usage_log_call_id ON usage_log(call_id);\nCREATE INDEX IF NOT EXISTS idx_usage_log_ts ON usage_log(ts);\nCREATE INDEX IF NOT EXISTS idx_usage_log_channel_id ON usage_log(channel_id);\n\nCREATE INDEX IF NOT EXISTS idx_watchlist_tenant_workspace ON watchlist(tenant, workspace);\nCREATE INDEX IF NOT EXISTS idx_watchlist_source_type ON watchlist(source_type);\nCREATE INDEX IF NOT EXISTS idx_watchlist_enabled ON watchlist(enabled);\n\nCREATE INDEX IF NOT EXISTS idx_ingest_state_watchlist_id ON ingest_state(watchlist_id);\nCREATE INDEX IF NOT EXISTS idx_ingest_state_failure_count ON ingest_state(failure_count);\n\nCREATE INDEX IF NOT EXISTS idx_ingest_job_tenant_workspace ON ingest_job(tenant, workspace);\nCREATE INDEX IF NOT EXISTS idx_ingest_job_status ON ingest_job(status);\nCREATE INDEX IF NOT EXISTS idx_ingest_job_priority ON ingest_job(priority);\nCREATE INDEX IF NOT EXISTS idx_ingest_job_scheduled_at ON ingest_job(scheduled_at);\n"


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
    except Exception:
        pass
    conn.executescript(SCHEMA)
    return conn


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
            "UPDATE creator_profile SET youtube_id=?, last_checked_at=datetime('now') WHERE id=?", (channel_id, cid)
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
    conn: sqlite3.Connection, *, tenant: str, workspace: str, source_type: str, handle: str, label: str | None = None
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
        "SELECT * FROM episode WHERE creator_id = ? ORDER BY published_at DESC LIMIT ?", (creator_id, limit)
    )
    return [Episode(*row) for row in cursor.fetchall()]


def get_transcript_segments(conn: sqlite3.Connection, episode_id: int) -> list[TranscriptSegment]:
    """Get transcript segments for an episode (uses index)."""
    cursor = conn.execute("SELECT * FROM transcript_segment WHERE episode_id = ? ORDER BY start", (episode_id,))
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
        "SELECT * FROM watchlist WHERE tenant = ? AND workspace = ? AND enabled = 1", (tenant, workspace)
    )
    return [Watchlist(*row) for row in cursor.fetchall()]


def get_pending_ingest_jobs(
    conn: sqlite3.Connection, tenant: str, workspace: str, limit: int = 10
) -> list[IngestJobRecord]:
    """Get pending ingest jobs ordered by priority (uses indexes)."""
    cursor = conn.execute(
        "\n        SELECT * FROM ingest_job\n        WHERE tenant = ? AND workspace = ? AND status = 'pending'\n        ORDER BY priority DESC, scheduled_at ASC\n        LIMIT ?\n        ",
        (tenant, workspace, limit),
    )
    return [IngestJobRecord(*row) for row in cursor.fetchall()]


def get_ingest_jobs_by_status(conn: sqlite3.Connection, status: str, limit: int = 100) -> list[IngestJobRecord]:
    """Get ingest jobs by status (uses index)."""
    cursor = conn.execute(
        "SELECT * FROM ingest_job WHERE status = ? ORDER BY scheduled_at DESC LIMIT ?", (status, limit)
    )
    return [IngestJobRecord(*row) for row in cursor.fetchall()]


def get_recent_usage_logs(conn: sqlite3.Connection, channel_id: str, limit: int = 50) -> list[UsageLog]:
    """Get recent usage logs for a channel (uses indexes)."""
    cursor = conn.execute("SELECT * FROM usage_log WHERE channel_id = ? ORDER BY ts DESC LIMIT ?", (channel_id, limit))
    return [UsageLog(*row) for row in cursor.fetchall()]


def bulk_insert_provenance(conn: sqlite3.Connection, provenance_records: list[Provenance]) -> None:
    """Bulk insert multiple provenance records efficiently."""
    if not provenance_records:
        return
    with conn:
        conn.executemany(
            "\n            INSERT INTO provenance (\n                content_id, source_url, source_type, retrieved_at, license,\n                terms_url, consent_flags, checksum_sha256, creator_id, episode_id\n            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ",
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
            "\n            INSERT INTO usage_log (\n                call_id, content_ids, policy_version, decisions, redactions,\n                output_hash, user_cmd, channel_id, ts\n            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ",
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


def pick_next_pending_job(conn: sqlite3.Connection) -> IngestJobRecord | None:
    """Atomically pick the next pending job and mark it as processing."""
    try:
        with conn:
            now = default_utc_now().isoformat()
            # Find candidate
            cur = conn.execute(
                "SELECT id FROM ingest_job WHERE status='pending' AND scheduled_at <= ? ORDER BY priority DESC, scheduled_at ASC LIMIT 1",
                (now,),
            )
            row = cur.fetchone()
            if not row:
                return None
            job_id = row[0]

            # Mark as processing
            conn.execute(
                "UPDATE ingest_job SET status='processing', picked_at=?, attempts=attempts+1 WHERE id=?",
                (now, job_id),
            )

            # Return full record
            cur = conn.execute("SELECT * FROM ingest_job WHERE id=?", (job_id,))
            return IngestJobRecord(*cur.fetchone())
    except sqlite3.OperationalError:
        # Avoid crashing on lock contention
        return None


def update_ingest_job_status(
    conn: sqlite3.Connection, job_id: int, status: str, error: str | None = None
) -> None:
    """Update job status and set finished_at if terminal status."""
    finished_at = None
    if status in ("completed", "failed", "cancelled"):
        finished_at = default_utc_now().isoformat()

    with conn:
        # We only update finished_at if it's not None, to preserve existing if somehow updated twice
        if finished_at:
            conn.execute(
                "UPDATE ingest_job SET status=?, finished_at=?, error=? WHERE id=?",
                (status, finished_at, error, job_id),
            )
        else:
            conn.execute("UPDATE ingest_job SET status=?, error=? WHERE id=?", (status, error, job_id))
