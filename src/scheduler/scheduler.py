"""Simple ingest scheduler with RL-controlled pacing."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from platform.batching import BulkInserter, RequestBatcher
from platform.db_locks import get_lock_for_connection
from platform.error_handling import handle_error_safely
from platform.rl.learning_engine import LearningEngine
from platform.time import default_utc_now
from typing import TYPE_CHECKING, Any

from domains.ingestion.pipeline import models, pipeline
from domains.ingestion.pipeline.sources.base import SourceConnector, Watch
from ultimate_discord_intelligence_bot.obs import metrics

from .priority_queue import PriorityQueue


if TYPE_CHECKING:
    import sqlite3

    from domains.memory.unified_graph_store import UnifiedGraphStore
    from domains.memory.vector_store import VectorStore
logger = logging.getLogger(__name__)


class Scheduler:
    """Coordinate watchlist discovery and ingest job processing."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        queue: PriorityQueue,
        connectors: dict[str, SourceConnector],
        *,
        learner: LearningEngine | None = None,
    ) -> None:
        self.conn = conn
        self.queue = queue
        self.connectors = connectors
        self.learner = learner or LearningEngine()
        self._lock = get_lock_for_connection(self.conn)
        self._background_tasks: set[asyncio.Task[Any]] = set()
        if "scheduler" not in self.learner.status():
            self.learner.register_domain("scheduler")
        self._bulk_inserter = BulkInserter(self.conn, batch_size=50)
        self._state_batcher = RequestBatcher(self.conn, batch_size=50, batch_timeout=30.0)

    def add_watch(
        self, *, tenant: str, workspace: str, source_type: str, handle: str, label: str | None = None
    ) -> models.Watchlist:
        now = default_utc_now().isoformat()
        with self._lock:
            cur = self.conn.execute(
                "INSERT INTO watchlist (tenant, workspace, source_type, handle, label, enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (tenant, workspace, source_type, handle, label, 1, now, now),
            )
            raw_id = cur.lastrowid
            watch_id = int(raw_id) if raw_id is not None else 0
            self.conn.execute(
                "INSERT INTO ingest_state (watchlist_id, cursor, last_seen_at, etag, failure_count, backoff_until) VALUES (?,?,?,?,?,?)",
                (watch_id, None, None, None, 0, None),
            )
            self.conn.commit()
        return models.Watchlist(
            id=watch_id,
            tenant=tenant,
            workspace=workspace,
            source_type=source_type,
            handle=handle,
            label=label,
            enabled=True,
            created_at=now,
            updated_at=now,
        )

    def list_watches(self, tenant: str | None = None) -> list[models.Watchlist]:
        sql = "SELECT id, tenant, workspace, source_type, handle, label, enabled, created_at, updated_at FROM watchlist"
        params: tuple[object, ...] = ()
        if tenant:
            sql += " WHERE tenant=?"
            params = (tenant,)
        with self._lock:
            rows = self.conn.execute(sql, params).fetchall()
        return [
            models.Watchlist(
                id=r[0],
                tenant=r[1],
                workspace=r[2],
                source_type=r[3],
                handle=r[4],
                label=r[5],
                enabled=bool(r[6]),
                created_at=r[7],
                updated_at=r[8],
            )
            for r in rows
        ]

    def add_watches_bulk(self, watches: list[dict[str, Any]]) -> list[models.Watchlist]:
        """Add multiple watches in bulk for improved performance."""
        if not watches:
            return []
        now = default_utc_now().isoformat()
        watchlist_rows = [
            (
                watch_data["tenant"],
                watch_data["workspace"],
                watch_data["source_type"],
                watch_data["handle"],
                watch_data.get("label"),
                1,
                now,
                now,
            )
            for watch_data in watches
        ]
        self._bulk_inserter.add_row(
            "watchlist",
            ["tenant", "workspace", "source_type", "handle", "label", "enabled", "created_at", "updated_at"],
            watchlist_rows[0],
        )
        watch_ids = []
        with self._lock:
            for wrow in watchlist_rows:
                cur = self.conn.execute(
                    "INSERT INTO watchlist (tenant, workspace, source_type, handle, label, enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                    wrow,
                )
                watch_ids.append(cur.lastrowid)
        state_rows = [(int(watch_id), None, None, None, 0, None) for watch_id in watch_ids if watch_id]
        if state_rows:
            for srow in state_rows:
                self._bulk_inserter.add_row(
                    "ingest_state",
                    ["watchlist_id", "cursor", "last_seen_at", "etag", "failure_count", "backoff_until"],
                    srow,
                )
        with self._lock:
            self.conn.commit()
        return [
            models.Watchlist(
                id=watch_ids[i],
                tenant=watch_data["tenant"],
                workspace=watch_data["workspace"],
                source_type=watch_data["source_type"],
                handle=watch_data["handle"],
                label=watch_data.get("label"),
                enabled=True,
                created_at=now,
                updated_at=now,
            )
            for i, watch_data in enumerate(watches)
            if watch_ids[i]
        ]

    def update_ingest_states_bulk(self, state_updates: list[dict[str, Any]]) -> None:
        """Update multiple ingest states in bulk."""
        if not state_updates:
            return
        for update in state_updates:
            self._state_batcher.add_update(
                "ingest_state",
                "cursor=?, last_seen_at=?",
                "watchlist_id=?",
                (update["cursor"], update["last_seen_at"], update["watchlist_id"]),
            )
        try:
            task = asyncio.create_task(self._state_batcher.flush())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
        except RuntimeError:
            with self._lock:
                for update in state_updates:
                    self.conn.execute(
                        "UPDATE ingest_state SET cursor=?, last_seen_at=? WHERE watchlist_id=?",
                        (update["cursor"], update["last_seen_at"], update["watchlist_id"]),
                    )
                self.conn.commit()

    def tick(self) -> None:
        with self._lock:
            rows = self.conn.execute(
                "SELECT id, tenant, workspace, source_type, handle, label FROM watchlist WHERE enabled=1"
            ).fetchall()
        now = default_utc_now()
        jobs_to_enqueue = []
        state_updates = []
        for wid, tenant, workspace, source_type, handle, label in rows:
            with self._lock:
                state_row = self.conn.execute(
                    "SELECT cursor, last_seen_at FROM ingest_state WHERE watchlist_id=?", (wid,)
                ).fetchone()
            cursor = state_row[0] if state_row else None
            last_polled = datetime.fromisoformat(state_row[1]) if state_row and state_row[1] else None
            interval = self.learner.recommend("scheduler", {"source_type": source_type}, [30, 300])
            if last_polled and now - last_polled < timedelta(seconds=interval):
                continue
            state = {"cursor": cursor} if cursor is not None else {}
            watch = Watch(
                id=wid, source_type=source_type, handle=handle, tenant=tenant, workspace=workspace, label=label
            )
            connector = self.connectors.get(source_type)
            if not connector:
                continue
            items = connector.discover(watch, state)
            reward = len(items)
            if items:
                for item in items:
                    job = pipeline.IngestJob(
                        source=source_type,
                        external_id=item.external_id,
                        url=item.url,
                        tenant=tenant,
                        workspace=workspace,
                        tags=[],
                        visibility="public",
                    )
                    jobs_to_enqueue.append(job)
            state_updates.append({"watchlist_id": wid, "cursor": state.get("cursor"), "last_seen_at": now.isoformat()})
            self.learner.record("scheduler", {"source_type": source_type}, interval, float(reward))
        if jobs_to_enqueue:
            self.queue.enqueue_bulk(jobs_to_enqueue)
            for job in jobs_to_enqueue:
                handle_error_safely(
                    lambda job=job: metrics.SCHEDULER_ENQUEUED.labels(**metrics.label_ctx(), source=job.source).inc(),
                    error_message=f"Failed to record scheduler enqueued metric for source {job.source}",
                )
                handle_error_safely(
                    lambda job=job: metrics.SCHEDULER_QUEUE_BACKLOG.labels(
                        tenant=job.tenant, workspace=job.workspace
                    ).set(self.queue.pending_count_for(job.tenant, job.workspace)),
                    error_message=f"Failed to update scheduler queue backlog metric for {job.tenant}/{job.workspace}",
                )
        if state_updates:
            self.update_ingest_states_bulk(state_updates)

    def worker_run_once(
        self, store: VectorStore | UnifiedGraphStore
    ) -> pipeline.IngestJob | None:
        qjob = self.queue.dequeue()
        if not qjob:
            return None
        try:
            pipeline.run(qjob.job, store)
            self.queue.mark_done(qjob.id)
            handle_error_safely(
                lambda job=qjob.job: metrics.SCHEDULER_PROCESSED.labels(**metrics.label_ctx(), source=job.source).inc(),
                error_message=f"Failed to record scheduler processed metric for source {qjob.job.source}",
            )
        except Exception as exc:
            self.queue.mark_error(qjob.id, str(exc))
            handle_error_safely(
                lambda job=qjob.job: metrics.SCHEDULER_ERRORS.labels(**metrics.label_ctx(), source=job.source).inc(),
                error_message=f"Failed to record scheduler error metric for source {qjob.job.source}",
            )
        finally:
            handle_error_safely(
                lambda job=qjob.job: metrics.SCHEDULER_QUEUE_BACKLOG.labels(
                    tenant=job.tenant, workspace=job.workspace
                ).set(self.queue.pending_count_for(job.tenant, job.workspace)),
                error_message=f"Failed to update scheduler queue backlog metric for {qjob.job.tenant}/{qjob.job.workspace}",
            )
        return qjob.job

    def get_batching_metrics(self) -> dict[str, Any]:
        """Get comprehensive batching performance metrics."""
        return {
            "bulk_inserter": self._bulk_inserter.get_metrics().__dict__,
            "state_batcher": self._state_batcher.get_metrics().__dict__,
            "queue_batching": self.queue.get_batching_metrics(),
        }

    def flush_pending_operations(self) -> None:
        """Flush all pending batch operations."""
        task = asyncio.create_task(self._state_batcher.flush())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        self._bulk_inserter.flush_all()
        self.queue.flush_pending_operations()


__all__ = ["PriorityQueue", "Scheduler"]
