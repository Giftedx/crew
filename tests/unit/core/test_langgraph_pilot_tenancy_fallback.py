from platform.observability import metrics

import pytest

from graphs.langgraph_pilot import run_ingest_analysis_pilot


def test_pilot_emits_tenancy_fallback_when_no_context(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT", "1")
    metrics.reset()

    def _ingest(job: dict):
        return {"ok": True}

    def _analyze(ctx: dict):
        return {"analysis": 1}

    job = {}
    out = run_ingest_analysis_pilot(job, _ingest, _analyze)
    assert out["analysis"]["analysis"] == 1
    if metrics.PROMETHEUS_AVAILABLE:
        rendered = metrics.render().decode("utf-8")
        assert "tenancy_fallback_total" in rendered
        assert 'tenant="unknown"' in rendered
        assert 'workspace="unknown"' in rendered
        assert 'component="langgraph_pilot"' in rendered
