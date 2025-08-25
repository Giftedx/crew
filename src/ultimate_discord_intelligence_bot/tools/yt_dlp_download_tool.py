"""Generic downloader utilities built on yt-dlp.

This module defines a :class:`YtDlpDownloadTool` base class that encapsulates the
common logic for downloading media from platforms supported by yt-dlp. Specific
platform tools inherit from this base to reduce duplication while exposing a
clear, descriptive interface for crew agents.
"""

import logging
import os
import subprocess
from typing import Dict

from crewai_tools import BaseTool

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
            Preferred quality setting. Currently unused but kept for API parity
            with future enhancements.
        """

        config_file = str(YTDLP_CONFIG)
        command = [
            "yt-dlp",
            "--config-locations",
            config_file,
            "--print",
            "%(id)s|%(title)s|%(uploader)s|%(duration)s|%(filesize_approx)s|%(filepath)s",
            video_url,
        ]

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
                download_info = output_lines[-1].split("|")
                if len(download_info) != 6:
                    return {
                        "status": "error",
                        "platform": self.platform,
                        "error": f"Unexpected yt-dlp output: {output_lines[-1]}",
                        "command": " ".join(command),
                    }
                local_path = download_info[5]
                return {
                    "status": "success",
                    "platform": self.platform,
                    "video_id": download_info[0],
                    "title": download_info[1],
                    "uploader": download_info[2],
                    "duration": download_info[3],
                    "file_size": download_info[4],
                    "local_path": local_path,
                    "download_command": " ".join(command),
                }
            else:
                return {
                    "status": "error",
                    "platform": self.platform,
                    "error": result.stderr,
                    "command": " ".join(command),
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "platform": self.platform,
                "error": "Download timeout after 30 minutes",
            }
        except Exception as e:  # pragma: no cover - defensive logging path
            logging.exception("%s download failed", self.platform)
            return {"status": "error", "platform": self.platform, "error": str(e)}

    # Provide run wrapper for consistency with other tools
    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)


class YouTubeDownloadTool(YtDlpDownloadTool):
    name = "YouTube Download Tool"
    description = "Download YouTube videos with optimal settings for Discord sharing"
    platform = "YouTube"


class TwitchDownloadTool(YtDlpDownloadTool):
    name = "Twitch Download Tool"
    description = "Download Twitch VODs or clips"
    platform = "Twitch"


class KickDownloadTool(YtDlpDownloadTool):
    name = "Kick Download Tool"
    description = "Download Kick streams"
    platform = "Kick"


class TwitterDownloadTool(YtDlpDownloadTool):
    name = "Twitter Download Tool"
    description = "Download videos from X/Twitter"
    platform = "Twitter"


class InstagramDownloadTool(YtDlpDownloadTool):
    name = "Instagram Download Tool"
    description = "Download Instagram reels or posts"
    platform = "Instagram"


class TikTokDownloadTool(YtDlpDownloadTool):
    name = "TikTok Download Tool"
    description = "Download TikTok videos"
    platform = "TikTok"

