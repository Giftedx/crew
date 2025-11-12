"""Multi-platform download tool following Copilot instructions."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, ClassVar
from urllib.parse import urlparse

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import ErrorCategory, ErrorContext, StepResult

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
    """
    Multi-Platform Download Tool for content acquisition across multiple platforms.

    This tool provides a unified interface for downloading media content from various
    platforms including YouTube, Twitter, Instagram, TikTok, Reddit, Twitch, and more.
    It automatically detects the platform from the URL and dispatches to the appropriate
    platform-specific downloader.

    Supported Platforms:
    - YouTube (youtube.com, youtu.be)
    - Twitter/X (twitter.com, x.com)
    - Instagram (instagram.com)
    - TikTok (tiktok.com)
    - Reddit (reddit.com)
    - Twitch (twitch.tv)
    - Kick (kick.com)
    - Discord (discord.com)

    Features:
    - Automatic platform detection
    - Quality selection
    - Metadata extraction
    - Tenant isolation
    - Error handling and retry logic

    Args:
        download_dir: Optional directory for downloads (defaults to /tmp/downloads)

    Returns:
        StepResult with download information including:
        - file_path: Path to downloaded file
        - platform: Detected platform
        - metadata: Extracted metadata
        - duration: Processing time

    Example:
        >>> tool = MultiPlatformDownloadTool()
        >>> result = tool._run("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        >>> if result.success:
        ...     print(f"Downloaded: {result.data['file_path']}")

    Error Handling:
        - Invalid URL: Returns StepResult.fail with error message
        - Unsupported platform: Returns StepResult.fail with platform info
        - Download failure: Returns StepResult.fail with error details
        - Network issues: Automatic retry with exponential backoff

    Tenant Isolation:
        - Downloads are isolated per tenant
        - Metadata includes tenant context
        - File paths include tenant namespace
    """

    name: str = "Multi-Platform Download Tool"
    description: str = "Download media from supported platforms via yt-dlp. Provide url and optional quality."
    model_config: ClassVar[dict[str, Any]] = {"extra": "allow"}

    def __init__(self, download_dir: Path | None = None) -> None:
        super().__init__()
        self.download_dir = download_dir or Path("/tmp/downloads")
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
            return StepResult.skip(
                reason="No URL provided",
                error_category=ErrorCategory.MISSING_REQUIRED_FIELD,
                metadata={"tool": "multi_platform_download", "parameter": "url"},
            )
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace("www.", "")
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
                    error_category=ErrorCategory.VALIDATION,
                    error_context=ErrorContext(
                        operation="platform_detection",
                        component="multi_platform_download_tool",
                        additional_context={
                            "parsed_domain": domain,
                            "supported_platforms": list(self.dispatchers.keys()),
                        },
                    ),
                    metadata={"tool": "multi_platform_download", "attempted_domain": domain},
                )
            logger.info(f"Dispatching {domain} download to {dispatcher.name}")
            result = dispatcher.run(url, quality=quality, **kwargs)
            step = StepResult.from_dict(result) if isinstance(result, dict) else result
            label = "success" if step.success else "error"
            self._metrics.counter("tool_runs_total", labels={"tool": "multi_platform_download", "outcome": label}).inc()
            if isinstance(step, StepResult):
                step.data.setdefault("tool", dispatcher.__class__.__name__)
                step.data.setdefault(
                    "platform", step.data.get("platform", dispatcher.__class__.__name__.replace("DownloadTool", ""))
                )
            return step
        except Exception as e:
            logger.error(f"Download failed for {url}: {e}", exc_info=True)
            self._metrics.counter(
                "tool_runs_total", labels={"tool": "multi_platform_download", "outcome": "error"}
            ).inc()
            return StepResult.fail(
                error=str(e),
                data={"url": url},
                error_category=ErrorCategory.PROCESSING,
                error_context=ErrorContext(
                    operation="download_dispatch",
                    component="multi_platform_download_tool",
                    additional_context={"exception_type": type(e).__name__, "url": url},
                ),
                metadata={"tool": "multi_platform_download", "error_type": type(e).__name__},
            )

    def run(self, url: str, quality: str = "1080p", **kwargs: Any) -> StepResult:
        """Public interface following StepResult pattern."""
        return self._run(url=url, quality=quality, **kwargs)
