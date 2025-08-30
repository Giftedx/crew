"""Generic social profile resolver for platforms like X, Instagram, TikTok."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...profiles.schema import CanonicalProfile
from .._base import BaseTool


@dataclass
class SocialResolverTool(BaseTool[dict[str, Any]]):
    """Resolve a social handle on a given platform to a canonical profile."""

    name: str = "Social Resolver"
    description: str = "Resolve social handles for platforms like X, Instagram, or TikTok."

    def _run(self, platform: str, handle: str) -> dict[str, Any]:  # pragma: no cover
        profile = resolve_social_handle(platform, handle)
        return profile.to_dict()

    def run(self, platform: str, handle: str) -> dict[str, Any]:  # thin wrapper
        return self._run(platform, handle)


def resolve_social_handle(platform: str, handle: str) -> CanonicalProfile:
    norm_handle = handle.lstrip("@").strip()
    url = f"https://{platform}.com/{norm_handle}" if platform else None
    return CanonicalProfile(id=norm_handle.lower(), handle=f"@{norm_handle}", url=url)
