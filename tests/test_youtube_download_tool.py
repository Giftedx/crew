import subprocess
from ultimate_discord_intelligence_bot___complete_social_media_analysis_fact_checking_system.tools.youtube_download_tool import YouTubeDownloadTool


def test_youtube_download_parses_filepath(monkeypatch):
    def fake_run(cmd, capture_output, text, timeout, env):
        class Result:
            returncode = 0
            stdout = "id|title|uploader|10|100|/tmp/uploader/title [id].mp4\n"
            stderr = ""
        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)
    tool = YouTubeDownloadTool()
    result = tool._run("http://example.com")
    assert result["local_path"].endswith("title [id].mp4")
    assert result["status"] == "success"
