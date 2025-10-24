"""Transcription Engineer Agent.

This agent delivers reliable transcripts, indices, and artifacts.
"""

from __future__ import annotations

from ultimate_discord_intelligence_bot.agents.base import BaseAgent
from ultimate_discord_intelligence_bot.agents.registry import register_agent
from ultimate_discord_intelligence_bot.tools import (
    AudioTranscriptionTool,
    DriveUploadTool,
    TextAnalysisTool,
    TimelineTool,
    TranscriptIndexTool,
)
from ultimate_discord_intelligence_bot.tools._base import BaseTool


@register_agent("transcription_engineer")
class TranscriptionEngineerAgent(BaseAgent):
    """Transcription Engineer Agent for audio processing and indexing."""

    def __init__(self):
        """Initialize the transcription engineer with its tools."""
        tools = self._get_transcription_tools()
        super().__init__(tools)

    @property
    def role(self) -> str:
        """Agent role."""
        return "Transcription & Index Engineer"

    @property
    def goal(self) -> str:
        """Agent goal."""
        return "Deliver reliable transcripts, indices, and artefacts."

    @property
    def backstory(self) -> str:
        """Agent backstory."""
        return "Audio/linguistic processing."

    @property
    def allow_delegation(self) -> bool:
        """No delegation for transcription engineer."""
        return False

    def _get_transcription_tools(self) -> list[BaseTool]:
        """Get transcription tools for audio processing."""
        return [
            AudioTranscriptionTool(),
            TranscriptIndexTool(),
            TimelineTool(),
            DriveUploadTool(),
            TextAnalysisTool(),
        ]
