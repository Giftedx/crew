from __future__ import annotations

import json
from typing import Any

import pytest

from client.a2a_client import A2AClient, A2AClientConfig, JsonRpcError


class _Resp:
    def __init__(self, payload: Any, status: int = 200):
        self._payload = payload
        self.status_code = status
        self.text = json.dumps(payload)
        self.headers = {}

    def json(self) -> Any:
        return self._payload


def test_single_success(monkeypatch):
    calls = {}

    def fake_post(url, **kwargs):
        calls["url"] = url
        body = kwargs.get("json_payload")
        assert isinstance(body, dict)
        assert body.get("method") == "tools.text_analyze"
        return _Resp({"jsonrpc": "2.0", "id": body.get("id"), "result": {"status": "success", "data": {"ok": True}}})

    monkeypatch.setattr("core.http_utils.resilient_post", fake_post)

    c = A2AClient(A2AClientConfig(base_url="http://host"))
    out = c.call("tools.text_analyze", {"text": "hello"}, id_value=42)
    assert out["status"] == "success"
    assert out["data"]["ok"] is True


def test_single_error(monkeypatch):
    def fake_post(url, **kwargs):
        body = kwargs.get("json_payload")
        return _Resp({"jsonrpc": "2.0", "id": body.get("id"), "error": {"code": -32602, "message": "Invalid params"}})

    monkeypatch.setattr("core.http_utils.resilient_post", fake_post)

    c = A2AClient(A2AClientConfig(base_url="http://host"))
    with pytest.raises(JsonRpcError) as err:
        c.call("tools.text_analyze", {"oops": True}, id_value=1)
    assert err.value.code == -32602


def test_batch_success(monkeypatch):
    def fake_post(url, **kwargs):
        body = kwargs.get("json_payload")
        assert isinstance(body, list)
        return _Resp(
            [
                {"jsonrpc": "2.0", "id": body[0].get("id"), "result": {"status": "success", "data": {"a": 1}}},
                {"jsonrpc": "2.0", "id": body[1].get("id"), "result": {"status": "success", "data": {"b": 2}}},
            ]
        )

    monkeypatch.setattr("core.http_utils.resilient_post", fake_post)

    c = A2AClient(A2AClientConfig(base_url="http://host"))
    out = c.call_batch(
        [
            ("tools.text_analyze", {"text": "x"}, 1),
            ("agent.execute", {"skill": "tools.lc_summarize", "args": {"text": "t"}}, 2),
        ]
    )
    assert isinstance(out, list) and len(out) == 2
    assert out[0]["status"] == "success"
    assert out[1]["status"] == "success"


def test_batch_error_item(monkeypatch):
    def fake_post(url, **kwargs):
        body = kwargs.get("json_payload")
        return _Resp(
            [
                {"jsonrpc": "2.0", "id": body[0].get("id"), "result": {"status": "success", "data": {}}},
                {"jsonrpc": "2.0", "id": body[1].get("id"), "error": {"code": -32601, "message": "Method not found"}},
            ]
        )

    monkeypatch.setattr("core.http_utils.resilient_post", fake_post)

    c = A2AClient(A2AClientConfig(base_url="http://host"))
    with pytest.raises(JsonRpcError) as err:
        c.call_batch(
            [
                ("tools.text_analyze", {"text": "x"}, 1),
                ("unknown.method", {}, 2),
            ]
        )
    assert err.value.code == -32601


def test_tenancy_headers_propagated(monkeypatch):
    seen = {"get": None, "post": None}

    def fake_get(url, **kwargs):
        seen["get"] = (url, kwargs.get("headers"))
        return _Resp({"skills": []})

    def fake_post(url, **kwargs):
        seen["post"] = (url, kwargs.get("headers"))
        body = kwargs.get("json_payload")
        return _Resp({"jsonrpc": "2.0", "id": body.get("id"), "result": {"status": "success", "data": {}}})

    monkeypatch.setattr("core.http_utils.resilient_get", fake_get)
    monkeypatch.setattr("core.http_utils.resilient_post", fake_post)

    c = A2AClient(A2AClientConfig(base_url="http://host", tenant_id="t1", workspace_id="w1"))
    c.get_skills()
    c.call("tools.text_analyze", {"text": "x"}, id_value=1)

    assert seen["get"][1].get("X-Tenant-Id") == "t1"
    assert seen["get"][1].get("X-Workspace-Id") == "w1"
    assert seen["post"][1].get("X-Tenant-Id") == "t1"
    assert seen["post"][1].get("X-Workspace-Id") == "w1"


def test_discovery_agent_card_and_skills(monkeypatch):
    # Patch GETs to return static payloads
    def fake_get(url, **kwargs):
        if url.endswith("/agent-card"):
            return _Resp({"name": "Adapter", "skills": []})
        if url.endswith("/skills"):
            return _Resp({"skills": [{"name": "tools.text_analyze"}]})
        return _Resp({}, status=404)

    monkeypatch.setattr("core.http_utils.resilient_get", fake_get)

    c = A2AClient(A2AClientConfig(base_url="http://host"))
    card = c.get_agent_card()
    skills = c.get_skills()
    assert card.get("name")
    assert any(s.get("name") == "tools.text_analyze" for s in skills.get("skills", []))
