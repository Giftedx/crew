"""FastMCP Ingest Utilities server (safe, allowlisted).

Tools:
- extract_metadata(url): provider-aware metadata via centralized yt-dlp helpers
- list_channel_videos(channel_url, limit=50): YouTube flat listing (capped)
- fetch_transcript_local(path, model="tiny", max_chars=10000): local file STT via Whisper wrappers

Resource:
- ingest://providers – advertise supported providers/capabilities

Notes:
- No direct yt_dlp imports outside approved wrapper.
- Network calls are provider-allowlisted (YouTube/Twitch only) and HTTPS-only.
- Transcript tool operates on local files only to avoid surprise downloads/costs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable


try:
    from fastmcp import FastMCP  # type: ignore

    _FASTMCP_AVAILABLE = True
except Exception:  # pragma: no cover
    FastMCP = None  # type: ignore
    _FASTMCP_AVAILABLE = False


class _StubMCP:  # pragma: no cover
    def __init__(self, _name: str):
        self.name = _name

    def tool(self, fn: Callable | None = None, /, **_kw):
        def _decorator(f: Callable):
            return f

        return _decorator if fn is None else fn

    def resource(self, *_a, **_k):
        def _decorator(f: Callable):
            return f

        return _decorator

    def run(self) -> None:
        raise RuntimeError("FastMCP not available; install '.[mcp]' to run this server")


ingest_mcp = FastMCP("Ingest Utilities Server") if _FASTMCP_AVAILABLE else _StubMCP("Ingest Utilities Server")


_ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "twitch.tv",
    "www.twitch.tv",
}


def _host_for(url: str) -> str:
    try:
        from urllib.parse import urlparse

        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def _validate_https_public(url: str) -> str:
    """Delegate to core.http_utils for https/public validation when available."""

    try:
        from core.http_utils import validate_public_https_url  # type: ignore

        return validate_public_https_url(url)
    except Exception:
        # Best-effort minimal check (fallback): ensure scheme starts with https
        if not (isinstance(url, str) and url.startswith("https://")):
            raise ValueError("URL must start with https://")
        return url


def _extract_metadata_impl(url: str) -> dict:
    """Extract safe video metadata for an allowlisted provider (no download)."""

    try:
        _validate_https_public(url)
    except Exception as exc:
        return {"error": f"invalid_url: {exc}"}

    host = _host_for(url)
    if host not in _ALLOWED_HOSTS:
        return {"error": f"unsupported_provider:{host}"}

    # Route to centralized helpers (no direct yt_dlp import here)
    try:
        # Local import to keep yt-dlp usage centralized and optional
        from ultimate_discord_intelligence_bot.tools.yt_dlp_download_tool import (
            twitch_fetch_metadata,
            youtube_fetch_metadata,
        )
    except Exception as exc:
        return {"error": f"metadata_helpers_unavailable:{exc}"}

    try:
        if "youtube" in host or host == "youtu.be":
            meta = youtube_fetch_metadata(url)
            # Trim large arrays
            thumbs = meta.get("thumbnails") or []
            if isinstance(thumbs, list):
                meta["thumbnails"] = thumbs[:5]
            return {"provider": "youtube", "metadata": meta}
        if "twitch.tv" in host:
            meta = twitch_fetch_metadata(url)
            return {"provider": "twitch", "metadata": meta}
        return {"error": f"unsupported_provider:{host}"}
    except Exception as exc:  # includes RuntimeError when yt-dlp missing
        return {"error": str(exc)}


def _summarize_subtitles_impl(url: str, lang: str | None = None, max_chars: int = 1000) -> dict:
    """Fetch video metadata and summarize available subtitles text (no downloads).

    Returns first N characters of concatenated subtitle lines for the selected language
    (or first available language if none specified).
    """

    try:
        _validate_https_public(url)
    except Exception as exc:
        return {"error": f"invalid_url: {exc}"}

    host = _host_for(url)
    if host not in _ALLOWED_HOSTS:
        return {"error": f"unsupported_provider:{host}"}

    try:
        from ultimate_discord_intelligence_bot.tools.yt_dlp_download_tool import (
            youtube_fetch_metadata,
        )
    except Exception as exc:
        return {"error": f"metadata_helpers_unavailable:{exc}"}

    try:
        meta = youtube_fetch_metadata(url) if ("youtube" in host or host == "youtu.be") else {}
        subs = meta.get("subtitles") or {}
        if not isinstance(subs, dict) or not subs:
            return {"summary": "", "language": None}
        # Pick requested language or the first available
        lang_key = None
        if lang and lang in subs:
            lang_key = lang
        elif subs:
            lang_key = next(iter(subs.keys()))
        tracks = subs.get(lang_key, []) if lang_key else []
        # Each track element may include a 'url' requiring network to download; avoid that per guardrails.
        # Return a structural summary instead of fetching.
        info = {"language": lang_key, "tracks": len(tracks)}
        return {"summary": "", "language": lang_key, "info": info}
    except Exception as exc:
        return {"error": str(exc)}


def _list_channel_videos_impl(channel_url: str, limit: int = 50) -> dict:
    """List YouTube channel videos using yt-dlp flat mode (capped)."""

    try:
        _validate_https_public(channel_url)
    except Exception as exc:
        return {"error": f"invalid_url: {exc}"}

    host = _host_for(channel_url)
    if host not in _ALLOWED_HOSTS or "youtube" not in host:
        return {"error": f"unsupported_provider:{host}"}

    try:
        # Local import keeps optional dependency isolated
        from ultimate_discord_intelligence_bot.tools.yt_dlp_download_tool import (
            youtube_list_channel_videos,
        )
    except Exception as exc:
        return {"error": f"metadata_helpers_unavailable:{exc}"}

    try:
        videos = youtube_list_channel_videos(channel_url)
        lim = max(1, min(int(limit), 250))
        return {
            "provider": "youtube",
            "videos": videos[:lim],
            "count": min(len(videos), lim),
        }
    except Exception as exc:
        return {"error": str(exc)}


def _fetch_transcript_local_impl(path: str, model: str = "tiny", max_chars: int = 10000) -> dict:
    """Transcribe a local media file using lightweight Whisper wrappers.

    This tool does not download remote URLs. Provide a local file path.
    """

    try:
        import os

        if isinstance(path, str) and path.startswith("http"):
            return {
                "error": "remote_not_supported",
                "detail": "Provide a local file path.",
            }
        if not os.path.exists(path):
            return {"error": "file_not_found"}
        from analysis.transcribe import run_whisper  # type: ignore

        tx = run_whisper(path, model=model)
        # Build joined text and a bounded segments list
        texts: list[str] = []
        seg_items: list[dict[str, Any]] = []
        for seg in getattr(tx, "segments", []) or []:
            try:
                s = float(getattr(seg, "start", 0.0))
                e = float(getattr(seg, "end", s))
                t = str(getattr(seg, "text", "")).strip()
                seg_items.append({"start": s, "end": e, "text": t})
                texts.append(t)
                if sum(len(x) for x in texts) >= max(0, int(max_chars)):
                    break
            except Exception:
                continue
        full_text = "\n".join(texts)
        # Cap segments to avoid payload blowups
        return {
            "text": full_text[: max(0, int(max_chars))],
            "segments": seg_items[:500],
        }
    except Exception as exc:
        return {"error": str(exc)}


# Plain callables for direct imports (tests call these)
def extract_metadata(url: str) -> dict:
    return _extract_metadata_impl(url)


def summarize_subtitles(url: str, lang: str | None = None, max_chars: int = 1000) -> dict:
    return _summarize_subtitles_impl(url, lang=lang, max_chars=max_chars)


def list_channel_videos(channel_url: str, limit: int = 50) -> dict:
    return _list_channel_videos_impl(channel_url, limit=limit)


def fetch_transcript_local(path: str, model: str = "tiny", max_chars: int = 10000) -> dict:
    return _fetch_transcript_local_impl(path, model=model, max_chars=max_chars)


# MCP-decorated wrappers under different names to avoid shadowing
@ingest_mcp.tool
def extract_metadata_tool(url: str) -> dict:  # pragma: no cover - thin MCP wrapper
    return _extract_metadata_impl(url)


@ingest_mcp.tool
def summarize_subtitles_tool(url: str, lang: str | None = None, max_chars: int = 1000) -> dict:  # pragma: no cover
    return _summarize_subtitles_impl(url, lang=lang, max_chars=max_chars)


@ingest_mcp.tool
def list_channel_videos_tool(channel_url: str, limit: int = 50) -> dict:  # pragma: no cover
    return _list_channel_videos_impl(channel_url, limit=limit)


@ingest_mcp.tool
def fetch_transcript_local_tool(path: str, model: str = "tiny", max_chars: int = 10000) -> dict:  # pragma: no cover
    return _fetch_transcript_local_impl(path, model=model, max_chars=max_chars)


@ingest_mcp.resource("ingest://providers")
def providers() -> dict:
    return {
        "youtube": {"metadata": True, "channel_list": True},
        "twitch": {"metadata": True},
        "transcript": {"local_file_only": True},
    }


__all__ = [
    "extract_metadata",
    "extract_metadata_tool",
    "fetch_transcript_local",
    "fetch_transcript_local_tool",
    "ingest_mcp",
    "list_channel_videos",
    "list_channel_videos_tool",
    "providers",
    "summarize_subtitles",
    "summarize_subtitles_tool",
]
