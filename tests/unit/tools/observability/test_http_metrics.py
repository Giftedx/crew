import os
from platform.observability import metrics

import pytest

from fastapi.testclient import TestClient
from ultimate_discord_intelligence_bot.server.app import create_app


@pytest.mark.skipif("fastapi" not in globals(), reason="fastapi not available")
def test_http_metrics_middleware_counts():
    os.environ["ENABLE_HTTP_METRICS"] = "1"
    os.environ["ENABLE_PROMETHEUS_ENDPOINT"] = "1"
    metrics.reset()
    app = create_app()
    client = TestClient(app)
    r1 = client.get("/metrics")
    assert r1.status_code == 200
    r2 = client.get("/non-existent")
    assert r2.status_code == 404
    r3 = client.get("/metrics")
    body = r3.text
    assert "http_requests_total" in body
    assert "404" in body
    assert "http_request_latency_ms_bucket" in body
