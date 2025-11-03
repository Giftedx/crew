import pytest

from src.fastapi.testclient import TestClient
from src.server.app import create_app


def test_pilot_endpoint(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT_API", "1")
    monkeypatch.delenv("ENABLE_LANGGRAPH_PILOT", raising=False)
    app = create_app()
    client = TestClient(app)
    resp = client.get("/pilot/run?tenant=t&workspace=w")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "ingest" in data and "analysis" in data
    assert data["ingest"].get("chunks") == 2
    ns = data["ingest"].get("namespace", "")
    assert ns.startswith("t:w:")


def test_pilot_endpoint_enabled_orchestrator(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT_API", "1")
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT", "1")
    app = create_app()
    client = TestClient(app)
    resp = client.get("/pilot/run")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("orchestrator") in ("langgraph_stub", "sequential")


def test_pilot_endpoint_includes_duration(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT_API", "1")
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT", "1")
    app = create_app()
    client = TestClient(app)
    resp = client.get("/pilot/run")
    assert resp.status_code == 200
    data = resp.json()
    assert "duration_seconds" in data
    assert isinstance(data["duration_seconds"], (int, float))
    assert data["duration_seconds"] >= 0.0


def test_pilot_endpoint_emits_duration_metric(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT_API", "1")
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT", "1")
    from platform.observability import metrics

    metrics.reset()
    app = create_app()
    client = TestClient(app)
    resp = client.get("/pilot/run")
    assert resp.status_code == 200
    rendered = metrics.render().decode("utf-8") if metrics.PROMETHEUS_AVAILABLE else ""
    assert "pipeline_duration_seconds" in rendered or not metrics.PROMETHEUS_AVAILABLE
