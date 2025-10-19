from __future__ import annotations

from fastapi.testclient import TestClient
from ultimate_discord_intelligence_bot.server.app import create_app


def test_activities_health_endpoint():
    app = create_app()
    client = TestClient(app)
    res = client.get("/activities/health")
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "ok"
    assert data.get("component") == "activities"
