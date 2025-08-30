import asyncio
import importlib
import logging
from unittest.mock import MagicMock

import pytest

from ultimate_discord_intelligence_bot.pipeline import ContentPipeline
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


def test_process_video(monkeypatch):
    downloader = MagicMock()
    downloader.run.return_value = {
        "status": "success",
        "platform": "Example",
        "video_id": "1",
        "title": "t",
        "uploader": "u",
        "duration": "1",
        "file_size": "1000",
    "local_path": "/tmp/video.mp4",  # noqa: S108 - fixture stub path acceptable in test
    }

    drive = MagicMock()
    drive.run.return_value = {"status": "success", "links": {"preview_link": "x"}}

    transcriber = MagicMock()
    transcriber.run.return_value = {"status": "success", "transcript": "hello"}

    analyzer = MagicMock()
    analyzer.run.return_value = {"status": "success", "sentiment": {}, "keywords": []}

    fallacy = MagicMock()
    fallacy.run.return_value = {"status": "success", "fallacies": []}

    perspective = MagicMock()
    perspective.run.return_value = {"status": "success", "summary": "s"}

    memory = MagicMock()
    memory.run.return_value = {"status": "success"}

    discord = MagicMock()
    discord.run.return_value = {"status": "success"}

    pipeline = ContentPipeline(
        webhook_url="http://example.com",
        downloader=downloader,
        transcriber=transcriber,
        analyzer=analyzer,
        drive=drive,
        discord=discord,
        fallacy_detector=fallacy,
        perspective=perspective,
        memory=memory,
    )
    result = asyncio.run(pipeline.process_video("http://example.com"))

    assert result["status"] == "success"
    downloader.run.assert_called_once()
    drive.run.assert_called_once()
    transcriber.run.assert_called_once()
    analyzer.run.assert_called_once()
    fallacy.run.assert_called_once()
    perspective.run.assert_called_once()
    assert memory.run.call_count == 2
    discord.run.assert_called_once()


def test_download_failure(monkeypatch):
    downloader = MagicMock()
    downloader.run.return_value = {"status": "error", "error": "boom", "platform": "Example"}

    transcriber = MagicMock()
    analyzer = MagicMock()
    drive = MagicMock()
    discord = MagicMock()
    fallacy = MagicMock()
    perspective = MagicMock()
    memory = MagicMock()
    memory.run.return_value = {"status": "success"}

    pipeline = ContentPipeline(
        webhook_url="http://example.com",
        downloader=downloader,
        transcriber=transcriber,
        analyzer=analyzer,
        drive=drive,
        discord=discord,
        fallacy_detector=fallacy,
        perspective=perspective,
        memory=memory,
    )

    result = asyncio.run(pipeline.process_video("http://example.com"))

    assert result["status"] == "error"
    assert result["step"] == "download"
    transcriber.run.assert_not_called()
    analyzer.run.assert_not_called()
    drive.run.assert_not_called()
    discord.run.assert_not_called()
    fallacy.run.assert_not_called()
    perspective.run.assert_not_called()
    memory.run.assert_not_called()


def test_pipeline_does_not_configure_root_logger(monkeypatch):
    """Importing the pipeline should not modify the root logger level."""
    root = logging.getLogger()
    root.setLevel(logging.WARNING)
    importlib.reload(importlib.import_module("ultimate_discord_intelligence_bot.pipeline"))
    assert logging.getLogger().level == logging.WARNING


def test_drive_upload_retry(monkeypatch):
    downloader = MagicMock()
    downloader.run.return_value = {
        "status": "success",
        "platform": "Example",
        "video_id": "1",
        "title": "t",
        "uploader": "u",
        "duration": "1",
        "file_size": "1000",
    "local_path": "/tmp/video.mp4",  # noqa: S108 - fixture stub path acceptable in test
    }

    drive = MagicMock()
    drive.run.side_effect = [
        {"status": "error", "error": "boom"},
        {"status": "success", "links": {"preview_link": "x"}},
    ]

    transcriber = MagicMock()
    transcriber.run.return_value = {"status": "success", "transcript": "hello"}

    analyzer = MagicMock()
    analyzer.run.return_value = {"status": "success", "sentiment": {}, "keywords": []}

    fallacy = MagicMock()
    fallacy.run.return_value = {"status": "success", "fallacies": []}

    perspective = MagicMock()
    perspective.run.return_value = {"status": "success", "summary": "s"}

    discord = MagicMock()
    discord.run.return_value = {"status": "success"}

    memory = MagicMock()
    memory.run.return_value = {"status": "success"}

    pipeline = ContentPipeline(
        webhook_url="http://example.com",
        downloader=downloader,
        transcriber=transcriber,
        analyzer=analyzer,
        drive=drive,
        discord=discord,
        fallacy_detector=fallacy,
        perspective=perspective,
        memory=memory,
    )

    result = asyncio.run(pipeline.process_video("http://example.com"))

    assert result["status"] == "success"
    assert drive.run.call_count == 2
    assert memory.run.call_count == 2


