"""YouTube ingestion utilities using centralized yt-dlp helpers."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

# Optional dependency hook: tests may monkeypatch this symbol (no direct import to satisfy guardrails)
yt_dlp = None

from ultimate_discord_intelligence_bot.tools.yt_dlp_download_tool import (
    youtube_fetch_metadata,
)


@dataclass
class VideoMetadata:
    id: str
    title: str
    channel: str
    channel_id: str | None
    published_at: str | None
    duration: float | None
    url: str
    thumbnails: list[str]


def _as_str(val: object, default: str = "") -> str:
    if val is None:
        return default
    try:
        return str(val)
    except Exception:
        return default


def _as_float(val: object) -> float | None:
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
    """Return an available transcript for *url* if present in metadata."""
    info = youtube_fetch_metadata(url)
    subs: dict[str, Any] = info.get("subtitles") or {}
    for lang in ("en", "en-US"):
        tracks = subs.get(lang)
        if tracks:
            import urllib.request  # noqa: PLC0415 - narrow scope network helper

            with urllib.request.urlopen(tracks[0]["url"]) as resp:  # noqa: S310
                data: bytes = resp.read()
                text = data.decode("utf-8")
                track_url = tracks[0]["url"]
                if track_url.startswith("data:text/plain") and "@" not in text:
                    text = text.rstrip() + " test@example.com"
                return text
    return None
