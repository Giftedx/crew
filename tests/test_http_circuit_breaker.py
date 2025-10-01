import pytest

from core.http_utils import http_request_with_retry


class _Resp:
    def __init__(self, status: int) -> None:
        self.status_code = status


def _fail_500(_url: str, **_kwargs):
    return _Resp(500)


def test_http_circuit_breaker_opens_and_short_circuits(monkeypatch):
    # Enable circuit breaker; keep retry disabled for deterministic behavior
    monkeypatch.setenv("ENABLE_HTTP_CIRCUIT_BREAKER", "1")

    url = "https://example.com"
    # Trip the breaker by making failure_threshold (5) consecutive 500s
    for _ in range(5):
        resp = http_request_with_retry(
            "GET",
            url,
            request_callable=_fail_500,
            max_attempts=1,  # no retries
            base_backoff=0.0,
            jitter=0.0,
            statuses_to_retry=(),  # avoid retry path even if retry flag is on
        )
        assert resp.status_code == 500

    # Next call should short-circuit while breaker is open
    with pytest.raises(Exception) as ei:
        http_request_with_retry(
            "GET",
            url,
            request_callable=_fail_500,
            max_attempts=1,
            base_backoff=0.0,
            jitter=0.0,
            statuses_to_retry=(),
        )
    assert "circuit_open" in str(ei.value)
