"""Profile schema definitions for debate analysis."""

from __future__ import annotations

from typing import TypedDict


class Platforms(TypedDict, total=False):
    """Platform handles for a creator."""

    youtube: list[str]
    twitch: list[str]
    twitter: list[str]
    instagram: list[str]
    tiktok: list[str]
    podcast: list[str]


class CreatorProfile(TypedDict, total=False):
    """Profile information for a content creator."""

    name: str
    type: str
    roles: list[str]
    shows: list[str]
    content_tags: list[str]
    platforms: Platforms


class SeedProfile(TypedDict, total=False):
    """Seed profile data for initialization."""

    name: str
    type: str
    roles: list[str]
    shows: list[str]
    content_tags: list[str]
    seed_handles: dict[str, list[str]]


def load_seeds(seed_path: str) -> list[SeedProfile]:
    """Load seed profiles from a YAML file."""
    try:
        import yaml

        with open(seed_path) as f:
            data = yaml.safe_load(f)
        return data.get("profiles", [])
    except Exception:
        # Return empty list if file doesn't exist or can't be parsed
        return []
