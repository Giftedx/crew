"""Track new content across multiple platforms."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypedDict

from ._base import BaseTool


class _MonitorResult(TypedDict):
    status: str
    new_items: list[dict[str, str]]


class MultiPlatformMonitorTool(BaseTool[_MonitorResult]):
    """Return unseen content items.

    The tool keeps an in-memory set of identifiers for items it has already
    observed. Subsequent calls filter out previously seen entries.
    """

    name: str = "Multi-Platform Monitor"
    description: str = (
        "Identify new content items across platforms, filtering out those already processed."
    )

    def __init__(self) -> None:
        super().__init__()
        self._seen_ids: set[str] = set()

    def _run(self, items: Iterable[dict[str, str]]) -> _MonitorResult:
        new_items: list[dict[str, str]] = []
        for item in items:
            item_id = item.get("id")
            if item_id and item_id not in self._seen_ids:
                self._seen_ids.add(item_id)
                new_items.append(item)
        return {"status": "success", "new_items": new_items}

    def run(self, items: Iterable[dict[str, str]]) -> _MonitorResult:  # pragma: no cover - thin wrapper
        return self._run(items)
