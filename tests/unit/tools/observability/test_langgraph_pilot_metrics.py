from platform.observability import metrics

import pytest

from graphs.langgraph_pilot import run_ingest_analysis_pilot


def test_pilot_emits_pipeline_duration(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT", "1")
    metrics.reset()

    def _ingest(job: dict):
        return {"ok": True}

    def _analyze(ctx: dict):
        return {"analysis": 1}

    out = run_ingest_analysis_pilot({}, _ingest, _analyze)
    assert out["analysis"]["analysis"] == 1
    rendered = metrics.render().decode("utf-8") if metrics.PROMETHEUS_AVAILABLE else ""
    assert (
        "pipeline_duration_seconds" in rendered
        and "pipeline_total_duration_seconds" in rendered
        and ("pipeline_step_duration_seconds" in rendered)
        and ("pipeline_requests_total" in rendered)
    ) or not metrics.PROMETHEUS_AVAILABLE
