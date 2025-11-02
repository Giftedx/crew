"""Analysis Cartographer Agent.

This agent maps linguistic, sentiment, and thematic signals.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from domains.orchestration.agents.base import BaseAgent
from domains.orchestration.agents.registry import register_agent
from ultimate_discord_intelligence_bot.tools import (
    EngagementPredictionTool,
    EnhancedAnalysisTool,
    LCSummarizeTool,
    PerspectiveSynthesizerTool,
    SentimentTool,
    TextAnalysisTool,
    TranscriptIndexTool,
    TrendForecastingTool,
)

if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.tools._base import BaseTool


@register_agent("analysis_cartographer")
class AnalysisCartographerAgent(BaseAgent):
    """Analysis Cartographer Agent for comprehensive linguistic analysis."""

    def __init__(self):
        """Initialize the analysis cartographer with its tools."""
        tools = self._get_analysis_tools()
        super().__init__(tools)

    @property
    def role(self) -> str:
        """Agent role."""
        return "Analysis Cartographer"

    @property
    def goal(self) -> str:
        """Agent goal."""
        return "Map linguistic, sentiment, and thematic signals."

    @property
    def backstory(self) -> str:
        """Agent backstory."""
        return "Comprehensive linguistic analysis with predictive capabilities."

    @property
    def allow_delegation(self) -> bool:
        """No delegation for analysis cartographer."""
        return False

    def _get_analysis_tools(self) -> list[BaseTool]:
        """Get analysis tools for content analysis."""
        return [
            EnhancedAnalysisTool(),
            TextAnalysisTool(),
            SentimentTool(),
            PerspectiveSynthesizerTool(),
            TranscriptIndexTool(),
            LCSummarizeTool(),
            TrendForecastingTool(),
            EngagementPredictionTool(),
        ]
