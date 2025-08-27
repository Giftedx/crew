"""Platform resolvers convert handles into canonical platform records."""

from .youtube_resolver import YouTubeResolverTool, resolve_youtube_handle
from .twitch_resolver import TwitchResolverTool, resolve_twitch_login
from .podcast_resolver import PodcastResolverTool, resolve_podcast_query
from .social_resolver import SocialResolverTool, resolve_social_handle

__all__ = [
    "YouTubeResolverTool",
    "TwitchResolverTool",
    "PodcastResolverTool",
    "SocialResolverTool",
    "resolve_youtube_handle",
    "resolve_twitch_login",
    "resolve_podcast_query",
    "resolve_social_handle",
]
