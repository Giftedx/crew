import requests
import pytest

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


def test_discord_alert_includes_metrics(monkeypatch):
    called = {}

    def fake_post(url, json):
        called["json"] = json

        class Resp:
            status_code = 204
            text = ""

        return Resp()

    monkeypatch.setattr(requests, "post", fake_post)
    tool = DiscordPrivateAlertTool("https://discord.com/api/webhooks/test")
    metrics = {"load_avg_1m": 1.2, "disk_free": 100}
    result = tool._run("status", metrics)
    assert result["status"] == "success"
    content = called["json"]["content"]
    assert "load_avg_1m" in content and "disk_free" in content


def test_discord_alert_rejects_non_https():
    with pytest.raises(ValueError):
        DiscordPrivateAlertTool("http://discord.com/api/webhooks/test")


def test_discord_alert_rejects_private_ip():
    with pytest.raises(ValueError):
        DiscordPrivateAlertTool("https://192.168.0.1/api/webhooks/test")


def test_discord_alert_warns_on_threshold(monkeypatch):
    called = {}

    def fake_post(url, json):
        called["json"] = json

        class Resp:
            status_code = 204
            text = ""

        return Resp()

    monkeypatch.setattr(requests, "post", fake_post)
    tool = DiscordPrivateAlertTool("https://discord.com/api/webhooks/test")
    metrics = {"load_avg_1m": 2.0}
    thresholds = {"load_avg_1m": 1.0}
    result = tool._run("status", metrics, thresholds)
    assert result["status"] == "success"
    assert called["json"]["content"].startswith("⚠️")

