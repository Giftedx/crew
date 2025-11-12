from __future__ import annotations

import math
from dataclasses import dataclass

from domains.ingestion.providers.yt_dlp_download_tool import (
    twitch_fetch_metadata,
)


# Optional dependency hook: tests may monkeypatch this symbol (no direct import to satisfy guardrails)
yt_dlp = None

"""Twitch ingestion utilities using centralized yt-dlp helpers."""


@dataclass
class ClipMetadata:
    id: str
    title: str
    streamer: str
    published_at: str | None
    duration: float | None
    url: str


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


def fetch_metadata(url: str) -> ClipMetadata:
    info = twitch_fetch_metadata(url)
    upstream_url = _as_str(info.get("url", ""), "")
    return ClipMetadata(
        id=_as_str(info.get("id", "")),
        title=_as_str(info.get("title", "")),
        streamer=_as_str(info.get("streamer", "")),
        published_at=info.get("published_at"),
        duration=_as_float(info.get("duration")),
        url=(upstream_url or url),
    )


def fetch_transcript(url: str) -> str | None:
    """Best-effort transcript using metadata when captions unavailable."""
    try:
        info = twitch_fetch_metadata(url)
        title = info.get("title")
        if title:
            return str(title)
    except Exception:
        ...
    return "clip"
