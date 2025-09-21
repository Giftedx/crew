import sys
import types

import pytest


@pytest.fixture(autouse=True)
def enable_call_tool(monkeypatch):
    # Ensure the orchestrator would inject the tool if needed
    monkeypatch.setenv("ENABLE_MCP_CALL_TOOL", "1")
    yield


def test_mcp_call_tool_unknown_namespace():
    from ultimate_discord_intelligence_bot.tools.mcp_call_tool import MCPCallTool

    tool = MCPCallTool()
    res = tool.run("nope", "does_not_exist")
    assert not res.success
    assert "unknown_or_forbidden" in (res.error or "")


def test_mcp_call_tool_known_namespace_unknown_name(monkeypatch):
    # Simulate that the module imports fine but the function is not allowed
    fake_mod = types.SimpleNamespace()
    monkeypatch.setitem(sys.modules, "mcp_server.http_server", fake_mod)

    from ultimate_discord_intelligence_bot.tools.mcp_call_tool import MCPCallTool

    tool = MCPCallTool()
    res = tool.run("http", "not_allowed")
    assert not res.success
    assert "unknown_or_forbidden" in (res.error or "")


def test_mcp_call_tool_http_json_get_signature_error(monkeypatch):
    # Provide a stub for http_json_get that requires a 'url' param
    def http_json_get(*, url: str):  # minimal signature
        return {"url": url, "status": 200}

    fake_mod = types.SimpleNamespace(http_json_get=http_json_get)

    monkeypatch.setitem(sys.modules, "mcp_server.http_server", fake_mod)

    from ultimate_discord_intelligence_bot.tools.mcp_call_tool import MCPCallTool

    tool = MCPCallTool()

    # Missing required param should yield a fail with invalid_params
    res_bad = tool.run("http", "http_json_get", {})
    assert not res_bad.success
    assert "invalid_params" in (res_bad.error or "")

    # Providing the param should succeed and wrap dict under result
    res_ok = tool.run("http", "http_json_get", {"url": "https://example.com/data.json"})
    assert res_ok.success
    assert isinstance(res_ok.data.get("result"), dict)
    assert res_ok.data["result"]["url"] == "https://example.com/data.json"
