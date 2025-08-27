"""Resolve YouTube channel handles to canonical channel URLs."""

from __future__ import annotations

from dataclasses import dataclass

from crewai_tools import BaseTool

from ...profiles.schema import CanonicalChannel


@dataclass
class YouTubeResolverTool(BaseTool):
    """Simple resolver mapping YouTube handles to canonical URLs."""

    name: str = "YouTube Resolver"
    description: str = "Resolve a YouTube handle to a canonical channel reference."

    def _run(self, handle: str) -> dict:
        canonical = resolve_youtube_handle(handle)
        return canonical.to_dict()


def resolve_youtube_handle(handle: str) -> CanonicalChannel:
    """Return a canonical reference for a YouTube handle.

    The function performs basic normalization only. Real deployments should
    call the YouTube Data API to validate and retrieve channel IDs.
    """
    norm = handle.lstrip("@").strip()
    channel_id = norm.lower()
    url = f"https://www.youtube.com/@{norm}"
    return CanonicalChannel(id=channel_id, handle=f"@{norm}", url=url)
