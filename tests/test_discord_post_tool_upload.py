from __future__ import annotations

import os
import tempfile

from ultimate_discord_intelligence_bot.tools.discord_post_tool import DiscordPostTool


class FakeResp:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = ""

    def json(self):  # noqa: D401 - test stub
        return self._payload


def test_discord_file_upload_uses_payload_json(monkeypatch):
    captured: dict = {}

    def fake_post(url, files=None, timeout_seconds=None, **_):
        captured["url"] = url
        captured["files"] = files
        return FakeResp(204)

    import ultimate_discord_intelligence_bot.tools.discord_post_tool as mod

    monkeypatch.setattr(mod, "resilient_post", fake_post)

    tool = DiscordPostTool("https://discord.com/api/webhooks/123/abc")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(b"x" * 1024)  # small file
        path = tmp.name
    try:
        content = {"title": "T", "uploader": "U", "platform": "P", "local_path": path, "file_size": os.path.getsize(path)}
        res = tool.run(content, {})
        assert res["status"] == "success"
        files = captured["files"]
        assert "file" in files and "payload_json" in files
        assert isinstance(files["payload_json"][1], str)  # JSON string
    finally:
        os.unlink(path)

