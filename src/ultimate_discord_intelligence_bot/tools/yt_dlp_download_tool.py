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
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, ClassVar, cast

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ..settings import DOWNLOADS_DIR, TEMP_DIR, YTDLP_ARCHIVE, YTDLP_CONFIG
from ._base import BaseTool


class YtDlpDownloadTool(BaseTool):
    """Reusable yt-dlp wrapper.

    Subclasses only need to provide ``platform`` metadata. The command and
    environment setup remain consistent across video platforms.
    """

    platform: ClassVar[str] = "generic"
    model_config = {"extra": "allow"}  # allow dynamic fields set by subclasses/tests

    def __init__(self):
        super().__init__()
        self._metrics = get_metrics()

    def _run(self, video_url: str, quality: str = "1080p") -> StepResult:
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

        str(YTDLP_CONFIG)

        match = re.match(r"(\d+)", quality)
        height = match.group(1) if match else "1080"
        format_selector = f"bv*[height<={height}]+ba/b[height<={height}]"

        # Use a simplified output template that doesn't require environment variables
        output_template = str(DOWNLOADS_DIR / "%(title)s [%(id)s].%(ext)s")

        # Resolve yt-dlp path; fall back to `python -m yt_dlp` if CLI not on PATH
        ytdlp_bin = shutil.which("yt-dlp")
        if ytdlp_bin:
            base_cmd = [ytdlp_bin]
        else:
            base_cmd = [sys.executable, "-m", "yt_dlp"]

        command = [
            *base_cmd,
            "-o",
            output_template,
            "-f",
            format_selector,
            "--restrict-filenames",
            "--write-info-json",
            "--print-json",
            "--retries",
            "3",
            video_url,
        ]
        # For user-facing and tests, normalize to a stable command string beginning with 'yt-dlp'
        display_cmd = [
            "yt-dlp",
            "-o",
            output_template,
            "-f",
            format_selector,
            "--restrict-filenames",
            "--write-info-json",
            "--print-json",
            "--retries",
            "3",
            video_url,
        ]
        command_str = " ".join(display_cmd)

        env = os.environ.copy()
        env.update(
            {
                "CREWAI_DOWNLOADS_DIR": str(DOWNLOADS_DIR),
                "CREWAI_YTDLP_ARCHIVE": str(YTDLP_ARCHIVE),
                "CREWAI_TEMP_DIR": str(TEMP_DIR),
            }
        )

        def _success(**fields: Any) -> StepResult:
            self._metrics.counter("tool_runs_total", labels={"tool": "yt_dlp_download", "outcome": "success"}).inc()
            return StepResult.ok(platform=self.platform, command=command_str, **fields)

        def _error(message: str) -> StepResult:
            self._metrics.counter("tool_runs_total", labels={"tool": "yt_dlp_download", "outcome": "error"}).inc()
            return StepResult.fail(error=message, platform=self.platform, command=command_str)

        start = time.monotonic()
        try:
            result = subprocess.run(  # noqa: S603, PLW1510
                command,
                capture_output=True,
                text=True,
                timeout=1800,
                env=env,
            )
            if result.returncode != 0:
                return _error(result.stderr.strip())

            output_lines = result.stdout.strip().split("\n")
            # Already downloaded?
            if any("[download]" in line and "has already been downloaded" in line for line in output_lines):
                try:
                    download_line = next(
                        line for line in output_lines if "[download]" in line and "has already been downloaded" in line
                    )
                    path_match = re.search(r"\[download\]\s+(.+?)\s+has already been downloaded", download_line)
                    if path_match:
                        existing_path = path_match.group(1)
                        file_name = Path(existing_path).stem
                        id_match = re.search(r"\[([^\]]+)\]$", file_name)
                        video_id = id_match.group(1) if id_match else ""
                        title = file_name.rsplit(" [", 1)[0] if id_match else file_name
                        return _success(
                            video_id=video_id,
                            title=title,
                            uploader="",
                            duration="",
                            file_size="",
                            local_path=existing_path,
                            note="File was already downloaded",
                        )
                except StopIteration:
                    # If pattern not found fall back to normal JSON parsing below.
                    pass

            # Parse JSON (scan from bottom up for robustness)
            json_line = None
            for _raw in reversed(output_lines):
                candidate = _raw.strip()
                if candidate.startswith("{") and candidate.endswith("}"):
                    json_line = candidate
                    break
            if not json_line:
                return _error("Unexpected yt-dlp output (no JSON metadata detected)")
            try:
                info = json.loads(json_line)
            except json.JSONDecodeError:
                return _error(f"Failed to parse JSON: {json_line}")

            # Resolve local path
            local_path = info.get("filepath") or info.get("_filename") or info.get("filename")
            if not local_path:
                downloads = info.get("requested_downloads") or []
                if downloads:
                    first = downloads[0]
                    local_path = first.get("filepath") or first.get("_filename") or first.get("filename")
            base_fields = dict(
                video_id=str(info.get("id", "unknown")),
                title=info.get("title", "unknown"),
                uploader=info.get("uploader", "unknown"),
                duration=str(info.get("duration", "unknown")),
                file_size=str(info.get("filesize_approx", "unknown")),
            )
            # Enrich with channel identifiers when available for downstream backfill
            try:
                base_fields.update(
                    {
                        "channel_id": info.get("channel_id") or info.get("uploader_id"),
                        "channel_url": info.get("channel_url") or info.get("uploader_url"),
                        "uploader_url": info.get("uploader_url"),
                        "uploader_id": info.get("uploader_id"),
                    }
                )
            except Exception:
                pass
            if not local_path:
                return _success(**base_fields, local_path="", note="Metadata only (no file path in output)")
            return _success(**base_fields, local_path=local_path)
        except subprocess.TimeoutExpired:
            return _error("Download timeout after 30 minutes")
        except Exception as e:  # pragma: no cover
            logging.exception("%s download failed", self.platform)
            return _error(str(e))
        finally:
            try:
                duration = time.monotonic() - start
                self._metrics.histogram("tool_run_seconds", duration, labels={"tool": "yt_dlp_download"})
            except Exception as metrics_exc:  # pragma: no cover
                logging.debug("Failed recording yt_dlp_download metrics: %s", metrics_exc)

    def run(self, video_url: str, quality: str = "1080p") -> StepResult:  # pragma: no cover - thin wrapper
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


