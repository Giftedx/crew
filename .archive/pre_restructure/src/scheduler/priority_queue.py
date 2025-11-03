from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from core.batching import get_batching_metrics, get_bulk_inserter, get_request_batcher
from core.db_locks import get_lock_for_connection
from core.time import default_utc_now

from ingest import pipeline


if TYPE_CHECKING:
    import sqlite3


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
        self._lock = get_lock_for_connection(conn)
        self._bulk_inserter = get_bulk_inserter(conn)
        self._request_batcher = get_request_batcher(conn)
        self._background_tasks: set[asyncio.Task[Any]] = set()

    # --------------------------------------------------------------- enqueue
    def enqueue(self, job: pipeline.IngestJob, priority: int = 0) -> int:
        tags = ",".join(job.tags)
        now = default_utc_now().isoformat()
        with self._lock:
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

    def enqueue_bulk(self, jobs: list[pipeline.IngestJob], priority: int = 0) -> list[int]:
        """Enqueue multiple jobs in bulk for improved performance."""
        if not jobs:
            return []

        # Prepare data tuples for immediate inserts
        now = default_utc_now().isoformat()
        values = []
        for job in jobs:
            tags = ",".join(job.tags)
            values.append(
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
                )
            )

        inserted_ids: list[int] = []
        # Insert rows immediately to reflect in tests (simpler than deferred batch for now)
        with self._lock:
            for value_tuple in values:
                cur = self.conn.execute(
                    "INSERT INTO ingest_job (tenant, workspace, source_type, external_id, url, tags, visibility, "
                    "priority, status, attempts, scheduled_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    value_tuple,
                )
                rid = cur.lastrowid
                if rid is not None:
                    inserted_ids.append(int(rid))
            self.conn.commit()
        return inserted_ids

    # --------------------------------------------------------------- dequeue
    def dequeue(self) -> QueuedJob | None:
        with self._lock:
            row = self.conn.execute(
                "SELECT id, tenant, workspace, source_type, external_id, url, tags, visibility, attempts "
                "FROM ingest_job WHERE status='pending' ORDER BY priority DESC, id ASC LIMIT 1"
            ).fetchone()
            if not row:
                return None
            (
                job_id,
                tenant,
                workspace,
                source,
                external_id,
                url,
                tags,
                visibility,
                attempts,
            ) = row
            self.conn.execute(
                "UPDATE ingest_job SET status='running', picked_at=? WHERE id=?",
                (default_utc_now().isoformat(), job_id),
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
        with self._lock:
            self.conn.execute(
                "UPDATE ingest_job SET status='done', finished_at=? WHERE id=?",
                (default_utc_now().isoformat(), job_id),
            )
            self.conn.commit()

    def mark_error(self, job_id: int, error: str) -> None:
        with self._lock:
            self.conn.execute(
                "UPDATE ingest_job SET status='err', error=?, finished_at=? WHERE id=?",
                (error, default_utc_now().isoformat(), job_id),
            )
            self.conn.commit()

    def mark_done_bulk(self, job_ids: list[int]) -> None:
        """Mark multiple jobs as done in bulk."""
        if not job_ids:
            return
        now = default_utc_now().isoformat()
        with self._lock:
            for job_id in job_ids:
                self._request_batcher.add_update(
                    table="ingest_job",
                    set_clause="status='done', finished_at=?",
                    where_clause="id=?",
                    params=(now, job_id),
                )

    def mark_error_bulk(self, job_errors: list[tuple[int, str]]) -> None:
        """Mark multiple jobs as error in bulk."""
        if not job_errors:
            return
        now = default_utc_now().isoformat()
        with self._lock:
            for job_id, error in job_errors:
                self._request_batcher.add_update(
                    table="ingest_job",
                    set_clause="status='err', error=?, finished_at=?",
                    where_clause="id=?",
                    params=(error, now, job_id),
                )

    # --------------------------------------------------------------- stats
    def pending_count(self) -> int:
        with self._lock:
            row = self.conn.execute("SELECT COUNT(*) FROM ingest_job WHERE status='pending'").fetchone()
        return int(row[0]) if row else 0

    def pending_count_for(self, tenant: str, workspace: str) -> int:
        """Get pending count for a specific tenant/workspace."""
        with self._lock:
            row = self.conn.execute(
                "SELECT COUNT(*) FROM ingest_job WHERE status='pending' AND tenant=? AND workspace=?",
                (tenant, workspace),
            ).fetchone()
        return int(row[0]) if row else 0

    async def _flush_async(self) -> None:
        """Async wrapper to flush batched operations under lock for thread safety."""
        with self._lock:
            await self._request_batcher.flush()
            self._bulk_inserter.flush_all()

    def flush_pending_operations(self) -> None:
        """Flush all pending batch operations."""
        task = asyncio.create_task(self._flush_async())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    def get_batching_metrics(self) -> dict[str, Any]:
        """Get batching performance metrics."""
        return get_batching_metrics(self.conn)
