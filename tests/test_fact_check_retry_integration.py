import os
from unittest.mock import patch

from core.http_utils import HTTP_RATE_LIMITED, retrying_get


class DummyResp:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data
        self.text = ""

    def json(self):
        return self._json

    def raise_for_status(self):  # mimic requests.Response
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


@patch.dict(os.environ, {"ENABLE_ANALYSIS_HTTP_RETRY": "1"})
def test_retrying_get_transient_status(monkeypatch):
    calls = {"n": 0}

    def fake_resilient(url, params=None, headers=None, timeout_seconds=10, stream=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return DummyResp(HTTP_RATE_LIMITED, {})
        return DummyResp(200, {})

    monkeypatch.setattr("core.http_utils.resilient_get", fake_resilient)
    resp = retrying_get("https://example.com/test")
    assert resp.status_code == 200
    assert calls["n"] == 2  # one retry
