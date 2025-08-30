"""Monitor new messages from Discord channels."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypedDict

from ._base import BaseTool
from .multi_platform_monitor_tool import MultiPlatformMonitorTool


class _DiscordMonitorResult(TypedDict):
    status: str
    new_messages: list[dict[str, str]]


class DiscordMonitorTool(BaseTool[_DiscordMonitorResult]):
    """Return unseen Discord messages."""

    name: str = "Discord Monitor Tool"
    description: str = "Track new messages from Discord channels"

    def __init__(self) -> None:
        super().__init__()
        self._monitor = MultiPlatformMonitorTool()

    def _run(self, messages: Iterable[dict[str, str]]) -> _DiscordMonitorResult:
        result = self._monitor._run(messages)
        return {"status": "success", "new_messages": result["new_items"]}

    def run(self, messages: Iterable[dict[str, str]]) -> _DiscordMonitorResult:  # pragma: no cover - thin wrapper
        return self._run(messages)
