"""Best-effort podcast feed resolver."""

from __future__ import annotations

from dataclasses import dataclass

from crewai_tools import BaseTool

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
    """Return a placeholder canonical feed for a query.

    Real implementations should look up podcast directories. This fallback
    simply formats the query into a mock URL for deterministic testing.
    """
    slug = query.replace(" ", "-")
    rss_url = f"https://example.com/{slug}.rss"
    return CanonicalFeed(rss_url=rss_url, directory_urls=[])
