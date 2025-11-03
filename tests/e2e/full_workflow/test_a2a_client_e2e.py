from __future__ import annotations

import json

import pytest

from client.a2a_client import A2AClient, A2AClientConfig, HttpError
from fastapi.testclient import TestClient
from server.app import create_app


@pytest.fixture()
def live_client(monkeypatch):
    monkeypatch.setenv("ENABLE_A2A_API", "1")
    app = create_app()
    http = TestClient(app)

    def fake_resilient_post(url, **kwargs):
        body = kwargs.get("json_payload")
        headers = kwargs.get("headers") or {}
        path = url.split("//", 1)[-1]
        path = path[path.find("/") :] if "/" in path else url
        r = http.post(path, json=body, headers=headers)

        class _Resp:
            def __init__(self, r):
                self.status_code = r.status_code
                self.text = json.dumps(r.json()) if r.json() is not None else ""
                self._json = r.json()
                self.headers = {}

            def json(self):
                return self._json

        return _Resp(r)

    def fake_resilient_get(url, **kwargs):
        headers = kwargs.get("headers") or {}
        path = url.split("//", 1)[-1]
        path = path[path.find("/") :] if "/" in path else url
        r = http.get(path, headers=headers)

        class _Resp:
            def __init__(self, r):
                self.status_code = r.status_code
                self.text = json.dumps(r.json()) if r.json() is not None else ""
                self._json = r.json()
                self.headers = {}

            def json(self):
                return self._json

        return _Resp(r)

    monkeypatch.setattr("core.http_utils.resilient_post", fake_resilient_post)
    monkeypatch.setattr("core.http_utils.resilient_get", fake_resilient_get)
    yield A2AClient(A2AClientConfig(base_url="http://local"))


def test_e2e_agent_card_and_call(live_client):
    card = live_client.get_agent_card()
    assert card.get("protocol") == "A2A-JSONRPC"
    result = live_client.call("agent.execute", {"skill": "tools.text_analyze", "args": {"text": "hello"}}, id_value=1)
    assert isinstance(result, dict)
    assert "status" in result


def test_e2e_batch_with_api_key(monkeypatch):
    monkeypatch.setenv("ENABLE_A2A_API", "1")
    monkeypatch.setenv("ENABLE_A2A_API_KEY", "1")
    monkeypatch.setenv("A2A_API_KEY", "k1")
    app = create_app()
    http = TestClient(app)

    def fake_resilient_post(url, **kwargs):
        body = kwargs.get("json_payload")
        headers = kwargs.get("headers") or {}
        path = url.split("//", 1)[-1]
        path = path[path.find("/") :] if "/" in path else url
        r = http.post(path, json=body, headers=headers)

        class _Resp:
            def __init__(self, r):
                self.status_code = r.status_code
                self.text = json.dumps(r.json()) if r.json() is not None else ""
                self._json = r.json()
                self.headers = {}

            def json(self):
                return self._json

        return _Resp(r)

    def fake_resilient_get(url, **kwargs):
        headers = kwargs.get("headers") or {}
        path = url.split("//", 1)[-1]
        path = path[path.find("/") :] if "/" in path else url
        r = http.get(path, headers=headers)

        class _Resp:
            def __init__(self, r):
                self.status_code = r.status_code
                self.text = json.dumps(r.json()) if r.json() is not None else ""
                self._json = r.json()
                self.headers = {}

            def json(self):
                return self._json

        return _Resp(r)

    monkeypatch.setattr("core.http_utils.resilient_post", fake_resilient_post)
    monkeypatch.setattr("core.http_utils.resilient_get", fake_resilient_get)
    c_bad = A2AClient(A2AClientConfig(base_url="http://local"))
    with pytest.raises(HttpError) as err:
        c_bad.call("tools.text_analyze", {"text": "nope"}, id_value=99)
    assert err.value.status_code == 401
    c = A2AClient(A2AClientConfig(base_url="http://local", api_key="k1"))
    out = c.call_batch(
        [
            ("tools.text_analyze", {"text": "x"}, 1),
            ("agent.execute", {"skill": "tools.text_analyze", "args": {"text": "y"}}, 2),
        ]
    )
    assert isinstance(out, list) and len(out) == 2
    assert all(isinstance(item, dict) and "status" in item for item in out)