def test_exception_in_analysis(monkeypatch):
    """Pipeline should surface step name when a tool raises."""
    downloader = MagicMock()
    downloader.run.return_value = {
        "status": "success",
        "platform": "Example",
        "video_id": "1",
        "title": "t",
        "uploader": "u",
        "duration": "1",
        "file_size": "1000",
    "local_path": "/tmp/video.mp4",  # noqa: S108 - fixture stub path acceptable in test
    }

    drive = MagicMock()
    drive.run.return_value = {"status": "success", "links": {}}

    transcriber = MagicMock()
    transcriber.run.return_value = {"status": "success", "transcript": "hello"}

    analyzer = MagicMock()
    analyzer.run.side_effect = ValueError("bad analysis")
    fallacy = MagicMock()
    perspective = MagicMock()
    memory = MagicMock()

    discord = MagicMock()

    pipeline = ContentPipeline(
        webhook_url="http://example.com",
        downloader=downloader,
        transcriber=transcriber,
        analyzer=analyzer,
        drive=drive,
        discord=discord,
        fallacy_detector=fallacy,
        perspective=perspective,
        memory=memory,
    )

    result = asyncio.run(pipeline.process_video("http://example.com"))

    assert result["status"] == "error"
    assert result["step"] == "analysis"
    discord.run.assert_not_called()
    fallacy.run.assert_not_called()
    perspective.run.assert_not_called()
    assert memory.run.call_count >= 1


def test_unsupported_platform(monkeypatch):
    """Pipeline should error on URLs without a matching downloader."""
    pipeline = ContentPipeline(
        webhook_url="http://example.com",
        drive=MagicMock(),
        transcriber=MagicMock(),
        analyzer=MagicMock(),
        discord=MagicMock(),
        fallacy_detector=MagicMock(),
        perspective=MagicMock(),
        memory=MagicMock(),
    )
    result = asyncio.run(pipeline.process_video("http://unknown.com"))
    assert result["status"] == "error"
    assert result["step"] == "download"


@pytest.mark.parametrize(
    "url, tool_cls, platform",
    [
        ("https://www.youtube.com/watch?v=1", YouTubeDownloadTool, "YouTube"),
        ("https://www.twitch.tv/videos/1", TwitchDownloadTool, "Twitch"),
        ("https://kick.com/video/1", KickDownloadTool, "Kick"),
        ("https://twitter.com/video/1", TwitterDownloadTool, "Twitter"),
        ("https://www.instagram.com/reel/1", InstagramDownloadTool, "Instagram"),
        ("https://www.tiktok.com/@user/video/1", TikTokDownloadTool, "TikTok"),
        ("https://vm.tiktok.com/ZM1/", TikTokDownloadTool, "TikTok"),
        ("https://vt.tiktok.com/ZM2/", TikTokDownloadTool, "TikTok"),
        ("https://www.reddit.com/r/videos/comments/1/demo/", RedditDownloadTool, "Reddit"),
        (
            "https://cdn.discordapp.com/attachments/1/2/video.mp4",
            DiscordDownloadTool,
            "Discord",
        ),
    ],
)
def test_pipeline_selects_correct_downloader(url, tool_cls, platform, monkeypatch):
    """ContentPipeline should dispatch to the appropriate downloader."""

    def fake_run(self, video_url, quality="1080p"):
        return {
            "status": "success",
            "platform": platform,
            "video_id": "1",
            "title": "t",
            "uploader": "u",
            "duration": "1",
            "file_size": "1000",
            "local_path": "/tmp/video.mp4",  # noqa: S108 - fixture stub path acceptable in test
            "command": "yt-dlp stub",
            "requested_quality": quality,
        }

    monkeypatch.setattr(tool_cls, "run", fake_run)

    drive = MagicMock()
    drive.run.return_value = {"status": "success", "links": {"preview_link": "x"}}
    transcriber = MagicMock()
    transcriber.run.return_value = {"status": "success", "transcript": "hello"}
    analyzer = MagicMock()
    analyzer.run.return_value = {"status": "success", "sentiment": {}, "keywords": []}
    fallacy = MagicMock()
    fallacy.run.return_value = {"status": "success", "fallacies": []}
    perspective = MagicMock()
    perspective.run.return_value = {"status": "success", "summary": "s"}
    memory = MagicMock()
    memory.run.return_value = {"status": "success"}
    discord = MagicMock()
    discord.run.return_value = {"status": "success"}

    pipeline = ContentPipeline(
        webhook_url="http://example.com",
        transcriber=transcriber,
        analyzer=analyzer,
        drive=drive,
        discord=discord,
        fallacy_detector=fallacy,
        perspective=perspective,
        memory=memory,
    )

    result = asyncio.run(pipeline.process_video(url, quality="720p"))

    assert result["status"] == "success"
    assert result["download"]["platform"] == platform
    assert result["download"]["command"].startswith("yt-dlp")
    assert result["download"].get("requested_quality") == "720p"
