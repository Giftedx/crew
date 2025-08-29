"""Best-effort podcast feed resolver."""

from __future__ import annotations

from dataclasses import dataclass

from crewai.tools import BaseTool

from ...profiles.schema import CanonicalFeed


@dataclass
class PodcastResolverTool(BaseTool):
    """Resolve a podcast search string to a canonical feed reference."""

    name: str = "Podcast Resolver"
    description: str = "Resolve podcast search queries to RSS feed URLs."

    def _run(self, query: str) -> dict:
        feed = resolve_podcast_query(query)
        return feed.to_dict()


def resolve_podcast_query(query: str) -> CanonicalFeed:
    """Return a canonical feed for a podcast query.

    This implements basic podcast directory lookups using common patterns.
    For production, this should integrate with iTunes Search API, Spotify API,
    or podcast index services.
    """
    query_lower = query.lower().strip()

    # Common podcast mappings for well-known shows
    KNOWN_PODCASTS = {
        "joe rogan": "https://feeds.redcircle.com/0eccc737-7d67-4fea-b3de-37faf0e5c9a1",
        "tim ferriss": "https://feeds.feedburner.com/thetimferrissshow",
        "lex fridman": "https://lexfridman.com/feed/podcast/",
        "ben shapiro": "https://feeds.dailywire.com/rss/the-ben-shapiro-show",
        "jordan peterson": "https://feeds.feedburner.com/JordanPetersonPodcast",
        "sam harris": "https://feeds.feedburner.com/samharrisorg",
        "dan carlin": "https://feeds.feedburner.com/dancarlin/history",
        "hardcore history": "https://feeds.feedburner.com/dancarlin/history",
    }

    # Check for exact matches or partial matches
    for show_name, rss_url in KNOWN_PODCASTS.items():
        if show_name in query_lower or query_lower in show_name:
            return CanonicalFeed(
                rss_url=rss_url,
                directory_urls=[
                    f"https://podcasts.apple.com/search?term={query.replace(' ', '+')}",
                    f"https://open.spotify.com/search/{query.replace(' ', '%20')}",
                ],
            )

    # Fallback: generate generic directory search URLs
    slug = query.replace(" ", "-").lower()
    search_term = query.replace(" ", "+")

    return CanonicalFeed(
        rss_url=f"https://feeds.example.com/{slug}.rss",  # Placeholder
        directory_urls=[
            f"https://podcasts.apple.com/search?term={search_term}",
            f"https://open.spotify.com/search/{query.replace(' ', '%20')}",
            f"https://podcastindex.org/search?q={search_term}",
        ],
    )
