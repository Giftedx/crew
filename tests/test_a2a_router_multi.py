# isort: skip_file
from fastapi.testclient import TestClient
import pytest

from ultimate_discord_intelligence_bot.server.app import create_app


@pytest.fixture()
def client_multi(monkeypatch):
    # Enable A2A and the multi-agent research skill
    monkeypatch.setenv("ENABLE_A2A_API", "true")
    monkeypatch.setenv("ENABLE_A2A_SKILL_RESEARCH_AND_BRIEF_MULTI", "true")
    # Keep underlying multi-agent orchestration optional; offline fallback must still work
    app = create_app()
    return TestClient(app)


def test_skill_list_includes_multi(client_multi):
    r = client_multi.get("/a2a/skills")
    assert r.status_code == 200
    data = r.json()
    names = [s["name"] for s in data.get("skills", [])]
    assert "tools.research_and_brief_multi" in names


def test_agent_card_includes_multi(client_multi):
    r = client_multi.get("/a2a/agent-card")
    assert r.status_code == 200
    data = r.json()
    skills = data.get("skills", [])
    names = [s.get("name") for s in skills]
    assert "tools.research_and_brief_multi" in names


def test_jsonrpc_call_multi_skill(client_multi):
    payload = {
        "jsonrpc": "2.0",
        "id": "m1",
        "method": "agent.execute",
        "params": {
            "skill": "tools.research_and_brief_multi",
            "args": {
                "query": "test multi agent research",
                "sources_text": [
                    "This is a short sample input used to validate the synthesis path.",
                    "Another source provides additional context and content for the brief.",
                ],
                "max_items": 3,
                "max_time": 0.5,
            },
        },
    }
    r = client_multi.post("/a2a/jsonrpc", json=payload)
    assert r.status_code == 200
    data = r.json()
    # We expect a result with data containing outline/key_findings/meta even if multi-agent path falls back
    assert "result" in data
    result = data["result"]
    assert "data" in result
    d = result["data"]
    assert "outline" in d and "key_findings" in d and "meta" in d
    assert isinstance(d["meta"], dict)
    assert "multi_agent" in d["meta"]
