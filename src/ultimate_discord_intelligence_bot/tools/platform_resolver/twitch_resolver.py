"""Resolve Twitch logins to canonical channel URLs."""

from __future__ import annotations

from dataclasses import dataclass

from crewai_tools import BaseTool

from ...profiles.schema import CanonicalChannel


@dataclass
class TwitchResolverTool(BaseTool):
    """Simple resolver mapping Twitch logins to canonical URLs."""

    name: str = "Twitch Resolver"
    description: str = "Resolve a Twitch login name to a canonical channel reference."

    def _run(self, login: str) -> dict:
        canonical = resolve_twitch_login(login)
        return canonical.to_dict()


def resolve_twitch_login(login: str) -> CanonicalChannel:
    norm = login.replace("https://", "").replace("twitch.tv/", "").strip("/")
    channel_id = norm.lower()
    url = f"https://twitch.tv/{norm}"
    return CanonicalChannel(id=channel_id, handle=norm, url=url)
