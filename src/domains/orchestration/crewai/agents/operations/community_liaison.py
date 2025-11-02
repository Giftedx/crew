"""Community Liaison Agent.

This agent answers community questions with verified intelligence.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from domains.orchestration.agents.base import BaseAgent
from domains.orchestration.agents.registry import register_agent
from app.config.settings import DISCORD_WEBHOOK
from ultimate_discord_intelligence_bot.tools import DiscordPostTool, DiscordQATool, Mem0MemoryTool, VectorSearchTool
if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.tools._base import BaseTool

@register_agent('community_liaison')
class CommunityLiaisonAgent(BaseAgent):
    """Community Liaison Agent for community engagement."""

    def __init__(self):
        """Initialize the community liaison with its tools."""
        tools = self._get_community_tools()
        super().__init__(tools)

    @property
    def role(self) -> str:
        """Agent role."""
        return 'Community Liaison'

    @property
    def goal(self) -> str:
        """Agent goal."""
        return 'Answer community questions with verified intelligence.'

    @property
    def backstory(self) -> str:
        """Agent backstory."""
        return 'Community engagement.'

    @property
    def allow_delegation(self) -> bool:
        """No delegation for community liaison."""
        return False

    def _get_community_tools(self) -> list[BaseTool]:
        """Get community tools for engagement."""
        return [DiscordQATool(), DiscordPostTool(webhook_url=DISCORD_WEBHOOK or 'https://placeholder.webhook.url'), VectorSearchTool(), Mem0MemoryTool()]