import pytest

from src.graphs.langgraph_pilot import run_ingest_analysis_pilot
from src.obs import metrics


def test_skipped_counters_when_segment_and_embed_omitted(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT", "1")
    metrics.reset()

    def _ingest(job: dict):
        return {"ok": True}

    def _analyze(ctx: dict):
        return {"analysis": 1}

    out = run_ingest_analysis_pilot({}, _ingest, _analyze)
    assert out["analysis"]["analysis"] == 1

    rendered = metrics.render().decode("utf-8") if metrics.PROMETHEUS_AVAILABLE else ""
    if metrics.PROMETHEUS_AVAILABLE:
        assert "pipeline_steps_skipped_total" in rendered
        assert 'step="segment"' in rendered
        assert 'step="embed"' in rendered
