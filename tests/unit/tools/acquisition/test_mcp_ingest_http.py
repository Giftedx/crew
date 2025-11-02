from pathlib import Path

import pytest


# Skip these tests entirely if FastMCP optional extra isn't installed
pytest.importorskip("fastmcp", reason="FastMCP optional extra not installed")


@pytest.fixture
def tmp_text_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.txt"
    p.write_text("first line\nsecond line\n", encoding="utf-8")
    return p


def test_ingest_extract_metadata_allowlist() -> None:
    # example.com is HTTPS but not in the provider allowlist
    from mcp_server.ingest_server import extract_metadata

    out = extract_metadata("https://example.com/video")
    assert isinstance(out, dict)
    # Should error with unsupported provider
    assert "error" in out and out["error"].startswith("unsupported_provider:")


def test_ingest_fetch_transcript_local_text(tmp_text_file: Path) -> None:
    from mcp_server.ingest_server import fetch_transcript_local

    out = fetch_transcript_local(str(tmp_text_file), model="tiny", max_chars=1000)
    assert isinstance(out, dict)
    assert "error" not in out
    assert "text" in out and "first line" in out["text"]
    assert isinstance(out.get("segments"), list)
    assert len(out["segments"]) >= 2


def test_http_get_allowlist_and_truncation(monkeypatch: pytest.MonkeyPatch) -> None:
    from mcp_server.http_server import http_get

    # Allow api.github.com
    monkeypatch.setenv("MCP_HTTP_ALLOWLIST", "api.github.com")

    # Stub cached_get to avoid real network
    class _Resp:
        def __init__(self, text: str, status_code: int = 200) -> None:
            self.text = text
            self.status_code = status_code

    def _fake_cached_get(url: str, **kwargs):
        assert url.startswith("https://api.github.com/")
        return _Resp("HELLOWORLD", 200)

    # Patch the symbol looked up within the function
    monkeypatch.setenv("HTTP_TIMEOUT", "5")  # ensure any timeout int parsing path is valid
    import core.http_utils as http_utils

    monkeypatch.setattr(http_utils, "cached_get", _fake_cached_get)

    out = http_get("https://api.github.com/test", use_cache=True, max_bytes=5)
    assert out["status"] == 200
    assert out["length"] == 10
    assert out["text"] == "HELLO"
