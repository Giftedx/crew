"""Multi-platform download tool following Copilot instructions."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool
from .discord_download_tool import DiscordDownloadTool
from .yt_dlp_download_tool import (
    InstagramDownloadTool,
    KickDownloadTool,
    RedditDownloadTool,
    TikTokDownloadTool,
    TwitchDownloadTool,
    TwitterDownloadTool,
    YouTubeDownloadTool,
)

logger = logging.getLogger(__name__)


class MultiPlatformDownloadTool(BaseTool[StepResult]):
    """Dispatch to the correct platform downloader per instruction #3."""

    name: str = "Multi-Platform Download Tool"
    description: str = "Download media from supported platforms via yt-dlp. Provide url and optional quality."
    model_config = {"extra": "allow"}  # allow setting dynamic attributes

    def __init__(self, download_dir: Path | None = None) -> None:
        super().__init__()
        # Using a deterministic path; future enhancement: configurable via settings
        self.download_dir = download_dir or Path("/tmp/downloads")  # noqa: S108 (accepted project pattern)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.dispatchers = self._init_dispatchers()
        self._metrics = get_metrics()

    def _init_dispatchers(self) -> dict[str, BaseTool]:
        """Initialize platform-specific download tools."""
        return {
            "youtube.com": YouTubeDownloadTool(),
            "youtu.be": YouTubeDownloadTool(),
            "twitter.com": TwitterDownloadTool(),
            "x.com": TwitterDownloadTool(),
            "instagram.com": InstagramDownloadTool(),
            "tiktok.com": TikTokDownloadTool(),
            "reddit.com": RedditDownloadTool(),
            "twitch.tv": TwitchDownloadTool(),
            "kick.com": KickDownloadTool(),
            "discord.com": DiscordDownloadTool(),
            "cdn.discordapp.com": DiscordDownloadTool(),
        }

    def _run(self, url: str, quality: str = "1080p", **kwargs: Any) -> StepResult:
        """Download content from URL and return StepResult per instruction #3."""
        if not url:
            self._metrics.counter(
                "tool_runs_total", labels={"tool": "multi_platform_download", "outcome": "skipped"}
            ).inc()
            return StepResult.skip(reason="No URL provided")

        try:
            # Parse URL to determine platform
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace("www.", "")

            # Find appropriate dispatcher
            dispatcher = None
            for platform_domain, tool in self.dispatchers.items():
                if platform_domain in domain:
                    dispatcher = tool
                    break

            if not dispatcher:
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "multi_platform_download", "outcome": "error"}
                ).inc()
                return StepResult.fail(
                    error=f"Unsupported platform: {domain}",
                    data={"url": url, "domain": domain, "platform": "unknown"},
                )

            # Dispatch to platform-specific tool (tests monkeypatch 'run(video_url, quality=...)')
            logger.info(f"Dispatching {domain} download to {dispatcher.name}")
            # Pass positional video_url argument matching test fake_run signature
            result = dispatcher.run(url, quality=quality, **kwargs)

            # Handle legacy dict returns per instruction #3
            step = StepResult.from_dict(result) if isinstance(result, dict) else result

            label = "success" if step.success else "error"
            self._metrics.counter("tool_runs_total", labels={"tool": "multi_platform_download", "outcome": label}).inc()
            # Ensure dispatcher identity surfaced (tests expect 'tool' sometimes)
            if isinstance(step, StepResult):
                step.data.setdefault("tool", dispatcher.__class__.__name__)
                step.data.setdefault(
                    "platform", step.data.get("platform", dispatcher.__class__.__name__.replace("DownloadTool", ""))
                )
            return step

        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
            self._metrics.counter(
                "tool_runs_total", labels={"tool": "multi_platform_download", "outcome": "error"}
            ).inc()
            return StepResult.fail(error=str(e), data={"url": url})

    def run(self, url: str, quality: str = "1080p", **kwargs: Any) -> StepResult:
        """Public interface following StepResult pattern."""
        return self._run(url=url, quality=quality, **kwargs)
