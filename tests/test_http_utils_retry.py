import pytest

from core.http_utils import HTTP_RATE_LIMITED, http_request_with_retry


def test_http_request_with_retry_status(monkeypatch):
    monkeypatch.setenv("ENABLE_HTTP_RETRY", "1")
    calls = {"count": 0}

    class Resp:
        def __init__(self, status):
            self.status_code = status

    def fake(url, **kwargs):  # always returns 429 twice then 200
        calls["count"] += 1
        if calls["count"] < 3:
            return Resp(HTTP_RATE_LIMITED)
        return Resp(200)

    resp = http_request_with_retry(
        "GET",
        "https://example.com",
        request_callable=fake,
        max_attempts=4,
        base_backoff=0.0,
        jitter=0.0,
    )
    assert resp.status_code == 200
    assert calls["count"] == 3  # two retries then success


def test_http_request_with_retry_network_error(monkeypatch):
    monkeypatch.setenv("ENABLE_HTTP_RETRY", "1")
    calls = {"count": 0}

    class Resp:
        status_code = 200

    def fake(url, **kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            raise Exception("boom")  # not a requests.RequestException, won't retry
        return Resp()

    # Since generic Exception isn't subclass of requests.RequestException,
    # the helper should NOT retry and should raise immediately.
    with pytest.raises(Exception):
        http_request_with_retry(
            "GET",
            "https://example.com",
            request_callable=fake,
            max_attempts=3,
            base_backoff=0.0,
            jitter=0.0,
        )
    assert calls["count"] == 1


def test_http_request_with_retry_network_requests_exception(monkeypatch):
    import requests

    monkeypatch.setenv("ENABLE_HTTP_RETRY", "1")
    calls = {"count": 0}

    class Resp:
        status_code = 200

    def fake(url, **kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            raise requests.ConnectionError("net down")
        return Resp()

    resp = http_request_with_retry(
        "GET",
        "https://example.com",
        request_callable=fake,
        max_attempts=3,
        base_backoff=0.0,
        jitter=0.0,
    )
    assert resp.status_code == 200
    assert calls["count"] == 3
