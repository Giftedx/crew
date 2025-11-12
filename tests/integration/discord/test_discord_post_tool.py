from unittest.mock import MagicMock

import pytest
import requests

from ultimate_discord_intelligence_bot.tools import DiscordPostTool


def test_embed_post(monkeypatch):
    captured = {}

    def fake_post(url, json=None, headers=None, files=None):
        captured["json"] = json
        response = MagicMock()
        response.status_code = 204
        return response

    monkeypatch.setattr(requests, "post", fake_post)

    tool = DiscordPostTool("https://example.com/webhook")
    data = {
        "title": "Video",
        "uploader": "Author",
        "duration": "10",
        "file_size": str(200 * 1024 * 1024),  # >100MB triggers embed posting
        "platform": "YouTube",
    }
    result = tool.run(data, {})
    assert result["status"] == "success"
    assert captured["json"]["embeds"][0]["title"] == "Video"


def test_file_upload(monkeypatch, tmp_path):
    payload = {}

    def fake_post(url, files=None, json=None, headers=None):
        payload["files"] = files
        response = MagicMock()
        response.status_code = 204
        return response

    monkeypatch.setattr(requests, "post", fake_post)

    file_path = tmp_path / "video.mp4"
    file_path.write_bytes(b"test")

    tool = DiscordPostTool("https://example.com/webhook")
    data = {
        "title": "Video",
        "uploader": "Author",
        "duration": "10",
        "file_size": str(50 * 1024 * 1024),  # <100MB triggers upload
        "local_path": str(file_path),
        "platform": "YouTube",
    }
    result = tool.run(data, {})
    assert result["status"] == "success"
    # ensure file handle closed after request
    assert payload["files"]["file"][1].closed


def test_reject_private_ip():
    with pytest.raises(ValueError):
        DiscordPostTool("https://192.168.1.10/webhook")
