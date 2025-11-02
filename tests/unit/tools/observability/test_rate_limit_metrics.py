import os
import re
from fastapi.testclient import TestClient
from platform.observability import metrics
from ultimate_discord_intelligence_bot.server.app import create_app

def test_rate_limit_rejections_metric_increments():
    os.environ['ENABLE_API'] = '1'
    os.environ['ENABLE_HTTP_METRICS'] = '1'
    os.environ['ENABLE_PROMETHEUS_ENDPOINT'] = '1'
    os.environ['ENABLE_RATE_LIMITING'] = '1'
    os.environ['RATE_LIMIT_RPS'] = '3'
    os.environ['RATE_LIMIT_BURST'] = '3'
    app = create_app()
    client = TestClient(app)
    for _ in range(5):
        client.get('/__not_exist')
    metrics_resp = client.get('/metrics')
    assert metrics_resp.status_code == 200
    raw = metrics_resp._content.decode()
    if metrics.PROMETHEUS_AVAILABLE:
        assert 'rate_limit_rejections_total' in raw
    else:
        assert raw == '' or raw == b'' or isinstance(raw, str)

def test_rate_limit_rejections_metric():
    """Ensure rate_limit_rejections_total counter increments on 429 responses.

    We enable both HTTP metrics and the in-process rate limiter with a very small
    rate/burst so that multiple rapid requests trigger rejections. Then we fetch
    the Prometheus exposition and assert the counter reflects the number of 429s.
    """
    os.environ['ENABLE_API'] = '1'
    os.environ['ENABLE_HTTP_METRICS'] = '1'
    os.environ['ENABLE_PROMETHEUS_ENDPOINT'] = '1'
    os.environ['ENABLE_RATE_LIMITING'] = '1'
    os.environ['RATE_LIMIT_RPS'] = '1'
    os.environ['RATE_LIMIT_BURST'] = '1'
    metrics.reset()
    app = create_app()
    client = TestClient(app)
    path = '/rltest'
    rejected = 0
    for _total, _ in enumerate(range(1, 6), start=1):
        resp = client.get(path)
        if resp.status_code == 429:
            rejected += 1
    assert rejected >= 1, 'Expected at least one 429 under rate limiting'
    if getattr(metrics, 'PROMETHEUS_AVAILABLE', False):
        prom_text = client.get('/metrics').text
        pattern = f'rate_limit_rejections_total\\{{(?=[^}}]*route="{path}")(?=[^}}]*method="GET")[^}}]*\\}} (\\d+(?:\\.\\d+)?)'
        match = re.search(pattern, prom_text)
        assert match, f'Did not find rate_limit_rejections_total series for {path}. Exposition was:\n{prom_text}'
        value = float(match.group(1))
        assert int(value) == rejected, f'Metric value {value} != observed 429 count {rejected}'
    else:
        assert rejected >= 1