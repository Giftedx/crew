import json
import subprocess

from ultimate_discord_intelligence_bot.tools.youtube_download_tool import (
    YouTubeDownloadTool,
)


def test_youtube_download_parses_filepath(monkeypatch):
    def fake_run(cmd, capture_output, text, timeout, env):
        class Result:
            returncode = 0
            stdout = json.dumps(
                {
                    "id": "id",
                    "title": "title",
                    "uploader": "uploader",
                    "duration": 10,
                    "filesize_approx": 100,
                    "filepath": "/tmp/uploader/title [id].mp4",
                }
            ) + "\n"
            stderr = ""

        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)
    tool = YouTubeDownloadTool()
    result = tool._run("http://example.com")
    assert result["local_path"].endswith("title [id].mp4")
    assert result["status"] == "success"
