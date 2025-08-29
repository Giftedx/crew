"""Monitor new posts from X/Twitter.

This lightweight wrapper reuses :class:`MultiPlatformMonitorTool` to track
unseen tweet IDs. It exposes a clearer interface for crews that specifically
watch X feeds.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypedDict

from crewai.tools import BaseTool

from .multi_platform_monitor_tool import MultiPlatformMonitorTool


class _XMonitorResult(TypedDict):
    status: str
    new_posts: list[dict[str, str]]


class XMonitorTool(BaseTool):
    """Return unseen tweets."""

    name: str = "X Monitor Tool"
    description: str = "Track new posts from X/Twitter feeds"

    def __init__(self) -> None:
        super().__init__()
        self._monitor = MultiPlatformMonitorTool()

    def _run(self, posts: Iterable[dict[str, str]]) -> _XMonitorResult:
        result = self._monitor._run(posts)
        return {"status": "success", "new_posts": result["new_items"]}

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
