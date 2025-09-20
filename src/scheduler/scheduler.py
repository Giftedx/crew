"""Simple ingest scheduler with RL-controlled pacing."""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from datetime import UTC, datetime, timedelta
from typing import Any

from core.batching import BulkInserter, RequestBatcher
from core.db_locks import get_lock_for_connection
from core.error_handling import handle_error_safely
from core.learning_engine import LearningEngine
from ingest import models, pipeline
from ingest.sources.base import SourceConnector, Watch
from memory.vector_store import VectorStore
from obs import metrics

from .priority_queue import PriorityQueue

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
        # Register scheduler domain if absent; arms represent poll interval seconds
        if "scheduler" not in self.learner.status():
            self.learner.register_domain("scheduler", priors={30: 0.0, 300: 0.0})

        # Initialize batching components
        self._bulk_inserter = BulkInserter(self.conn, batch_size=50)
        self._state_batcher = RequestBatcher(self.conn, batch_size=50, batch_timeout=30.0)

    # ----------------------------------------------------------- watchlists
    def add_watch(
        self,
        *,
        tenant: str,
        workspace: str,
        source_type: str,
        handle: str,
        label: str | None = None,
    ) -> models.Watchlist:
        now = datetime.now(UTC).isoformat()
        with self._lock:
            cur = self.conn.execute(
                (
                    "INSERT INTO watchlist (tenant, workspace, source_type, handle, label, enabled, created_at, "
                    "updated_at) VALUES (?,?,?,?,?,?,?,?)"
                ),
                (tenant, workspace, source_type, handle, label, 1, now, now),
            )
            raw_id = cur.lastrowid
            watch_id = int(raw_id) if raw_id is not None else 0
            self.conn.execute(
                (
                    "INSERT INTO ingest_state (watchlist_id, cursor, last_seen_at, etag, failure_count, "
                    "backoff_until) VALUES (?,?,?,?,?,?)"
                ),
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

        now = datetime.now(UTC).isoformat()
        watchlist_rows = [
            (
                watch_data["tenant"],
                watch_data["workspace"],
                watch_data["source_type"],
                watch_data["handle"],
                watch_data.get("label"),
                1,  # enabled
                now,  # created_at
                now,  # updated_at
            )
            for watch_data in watches
        ]

        # Bulk insert watchlists
        self._bulk_inserter.add_row(
            "watchlist",
            ["tenant", "workspace", "source_type", "handle", "label", "enabled", "created_at", "updated_at"],
            watchlist_rows[0],  # Add first row to start batching
        )

        # Get the IDs of inserted watchlists
        watch_ids = []
        with self._lock:
            for wrow in watchlist_rows:
                cur = self.conn.execute(
                    "INSERT INTO watchlist (tenant, workspace, source_type, handle, label, enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                    wrow,
                )
                watch_ids.append(cur.lastrowid)

        # Bulk insert ingest states
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

        # Return watchlist objects
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

        # Flush operations synchronously for testing
        try:
            # Try async flush first
            asyncio.create_task(self._state_batcher.flush())
        except RuntimeError:
            # No event loop, flush synchronously
            # Execute operations directly
            with self._lock:
                for update in state_updates:
                    self.conn.execute(
                        "UPDATE ingest_state SET cursor=?, last_seen_at=? WHERE watchlist_id=?",
                        (update["cursor"], update["last_seen_at"], update["watchlist_id"]),
                    )
                self.conn.commit()

    # ----------------------------------------------------------- scheduler tick
    def tick(self) -> None:
        with self._lock:
            rows = self.conn.execute(
                "SELECT id, tenant, workspace, source_type, handle, label FROM watchlist WHERE enabled=1",
            ).fetchall()
        now = datetime.now(UTC)

        # Collect jobs and state updates for batching
        jobs_to_enqueue = []
        state_updates = []

        for wid, tenant, workspace, source_type, handle, label in rows:
            with self._lock:
                state_row = self.conn.execute(
                    "SELECT cursor, last_seen_at FROM ingest_state WHERE watchlist_id=?",
                    (wid,),
                ).fetchone()
            cursor = state_row[0] if state_row else None
            last_polled = datetime.fromisoformat(state_row[1]) if state_row and state_row[1] else None

            # RL arm: decide poll interval (seconds)
            interval = self.learner.recommend("scheduler", {"source_type": source_type}, [30, 300])
            if last_polled and now - last_polled < timedelta(seconds=interval):
                continue

            state = {"cursor": cursor} if cursor is not None else {}
            watch = Watch(
                id=wid,
                source_type=source_type,
                handle=handle,
                tenant=tenant,
                workspace=workspace,
                label=label,
            )
            connector = self.connectors.get(source_type)
            if not connector:
                continue
            items = connector.discover(watch, state)
            reward = len(items)

            if items:
                # Collect jobs for bulk enqueue
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

            # Collect state updates for bulk update
            state_updates.append(
                {
                    "watchlist_id": wid,
                    "cursor": state.get("cursor"),
                    "last_seen_at": now.isoformat(),
                }
            )

            self.learner.record("scheduler", {"source_type": source_type}, interval, float(reward))

        # Execute bulk operations
        if jobs_to_enqueue:
            self.queue.enqueue_bulk(jobs_to_enqueue)
            for job in jobs_to_enqueue:
                # Record enqueued metric with error handling
                handle_error_safely(
                    lambda: metrics.SCHEDULER_ENQUEUED.labels(**metrics.label_ctx(), source=job.source).inc(),
                    error_message=f"Failed to record scheduler enqueued metric for source {job.source}",
                )
                # Update queue backlog metric with error handling
                handle_error_safely(
                    lambda: metrics.SCHEDULER_QUEUE_BACKLOG.labels(tenant=job.tenant, workspace=job.workspace).set(
                        self.queue.pending_count_for(job.tenant, job.workspace)
                    ),
                    error_message=f"Failed to update scheduler queue backlog metric for {job.tenant}/{job.workspace}",
                )

        if state_updates:
            self.update_ingest_states_bulk(state_updates)

    # ----------------------------------------------------------- worker
    def worker_run_once(self, store: VectorStore) -> pipeline.IngestJob | None:
        qjob = self.queue.dequeue()
        if not qjob:
            return None
        try:
            pipeline.run(qjob.job, store)
            self.queue.mark_done(qjob.id)
            # Record processed metric with error handling
            handle_error_safely(
                lambda: metrics.SCHEDULER_PROCESSED.labels(**metrics.label_ctx(), source=qjob.job.source).inc(),
                error_message=f"Failed to record scheduler processed metric for source {qjob.job.source}",
            )
        except Exception as exc:  # pragma: no cover - defensive
            self.queue.mark_error(qjob.id, str(exc))
            # Record error metric with error handling
            handle_error_safely(
                lambda: metrics.SCHEDULER_ERRORS.labels(**metrics.label_ctx(), source=qjob.job.source).inc(),
                error_message=f"Failed to record scheduler error metric for source {qjob.job.source}",
            )
        finally:
            # Update queue backlog metric with error handling
            handle_error_safely(
                lambda: metrics.SCHEDULER_QUEUE_BACKLOG.labels(
                    tenant=qjob.job.tenant, workspace=qjob.job.workspace
                ).set(self.queue.pending_count_for(qjob.job.tenant, qjob.job.workspace)),
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
        asyncio.create_task(self._state_batcher.flush())
        self._bulk_inserter.flush_all()
        self.queue.flush_pending_operations()


__all__ = ["Scheduler", "PriorityQueue"]
