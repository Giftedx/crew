"""Resolve Twitch logins to canonical channel URLs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...profiles.schema import CanonicalChannel
from .._base import BaseTool


@dataclass
class TwitchResolverTool(BaseTool[dict[str, Any]]):
    """Simple resolver mapping Twitch logins to canonical URLs."""

    name: str = "Twitch Resolver"
    description: str = "Resolve a Twitch login name to a canonical channel reference."

    def _run(self, login: str) -> dict[str, Any]:  # pragma: no cover - mapping only
        canonical = resolve_twitch_login(login)
        return canonical.to_dict()

    def run(self, login: str) -> dict[str, Any]:  # thin explicit wrapper
        return self._run(login)


def resolve_twitch_login(login: str) -> CanonicalChannel:
    norm = login.replace("https://", "").replace("twitch.tv/", "").strip("/")
    channel_id = norm.lower()
    url = f"https://twitch.tv/{norm}"
    return CanonicalChannel(id=channel_id, handle=norm, url=url)
