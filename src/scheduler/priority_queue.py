from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from ingest import pipeline


@dataclass
class QueuedJob:
    """A job pulled from the queue."""

    id: int
    job: pipeline.IngestJob
    attempts: int


class PriorityQueue:
    """SQLite-backed priority queue for ingest jobs."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    # --------------------------------------------------------------- enqueue
    def enqueue(self, job: pipeline.IngestJob, priority: int = 0) -> int:
        tags = ",".join(job.tags)
        now = datetime.now(timezone.utc).isoformat()
        cur = self.conn.execute(
            (
                "INSERT INTO ingest_job (tenant, workspace, source_type, external_id, url, tags, visibility, "
                "priority, status, attempts, scheduled_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
            ),
            (
                job.tenant,
                job.workspace,
                job.source,
                job.external_id,
                job.url,
                tags,
                job.visibility,
                priority,
                "pending",
                0,
                now,
            ),
        )
        self.conn.commit()
        job_id = cur.lastrowid
        return int(job_id) if job_id is not None else 0

    # --------------------------------------------------------------- dequeue
    def dequeue(self) -> QueuedJob | None:
        row = self.conn.execute(
            "SELECT id, tenant, workspace, source_type, external_id, url, tags, visibility, attempts "
            "FROM ingest_job WHERE status='pending' ORDER BY priority DESC, id ASC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        job_id, tenant, workspace, source, external_id, url, tags, visibility, attempts = row
        self.conn.execute(
            "UPDATE ingest_job SET status='running', picked_at=? WHERE id=?",
            (datetime.now(timezone.utc).isoformat(), job_id),
        )
        self.conn.commit()
        job = pipeline.IngestJob(
            source=source,
            external_id=external_id,
            url=url,
            tenant=tenant,
            workspace=workspace,
            tags=tags.split(",") if tags else [],
            visibility=visibility,
        )
        return QueuedJob(id=job_id, job=job, attempts=attempts)

    # --------------------------------------------------------------- mark
    def mark_done(self, job_id: int) -> None:
        self.conn.execute(
            "UPDATE ingest_job SET status='done', finished_at=? WHERE id=?",
            (datetime.now(timezone.utc).isoformat(), job_id),
        )
        self.conn.commit()

    def mark_error(self, job_id: int, error: str) -> None:
        self.conn.execute(
            "UPDATE ingest_job SET status='err', error=?, finished_at=? WHERE id=?",
            (error, datetime.now(timezone.utc).isoformat(), job_id),
        )
        self.conn.commit()

    # --------------------------------------------------------------- stats
    def pending_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) FROM ingest_job WHERE status='pending'").fetchone()
        return int(row[0]) if row else 0
