from __future__ import annotations

from fastapi.testclient import TestClient
from server.app import create_app


def test_metrics_not_rate_limited(monkeypatch):
    monkeypatch.setenv("ENABLE_PROMETHEUS_ENDPOINT", "1")
    monkeypatch.setenv("ENABLE_RATE_LIMITING", "1")
    monkeypatch.setenv("ENABLE_HTTP_METRICS", "1")
    monkeypatch.setenv("RATE_LIMIT_RPS", "1")
    monkeypatch.setenv("RATE_LIMIT_BURST", "1")

    app = create_app()
    client = TestClient(app)

    # Exhaust bucket with non-metrics calls
    for _ in range(5):
        client.get("/some_path")

    # Metrics endpoint should always succeed (never 429)
    resp = client.get("/metrics")
    assert resp.status_code == 200, f"Expected /metrics 200, got {resp.status_code}"
