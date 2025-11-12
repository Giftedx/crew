"""Platform resolver utilities for debate analysis."""


def resolve_podcast_query(query: str) -> str:
    """Resolve podcast query to handle."""
    return f"podcast:{query}"


def resolve_social_handle(platform: str, handle: str) -> str:
    """Resolve social media handle."""
    return f"{platform}:{handle}"


def resolve_twitch_login(login: str) -> str:
    """Resolve Twitch login."""
    return f"twitch:{login}"


def resolve_youtube_handle(handle: str) -> str:
    """Resolve YouTube handle."""
    return f"youtube:{handle}"
