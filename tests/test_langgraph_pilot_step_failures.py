import pytest

from src.graphs.langgraph_pilot import run_ingest_analysis_pilot
from src.obs import metrics


def test_segment_failure_emits_degradation_and_continues(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT", "1")
    metrics.reset()

    def _ingest(job: dict):
        return {"chunks": 1}

    def _segment(_ctx: dict):
        raise RuntimeError("seg fail")

    def _analyze(ctx: dict):
        # Should still run
        return {"ok": True, "chunks": ctx.get("chunks")}

    out = run_ingest_analysis_pilot({}, _ingest, _analyze, segment_fn=_segment)
    assert out["analysis"]["ok"] is True
    # segment step present but empty or missing; accept either behavior
    assert "analysis" in out

    rendered = metrics.render().decode("utf-8") if metrics.PROMETHEUS_AVAILABLE else ""
    if metrics.PROMETHEUS_AVAILABLE:
        assert "degradation_events_total" in rendered
        assert 'component="langgraph_pilot"' in rendered
        assert 'event_type="segment_failure"' in rendered
        assert "pipeline_steps_failed_total" in rendered
        assert 'step="segment"' in rendered


def test_embed_failure_emits_degradation_and_continues(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT", "1")
    metrics.reset()

    def _ingest(job: dict):
        return {"chunks": 1}

    def _segment(ctx: dict):
        return {"segments": 2}

    def _embed(_ctx: dict):
        raise ValueError("embed fail")

    def _analyze(ctx: dict):
        # Should still run
        return {"ok": True}

    out = run_ingest_analysis_pilot({}, _ingest, _analyze, segment_fn=_segment, embed_fn=_embed)
    assert out["analysis"]["ok"] is True

    rendered = metrics.render().decode("utf-8") if metrics.PROMETHEUS_AVAILABLE else ""
    if metrics.PROMETHEUS_AVAILABLE:
        assert "degradation_events_total" in rendered
        assert 'component="langgraph_pilot"' in rendered
        assert 'event_type="embed_failure"' in rendered
        assert "pipeline_steps_failed_total" in rendered
        assert 'step="embed"' in rendered
