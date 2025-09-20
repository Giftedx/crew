import pytest

from src.graphs.langgraph_pilot import run_ingest_analysis_pilot
from src.obs import metrics


def test_langgraph_pilot_sequential_fallback(monkeypatch: pytest.MonkeyPatch):
    # Ensure pilot is disabled so fallback triggers, independent of library presence
    monkeypatch.delenv("ENABLE_LANGGRAPH_PILOT", raising=False)

    metrics.reset()

    def _ingest(job: dict):
        return {"chunks": 3, "namespace": "t:w:n"}

    def _analyze(ctx: dict):
        # Basic assertion the ingest result is visible
        assert ctx.get("chunks") == 3
        return {"insights": 2}

    out = run_ingest_analysis_pilot({"tenant": "t", "workspace": "w"}, _ingest, _analyze)

    assert out["ingest"]["chunks"] == 3
    assert out["analysis"]["insights"] == 2
    assert out["orchestrator"] == "sequential"

    rendered = metrics.render().decode("utf-8") if metrics.PROMETHEUS_AVAILABLE else ""
    # We can't guarantee counters > 0 without full client, but metric names should be present if available
    assert "degradation_events_total" in rendered or not metrics.PROMETHEUS_AVAILABLE
