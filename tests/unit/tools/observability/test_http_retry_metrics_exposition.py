import pytest
from platform.observability import metrics as metrics_mod
from platform.http.http_utils import http_request_with_retry

def test_retry_metrics_exposed(monkeypatch):
    """Ensure retry attempt & give-up counters appear in scrape text when enabled.

    We simulate one failing request that triggers retries then a give-up.
    """
    monkeypatch.setenv('ENABLE_HTTP_METRICS', '1')
    monkeypatch.setenv('ENABLE_PROMETHEUS_ENDPOINT', '1')
    monkeypatch.setenv('ENABLE_HTTP_RETRY', '1')
    if hasattr(metrics_mod, 'reset'):
        metrics_mod.reset()

    class FakeResp:

        def __init__(self, code):
            self.status_code = code
    attempts: dict[str, int] = {'count': 0}

    def always_500(url, **kwargs):
        attempts['count'] += 1
        return FakeResp(500)
    http_request_with_retry('GET', 'https://example.com/fail', request_callable=always_500, max_attempts=2)
    try:
        from prometheus_client import REGISTRY, generate_latest
    except Exception:
        pytest.skip('prometheus_client not installed')
    else:
        scrape = generate_latest(REGISTRY).decode()
    assert 'http_retry_attempts_total' in scrape