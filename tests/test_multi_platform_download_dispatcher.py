import pytest

from ultimate_discord_intelligence_bot.tools.discord_download_tool import (
    DiscordDownloadTool,
)
from ultimate_discord_intelligence_bot.tools.multi_platform_download_tool import (
    MultiPlatformDownloadTool,
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
    "url,tool_cls",
    [
        ("https://www.youtube.com/watch?v=1", YouTubeDownloadTool),
        ("https://youtu.be/1", YouTubeDownloadTool),
        ("https://www.twitch.tv/videos/1", TwitchDownloadTool),
        ("https://kick.com/video/1", KickDownloadTool),
        ("https://twitter.com/user/status/1", TwitterDownloadTool),
        ("https://x.com/user/status/1", TwitterDownloadTool),
        ("https://www.instagram.com/reel/1", InstagramDownloadTool),
        ("https://www.tiktok.com/@user/video/1", TikTokDownloadTool),
        ("https://vm.tiktok.com/ZM1/", TikTokDownloadTool),
        ("https://vt.tiktok.com/ZM2/", TikTokDownloadTool),
        ("https://www.reddit.com/r/videos/comments/1/demo/", RedditDownloadTool),
        (
            "https://cdn.discordapp.com/attachments/1/2/video.mp4",
            DiscordDownloadTool,
        ),
    ],
)
def test_dispatcher_selects_tool(monkeypatch, url, tool_cls):
    tool = MultiPlatformDownloadTool()
    called = {}

    def fake_run(self, url_arg, quality="1080p"):
        called["tool"] = self.platform
        called["quality"] = quality
        return {
            "status": "success",
            "platform": self.platform,
            "command": "yt-dlp stub",
        }

    monkeypatch.setattr(tool_cls, "run", fake_run)
    result = tool.run(url)
    assert called["tool"] == tool_cls.platform
    assert called["quality"] == "1080p"
    assert result["platform"] == tool_cls.platform
    assert result["command"] == "yt-dlp stub"


def test_dispatcher_forwards_quality(monkeypatch):
    tool = MultiPlatformDownloadTool()
    called = {}

    def fake_run(self, url_arg, quality="1080p"):
        called["tool"] = self.platform
        called["quality"] = quality
        return {
            "status": "success",
            "platform": self.platform,
            "command": "yt-dlp stub",
        }

    monkeypatch.setattr(YouTubeDownloadTool, "run", fake_run)
    url = "https://www.youtube.com/watch?v=1"
    tool.run(url, quality="720p")
    assert called["tool"] == "YouTube"
    assert called["quality"] == "720p"


def test_dispatcher_reports_unsupported_url():
    tool = MultiPlatformDownloadTool()
    result = tool.run("https://example.com/video/1")
    assert result["status"] == "error"
    assert "Unsupported platform" in result["error"]
    assert result["platform"] == "unknown"
