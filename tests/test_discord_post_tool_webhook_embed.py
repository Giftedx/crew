from __future__ import annotations

from ultimate_discord_intelligence_bot.tools.discord_post_tool import DiscordPostTool


class FakeResp:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = ""

    def json(self):  # noqa: D401 - test stub
        return self._payload


def test_discord_post_embed_monkeypatched(monkeypatch):
    captured: dict = {}

    def fake_post(url, json_payload=None, headers=None, timeout_seconds=None, **_):
        captured["url"] = url
        captured["json"] = json_payload
        captured["headers"] = headers
        return FakeResp(204)

    # Patch resilient_post
    import ultimate_discord_intelligence_bot.tools.discord_post_tool as mod

    monkeypatch.setattr(mod, "resilient_post", fake_post)

    tool = DiscordPostTool("https://discord.com/api/webhooks/123/abc")
    content = {"title": "T", "uploader": "U", "platform": "P", "file_size": 999999999}
    links = {"preview_link": "https://drive/preview", "direct_link": "https://drive/download", "thumbnail": "https://cdn/thumb"}
    res = tool.run(content, links)
    assert res["status"] == "success"
    assert captured["url"].startswith("https://discord.com/api/webhooks/")
    assert captured["headers"]["Content-Type"] == "application/json"
    embed = captured["json"]["embeds"][0]
    assert embed["thumbnail"]["url"] == links["thumbnail"]
    assert "Watch Online" in embed["fields"][0]["name"]
    assert "Download" in embed["fields"][1]["name"]

