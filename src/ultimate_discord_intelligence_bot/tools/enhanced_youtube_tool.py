"""Legacy YouTube tool delegating to the unified wrappers.

This shim preserves the old `EnhancedYouTubeDownloadTool` API while routing all
work through the repository-standard download wrappers to enforce policy:
dispatch via `MultiPlatformDownloadTool` / `YouTubeDownloadTool` and never
shell out to `yt-dlp` directly from here.
"""

import shutil
from typing import Any, cast

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool
from .yt_dlp_download_tool import YouTubeDownloadTool


class EnhancedYouTubeDownloadTool(BaseTool):
    name: str = "Enhanced YouTube Download Tool"
    description: str = "Download YouTube videos using the unified yt-dlp wrapper"

    def __init__(self) -> None:
        super().__init__()
        self.ytdlp_available = bool(shutil.which("yt-dlp"))
        self._metrics = get_metrics()

    def _extract_metadata_only(self, url: str) -> dict[str, Any]:
        # Basic YouTube URL parsing
        if "youtube.com/watch?v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        else:
            video_id = "unknown"
        return {
            "status": "success",
            "platform": "youtube",
            "title": f"YouTube Video {video_id}",
            "description": "Metadata extracted without full download",
            "video_id": video_id,
            "url": url,
            "note": "Limited metadata - install yt-dlp for full functionality",
        }

    def _run(self, url: str, quality: str = "720p") -> StepResult:
        if not self.ytdlp_available:
            meta = self._extract_metadata_only(url)
            # Remove internal platform key to avoid duplication with explicit kwarg
            meta.pop("platform", None)
            self._metrics.counter("tool_runs_total", labels={"tool": "enhanced_youtube", "outcome": "success"}).inc()
            return StepResult.ok(platform="YouTube", command="<metadata-only>", **meta)

        result = YouTubeDownloadTool().run(url, quality=quality)
        # If the downstream result already has platform/command, forward it directly.
        if isinstance(result, StepResult):
            if result.success:
                # Promote underlying data fields to top-level if they exist and are simple scalars
                payload = result.data.copy() if result.data else {}
                platform = payload.pop("platform", getattr(YouTubeDownloadTool, "platform", "YouTube"))
                command = payload.pop("command", "")
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "enhanced_youtube", "outcome": "success"}
                ).inc()
                return StepResult.ok(platform=platform, command=command, **payload)
            else:
                self._metrics.counter("tool_runs_total", labels={"tool": "enhanced_youtube", "outcome": "error"}).inc()
                # Ensure platform/command still included on failure path
                payload = result.data.copy() if result.data else {}
                platform = payload.pop("platform", getattr(YouTubeDownloadTool, "platform", "YouTube"))
                command = payload.pop("command", "")
                # Legacy compatibility: always prefix yt-dlp stderr with 'yt-dlp failed: '
                raw_error = result.error or "download failed"
                if raw_error and not raw_error.lower().startswith("yt-dlp failed"):
                    formatted_error = f"yt-dlp failed: {raw_error}".strip()
                else:
                    formatted_error = raw_error
                return StepResult.fail(error=formatted_error, platform=platform, command=command, **payload)
        elif isinstance(result, dict):  # Legacy dict path
            result_dict = cast(dict[str, Any], result)
            outcome = "success" if result_dict.get("status") == "success" else "error"
            self._metrics.counter("tool_runs_total", labels={"tool": "enhanced_youtube", "outcome": outcome}).inc()
            platform = result_dict.get("platform", getattr(YouTubeDownloadTool, "platform", "YouTube"))
            command = result_dict.get("command", "")
            filtered = {k: v for k, v in result_dict.items() if k not in {"platform", "command"}}
            if outcome == "error":
                err = filtered.pop("error", result_dict.get("error", "yt-dlp failed"))
                if err and not err.lower().startswith("yt-dlp failed"):
                    err = f"yt-dlp failed: {err}".strip()
                return StepResult.fail(error=err, platform=platform, command=command, **filtered)
            return StepResult.ok(platform=platform, command=command, **filtered)
        else:  # Unexpected type
            self._metrics.counter("tool_runs_total", labels={"tool": "enhanced_youtube", "outcome": "error"}).inc()
            return StepResult.fail(
                error="Unexpected return type from YouTubeDownloadTool", platform="YouTube", command=""
            )

    def run(self, url: str, quality: str = "720p") -> StepResult:  # pragma: no cover - thin wrapper
        return self._run(url, quality)
