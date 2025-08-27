from __future__ import annotations

"""Twitch ingestion utilities using ``yt-dlp`` for simplicity."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ClipMetadata:
    id: str
    title: str
    streamer: str
    published_at: Optional[str]
    duration: Optional[float]
    url: str


def fetch_metadata(url: str) -> ClipMetadata:
    import yt_dlp

    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:  # pragma: no cover - network
        info = ydl.extract_info(url, download=False)
    return ClipMetadata(
        id=info["id"],
        title=info.get("title", ""),
        streamer=info.get("uploader", ""),
        published_at=info.get("upload_date"),
        duration=info.get("duration"),
        url=info.get("webpage_url", url),
    )


def fetch_transcript(url: str) -> Optional[str]:
    """Twitch rarely exposes transcripts; return ``None`` to signal fallback."""
    return None
