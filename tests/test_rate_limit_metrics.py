import os
import re

from fastapi.testclient import TestClient

from obs import metrics
from server.app import create_app


def test_rate_limit_rejections_metric():
    """Ensure rate_limit_rejections_total counter increments on 429 responses.

    We enable both HTTP metrics and the in-process rate limiter with a very small
    rate/burst so that multiple rapid requests trigger rejections. Then we fetch
    the Prometheus exposition and assert the counter reflects the number of 429s.
    """
    # Environment flags
    os.environ["ENABLE_API"] = "1"
    os.environ["ENABLE_HTTP_METRICS"] = "1"
    os.environ["ENABLE_PROMETHEUS_ENDPOINT"] = "1"
    os.environ["ENABLE_RATE_LIMITING"] = "1"
    os.environ["RATE_LIMIT_RPS"] = "1"
    os.environ["RATE_LIMIT_BURST"] = "1"

    # Fresh metrics registry for deterministic assertions
    metrics.reset()

    app = create_app()
    client = TestClient(app)

    path = "/rltest"
    total = 0
    rejected = 0
    # First request should pass (fills bucket), remaining (without pause) should 429
    for _ in range(5):
        total += 1
        resp = client.get(path)
        if resp.status_code == 429:
            rejected += 1

    # Basic sanity: we expect at least one rejection given tight limits
    assert rejected >= 1, "Expected at least one 429 under rate limiting"

    # If prometheus client not installed, metrics are no-ops; just ensure rejection count >0
    if getattr(metrics, "PROMETHEUS_AVAILABLE", False):
        prom_text = client.get("/metrics").text
        pattern = rf'rate_limit_rejections_total\{{route="{path}",method="GET"}} (\d+(?:\.\d+)?)'
        m = re.search(pattern, prom_text)
        assert m, f"Did not find rate_limit_rejections_total series for {path}. Exposition was:\n{prom_text}"
        value = float(m.group(1))
        assert int(value) == rejected, f"Metric value {value} != observed 429 count {rejected}"
    else:
        # Document expectation: without prometheus_client metrics are inert but code path ran
        assert rejected >= 1
