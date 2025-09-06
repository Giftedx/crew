"""Monitor new posts from X/Twitter.

This lightweight wrapper reuses :class:`MultiPlatformMonitorTool` to track
unseen tweet IDs. It exposes a clearer interface for crews that specifically
watch X feeds.
"""

from __future__ import annotations

from collections.abc import Iterable

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool
from .multi_platform_monitor_tool import MultiPlatformMonitorTool


class XMonitorTool(BaseTool[StepResult]):
    """Return unseen tweets."""

    name: str = "X Monitor Tool"
    description: str = "Track new posts from X/Twitter feeds"

    def __init__(self) -> None:
        super().__init__()
        self._monitor = MultiPlatformMonitorTool()
        self._metrics = get_metrics()

    def _run(self, posts: Iterable[dict[str, str]]) -> StepResult:
        items = list(posts)
        if not items:
            self._metrics.counter("tool_runs_total", labels={"tool": "x_monitor", "outcome": "skipped"}).inc()
            return StepResult.ok(skipped=True, reason="no posts provided", new_posts=[])
        result = self._monitor._run(items)
        # Result is a StepResult; rely on its mapping interface (supports nested fallback)
        try:
            new_posts = result["new_items"]  # type: ignore[index]
        except KeyError:
            new_posts = []
        self._metrics.counter("tool_runs_total", labels={"tool": "x_monitor", "outcome": "success"}).inc()
        return StepResult.ok(new_posts=new_posts)

    def run(self, posts: Iterable[dict[str, str]]) -> StepResult:  # pragma: no cover - thin wrapper
        try:
            return self._run(posts)
        except Exception as exc:  # pragma: no cover - unexpected
            self._metrics.counter("tool_runs_total", labels={"tool": "x_monitor", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))
