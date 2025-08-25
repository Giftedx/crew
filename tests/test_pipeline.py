import asyncio
import importlib
import logging
from unittest.mock import MagicMock

from ultimate_discord_intelligence_bot___complete_social_media_analysis_fact_checking_system.pipeline import (
    ContentPipeline,
)


def test_process_video(monkeypatch):
    downloader = MagicMock()
    downloader.run.return_value = {
        "status": "success",
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

    discord = MagicMock()
    discord.run.return_value = {"status": "success"}

    pipeline = ContentPipeline(
        webhook_url="http://example.com",
        youtube_downloader=downloader,
        transcriber=transcriber,
        analyzer=analyzer,
        drive=drive,
        discord=discord,
    )
    result = asyncio.run(pipeline.process_video("http://example.com"))

    assert result["status"] == "success"
    downloader.run.assert_called_once()
    drive.run.assert_called_once()
    transcriber.run.assert_called_once()
    analyzer.run.assert_called_once()
    discord.run.assert_called_once()


def test_download_failure(monkeypatch):
    downloader = MagicMock()
    downloader.run.return_value = {"status": "error", "error": "boom"}

    transcriber = MagicMock()
    analyzer = MagicMock()
    drive = MagicMock()
    discord = MagicMock()

    pipeline = ContentPipeline(
        webhook_url="http://example.com",
        youtube_downloader=downloader,
        transcriber=transcriber,
        analyzer=analyzer,
        drive=drive,
        discord=discord,
    )

    result = asyncio.run(pipeline.process_video("http://example.com"))

    assert result["status"] == "error"
    assert result["step"] == "download"
    transcriber.run.assert_not_called()
    analyzer.run.assert_not_called()
    drive.run.assert_not_called()
    discord.run.assert_not_called()


def test_pipeline_does_not_configure_root_logger(monkeypatch):
    """Importing the pipeline should not modify the root logger level."""
    root = logging.getLogger()
    root.setLevel(logging.WARNING)
    importlib.reload(
        importlib.import_module(
            "ultimate_discord_intelligence_bot___complete_social_media_analysis_fact_checking_system.pipeline"
        )
    )
    assert logging.getLogger().level == logging.WARNING


def test_drive_upload_retry(monkeypatch):
    downloader = MagicMock()
    downloader.run.return_value = {
        "status": "success",
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

    discord = MagicMock()
    discord.run.return_value = {"status": "success"}

    pipeline = ContentPipeline(
        webhook_url="http://example.com",
        youtube_downloader=downloader,
        transcriber=transcriber,
        analyzer=analyzer,
        drive=drive,
        discord=discord,
    )

    result = asyncio.run(pipeline.process_video("http://example.com"))

    assert result["status"] == "success"
    assert drive.run.call_count == 2


def test_exception_in_analysis(monkeypatch):
    """Pipeline should surface step name when a tool raises."""
    downloader = MagicMock()
    downloader.run.return_value = {
        "status": "success",
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

    discord = MagicMock()

    pipeline = ContentPipeline(
        webhook_url="http://example.com",
        youtube_downloader=downloader,
        transcriber=transcriber,
        analyzer=analyzer,
        drive=drive,
        discord=discord,
    )

    result = asyncio.run(pipeline.process_video("http://example.com"))

    assert result["status"] == "error"
    assert result["step"] == "analysis"
    discord.run.assert_not_called()
