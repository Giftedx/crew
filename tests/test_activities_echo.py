from __future__ import annotations

from fastapi.testclient import TestClient
from server.app import create_app


def test_activities_echo_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_ACTIVITIES_ECHO", "1")
    app = create_app()
    client = TestClient(app)
    resp = client.get(
        "/activities/echo?q=ping",
        headers={
            "Origin": "http://localhost:5173",
            "User-Agent": "pytest",
            "Accept": "application/json",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["component"] == "activities-echo"
    assert data["path"] == "/activities/echo"
    assert data["query"].get("q") == "ping"
    assert "headers" in data


def test_activities_echo_disabled(monkeypatch):
    monkeypatch.delenv("ENABLE_ACTIVITIES_ECHO", raising=False)
    app = create_app()
    client = TestClient(app)
    resp = client.get("/activities/echo")
    assert resp.status_code == 404
