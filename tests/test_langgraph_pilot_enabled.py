import pytest

from src.graphs.langgraph_pilot import run_ingest_analysis_pilot
from src.obs import metrics


def test_langgraph_pilot_enabled_stub(monkeypatch: pytest.MonkeyPatch):
    # Enable the pilot; LANGGRAPH_AVAILABLE is False in our stub, but code runs same stub path and records completion metric
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT", "1")

    metrics.reset()

    def _ingest(job: dict):
        return {"chunks": 1}

    def _analyze(ctx: dict):
        return {"analysis": True}

    out = run_ingest_analysis_pilot({}, _ingest, _analyze)
    assert out["ingest"]["chunks"] == 1
    assert out["analysis"]["analysis"] is True

    rendered = metrics.render().decode("utf-8") if metrics.PROMETHEUS_AVAILABLE else ""
    # We expect pipeline_steps_completed_total series name to exist in exposition or metrics to be no-op
    assert "pipeline_steps_completed_total" in rendered or not metrics.PROMETHEUS_AVAILABLE
