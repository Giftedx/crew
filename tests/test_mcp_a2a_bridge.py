import pytest

# Skip if MCP extra is not installed
pytest.importorskip("fastmcp", reason="FastMCP optional extra not installed")


def test_a2a_call_success_text_analyze():
    from mcp_server.a2a_bridge_server import a2a_call

    out = a2a_call("tools.text_analyze", {"text": "hello world"})
    assert isinstance(out, dict)
    assert out.get("status") in ("ok", "success")
    data = out.get("data") or {}
    assert isinstance(data, dict)
    # Expect at least preview field in the StepResult payload
    assert "preview" in (data if "preview" in data else data.get("data", {}))


def test_a2a_call_forbidden_method():
    from mcp_server.a2a_bridge_server import a2a_call

    out = a2a_call("system.shutdown", {})
    assert out.get("status") == "error"
    assert out.get("error") == "forbidden_method"
