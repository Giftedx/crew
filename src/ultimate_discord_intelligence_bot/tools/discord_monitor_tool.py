"""Monitor new messages from Discord channels."""

from __future__ import annotations

from typing import Dict, Iterable, List

from crewai_tools import BaseTool

from .multi_platform_monitor_tool import MultiPlatformMonitorTool


class DiscordMonitorTool(BaseTool):
    """Return unseen Discord messages."""

    name = "Discord Monitor Tool"
    description = "Track new messages from Discord channels"

    def __init__(self) -> None:
        super().__init__()
        self._monitor = MultiPlatformMonitorTool()

    def _run(self, messages: Iterable[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        result = self._monitor._run(messages)
        return {"status": "success", "new_messages": result["new_items"]}

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
