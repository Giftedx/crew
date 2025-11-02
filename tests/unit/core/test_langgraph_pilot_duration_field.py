import pytest

from src.graphs.langgraph_pilot import run_ingest_analysis_pilot


def test_run_ingest_analysis_pilot_includes_duration(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT", "1")

    def _ingest(job: dict):
        return {"ok": True}

    def _analyze(ctx: dict):
        return {"done": True}

    out = run_ingest_analysis_pilot({}, _ingest, _analyze)
    assert "duration_seconds" in out
    assert isinstance(out["duration_seconds"], (int, float))
    assert out["duration_seconds"] >= 0.0
