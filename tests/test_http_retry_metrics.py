import os
import requests
import pytest

from core.http_utils import http_request_with_retry
from obs import metrics as m
from obs.metrics import HTTP_RETRY_ATTEMPTS, HTTP_RETRY_GIVEUPS


def _counter_value(counter, **label_match):  # helper resilient to missing prometheus
    # No-op counters won't have collect(); return None to signal unassertable
    collect = getattr(counter, "collect", None)
    if collect is None:
        return None
    for metric in collect():
        for sample in metric.samples:
            if all(sample.labels.get(k) == v for k, v in label_match.items()):
                return sample.value
    return 0.0


def test_http_retry_metrics_giveup(monkeypatch):
    """Network exception path should increment attempts for each retry beyond first and one giveup."""
    monkeypatch.setenv("ENABLE_ANALYSIS_HTTP_RETRY", "1")
    # speed: eliminate real sleeping
    monkeypatch.setattr("time.sleep", lambda _x: None)
    m.reset()

    calls = {"n": 0}

    def failing(url, **kwargs):
        calls["n"] += 1
        # Always raise retriable ConnectionError
        raise requests.ConnectionError("net down")

    with pytest.raises(requests.ConnectionError):
        http_request_with_retry(
            "GET",
            "https://example.com/x",
            request_callable=failing,
            max_attempts=3,
            base_backoff=0.0,
            jitter=0.0,
        )
    attempts_val = _counter_value(HTTP_RETRY_ATTEMPTS, tenant="unknown", workspace="unknown", method="GET")
    giveups_val = _counter_value(HTTP_RETRY_GIVEUPS, tenant="unknown", workspace="unknown", method="GET")

    if getattr(m, "PROMETHEUS_AVAILABLE", False):
        # Two retries beyond the first attempt (attempts = 3 total => 2 increments) and one giveup.
        assert attempts_val == 2
        assert giveups_val == 1
    else:
        # No-op metrics; just ensure logic executed expected number of attempts.
        assert calls["n"] == 3


def test_http_retry_metrics_success_after_retries(monkeypatch):
    """Status-based retry success should increment attempts but not giveups."""
    monkeypatch.setenv("ENABLE_ANALYSIS_HTTP_RETRY", "1")
    monkeypatch.setattr("time.sleep", lambda _x: None)
    m.reset()

    calls = {"n": 0}

    class Resp:
        def __init__(self, status_code):
            self.status_code = status_code

    def flaky(url, **kwargs):
        calls["n"] += 1
        # First two attempts return 500, third succeeds
        return Resp(500 if calls["n"] < 3 else 200)

    resp = http_request_with_retry(
        "GET",
        "https://example.com/y",
        request_callable=flaky,
        max_attempts=5,
        base_backoff=0.0,
        jitter=0.0,
    )
    assert resp.status_code == 200

    attempts_val = _counter_value(HTTP_RETRY_ATTEMPTS, tenant="unknown", workspace="unknown", method="GET")
    giveups_val = _counter_value(HTTP_RETRY_GIVEUPS, tenant="unknown", workspace="unknown", method="GET")

    if getattr(m, "PROMETHEUS_AVAILABLE", False):
        # Two retries performed (attempts beyond first) and no giveup.
        assert attempts_val == 2
        assert giveups_val == 0
    else:
        assert calls["n"] == 3
