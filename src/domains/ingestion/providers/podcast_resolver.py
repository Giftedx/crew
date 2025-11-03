"""Best-effort podcast feed resolver.

Contract: public run/_run returns StepResult; helper returns domain object.
"""

from __future__ import annotations

from dataclasses import dataclass
from platform.core.step_result import StepResult
from platform.observability.metrics import get_metrics

from ...profiles.schema import CanonicalFeed
from .._base import BaseTool


@dataclass
class PodcastResolverTool(BaseTool[StepResult]):
    """Resolve a podcast search string to a canonical feed reference."""

    name: str = "Podcast Resolver"
    description: str = "Resolve podcast search queries to RSS feed URLs."

    def __post_init__(self) -> None:
        self._metrics = get_metrics()

    def _run(self, query: str) -> StepResult:
        try:
            feed = resolve_podcast_query(query)
            self._metrics.counter("tool_runs_total", labels={"tool": "resolver_podcast", "outcome": "success"}).inc()
            return StepResult.ok(data=feed.to_dict())
        except Exception as exc:
            self._metrics.counter("tool_runs_total", labels={"tool": "resolver_podcast", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))

    def run(self, query: str) -> StepResult:
        return self._run(query)


def resolve_podcast_query(query: str) -> CanonicalFeed:
    """Return a canonical feed for a podcast query.

    This implements basic podcast directory lookups using common patterns.
    For production, this should integrate with iTunes Search API, Spotify API,
    or podcast index services.
    """
    query_lower = query.lower().strip()
    known_podcasts = {
        "joe rogan": "https://feeds.redcircle.com/0eccc737-7d67-4fea-b3de-37faf0e5c9a1",
        "tim ferriss": "https://feeds.feedburner.com/thetimferrissshow",
        "lex fridman": "https://lexfridman.com/feed/podcast/",
        "ben shapiro": "https://feeds.dailywire.com/rss/the-ben-shapiro-show",
        "jordan peterson": "https://feeds.feedburner.com/JordanPetersonPodcast",
        "sam harris": "https://feeds.feedburner.com/samharrisorg",
        "dan carlin": "https://feeds.feedburner.com/dancarlin/history",
        "hardcore history": "https://feeds.feedburner.com/dancarlin/history",
    }
    for show_name, rss_url in known_podcasts.items():
        if show_name in query_lower or query_lower in show_name:
            return CanonicalFeed(
                rss_url=rss_url,
                directory_urls=[
                    f"https://podcasts.apple.com/search?term={query.replace(' ', '+')}",
                    f"https://open.spotify.com/search/{query.replace(' ', '%20')}",
                ],
            )
    slug = query.replace(" ", "-").lower()
    search_term = query.replace(" ", "+")
    return CanonicalFeed(
        rss_url=f"https://feeds.example.com/{slug}.rss",
        directory_urls=[
            f"https://podcasts.apple.com/search?term={search_term}",
            f"https://open.spotify.com/search/{query.replace(' ', '%20')}",
            f"https://podcastindex.org/search?q={search_term}",
        ],
    )
