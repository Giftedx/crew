import pytest
import requests
from platform.observability import metrics as m
from platform.core.http import reset_circuit_breakers
from platform.http.http_utils import http_request_with_retry

@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset metrics and circuit breaker state between tests to avoid cross-test contamination."""
    m.reset()
    reset_circuit_breakers()
    yield
    m.reset()
    reset_circuit_breakers()

def _counter_value(counter, **label_match):
    collect = getattr(counter, 'collect', None)
    if collect is None:
        return None
    for metric in collect():
        for sample in metric.samples:
            if all((sample.labels.get(k) == v for k, v in label_match.items())):
                return sample.value
    return 0.0

def test_http_retry_metrics_giveup(monkeypatch):
    """Network exception path should increment attempts for each retry beyond first and one giveup."""
    monkeypatch.setenv('ENABLE_HTTP_RETRY', '1')
    monkeypatch.setenv('ENABLE_HTTP_CIRCUIT_BREAKER', '1')
    monkeypatch.setattr('time.sleep', lambda _x: None)
    calls = {'n': 0}

    def failing(url, **kwargs):
        calls['n'] += 1
        raise requests.ConnectionError('net down')
    with pytest.raises(requests.ConnectionError):
        http_request_with_retry('GET', 'https://example.com/x', request_callable=failing, max_attempts=3, base_backoff=0.0, jitter=0.0)
    attempts_val = _counter_value(m.HTTP_RETRY_ATTEMPTS, tenant='unknown', workspace='unknown', method='GET')
    giveups_val = _counter_value(m.HTTP_RETRY_GIVEUPS, tenant='unknown', workspace='unknown', method='GET')
    if getattr(m, 'PROMETHEUS_AVAILABLE', False):
        assert attempts_val == 2
        assert giveups_val == 1
    else:
        assert calls['n'] == 3

def test_http_retry_metrics_success_after_retries(monkeypatch):
    """Status-based retry success should increment attempts but not giveups."""
    monkeypatch.setenv('ENABLE_HTTP_RETRY', '1')
    monkeypatch.setenv('ENABLE_HTTP_CIRCUIT_BREAKER', '1')
    monkeypatch.setattr('time.sleep', lambda _x: None)
    calls = {'n': 0}

    class Resp:

        def __init__(self, status_code):
            self.status_code = status_code

    def flaky(url, **kwargs):
        calls['n'] += 1
        return Resp(500 if calls['n'] < 3 else 200)
    resp = http_request_with_retry('GET', 'https://example.com/y', request_callable=flaky, max_attempts=5, base_backoff=0.0, jitter=0.0)
    assert resp.status_code == 200
    attempts_val = _counter_value(m.HTTP_RETRY_ATTEMPTS, tenant='unknown', workspace='unknown', method='GET')
    giveups_val = _counter_value(m.HTTP_RETRY_GIVEUPS, tenant='unknown', workspace='unknown', method='GET')
    if getattr(m, 'PROMETHEUS_AVAILABLE', False):
        assert attempts_val == 2
        assert giveups_val == 0
    else:
        assert calls['n'] == 3