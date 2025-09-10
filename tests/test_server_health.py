from __future__ import annotations

from fastapi.testclient import TestClient
from server.app import create_app


def test_health_endpoint():
    app = create_app()
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json().get("status") == "ok"
