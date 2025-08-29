from __future__ import annotations

"""YouTube ingestion utilities."""

from dataclasses import dataclass


@dataclass
class VideoMetadata:
    id: str
    title: str
    channel: str
    published_at: str | None
    duration: float | None
    url: str
    thumbnails: list[str]


def fetch_metadata(url: str) -> VideoMetadata:
    """Return basic metadata for a YouTube video *url* using ``yt-dlp``."""
    import yt_dlp

    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:  # pragma: no cover - network
        info = ydl.extract_info(url, download=False)
    return VideoMetadata(
        id=info["id"],
        title=info.get("title", ""),
        channel=info.get("uploader", ""),
        published_at=info.get("upload_date"),
        duration=info.get("duration"),
        url=info.get("webpage_url", url),
        thumbnails=[t["url"] for t in info.get("thumbnails", [])],
    )


def fetch_transcript(url: str) -> str | None:
    """Return an available transcript for *url* if yt-dlp exposes one."""
    import yt_dlp

    with yt_dlp.YoutubeDL({"skip_download": True, "quiet": True}) as ydl:  # pragma: no cover
        info = ydl.extract_info(url, download=False)
    subs = info.get("subtitles") or {}
    for lang in ("en", "en-US"):
        tracks = subs.get(lang)
        if tracks:
            import urllib.request

            with urllib.request.urlopen(tracks[0]["url"]) as resp:
                return resp.read().decode("utf-8")
    return None
