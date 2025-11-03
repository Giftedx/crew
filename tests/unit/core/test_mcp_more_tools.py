import json
from pathlib import Path

import pytest


pytest.importorskip("fastmcp", reason="FastMCP optional extra not installed")


def test_obs_recent_degradations_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    from mcp_server.obs_server import recent_degradations

    class _E:
        def __init__(self):
            self.ts_epoch = 1.0
            self.component = "ingest"
            self.event_type = "fallback"
            self.severity = "warn"
            self.detail = "demo"
            self.added_latency_ms = 5.5

    class _Rep:
        def snapshot(self):
            return [_E(), _E()]

    import core.degradation_reporter as dr

    monkeypatch.setattr(dr, "get_degradation_reporter", lambda: _Rep())
    out = recent_degradations(2)
    assert "events" in out and isinstance(out["events"], list)
    assert len(out["events"]) == 2
    assert {"ts", "component", "event", "severity"}.issubset(out["events"][0].keys())


def test_http_json_get_parses(monkeypatch: pytest.MonkeyPatch) -> None:
    from mcp_server.http_server import http_json_get

    monkeypatch.setenv("MCP_HTTP_ALLOWLIST", "api.github.com")

    class _Resp:
        def __init__(self, text: str, status_code: int = 200) -> None:
            self.text = text
            self.status_code = status_code

    def _fake_cached_get(url: str, **kwargs):
        assert url == "https://api.github.com/path"
        return _Resp(json.dumps({"ok": True, "items": [1, 2, 3]}))

    import platform.http.http_utils as http_utils

    monkeypatch.setattr(http_utils, "cached_get", _fake_cached_get)
    out = http_json_get("https://api.github.com/path", use_cache=True)
    assert out.get("status") == 200
    assert out.get("data", {}).get("ok") is True


def test_ingest_summarize_subtitles(monkeypatch: pytest.MonkeyPatch) -> None:
    from mcp_server.ingest_server import summarize_subtitles

    def _fake_meta(_url: str):
        return {"subtitles": {"en": [{"url": "https://example/subs.vtt"}], "es": []}}

    import ultimate_discord_intelligence_bot.tools.yt_dlp_download_tool as ydlp

    monkeypatch.setattr(ydlp, "youtube_fetch_metadata", _fake_meta)
    out = summarize_subtitles("https://www.youtube.com/watch?v=abc")
    assert "language" in out
    assert "info" in out and isinstance(out["info"], dict)


def test_kg_policy_keys_reads_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from mcp_server.kg_server import policy_keys

    p = Path("config")
    p.mkdir(exist_ok=True)
    (p / "policy.yaml").write_text("a: 1\nb: 2\n", encoding="utf-8")
    out = policy_keys()
    assert isinstance(out, dict)
    assert set(out.get("keys", [])) >= {"a", "b"}
