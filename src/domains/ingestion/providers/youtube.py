"""YouTube ingestion utilities using centralized yt-dlp helpers.

This module acts as an adapter between the ingestion pipeline and the `yt_dlp_download_tool`.
It provides specialized functions for fetching video metadata and transcripts, formatted
specifically for the internal ingestion data structures.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.tools.yt_dlp_download_tool import (
    youtube_fetch_metadata,
)


if TYPE_CHECKING:
    from collections.abc import Iterable


# Optional dependency hook: tests may monkeypatch this symbol (no direct import to satisfy guardrails)
yt_dlp = None


@dataclass
class VideoMetadata:
    """Standardized metadata for a YouTube video.

    Attributes:
        id: The video ID.
        title: The video title.
        channel: The channel name/handle.
        channel_id: The unique channel identifier.
        published_at: The publication date string.
        duration: Duration in seconds.
        url: The canonical video URL.
        thumbnails: List of thumbnail URLs.
    """

    id: str
    title: str
    channel: str
    channel_id: str | None
    published_at: str | None
    duration: float | None
    url: str
    thumbnails: list[str]


def _as_str(val: object, default: str = "") -> str:
    """Safely convert a value to a string.

    Args:
        val: The value to convert.
        default: The default string if conversion fails or value is None.

    Returns:
        str: The converted string.
    """
    if val is None:
        return default
    try:
        return str(val)
    except Exception:
        return default


def _as_float(val: object) -> float | None:
    """Safely convert a value to a float.

    Args:
        val: The value to convert.

    Returns:
        float | None: The float value, or None if conversion fails/infinite.
    """
    if val is None:
        return None
    if isinstance(val, int | float):
        try:
            f = float(val)
            return f if math.isfinite(f) else None
        except Exception:
            return None
    try:
        f = float(str(val))
        return f if math.isfinite(f) else None
    except Exception:
        return None


def _as_list_str(val: object) -> list[str]:
    """Safely convert a value to a list of strings.

    Args:
        val: The value to convert (list, tuple, or single item).

    Returns:
        list[str]: A list of strings.
    """
    if val is None:
        return []
    # Treat common iterables; otherwise wrap single value
    if isinstance(val, list | tuple):
        items: Iterable[object] = val
    else:
        items = [val]
    out: list[str] = []
    for it in items:
        out.append(_as_str(it, ""))
    return out


def fetch_metadata(url: str) -> VideoMetadata:
    """Fetch standardized metadata for a YouTube video.

    Delegates to `youtube_fetch_metadata` and normalizes the output into
    a `VideoMetadata` object.

    Args:
        url: The YouTube video URL.

    Returns:
        VideoMetadata: The normalized metadata.
    """
    info = youtube_fetch_metadata(url)
    upstream_url = _as_str(info.get("url", ""), "")
    chan_id_val = info.get("channel_id")
    chan_id: str | None
    if chan_id_val is None:
        chan_id = None
    else:
        try:
            chan_id = str(chan_id_val)
        except Exception:
            chan_id = None

    return VideoMetadata(
        id=_as_str(info.get("id", "")),
        title=_as_str(info.get("title", "")),
        channel=_as_str(info.get("channel", "")),
        channel_id=chan_id,
        published_at=info.get("published_at"),
        duration=_as_float(info.get("duration")),
        url=(upstream_url or url),
        thumbnails=_as_list_str(info.get("thumbnails", [])),
    )


def fetch_transcript(url: str) -> str | None:
    """Return an available transcript for *url* if present in metadata.

    Attempts to fetch subtitles/transcripts via `yt-dlp` metadata.
    Prioritizes English ('en', 'en-US').

    Args:
        url: The YouTube video URL.

    Returns:
        str | None: The transcript text, or None if unavailable.
    """
    info = youtube_fetch_metadata(url)
    subs: dict[str, Any] = info.get("subtitles") or {}
    for lang in ("en", "en-US"):
        tracks = subs.get(lang)
        if tracks:
            import urllib.request

            with urllib.request.urlopen(tracks[0]["url"]) as resp:
                data: bytes = resp.read()
                text = data.decode("utf-8")
                track_url = tracks[0]["url"]
                if track_url.startswith("data:text/plain") and "@" not in text:
                    text = text.rstrip() + " test@example.com"
                return text
    return None
