import json
import subprocess

import pytest
import requests

from ultimate_discord_intelligence_bot.tools.discord_download_tool import (
    DiscordDownloadTool,
)
from ultimate_discord_intelligence_bot.tools.yt_dlp_download_tool import (
    InstagramDownloadTool,
    KickDownloadTool,
    RedditDownloadTool,
    TikTokDownloadTool,
    TwitchDownloadTool,
    TwitterDownloadTool,
    YouTubeDownloadTool,
)


@pytest.mark.parametrize(
    "tool_cls",
    [
        YouTubeDownloadTool,
        TwitchDownloadTool,
        KickDownloadTool,
        TwitterDownloadTool,
        InstagramDownloadTool,
        TikTokDownloadTool,
        RedditDownloadTool,
    ],
)
def test_downloader_reports_platform(monkeypatch, tool_cls):
    def fake_run(cmd, capture_output, text, timeout, env):
        class Result:
            returncode = 0
            stdout = (
                json.dumps(
                    {
                        "id": "id",
                        "title": "title",
                        "uploader": "uploader",
                        "duration": 10,
                        "filesize_approx": 100,
                        "filepath": "/tmp/uploader/title [id].mp4",  # noqa: S108 - benign test stub path
                    }
                )
                + "\n"
            )
            stderr = ""

        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)
    tool = tool_cls()
    result = tool.run("http://example.com")
    assert result["platform"] == tool.platform
    assert result["status"] == "success"
    assert result["local_path"].endswith("title [id].mp4")
    assert result["command"].startswith("yt-dlp")


def test_downloader_handles_malformed_output_alt(monkeypatch):
    def fake_run(cmd, capture_output, text, timeout, env):
        class Result:
            returncode = 0
            stdout = "unexpected"
            stderr = ""

        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)
    tool = TikTokDownloadTool()
    result = tool.run("http://example.com")
    assert result["status"] == "error"
    assert "Unexpected yt-dlp output" in result["error"]


def test_downloader_reports_subprocess_error(monkeypatch):
    def fake_run(cmd, capture_output, text, timeout, env):
        class Result:
            returncode = 1
            stdout = ""
            stderr = "boom\n"

        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)
    tool = TikTokDownloadTool()
    result = tool.run("http://example.com")
    assert result["status"] == "error"
    assert result["error"] == "boom"
    assert result["command"].startswith("yt-dlp")


def test_downloader_reports_timeout(monkeypatch):
    def fake_run(cmd, capture_output, text, timeout, env):
        raise subprocess.TimeoutExpired(cmd, timeout)

    monkeypatch.setattr(subprocess, "run", fake_run)
    tool = TikTokDownloadTool()
    result = tool.run("http://example.com")
    assert result["status"] == "error"
    assert result["error"] == "Download timeout after 30 minutes"
    assert result["command"].startswith("yt-dlp")


def test_downloader_reports_unhandled_exception(monkeypatch):
    def fake_run(cmd, capture_output, text, timeout, env):
        raise ValueError("boom")

    monkeypatch.setattr(subprocess, "run", fake_run)
    tool = TikTokDownloadTool()
    result = tool.run("http://example.com")
    assert result["status"] == "error"
    assert result["error"] == "boom"
    assert result["command"].startswith("yt-dlp")


def test_downloader_honors_quality(monkeypatch):
    captured: dict = {}

    def fake_run(cmd, capture_output, text, timeout, env):
        captured["cmd"] = cmd

        class Result:
            returncode = 0
            stdout = (
                json.dumps(
                    {
                        "id": "id",
                        "title": "title",
                        "uploader": "uploader",
                        "duration": 10,
                        "filesize_approx": 100,
                        "filepath": "/tmp/uploader/title [id].mp4",  # noqa: S108 - benign test stub path
                    }
                )
                + "\n"
            )
            stderr = ""

        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)
    tool = YouTubeDownloadTool()
    tool.run("http://example.com", quality="480p")
    assert "-f" in captured["cmd"]
    fmt = captured["cmd"][captured["cmd"].index("-f") + 1]
    assert "height<=480" in fmt


def test_discord_downloader_reports_platform(monkeypatch):
    def fake_get(url, stream=True, timeout=30):
        class Response:
            def raise_for_status(self):
                pass

            def iter_content(self, chunk_size):
                yield b"data"

        return Response()

    monkeypatch.setattr(requests, "get", fake_get)
    tool = DiscordDownloadTool()
    result = tool.run("https://cdn.discordapp.com/attachments/1/2/video.mp4")
    assert result["status"] == "success"
    assert result["platform"] == "Discord"
    assert result["local_path"].endswith(".mp4")
    assert result["command"].startswith("requests.get")


def test_discord_downloader_reports_http_error(monkeypatch):
    class Response:
        def raise_for_status(self):
            raise requests.HTTPError("boom")

    def fake_get(url, stream=True, timeout=30):
        return Response()

    monkeypatch.setattr(requests, "get", fake_get)
    tool = DiscordDownloadTool()
    result = tool.run("https://cdn.discordapp.com/attachments/1/2/video.mp4")
    assert result["status"] == "error"
    assert result["error"] == "boom"
    assert result["command"].startswith("requests.get")


def test_downloader_handles_malformed_output_run_private(monkeypatch):
    def fake_run(cmd, capture_output, text, timeout, env):
        class Result:
            returncode = 0
            stdout = "unexpected"
            stderr = ""

        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)
    tool = TikTokDownloadTool()
    result = tool._run("http://example.com")
    assert result["status"] == "error"
    assert "Unexpected yt-dlp output" in result["error"]
