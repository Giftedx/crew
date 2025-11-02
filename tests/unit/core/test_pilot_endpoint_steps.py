import pytest

from src.fastapi.testclient import TestClient
from src.server.app import create_app


def test_pilot_endpoint_with_segment_and_embed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_LANGGRAPH_PILOT_API", "1")
    app = create_app()
    client = TestClient(app)

    resp = client.get("/pilot/run?enable_segment=1&enable_embed=1")
    assert resp.status_code == 200
    data = resp.json()
    # When segment and embed are enabled, expect derived keys
    assert data.get("ingest", {}).get("chunks") == 2
    # segment and embed keys present only when enabled
    # (Note: step outputs are attached at top-level by pilot function)
    # Since endpoint returns the pilot outputs, ensure keys exist
    assert "analysis" in data
