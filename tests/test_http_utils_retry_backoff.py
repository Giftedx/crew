from __future__ import annotations

from typing import Any

import pytest
from core import http_utils


class _Resp:
    def __init__(self, status_code: int = 200, text: str = "ok") -> None:
        self.status_code = status_code
        self.text = text


def test_http_request_with_retry_backoff_and_success(monkeypatch):
    # Enable retries via environment
    monkeypatch.setenv("ENABLE_HTTP_RETRY", "1")

    calls: list[str] = []
    sleeps: list[float] = []

    def fake_sleep(n: float) -> None:
        sleeps.append(n)

    monkeypatch.setattr(http_utils.time, "sleep", fake_sleep)

    # First two attempts raise, third succeeds
    state = {"n": 0}

    def req(url: str, **_: Any) -> Any:
        state["n"] += 1
        calls.append(url)
        if state["n"] < 3:
            raise http_utils.requests.ConnectionError("Connection refused")
        return _Resp(200)

    out = http_utils.http_request_with_retry(
        "GET",
        "https://example.com",
        request_callable=req,
        max_attempts=3,
        base_backoff=0.1,
        jitter=0.0,
    )
    assert isinstance(out, _Resp)
    # Two sleeps between three attempts; connection-refused reduces base by 0.3
    # so backoffs are 0.03, 0.06 (with jitter=0.0)
    assert sleeps == pytest.approx([0.03, 0.06])
    assert calls == ["https://example.com", "https://example.com", "https://example.com"]


def test_retrying_get_uses_wrapper_and_honors_attempts(monkeypatch):
    monkeypatch.setenv("ENABLE_HTTP_RETRY", "1")

    sleeps: list[float] = []
    monkeypatch.setattr(http_utils.time, "sleep", lambda n: sleeps.append(n))

    attempt = {"i": 0}

    def callable(url: str, **_: Any) -> Any:
        attempt["i"] += 1
        if attempt["i"] < 2:
            # Immediate retry once
            return _Resp(500)
        return _Resp(200)

    resp = http_utils.retrying_get(
        "https://example.com/x",
        request_callable=callable,
        max_attempts=3,
    )
    assert isinstance(resp, _Resp)
    # One retry sleep with base 0.5 and default jitter 0.05 => 0.525
    assert sleeps == pytest.approx([0.525])
