"""Base classes for acquisition tools.

This module provides specialized base classes for content acquisition tools
that handle downloading, transcribing, and processing content from various platforms.
"""

from __future__ import annotations

from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class AcquisitionTool(BaseTool):
    """Base class for content acquisition tools.

    Provides common functionality for tools that download, transcribe, or
    process content from external sources.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def validate_url(self, url: str) -> StepResult:
        """Validate that a URL is properly formatted and accessible.

        Args:
            url: The URL to validate

        Returns:
            StepResult indicating validation success or failure
        """
        if not url or not isinstance(url, str):
            return StepResult.fail("Invalid URL: must be a non-empty string")

        if not url.startswith(("http://", "https://")):
            return StepResult.fail("Invalid URL: must start with http:// or https://")

        return StepResult.ok(data={"url": url, "valid": True})

    def get_platform_from_url(self, url: str) -> str:
        """Extract platform identifier from URL.

        Args:
            url: The URL to analyze

        Returns:
            Platform identifier (e.g., 'youtube', 'tiktok', 'twitter')
        """
        url_lower = url.lower()

        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "youtube"
        elif "tiktok.com" in url_lower:
            return "tiktok"
        elif "twitter.com" in url_lower or "x.com" in url_lower:
            return "twitter"
        elif "instagram.com" in url_lower:
            return "instagram"
        elif "reddit.com" in url_lower:
            return "reddit"
        elif "twitch.tv" in url_lower:
            return "twitch"
        elif "discord.com" in url_lower:
            return "discord"
        else:
            return "unknown"


class TranscriptionTool(BaseTool):
    """Base class for transcription and audio processing tools."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def validate_audio_file(self, file_path: str) -> StepResult:
        """Validate that an audio file exists and is accessible.

        Args:
            file_path: Path to the audio file

        Returns:
            StepResult indicating validation success or failure
        """
        import os

        if not file_path or not isinstance(file_path, str):
            return StepResult.fail("Invalid file path: must be a non-empty string")

        if not os.path.exists(file_path):
            return StepResult.fail(f"Audio file not found: {file_path}")

        # Check file extension
        valid_extensions = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm"}
        _, ext = os.path.splitext(file_path.lower())

        if ext not in valid_extensions:
            return StepResult.fail(f"Unsupported audio format: {ext}. Supported formats: {', '.join(valid_extensions)}")

        return StepResult.ok(data={"file_path": file_path, "valid": True})


__all__ = ["AcquisitionTool", "TranscriptionTool"]
