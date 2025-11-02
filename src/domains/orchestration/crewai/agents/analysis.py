"""Analysis agents for content analysis and processing.

This module contains agents responsible for analyzing content including
sentiment analysis, bias detection, claim extraction, and trend analysis.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from crewai import Agent
from app.config.feature_flags import FeatureFlags
from ultimate_discord_intelligence_bot.tools import AdvancedAudioAnalysisTool, ClaimExtractorTool, EnhancedAnalysisTool, ImageAnalysisTool, LiveStreamAnalysisTool, LogicalFallacyTool, MultimodalAnalysisTool, OpenAIEnhancedAnalysisTool, SentimentTool, SocialGraphAnalysisTool, TextAnalysisTool, TrendAnalysisTool, TrendForecastingTool, VideoFrameAnalysisTool
_flags = FeatureFlags.from_env()

class AnalysisAgents:
    """Analysis agents for content analysis and processing."""

    def __init__(self):
        """Initialize analysis agents."""
        self.flags = _flags

    def analysis_cartographer(self) -> Agent:
        """Content analysis and insight mapping specialist."""
        from crewai import Agent
        return Agent(role='Analysis Cartographer', goal='Map content insights, sentiment shifts, and topical clusters with comprehensive analysis.', backstory='Expert in content analysis with focus on insight mapping and pattern recognition.', tools=[EnhancedAnalysisTool(), OpenAIEnhancedAnalysisTool(), TextAnalysisTool(), SentimentTool(), LogicalFallacyTool(), ClaimExtractorTool(), TrendAnalysisTool(), MultimodalAnalysisTool()], verbose=True, allow_delegation=False)

    def political_analysis_specialist(self) -> Agent:
        """Political content analysis specialist."""
        from crewai import Agent
        return Agent(role='Political Analysis Specialist', goal='Analyze political content for bias, claims, and factual accuracy with comprehensive reporting.', backstory='Specialist in political content analysis with expertise in bias detection and fact-checking.', tools=[EnhancedAnalysisTool(), OpenAIEnhancedAnalysisTool(), LogicalFallacyTool(), ClaimExtractorTool(), SentimentTool(), TextAnalysisTool()], verbose=True, allow_delegation=False)

    def sentiment_analysis_specialist(self) -> Agent:
        """Sentiment analysis specialist."""
        from crewai import Agent
        return Agent(role='Sentiment Analysis Specialist', goal='Analyze emotional tone and sentiment in content with detailed reporting.', backstory='Expert in sentiment analysis with focus on emotional tone and mood detection.', tools=[SentimentTool(), TextAnalysisTool(), EnhancedAnalysisTool()], verbose=True, allow_delegation=False)

    def claim_extraction_specialist(self) -> Agent:
        """Claim extraction specialist."""
        from crewai import Agent
        return Agent(role='Claim Extraction Specialist', goal='Extract factual claims from content with high accuracy and context preservation.', backstory='Specialist in claim extraction with expertise in natural language processing and fact identification.', tools=[ClaimExtractorTool(), TextAnalysisTool(), EnhancedAnalysisTool(), LogicalFallacyTool()], verbose=True, allow_delegation=False)

    def trend_analysis_specialist(self) -> Agent:
        """Trend analysis specialist."""
        from crewai import Agent
        return Agent(role='Trend Analysis Specialist', goal='Analyze trends and patterns in content with forecasting capabilities.', backstory='Expert in trend analysis with focus on pattern recognition and forecasting.', tools=[TrendAnalysisTool(), TrendForecastingTool(), TextAnalysisTool(), EnhancedAnalysisTool()], verbose=True, allow_delegation=False)

    def multimodal_analysis_specialist(self) -> Agent:
        """Multimodal content analysis specialist."""
        from crewai import Agent
        return Agent(role='Multimodal Analysis Specialist', goal='Analyze content across multiple modalities (text, audio, video, images) with comprehensive insights.', backstory='Specialist in multimodal content analysis with expertise in cross-modal pattern recognition.', tools=[MultimodalAnalysisTool(), ImageAnalysisTool(), VideoFrameAnalysisTool(), AdvancedAudioAnalysisTool(), TextAnalysisTool(), EnhancedAnalysisTool()], verbose=True, allow_delegation=False)

    def social_graph_analysis_specialist(self) -> Agent:
        """Social graph analysis specialist."""
        from crewai import Agent
        return Agent(role='Social Graph Analysis Specialist', goal='Analyze social networks and relationships in content with graph-based insights.', backstory='Expert in social graph analysis with focus on network relationships and influence patterns.', tools=[SocialGraphAnalysisTool(), TextAnalysisTool(), EnhancedAnalysisTool()], verbose=True, allow_delegation=False)

    def live_stream_analysis_specialist(self) -> Agent:
        """Live stream analysis specialist."""
        from crewai import Agent
        return Agent(role='Live Stream Analysis Specialist', goal='Analyze live streaming content with real-time insights and monitoring.', backstory='Specialist in live stream analysis with expertise in real-time content processing.', tools=[LiveStreamAnalysisTool(), AdvancedAudioAnalysisTool(), TextAnalysisTool(), EnhancedAnalysisTool()], verbose=True, allow_delegation=False)