"""Lazy Acquisition Specialist Agent.

This agent demonstrates lazy loading for acquisition tools, reducing startup time
by only loading tools when they are actually needed.
"""

from __future__ import annotations

from typing import Any

from ultimate_discord_intelligence_bot.agents.lazy_base import LazyBaseAgent, create_lazy_tool_specs
from ultimate_discord_intelligence_bot.agents.registry import register_agent


@register_agent("lazy_acquisition_specialist")
class LazyAcquisitionSpecialistAgent(LazyBaseAgent):
    """Lazy Acquisition Specialist Agent for multi-platform content capture."""

    def __init__(self):
        """Initialize the lazy acquisition specialist with tool specifications."""
        tool_specs = self._get_acquisition_tool_specs()
        super().__init__(tool_specs)

    @property
    def role(self) -> str:
        """Agent role."""
        return "Lazy Acquisition Specialist"

    @property
    def goal(self) -> str:
        """Agent goal."""
        return "Capture pristine source media and metadata from every supported platform using lazy loading."

    @property
    def backstory(self) -> str:
        """Agent backstory."""
        return "Multi-platform capture expert with optimized startup time through lazy loading."

    @property
    def allow_delegation(self) -> bool:
        """No delegation for acquisition specialist."""
        return False

    def _get_acquisition_tool_specs(self) -> list[dict[str, Any]]:
        """Get acquisition tool specifications for lazy loading."""
        return create_lazy_tool_specs(
            [
                "MultiPlatformDownloadTool",
                "TwitchDownloadTool",
                "KickDownloadTool",
                "TwitterDownloadTool",
                "InstagramDownloadTool",
                "TikTokDownloadTool",
                "RedditDownloadTool",
                "DiscordDownloadTool",
                "DriveUploadTool",
                "DriveUploadToolBypass",
            ]
        )

    def get_startup_performance(self) -> dict[str, Any]:
        """Get startup performance metrics."""
        stats = self.get_tool_loading_stats()
        stats["agent_type"] = "lazy_acquisition_specialist"
        stats["lazy_loading_enabled"] = True
        return stats
