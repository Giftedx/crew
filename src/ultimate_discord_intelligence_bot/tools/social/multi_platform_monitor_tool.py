"""Track new content across multiple platforms.

Migrated to StepResult pattern. Returns StepResult.ok with data={new_items:[...]}
Metrics: tool_runs_total{tool="multi_platform_monitor", outcome=success}
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from .._base import BaseTool


if TYPE_CHECKING:
    from collections.abc import Iterable


class _MonitorResult(TypedDict):
    status: str
    new_items: list[dict[str, str]]


class MultiPlatformMonitorTool(BaseTool[StepResult]):
    """Return unseen content items.

    The tool keeps an in-memory set of identifiers for items it has already
    observed. Subsequent calls filter out previously seen entries.
    """

    name: str = "Multi-Platform Monitor"
    description: str = "Identify new content items across platforms, filtering out those already processed."

    def __init__(self) -> None:
        super().__init__()
        self._seen_ids: set[str] = set()
        self._metrics = get_metrics()

    def _run(self, items: Iterable[dict[str, str]]) -> StepResult:
        new_items: list[dict[str, str]] = []
        try:
            for item in items:
                item_id = item.get("id")
                if item_id and item_id not in self._seen_ids:
                    self._seen_ids.add(item_id)
                    new_items.append(item)
            self._metrics.counter(
                "tool_runs_total", labels={"tool": "multi_platform_monitor", "outcome": "success"}
            ).inc()
            return StepResult.ok(new_items=new_items, data={"new_items": new_items})
        except Exception as e:
            self._metrics.counter(
                "tool_runs_total", labels={"tool": "multi_platform_monitor", "outcome": "error"}
            ).inc()
            return StepResult.fail(error=str(e))

    def run(self, items: Iterable[dict[str, str]]) -> StepResult:
        return self._run(items)
