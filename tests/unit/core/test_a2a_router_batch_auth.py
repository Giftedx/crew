# isort: skip_file
from fastapi.testclient import TestClient
import pytest

from ultimate_discord_intelligence_bot.server.app import create_app


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("ENABLE_A2A_API", "true")
    # Enable API key requirement and set acceptable key
    monkeypatch.setenv("ENABLE_A2A_API_KEY", "true")
    monkeypatch.setenv("A2A_API_KEY", "secret1,secret2")
    app = create_app()
    return TestClient(app)


def test_jsonrpc_batch_mixed_success(client):
    headers = {"X-API-Key": "secret2"}
    payload = [
        {"jsonrpc": "2.0", "id": 1, "method": "no.such"},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "agent.execute",
            "params": {"skill": "tools.lc_summarize", "args": {"text": "hello world"}},
        },
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "agent.execute",
            "params": {
                "skill": "tools.rag_query",
                "args": {"query": "x", "documents": ["a", "b"]},
            },
        },
    ]
    r = client.post("/a2a/jsonrpc", json=payload, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    # Expect three responses with ids 1,2,3
    ids = {item.get("id") for item in data}
    assert ids == {1, 2, 3}
    # One error for unknown method
    err_items = [d for d in data if "error" in d]
    assert len(err_items) == 1 and err_items[0]["error"]["code"] == -32601


def test_jsonrpc_batch_empty_invalid(client):
    headers = {"X-API-Key": "secret1"}
    r = client.post("/a2a/jsonrpc", json=[], headers=headers)
    assert r.status_code == 200
    data = r.json()
    # For empty batch, we return a single error object
    assert isinstance(data, dict)
    assert data.get("error", {}).get("code") == -32600


def test_auth_missing_key_rejected(client):
    # No API key header
    r = client.post("/a2a/jsonrpc", json={"jsonrpc": "2.0", "id": 1, "method": "no.such"})
    assert r.status_code == 401


def test_auth_wrong_key_rejected(client):
    headers = {"X-API-Key": "not-valid"}
    r = client.post(
        "/a2a/jsonrpc",
        json={"jsonrpc": "2.0", "id": 1, "method": "no.such"},
        headers=headers,
    )
    assert r.status_code == 401
