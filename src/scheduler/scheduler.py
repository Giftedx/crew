"""Simple ingest scheduler with RL-controlled pacing."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from core.learning_engine import LearningEngine
from ingest import models, pipeline
from ingest.sources.base import SourceConnector, Watch
from memory.vector_store import VectorStore

from .priority_queue import PriorityQueue


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
        # Register scheduler domain if absent; arms represent poll interval seconds
        if "scheduler" not in self.learner.status():
            self.learner.register_domain("scheduler", priors={30: 0.0, 300: 0.0})

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
        now = datetime.now(timezone.utc).isoformat()
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
        sql = (
            "SELECT id, tenant, workspace, source_type, handle, label, enabled, created_at, updated_at "
            "FROM watchlist"
        )
        params: tuple[object, ...] = ()
        if tenant:
            sql += " WHERE tenant=?"
            params = (tenant,)
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

    # ----------------------------------------------------------- scheduler tick
    def tick(self) -> None:
        rows = self.conn.execute(
            "SELECT id, tenant, workspace, source_type, handle, label FROM watchlist WHERE enabled=1",
        ).fetchall()
        now = datetime.now(timezone.utc)
        for wid, tenant, workspace, source_type, handle, label in rows:
            state_row = self.conn.execute(
                "SELECT cursor, last_seen_at FROM ingest_state WHERE watchlist_id=?",
                (wid,),
            ).fetchone()
            cursor = state_row[0] if state_row else None
            last_polled = (
                datetime.fromisoformat(state_row[1]) if state_row and state_row[1] else None
            )

            # RL arm: decide poll interval (seconds)
            interval = self.learner.recommend("scheduler", {"source_type": source_type}, [30, 300])
            if last_polled and now - last_polled < timedelta(seconds=interval):
                continue

            state = {"cursor": cursor}
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
                    self.queue.enqueue(job)
            self.conn.execute(
                "UPDATE ingest_state SET cursor=?, last_seen_at=? WHERE watchlist_id=?",
                (state.get("cursor"), now.isoformat(), wid),
            )
            self.conn.commit()
            self.learner.record("scheduler", {"source_type": source_type}, interval, float(reward))

    # ----------------------------------------------------------- worker
    def worker_run_once(self, store: VectorStore) -> pipeline.IngestJob | None:
        qjob = self.queue.dequeue()
        if not qjob:
            return None
        try:
            pipeline.run(qjob.job, store)
            self.queue.mark_done(qjob.id)
        except Exception as exc:  # pragma: no cover - defensive
            self.queue.mark_error(qjob.id, str(exc))
        return qjob.job


__all__ = ["Scheduler", "PriorityQueue"]