# ---------------------------------------------------------------------------
# Lightweight metadata extraction helpers (centralized yt-dlp usage)
# ---------------------------------------------------------------------------
def _extract_info_with_yt_dlp(url: str, opts: dict[str, Any] | None = None) -> dict[str, Any]:
    """Use python yt_dlp to extract metadata without downloading.

    Encapsulated here to keep all direct yt_dlp imports in one approved module.
    """
    try:
        import yt_dlp as _real  # noqa: PLC0415
    except Exception as e:  # pragma: no cover - surface a consistent error for callers
        raise RuntimeError("yt-dlp is not installed") from e

    effective: dict[str, Any] = {"quiet": True, "skip_download": True}
    if opts:
        effective.update(opts)
    # Cast options to Any to satisfy yt-dlp's typed _Params without importing private types
    with _real.YoutubeDL(cast(Any, effective)) as ydl:  # pragma: no cover - network-using path
        extracted = ydl.extract_info(url, download=False)
        # yt-dlp returns an InfoDict (Mapping-like). Convert to a plain dict for downstream typing stability.
        try:
            return dict(extracted)
        except Exception as e:  # pragma: no cover - defensive
            raise RuntimeError("Unexpected yt-dlp return type (expected Mapping)") from e


def youtube_fetch_metadata(url: str) -> dict[str, Any]:
    info = _extract_info_with_yt_dlp(url, {"skip_download": True})
    return {
        "id": info.get("id", ""),
        "title": info.get("title", ""),
        "channel": info.get("uploader", ""),
        "channel_id": info.get("channel_id") or info.get("uploader_id", ""),
        "published_at": info.get("upload_date"),
        "duration": info.get("duration"),
        "url": info.get("webpage_url", url),
        "thumbnails": [t.get("url", "") for t in info.get("thumbnails", []) if isinstance(t, dict)],
        "subtitles": info.get("subtitles", {}),
    }


def twitch_fetch_metadata(url: str) -> dict[str, Any]:
    info = _extract_info_with_yt_dlp(url, {"skip_download": True})
    return {
        "id": info.get("id", ""),
        "title": info.get("title", ""),
        "streamer": info.get("uploader", ""),
        "published_at": info.get("upload_date"),
        "duration": info.get("duration"),
        "url": info.get("webpage_url", url),
    }


def youtube_list_channel_videos(channel_url: str) -> list[dict[str, Any]]:
    """List videos for a YouTube channel using yt-dlp in flat mode.

    Returns a list of dicts with keys: id, url, upload_date (YYYYMMDD), title.
    This function centralizes yt-dlp usage per guardrails.
    """
    # Allow overridable pagination depth to ensure a complete year of content
    import os

    try:
        playlistend = int(os.getenv("YTDLP_PLAYLISTEND_MAX", "250"))
    except Exception:
        playlistend = 250

    info = _extract_info_with_yt_dlp(
        channel_url,
        {
            "skip_download": True,
            "extract_flat": True,  # faster listing
            "playlistend": playlistend,
        },
    )
    entries = info.get("entries") or []
    out: list[dict[str, Any]] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        vid = e.get("id") or e.get("url") or ""
        url = e.get("url") or e.get("webpage_url") or ""
        if url and not url.startswith("http"):
            # yt-dlp flat entries may include only id; construct standard URL
            url = f"https://www.youtube.com/watch?v={vid}"
        out.append(
            {
                "id": vid,
                "url": url,
                "upload_date": e.get("upload_date"),
                "title": e.get("title", ""),
            }
        )
    return out
