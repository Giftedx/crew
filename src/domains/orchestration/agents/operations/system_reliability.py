"""System Reliability Officer Agent.

This agent guards pipeline health and visibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ultimate_discord_intelligence_bot.agents.base import BaseAgent
from ultimate_discord_intelligence_bot.agents.registry import register_agent
from ultimate_discord_intelligence_bot.settings import (
    DISCORD_PRIVATE_WEBHOOK,
    DISCORD_WEBHOOK,
)
from ultimate_discord_intelligence_bot.tools import (
    AdvancedPerformanceAnalyticsTool,
    DiscordPrivateAlertTool,
    MCPCallTool,
    PipelineTool,
    SystemStatusTool,
    TimelineTool,
)


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.tools._base import BaseTool


@register_agent("system_reliability_officer")
class SystemReliabilityOfficerAgent(BaseAgent):
    """System Reliability Officer Agent for operations and reliability."""

    def __init__(self):
        """Initialize the system reliability officer with its tools."""
        tools = self._get_reliability_tools()
        super().__init__(tools)

    @property
    def role(self) -> str:
        """Agent role."""
        return "System Reliability Officer"

    @property
    def goal(self) -> str:
        """Agent goal."""
        return "Guard pipeline health and visibility."

    @property
    def backstory(self) -> str:
        """Agent backstory."""
        return "Operations and reliability."

    @property
    def allow_delegation(self) -> bool:
        """No delegation for system reliability officer."""
        return False

    def _get_reliability_tools(self) -> list[BaseTool]:
        """Get reliability tools for system monitoring."""
        return [
            SystemStatusTool(),
            AdvancedPerformanceAnalyticsTool(),
            DiscordPrivateAlertTool(
                DISCORD_PRIVATE_WEBHOOK or DISCORD_WEBHOOK or "https://discord.com/api/webhooks/placeholder/crew-intel"
            ),
            PipelineTool(),
            TimelineTool(),
            MCPCallTool(),
        ]
