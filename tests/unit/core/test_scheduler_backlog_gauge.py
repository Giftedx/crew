from __future__ import annotations

from platform.observability import metrics

from ingest import models, pipeline
from ingest.sources.youtube import YouTubeConnector
from scheduler import PriorityQueue, Scheduler


class _GaugeStub:
    def __init__(self) -> None:
        self.last: dict[str, tuple[dict[str, str], float]] = {}

    def labels(self, **kwargs):
        self._labels = dict(kwargs)
        return self

    def set(self, value: float) -> None:
        self.last["val"] = (getattr(self, "_labels", {}), float(value))


def test_queue_backlog_gauge_updates(tmp_path, monkeypatch):
    conn = models.connect(tmp_path / "sched.db")
    queue = PriorityQueue(conn)
    sched = Scheduler(conn, queue, {"youtube": YouTubeConnector()})
    g = _GaugeStub()
    monkeypatch.setattr(metrics, "SCHEDULER_QUEUE_BACKLOG", g)
    sched.add_watch(tenant="t", workspace="w", source_type="youtube", handle="vid1")
    sched.tick()
    labels, val = g.last["val"]
    assert labels.get("tenant") == "t" and labels.get("workspace") == "w"
    assert val >= 1
    monkeypatch.setattr(pipeline, "run", lambda job, store: {})
    sched.worker_run_once(store=None)
    labels2, val2 = g.last["val"]
    assert labels2.get("tenant") == "t" and labels2.get("workspace") == "w"
    assert val2 >= 0
