"""Acquisition Specialist Agent.

This agent captures pristine source media and metadata from every supported platform.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from domains.orchestration.agents.base import BaseAgent
from domains.orchestration.agents.registry import register_agent
from ultimate_discord_intelligence_bot.tools import DiscordDownloadTool, DriveUploadTool, DriveUploadToolBypass, InstagramDownloadTool, KickDownloadTool, MultiPlatformDownloadTool, RedditDownloadTool, TikTokDownloadTool, TwitchDownloadTool, TwitterDownloadTool
if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.tools._base import BaseTool

@register_agent('acquisition_specialist')
class AcquisitionSpecialistAgent(BaseAgent):
    """Acquisition Specialist Agent for multi-platform content capture."""

    def __init__(self):
        """Initialize the acquisition specialist with its tools."""
        tools = self._get_acquisition_tools()
        super().__init__(tools)

    @property
    def role(self) -> str:
        """Agent role."""
        return 'Acquisition Specialist'

    @property
    def goal(self) -> str:
        """Agent goal."""
        return 'Capture pristine source media and metadata from every supported platform.'

    @property
    def backstory(self) -> str:
        """Agent backstory."""
        return 'Multi-platform capture expert.'

    @property
    def allow_delegation(self) -> bool:
        """No delegation for acquisition specialist."""
        return False

    def _get_acquisition_tools(self) -> list[BaseTool]:
        """Get acquisition tools for content capture."""
        return [MultiPlatformDownloadTool(), TwitchDownloadTool(), KickDownloadTool(), TwitterDownloadTool(), InstagramDownloadTool(), TikTokDownloadTool(), RedditDownloadTool(), DiscordDownloadTool(), DriveUploadTool(), DriveUploadToolBypass()]