from __future__ import annotations

from ingest import models, pipeline
from ingest.sources.youtube import YouTubeConnector
from scheduler import PriorityQueue, Scheduler
from ultimate_discord_intelligence_bot.obs import metrics


class _CounterStub:
    def __init__(self) -> None:
        self.count = 0
        self.labels_seen: list[dict[str, str]] = []

    def labels(self, **kwargs):
        self.labels_seen.append(dict(kwargs))
        return self

    def inc(self) -> None:
        self.count += 1


def test_scheduler_enqueued_and_processed_metrics(tmp_path, monkeypatch):
    conn = models.connect(tmp_path / "sched.db")
    queue = PriorityQueue(conn)
    sched = Scheduler(conn, queue, {"youtube": YouTubeConnector()})
    enq = _CounterStub()
    proc = _CounterStub()
    monkeypatch.setattr(metrics, "SCHEDULER_ENQUEUED", enq)
    monkeypatch.setattr(metrics, "SCHEDULER_PROCESSED", proc)
    sched.add_watch(tenant="t", workspace="w", source_type="youtube", handle="vid1")
    sched.tick()
    assert enq.count == 1
    monkeypatch.setattr(pipeline, "run", lambda job, store: {})
    sched.worker_run_once(store=None)
    assert proc.count == 1


def test_scheduler_error_metric(tmp_path, monkeypatch):
    conn = models.connect(tmp_path / "sched.db")
    queue = PriorityQueue(conn)
    sched = Scheduler(conn, queue, {"youtube": YouTubeConnector()})
    enq = _CounterStub()
    err = _CounterStub()
    monkeypatch.setattr(metrics, "SCHEDULER_ENQUEUED", enq)
    monkeypatch.setattr(metrics, "SCHEDULER_ERRORS", err)
    sched.add_watch(tenant="t", workspace="w", source_type="youtube", handle="vid2")
    sched.tick()
    assert enq.count >= 1

    def boom(job, store):
        raise RuntimeError("fail")

    monkeypatch.setattr(pipeline, "run", boom)
    sched.worker_run_once(store=None)
    assert err.count == 1
