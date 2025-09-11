import os

import pytest
from fastapi.testclient import TestClient
from obs import metrics
from server.app import create_app


@pytest.mark.skipif("fastapi" not in globals(), reason="fastapi not available")
def test_http_metrics_middleware_counts():
    # Enable metrics explicitly
    os.environ["ENABLE_HTTP_METRICS"] = "1"
    os.environ["ENABLE_PROMETHEUS_ENDPOINT"] = "1"
    metrics.reset()
    app = create_app()
    client = TestClient(app)

    # Simulate a couple of requests (one normal, one metrics scrape)
    r1 = client.get("/metrics")  # scrape (should not self-instrument)
    assert r1.status_code == 200
    r2 = client.get("/non-existent")  # generates 404 and should be counted
    assert r2.status_code == 404

    # Scrape metrics again to inspect counters
    r3 = client.get("/metrics")
    body = r3.text
    # Expect at least one request counter line for the 404
    assert "http_requests_total" in body
    assert "404" in body

    # Latency histogram name should appear
    assert "http_request_latency_ms_bucket" in body
