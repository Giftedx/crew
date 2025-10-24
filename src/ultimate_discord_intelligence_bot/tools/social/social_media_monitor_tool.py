"""Aggregate basic social media chatter across platforms.

This lightweight tool simulates monitoring Reddit, X/Twitter and Discord by
scanning provided text snippets for a keyword. It establishes the contract for
future, API-driven implementations while keeping unit tests fast and
self-contained.

Instrumentation:
    * tool_runs_total{tool="social_media_monitor", outcome}
    * Outcomes: success | error | skipped (missing keyword)
    * No latency histogram (pure in-memory filtering, negligible cost)
"""

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from .._base import BaseTool


class SocialMediaMonitorTool(BaseTool[StepResult]):
    """Collect posts mentioning a keyword across platforms.

    Returns StepResult with data:
      matches: mapping platform -> list[str]
    """

    name: str = "Social Media Monitor"
    description: str = "Aggregate social media posts and return those containing the keyword"

    def __init__(self) -> None:
        self._metrics = get_metrics()

    def _run(self, posts: dict[str, list[str]], keyword: str) -> StepResult:
        if not keyword:
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "social_media_monitor", "outcome": "skipped"},
            ).inc()
            return StepResult.skip(reason="No keyword provided")
        try:
            matches: dict[str, list[str]] = {}
            lower = keyword.lower()
            for platform, items in posts.items():
                platform_matches = [p for p in items if lower in p.lower()]
                if platform_matches:
                    matches[platform] = platform_matches
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "social_media_monitor", "outcome": "success"},
            ).inc()
            return StepResult.ok(matches=matches)
        except Exception as e:  # pragma: no cover - defensive
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "social_media_monitor", "outcome": "error"},
            ).inc()
            return StepResult.fail(error=str(e))

    def run(self, posts: dict[str, list[str]], keyword: str) -> StepResult:  # pragma: no cover - thin wrapper
        return self._run(posts, keyword)
