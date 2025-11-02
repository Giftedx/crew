import asyncio
import importlib
import logging
import os
from unittest.mock import MagicMock

import pytest

from ultimate_discord_intelligence_bot.cache import TranscriptCache
from ultimate_discord_intelligence_bot.core.secure_config import reload_config
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
        "local_path": "/tmp/video.mp4",
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
        transcript_cache=TranscriptCache(enabled=False),
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


def test_transcription_cache_hit(tmp_path):
    def _download_response():
        return {
            "status": "success",
            "platform": "Example",
            "video_id": "video-1",
            "title": "t",
            "uploader": "u",
            "duration": "1",
            "file_size": "1000",
            "local_path": "/tmp/video.mp4",
        }

    downloader = MagicMock()
    downloader.run.side_effect = lambda *args, **kwargs: _download_response()

    drive = MagicMock()
    drive.run.return_value = {"status": "success", "links": {"preview_link": "x"}}

    transcriber = MagicMock()
    transcriber.run.return_value = {
        "status": "success",
        "transcript": "hello",
        "segments": [{"start": 0.0, "end": 1.0, "text": "hello"}],
    }

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

    cache = TranscriptCache(root=tmp_path, enabled=True)

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
        transcript_cache=cache,
        pipeline_rate_limit=1000.0,
        tool_rate_limit=1000.0,
    )

    first = asyncio.run(pipeline.process_video("http://example.com/video"))
    assert first["transcription"]["cache_hit"] is False
    transcriber.run.assert_called_once()

    transcriber.run.reset_mock()

    second = asyncio.run(pipeline.process_video("http://example.com/video"))
    transcriber.run.assert_not_called()
    assert second["transcription"]["cache_hit"] is True
    assert second["transcription"]["transcript"] == "hello"


def test_download_failure(monkeypatch):
    downloader = MagicMock()
    downloader.run.return_value = {
        "status": "error",
        "error": "boom",
        "platform": "Example",
    }

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
        transcript_cache=TranscriptCache(enabled=False),
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
        "local_path": "/tmp/video.mp4",
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
        transcript_cache=TranscriptCache(enabled=False),
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
        "local_path": "/tmp/video.mp4",
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
        transcript_cache=TranscriptCache(enabled=False),
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
        transcript_cache=TranscriptCache(enabled=False),
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
        (
            "https://www.reddit.com/r/videos/comments/1/demo/",
            RedditDownloadTool,
            "Reddit",
        ),
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
            "local_path": "/tmp/video.mp4",
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
        transcript_cache=TranscriptCache(enabled=False),
    )

    result = asyncio.run(pipeline.process_video(url, quality="720p"))

    assert result["status"] == "success"
    assert result["download"]["platform"] == platform
    assert result["download"]["command"].startswith("yt-dlp")
    assert result["download"].get("requested_quality") == "720p"


def test_transcript_memory_toggle_via_secure_config(monkeypatch):
    downloader = MagicMock()
    downloader.run.return_value = {
        "status": "success",
        "platform": "Example",
        "video_id": "vid",
        "title": "title",
        "uploader": "u",
        "duration": "1",
        "file_size": "1000",
        "local_path": "/tmp/video.mp4",
        "command": "yt-dlp stub",
        "requested_quality": "1080p",
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
    perspective.run.return_value = {"status": "success", "summary": "sum"}

    discord = MagicMock()
    discord.run.return_value = {"status": "success"}

    original_flag = os.getenv("DISABLE_TRANSCRIPT_MEMORY")

    try:
        # Disable transcript storage and run pipeline
        monkeypatch.setenv("DISABLE_TRANSCRIPT_MEMORY", "1")
        reload_config()
        memory_disabled = MagicMock()
        memory_disabled.run.return_value = {"status": "success"}
        pipeline_disabled = ContentPipeline(
            webhook_url="http://example.com",
            downloader=downloader,
            transcriber=transcriber,
            analyzer=analyzer,
            drive=drive,
            discord=discord,
            fallacy_detector=fallacy,
            perspective=perspective,
            memory=memory_disabled,
            transcript_cache=TranscriptCache(enabled=False),
        )

        result_disabled = asyncio.run(pipeline_disabled.process_video("http://example.com"))
        assert result_disabled["status"] == "success"
        # Only the analysis memory should run when transcript storage is disabled
        assert memory_disabled.run.call_count == 1

        # Enable transcript storage and run pipeline again
        monkeypatch.setenv("DISABLE_TRANSCRIPT_MEMORY", "0")
        reload_config()
        memory_enabled = MagicMock()
        memory_enabled.run.return_value = {"status": "success"}
        pipeline_enabled = ContentPipeline(
            webhook_url="http://example.com",
            downloader=downloader,
            transcriber=transcriber,
            analyzer=analyzer,
            drive=drive,
            discord=discord,
            fallacy_detector=fallacy,
            perspective=perspective,
            memory=memory_enabled,
            transcript_cache=TranscriptCache(enabled=False),
        )

        result_enabled = asyncio.run(pipeline_enabled.process_video("http://example.com"))
        assert result_enabled["status"] == "success"
        # Transcript and analysis memory both run when the feature is enabled
        assert memory_enabled.run.call_count == 2
    finally:
        if original_flag is None:
            monkeypatch.delenv("DISABLE_TRANSCRIPT_MEMORY", raising=False)
        else:
            monkeypatch.setenv("DISABLE_TRANSCRIPT_MEMORY", original_flag)
        reload_config()


def test_process_video_handles_missing_download(monkeypatch):
    downloader = MagicMock()
    downloader.run.return_value = {
        "status": "error",
        "error": "not found",
        "platform": "Example",
    }

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
        transcript_cache=TranscriptCache(enabled=False),
    )

    result = asyncio.run(pipeline.process_video("http://example.com"))

    assert result["status"] == "error"
    assert result["step"] == "download"
    assert "not found" in result["error"]
    transcriber.run.assert_not_called()
    analyzer.run.assert_not_called()
    drive.run.assert_not_called()
    discord.run.assert_not_called()
    fallacy.run.assert_not_called()
    perspective.run.assert_not_called()
    memory.run.assert_not_called()
