import os
import importlib
from unittest.mock import patch, MagicMock

import pytest

from core.http_utils import (
    retrying_post,
    retrying_get,
    DEFAULT_HTTP_RETRY_ATTEMPTS,
    HTTP_RATE_LIMITED,
)
from obs.metrics import HTTP_RETRY_ATTEMPTS, HTTP_RETRY_GIVEUPS


def _reset_metrics():
    # Prometheus client counters can be cleared by recreating the registry via reload if needed, but
    # here we just rely on labels() to isolate. No-op placeholder for future refinement.
    pass


@patch.dict(os.environ, {"ENABLE_ANALYSIS_HTTP_RETRY": "1"})
@patch("core.http_utils.resilient_post")
@patch("core.http_utils.http_request_with_retry")
def test_retrying_post_enabled(mock_retry, mock_post):
    mock_post.return_value = {"ok": True}
    mock_retry.return_value = {"ok": True}
    url = "https://example.com/api"
    result = retrying_post(url, json_payload={"x": 1})
    assert result["ok"] is True
    mock_retry.assert_called_once()
    # underlying resilient_post should be wrapped in lambda and called within retry fn
    assert mock_post.call_count == 0  # not called directly when retries enabled


@patch.dict(os.environ, {"ENABLE_ANALYSIS_HTTP_RETRY": ""})
@patch("core.http_utils.resilient_post")
@patch("core.http_utils.http_request_with_retry")
def test_retrying_post_disabled(mock_retry, mock_post):
    mock_post.return_value = {"ok": True}
    url = "https://example.com/api"
    result = retrying_post(url, json_payload={"x": 1})
    assert result["ok"] is True
    mock_retry.assert_not_called()
    mock_post.assert_called_once()


@patch.dict(os.environ, {"ENABLE_ANALYSIS_HTTP_RETRY": "1"})
@patch("core.http_utils.resilient_get")
@patch("core.http_utils.http_request_with_retry")
def test_retrying_get_enabled(mock_retry, mock_get):
    mock_get.return_value = {"ok": True}
    mock_retry.return_value = {"ok": True}
    url = "https://example.com/data"
    result = retrying_get(url, params={"q": "x"})
    assert result["ok"] is True
    mock_retry.assert_called_once()
    assert mock_get.call_count == 0


@patch.dict(os.environ, {"ENABLE_ANALYSIS_HTTP_RETRY": ""})
@patch("core.http_utils.resilient_get")
@patch("core.http_utils.http_request_with_retry")
def test_retrying_get_disabled(mock_retry, mock_get):
    mock_get.return_value = {"ok": True}
    url = "https://example.com/data"
    result = retrying_get(url, params={"q": "x"})
    assert result["ok"] is True
    mock_retry.assert_not_called()
    mock_get.assert_called_once()


@patch.dict(os.environ, {"ENABLE_ANALYSIS_HTTP_RETRY": "1"})
def test_retrying_post_actual_retry(monkeypatch):
    calls = {"n": 0}

    class DummyResp:
        def __init__(self, status_code):
            self.status_code = status_code

    def failing_post(url, **kwargs):
        calls["n"] += 1
        if calls["n"] < 2:
            return DummyResp(500)
        return DummyResp(200)

    monkeypatch.setattr("core.http_utils.resilient_post", failing_post)
    # ensure real retry path used
    from core import http_utils as http_mod
    importlib.reload(http_mod)
    r = http_mod.retrying_post("https://example.com/x")
    assert isinstance(r, DummyResp)
    assert calls["n"] == 2


@patch.dict(os.environ, {"ENABLE_ANALYSIS_HTTP_RETRY": "1"})
def test_retrying_get_actual_retry(monkeypatch):
    calls = {"n": 0}

    class DummyResp:
        def __init__(self, status_code):
            self.status_code = status_code

    def failing_get(url, **kwargs):
        calls["n"] += 1
        if calls["n"] < 2:
            return DummyResp(HTTP_RATE_LIMITED)
        return DummyResp(200)

    monkeypatch.setattr("core.http_utils.resilient_get", failing_get)
    from core import http_utils as http_mod
    importlib.reload(http_mod)
    r = http_mod.retrying_get("https://example.com/y")
    assert isinstance(r, DummyResp)
    assert calls["n"] == 2
