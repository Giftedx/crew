from platform.observability import metrics

import pytest

from graphs.langgraph_pilot import run_ingest_analysis_pilot


def test_pilot_metrics_include_tenant_workspace_labels(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT", "1")
    metrics.reset()

    def _ingest(job: dict):
        return {"ok": True}

    def _analyze(ctx: dict):
        return {"analysis": 1}

    job = {"tenant": "t123", "workspace": "w456"}
    out = run_ingest_analysis_pilot(job, _ingest, _analyze)
    assert out["analysis"]["analysis"] == 1
    rendered = metrics.render().decode("utf-8") if metrics.PROMETHEUS_AVAILABLE else ""
    if metrics.PROMETHEUS_AVAILABLE:
        assert "pipeline_requests_total" in rendered
        assert 'tenant="t123"' in rendered
        assert 'workspace="w456"' in rendered
        assert "pipeline_total_duration_seconds" in rendered
        assert 'orchestrator="' in rendered
