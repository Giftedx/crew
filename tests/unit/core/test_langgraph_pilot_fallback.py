from platform.observability import metrics

import pytest

from graphs.langgraph_pilot import run_ingest_analysis_pilot


def test_langgraph_pilot_sequential_fallback(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ENABLE_LANGGRAPH_PILOT", raising=False)
    metrics.reset()

    def _ingest(job: dict):
        return {"chunks": 3, "namespace": "t:w:n"}

    def _analyze(ctx: dict):
        assert ctx.get("chunks") == 3
        return {"insights": 2}

    out = run_ingest_analysis_pilot({"tenant": "t", "workspace": "w"}, _ingest, _analyze)
    assert out["ingest"]["chunks"] == 3
    assert out["analysis"]["insights"] == 2
    assert out["orchestrator"] == "sequential"
    rendered = metrics.render().decode("utf-8") if metrics.PROMETHEUS_AVAILABLE else ""
    assert "degradation_events_total" in rendered or not metrics.PROMETHEUS_AVAILABLE
