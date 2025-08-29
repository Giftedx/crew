from core.learning_engine import LearningEngine
from discord import commands
from ingest import models, pipeline
from ingest.sources.youtube import YouTubeConnector
from scheduler import PriorityQueue, Scheduler


def test_scheduler_enqueues_and_processes(tmp_path, monkeypatch):
    conn = models.connect(tmp_path / "sched.db")
    queue = PriorityQueue(conn)
    learner = LearningEngine()
    learner.register_domain("scheduler")
    sched = Scheduler(conn, queue, {"youtube": YouTubeConnector()}, learner=learner)

    sched.add_watch(tenant="t", workspace="w", source_type="youtube", handle="vid1")
    sched.tick()
    assert queue.pending_count() == 1

    ran: list[str] = []

    def fake_run(job, store):
        ran.append(job.external_id)
        return {"chunks": 0}

    monkeypatch.setattr(pipeline, "run", fake_run)
    sched.worker_run_once(store=None)
    assert ran == ["vid1"]
    assert queue.pending_count() == 0

    sched.tick()
    assert queue.pending_count() == 0

    status = learner.status()["scheduler"]["arms"]
    assert sum(v["n"] for v in status.values()) == 1


def test_ops_helpers(tmp_path, monkeypatch):
    conn = models.connect(tmp_path / "sched.db")
    queue = PriorityQueue(conn)
    sched = Scheduler(conn, queue, {"youtube": YouTubeConnector()})

    commands.ops_ingest_watch_add(sched, "youtube", "vid1", tenant="t", workspace="w")
    assert commands.ops_ingest_watch_list(sched)
    sched.tick()
    status = commands.ops_ingest_queue_status(queue)
    assert status["pending"] == 1

    monkeypatch.setattr(pipeline, "run", lambda job, store: {})
    commands.ops_ingest_run_once(sched, store=None)
    status = commands.ops_ingest_queue_status(queue)
    assert status["pending"] == 0
