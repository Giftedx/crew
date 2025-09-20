# isort: skip_file
from fastapi.testclient import TestClient
import pytest

from server.app import create_app


@pytest.fixture()
def client(monkeypatch):
    # Ensure A2A router is enabled in the app
    monkeypatch.setenv("ENABLE_A2A_API", "true")
    app = create_app()
    return TestClient(app)


def test_agent_card(client):
    r = client.get("/a2a/agent-card")
    assert r.status_code == 200
    data = r.json()
    assert data.get("endpoints", {}).get("rpc") == "/a2a/jsonrpc"


def test_list_skills(client):
    r = client.get("/a2a/skills")
    assert r.status_code == 200
    data = r.json()
    assert "skills" in data


def test_jsonrpc_unknown_method(client):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "no.such.method", "params": {}}
    r = client.post("/a2a/jsonrpc", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "error" in data and data["error"]["code"] == -32601


def test_jsonrpc_invalid_request(client):
    r = client.post("/a2a/jsonrpc", json={"method": "x"})
    assert r.status_code == 400


def test_jsonrpc_agent_execute_missing_skill(client):
    payload = {"jsonrpc": "2.0", "id": 2, "method": "agent.execute", "params": {}}
    r = client.post("/a2a/jsonrpc", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["error"]["code"] == -32602


def test_jsonrpc_tool_dispatch_param_shape(client):
    # If text_analysis tool is present, this should succeed; otherwise server should still 200 with error
    payload = {
        "jsonrpc": "2.0",
        "id": "abc",
        "method": "agent.execute",
        "params": {"skill": "tools.text_analyze", "args": {"text": "hello"}},
    }
    r = client.post("/a2a/jsonrpc", json=payload)
    assert r.status_code == 200
    data = r.json()
    # Either result present or error returned depending on optional tool availability
    assert "result" in data or "error" in data


def test_jsonrpc_rag_query_happy_path(client):
    payload = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "agent.execute",
        "params": {
            "skill": "tools.rag_query",
            "args": {
                "query": "policy",
                "documents": [
                    "The policy states that all users must rotate keys every 90 days.",
                    "Our help docs explain API usage and retry limits.",
                    "Budget checks apply to all LLM calls.",
                ],
                "top_k": 2,
            },
        },
    }
    r = client.post("/a2a/jsonrpc", json=payload)
    assert r.status_code == 200
    data = r.json()
    # Depending on optional availability, we expect either result or error, but most likely result here
    assert "result" in data
    hits = data["result"]["data"]["hits"]
    assert isinstance(hits, list)
    assert len(hits) <= 2
    if hits:
        # score present and between 0 and 1
        assert 0.0 <= hits[0]["score"] <= 1.0


def test_jsonrpc_rag_query_invalid_docs(client):
    payload = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "agent.execute",
        "params": {
            "skill": "tools.rag_query",
            "args": {"query": "x", "documents": "not-a-list"},
        },
    }
    r = client.post("/a2a/jsonrpc", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "error" in data
