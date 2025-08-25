import requests

from ultimate_discord_intelligence_bot.tools.discord_private_alert_tool import (
    DiscordPrivateAlertTool,
)


def test_discord_alert_posts(monkeypatch):
    called = {}

    def fake_post(url, json):
        called["url"] = url
        called["json"] = json

        class Resp:
            status_code = 204
            text = ""

        return Resp()

    monkeypatch.setattr(requests, "post", fake_post)
    tool = DiscordPrivateAlertTool("https://discord.com/api/webhooks/test")
    result = tool._run("hello")
    assert result["status"] == "success"
    assert called["json"]["content"] == "hello"

