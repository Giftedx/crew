"""Verification Director Agent.

This agent delivers defensible verdicts and reasoning for significant claims.
"""

from __future__ import annotations

from ultimate_discord_intelligence_bot.agents.base import BaseAgent
from ultimate_discord_intelligence_bot.agents.registry import register_agent
from ultimate_discord_intelligence_bot.tools import (
    ClaimExtractorTool,
    ContextVerificationTool,
    FactCheckTool,
    ImageAnalysisTool,
    LogicalFallacyTool,
    PerspectiveSynthesizerTool,
)
from ultimate_discord_intelligence_bot.tools._base import BaseTool


@register_agent("verification_director")
class VerificationDirectorAgent(BaseAgent):
    """Verification Director Agent for fact-checking and claim verification."""

    def __init__(self):
        """Initialize the verification director with its tools."""
        tools = self._get_verification_tools()
        super().__init__(tools)

    @property
    def role(self) -> str:
        """Agent role."""
        return "Verification Director"

    @property
    def goal(self) -> str:
        """Agent goal."""
        return "Deliver defensible verdicts and reasoning for significant claims."

    @property
    def backstory(self) -> str:
        """Agent backstory."""
        return "Fact-checking leadership with visual verification capabilities."

    @property
    def allow_delegation(self) -> bool:
        """No delegation for verification director."""
        return False

    def _get_verification_tools(self) -> list[BaseTool]:
        """Get verification tools for fact-checking."""
        return [
            FactCheckTool(),
            LogicalFallacyTool(),
            ClaimExtractorTool(),
            ContextVerificationTool(),
            PerspectiveSynthesizerTool(),
            ImageAnalysisTool(),
        ]
