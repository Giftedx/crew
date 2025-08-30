"""Generic downloader utilities built on yt-dlp.

This module defines a :class:`YtDlpDownloadTool` base class that encapsulates the
common logic for downloading media from platforms supported by yt-dlp. Specific
platform tools inherit from this base to reduce duplication while exposing a
clear, descriptive interface for crew agents.
"""

import json
import logging
import os
import re
import subprocess
from typing import ClassVar

from ..settings import DOWNLOADS_DIR, TEMP_DIR, YTDLP_ARCHIVE, YTDLP_CONFIG
from ._base import BaseTool


class YtDlpDownloadTool(BaseTool[dict[str, str]]):
    """Reusable yt-dlp wrapper.

    Subclasses only need to provide ``platform`` metadata. The command and
    environment setup remain consistent across video platforms.
    """

    platform: ClassVar[str] = "generic"
    model_config = {"extra": "allow"}  # allow dynamic fields set by subclasses/tests

    def _run(self, video_url: str, quality: str = "1080p") -> dict[str, str]:
        """Download media using yt-dlp.

        Parameters
        ----------
        video_url:
            URL for the target video or stream.
        quality:
            Preferred maximum resolution (e.g. ``720p``). The downloader will
            request the highest stream not exceeding this value. Defaults to
            ``1080p``.
        """

        config_file = str(YTDLP_CONFIG)

        match = re.match(r"(\d+)", quality)
        height = match.group(1) if match else "1080"
        format_selector = f"bv*[height<={height}]+ba/b[height<={height}]"

        command = [
            "yt-dlp",
            "--config-locations",
            config_file,
            "-f",
            format_selector,
            "--dump-json",
            video_url,
        ]
        command_str = " ".join(command)

        env = os.environ.copy()
        env.update(
            {
                "CREWAI_DOWNLOADS_DIR": str(DOWNLOADS_DIR),
                "CREWAI_YTDLP_ARCHIVE": str(YTDLP_ARCHIVE),
                "CREWAI_TEMP_DIR": str(TEMP_DIR),
            }
        )

        try:
            # Avoid passing 'check' so test monkeypatch functions with a simpler
            # signature (without 'check' kwarg) still work. We manually handle
            # the return code below to classify success vs error.
            # Security note (S603): command list is constructed from static yt-dlp
            # arguments plus the user-provided URL. yt-dlp internally sanitizes
            # the URL; we do not invoke a shell. Adding a justification comment
            # to silence/clarify the audit rule.
            # Pass no 'check' kwarg so simple test monkeypatch functions without
            # that parameter continue to work. We'll examine returncode manually.
            result = subprocess.run(  # noqa: S603, PLW1510 - manual returncode handling preferred for test monkeypatch compatibility
                command,
                # Deliberately omit 'check' so simple monkeypatched test fakes
                # (signature without 'check') work; we inspect returncode.
                capture_output=True,
                text=True,
                timeout=1800,
                env=env,
            )

            if result.returncode == 0:
                output_lines = result.stdout.strip().split("\n")
                try:
                    info = json.loads(output_lines[-1])
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "platform": self.platform,
                        "error": f"Unexpected yt-dlp output: {output_lines[-1]}",
                        "command": command_str,
                    }
                local_path = info.get("filepath")
                if not local_path:
                    downloads = info.get("requested_downloads") or []
                    if downloads:
                        local_path = downloads[0].get("filepath")
                if not local_path:
                    return {
                        "status": "error",
                        "platform": self.platform,
                        "error": "File path missing from yt-dlp output",
                        "command": command_str,
                    }
                return {
                    "status": "success",
                    "platform": self.platform,
                    "video_id": str(info.get("id", "")),
                    "title": info.get("title", ""),
                    "uploader": info.get("uploader", ""),
                    "duration": str(info.get("duration", "")),
                    "file_size": str(info.get("filesize_approx", "")),
                    "local_path": local_path,
                    "command": command_str,
                }
            else:
                return {
                    "status": "error",
                    "platform": self.platform,
                    "error": result.stderr.strip(),
                    "command": command_str,
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "platform": self.platform,
                "error": "Download timeout after 30 minutes",
                "command": command_str,
            }
        except Exception as e:  # pragma: no cover - defensive logging path
            logging.exception("%s download failed", self.platform)
            return {
                "status": "error",
                "platform": self.platform,
                "error": str(e),
                "command": command_str,
            }

    def run(
        self, video_url: str, quality: str = "1080p"
    ) -> dict[str, str]:  # pragma: no cover - thin wrapper
        """Public wrapper delegating to :meth:`_run`."""
        return self._run(video_url, quality)

    # Ensure class-level attribute access for tests retrieving subclass.platform
    @classmethod
    def __getattr__(cls, item):  # pragma: no cover - compatibility shim
        if item == "platform" and "platform" in cls.__dict__:
            return cls.__dict__["platform"]
        raise AttributeError(item)


class YouTubeDownloadTool(YtDlpDownloadTool):
    name: str = "YouTube Download Tool"
    description: str = "Download YouTube videos with optimal settings for Discord sharing"
    platform: ClassVar[str] = "YouTube"


class TwitchDownloadTool(YtDlpDownloadTool):
    name: str = "Twitch Download Tool"
    description: str = "Download Twitch VODs or clips"
    platform: ClassVar[str] = "Twitch"


class KickDownloadTool(YtDlpDownloadTool):
    name: str = "Kick Download Tool"
    description: str = "Download Kick streams"
    platform: ClassVar[str] = "Kick"


class TwitterDownloadTool(YtDlpDownloadTool):
    name: str = "Twitter Download Tool"
    description: str = "Download videos from X/Twitter"
    platform: ClassVar[str] = "Twitter"


class InstagramDownloadTool(YtDlpDownloadTool):
    name: str = "Instagram Download Tool"
    description: str = "Download Instagram reels or posts"
    platform: ClassVar[str] = "Instagram"


class TikTokDownloadTool(YtDlpDownloadTool):
    name: str = "TikTok Download Tool"
    description: str = "Download TikTok videos"
    platform: ClassVar[str] = "TikTok"


class RedditDownloadTool(YtDlpDownloadTool):
    name: str = "Reddit Download Tool"
    description: str = "Download Reddit-hosted videos"
    platform: ClassVar[str] = "Reddit"
