"""Acquisition agents for content download and ingestion.

This module contains agents responsible for downloading and ingesting content
from various platforms including YouTube, Twitch, TikTok, and others.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from crewai import Agent
from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags
from ultimate_discord_intelligence_bot.tools import AudioTranscriptionTool, DiscordDownloadTool, InstagramDownloadTool, KickDownloadTool, MultiPlatformDownloadTool, RedditDownloadTool, TikTokDownloadTool, TranscriptIndexTool, TwitchDownloadTool, TwitterDownloadTool, YtDlpDownloadTool
from ultimate_discord_intelligence_bot.tools.web import PlaywrightAutomationTool
_flags = FeatureFlags.from_env()

class AcquisitionAgents:
    """Acquisition agents for content download and ingestion."""

    def __init__(self):
        """Initialize acquisition agents."""
        self.flags = _flags

    def acquisition_specialist(self) -> Agent:
        """Multi-platform content acquisition specialist."""
        from crewai import Agent
        tools = [MultiPlatformDownloadTool(), YtDlpDownloadTool(), DiscordDownloadTool(), InstagramDownloadTool(), TikTokDownloadTool(), TwitchDownloadTool(), TwitterDownloadTool(), RedditDownloadTool(), KickDownloadTool()]
        if self.flags.enable_playwright_automation:
            tools.append(PlaywrightAutomationTool())
        return Agent(role='Multi-Platform Acquisition Specialist', goal='Download and prepare content from any supported platform with quality optimization.', backstory='Expert in content acquisition across platforms with focus on quality and metadata preservation.', tools=tools, verbose=True, allow_delegation=False)

    def transcription_engineer(self) -> Agent:
        """Audio transcription and indexing specialist."""
        from crewai import Agent
        return Agent(role='Transcription Engineer', goal='Convert audio/video content to searchable text with timestamps and quality indicators.', backstory='Specialist in audio processing and transcription with expertise in multiple languages and formats.', tools=[AudioTranscriptionTool(), TranscriptIndexTool()], verbose=True, allow_delegation=False)

    def content_ingestion_specialist(self) -> Agent:
        """Content ingestion and preparation specialist."""
        from crewai import Agent
        return Agent(role='Content Ingestion Specialist', goal='Prepare and validate content for downstream processing with metadata extraction.', backstory='Expert in content preparation and validation with focus on data quality and completeness.', tools=[MultiPlatformDownloadTool(), AudioTranscriptionTool(), TranscriptIndexTool()], verbose=True, allow_delegation=False)

    def enhanced_download_specialist(self) -> Agent:
        """Enhanced download capabilities specialist."""
        from crewai import Agent
        return Agent(role='Enhanced Download Specialist', goal='Provide advanced download capabilities with quality optimization and metadata preservation.', backstory='Specialist in advanced content acquisition with focus on quality and metadata extraction.', tools=[YtDlpDownloadTool(), MultiPlatformDownloadTool(), AudioTranscriptionTool()], verbose=True, allow_delegation=False)