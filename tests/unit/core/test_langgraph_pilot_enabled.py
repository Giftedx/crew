import pytest

from graphs.langgraph_pilot import run_ingest_analysis_pilot
from ultimate_discord_intelligence_bot.obs import metrics


def test_langgraph_pilot_enabled_stub(monkeypatch: pytest.MonkeyPatch):
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
    assert "pipeline_steps_completed_total" in rendered or not metrics.PROMETHEUS_AVAILABLE
