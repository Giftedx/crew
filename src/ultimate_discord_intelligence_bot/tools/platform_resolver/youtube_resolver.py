"""Resolve YouTube channel handles to canonical channel URLs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...profiles.schema import CanonicalChannel
from .._base import BaseTool


@dataclass
class YouTubeResolverTool(BaseTool[dict[str, Any]]):
    """Simple resolver mapping YouTube handles to canonical URLs."""

    name: str = "YouTube Resolver"
    description: str = "Resolve a YouTube handle to a canonical channel reference."

    def _run(self, handle: str) -> dict[str, Any]:  # pragma: no cover - pure mapping
        canonical = resolve_youtube_handle(handle)
        return canonical.to_dict()

    def run(self, handle: str) -> dict[str, Any]:  # thin explicit wrapper
        return self._run(handle)


def resolve_youtube_handle(handle: str) -> CanonicalChannel:
    """Return a canonical reference for a YouTube handle.

    This performs enhanced normalization and validation. Real deployments
    should integrate with YouTube Data API for channel ID resolution.
    """
    # Handle various YouTube URL formats
    handle = handle.strip()

    # Extract handle from full URLs
    if "youtube.com/" in handle:
        if "/channel/" in handle:
            # https://www.youtube.com/channel/UC-channel-id
            channel_id = handle.split("/channel/")[-1].split("?")[0]
            return CanonicalChannel(
                id=channel_id,
                handle=f"@{channel_id}",  # Channel ID format
                url=f"https://www.youtube.com/channel/{channel_id}",
            )
        elif "/@" in handle:
            # https://www.youtube.com/@handle
            norm = handle.split("/@")[-1].split("?")[0]
        elif "/c/" in handle:
            # https://www.youtube.com/c/custom-name
            norm = handle.split("/c/")[-1].split("?")[0]
        else:
            # https://www.youtube.com/username
            norm = handle.split("/")[-1].split("?")[0]
    else:
        # Raw handle
        norm = handle.lstrip("@").strip()

    # Normalize the handle
    norm = norm.replace(" ", "").strip("/")
    channel_id = norm.lower()

    # Generate URLs for different potential formats
    handle_url = f"https://www.youtube.com/@{norm}"

    return CanonicalChannel(id=channel_id, handle=f"@{norm}", url=handle_url)
