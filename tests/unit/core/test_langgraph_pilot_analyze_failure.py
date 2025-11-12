import pytest

from graphs.langgraph_pilot import run_ingest_analysis_pilot
from ultimate_discord_intelligence_bot.obs import metrics


def test_analyze_failure_increments_failed_and_error_status(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT", "1")
    metrics.reset()

    def _ingest(job: dict):
        return {"ok": True}

    def _analyze(ctx: dict):
        raise RuntimeError("analysis boom")

    with pytest.raises(RuntimeError):
        run_ingest_analysis_pilot({}, _ingest, _analyze)
    rendered = metrics.render().decode("utf-8") if metrics.PROMETHEUS_AVAILABLE else ""
    if metrics.PROMETHEUS_AVAILABLE:
        assert "pipeline_steps_failed_total" in rendered
        assert 'step="analyze"' in rendered
        assert "pipeline_duration_seconds" in rendered
        assert 'status="error"' in rendered
