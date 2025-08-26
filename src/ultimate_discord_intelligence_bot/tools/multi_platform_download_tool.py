"""Select the appropriate downloader based on URL domain."""

from __future__ import annotations

from typing import Any, Dict, Type
from urllib.parse import urlparse

from crewai_tools import BaseTool

from .yt_dlp_download_tool import (
    YtDlpDownloadTool,
    YouTubeDownloadTool,
    TwitchDownloadTool,
    KickDownloadTool,
    TwitterDownloadTool,
    InstagramDownloadTool,
    TikTokDownloadTool,
    RedditDownloadTool,
)
from .discord_download_tool import DiscordDownloadTool


class MultiPlatformDownloadTool(BaseTool):
    """Dispatch to the correct platform downloader."""

    name = "Multi-Platform Download Tool"
    description = "Download media from supported platforms via yt-dlp"

    def __init__(self) -> None:
        super().__init__()
        self._dispatch: Dict[str, Type[BaseTool]] = {
            "youtube.com": YouTubeDownloadTool,
            "youtu.be": YouTubeDownloadTool,
            "twitch.tv": TwitchDownloadTool,
            "kick.com": KickDownloadTool,
            "twitter.com": TwitterDownloadTool,
            "x.com": TwitterDownloadTool,
            "instagram.com": InstagramDownloadTool,
            # TikTok share links often use vm.tiktok.com or vt.tiktok.com aliases
            "vm.tiktok.com": TikTokDownloadTool,
            "vt.tiktok.com": TikTokDownloadTool,
            "tiktok.com": TikTokDownloadTool,
            "reddit.com": RedditDownloadTool,
            "redd.it": RedditDownloadTool,
            "v.redd.it": RedditDownloadTool,
            "cdn.discordapp.com": DiscordDownloadTool,
            "media.discordapp.net": DiscordDownloadTool,
        }

    def _run(self, url: str, quality: str = "1080p") -> Dict[str, Any]:
        """Route ``url`` to the appropriate downloader.

        Parameters
        ----------
        url:
            Media link to fetch.
        quality:
            Preferred quality setting passed through to the underlying
            platform tool. Defaults to ``1080p``.
        """

        domain = urlparse(url).netloc.lower()
        for pattern, tool_cls in self._dispatch.items():
            if domain.endswith(pattern):
                return tool_cls().run(url, quality=quality)
        return {
            "status": "error",
            "error": f"Unsupported platform for URL: {url}",
            "platform": "unknown",
        }

    def run(self, url: str, quality: str = "1080p") -> Dict[str, Any]:  # pragma: no cover - thin wrapper
        """Public wrapper delegating to :meth:`_run`."""
        return self._run(url, quality=quality)
