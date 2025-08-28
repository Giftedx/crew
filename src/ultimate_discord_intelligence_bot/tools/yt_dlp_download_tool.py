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
from typing import Dict

from crewai.tools import BaseTool

from ..settings import DOWNLOADS_DIR, YTDLP_ARCHIVE, YTDLP_CONFIG, TEMP_DIR


class YtDlpDownloadTool(BaseTool):
    """Reusable yt-dlp wrapper.

    Subclasses only need to provide ``platform`` metadata. The command and
    environment setup remain consistent across video platforms.
    """

    platform: str = "generic"

    def _run(self, video_url: str, quality: str = "1080p") -> Dict[str, str]:
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
            result = subprocess.run(
                command,
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

    def run(self, video_url: str, quality: str = "1080p") -> Dict[str, str]:  # pragma: no cover - thin wrapper
        """Public wrapper delegating to :meth:`_run`."""
        return self._run(video_url, quality)

class YouTubeDownloadTool(YtDlpDownloadTool):
    name: str = "YouTube Download Tool"
    description: str = "Download YouTube videos with optimal settings for Discord sharing"
    platform: str = "YouTube"


class TwitchDownloadTool(YtDlpDownloadTool):
    name: str = "Twitch Download Tool" 
    description: str = "Download Twitch VODs or clips"
    platform: str = "Twitch"


class KickDownloadTool(YtDlpDownloadTool):
    name: str = "Kick Download Tool"
    description: str = "Download Kick streams"
    platform: str = "Kick"


class TwitterDownloadTool(YtDlpDownloadTool):
    name: str = "Twitter Download Tool"
    description: str = "Download videos from X/Twitter"
    platform: str = "Twitter"


class InstagramDownloadTool(YtDlpDownloadTool):
    name: str = "Instagram Download Tool"
    description: str = "Download Instagram reels or posts"
    platform: str = "Instagram"


class TikTokDownloadTool(YtDlpDownloadTool):
    name: str = "TikTok Download Tool"
    description: str = "Download TikTok videos"
    platform: str = "TikTok"


class RedditDownloadTool(YtDlpDownloadTool):
    name: str = "Reddit Download Tool"
    description: str = "Download Reddit-hosted videos"
    platform: str = "Reddit"

