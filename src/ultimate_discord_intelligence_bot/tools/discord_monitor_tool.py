"""Monitor new messages from Discord channels.

Migrated to StepResult. Wraps MultiPlatformMonitorTool and re-maps key.
Metrics: tool_runs_total{tool="discord_monitor", outcome=success}
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypedDict

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool
from .multi_platform_monitor_tool import MultiPlatformMonitorTool


class _DiscordMonitorResult(TypedDict):
    status: str
    new_messages: list[dict[str, str]]


class DiscordMonitorTool(BaseTool):
    """Return unseen Discord messages."""

    name: str = "Discord Monitor Tool"
    description: str = "Track new messages from Discord channels"

    def __init__(self) -> None:
        super().__init__()
        self._monitor = MultiPlatformMonitorTool()
        self._metrics = get_metrics()

    def _run(self, messages: Iterable[dict[str, str]]) -> StepResult:
        # Delegate to underlying tool (already returns StepResult)
        underlying = self._monitor._run(messages)
        if not underlying.success:
            self._metrics.counter("tool_runs_total", labels={"tool": "discord_monitor", "outcome": "error"}).inc()
            return StepResult.fail(error=underlying.error or "monitor failure")
        data = underlying.data or {}
        new_items = data.get("new_items", [])
        self._metrics.counter("tool_runs_total", labels={"tool": "discord_monitor", "outcome": "success"}).inc()
        return StepResult.ok(data={"new_messages": new_items})

    def run(self, messages: Iterable[dict[str, str]]) -> StepResult:  # pragma: no cover - thin wrapper
        return self._run(messages)
