import subprocess

import pytest

from ultimate_discord_intelligence_bot.tools.yt_dlp_download_tool import (
    TwitchDownloadTool,
    KickDownloadTool,
    TwitterDownloadTool,
    InstagramDownloadTool,
    TikTokDownloadTool,
)


@pytest.mark.parametrize(
    "tool_cls",
    [
        TwitchDownloadTool,
        KickDownloadTool,
        TwitterDownloadTool,
        InstagramDownloadTool,
        TikTokDownloadTool,
    ],
)
def test_downloader_reports_platform(monkeypatch, tool_cls):
    def fake_run(cmd, capture_output, text, timeout, env):
        class Result:
            returncode = 0
            stdout = "id|title|uploader|10|100|/tmp/uploader/title [id].mp4\n"
            stderr = ""

        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)
    tool = tool_cls()
    result = tool._run("http://example.com")
    assert result["platform"] == tool.platform
    assert result["status"] == "success"
    assert result["local_path"].endswith("title [id].mp4")


def test_downloader_handles_malformed_output(monkeypatch):
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

