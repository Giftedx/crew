"""
Test factories for creating test data objects.

This module provides factories for creating StepResult, Transcript, Analysis,
and other test objects with realistic data.
"""

from dataclasses import dataclass
from typing import Any
from unittest.mock import Mock

from ultimate_discord_intelligence_bot.step_result import StepResult


@dataclass
class Transcript:
    """Transcript data structure for testing."""

    text: str
    language: str
    confidence: float
    duration: float
    segments: list[dict[str, Any]]
    metadata: dict[str, Any]


@dataclass
class Analysis:
    """Analysis data structure for testing."""

    sentiment: str
    score: float
    topics: list[str]
    entities: list[dict[str, Any]]
    summary: str
    metadata: dict[str, Any]


class StepResultFactory:
    """Factory for creating StepResult objects for testing."""

    @staticmethod
    def success(data: Any = None, metadata: dict[str, Any] | None = None) -> StepResult:
        """Create a successful StepResult."""
        return StepResult.ok(data=data, metadata=metadata)

    @staticmethod
    def failure(error: str, status: str = "error", metadata: dict[str, Any] | None = None) -> StepResult:
        """Create a failed StepResult."""
        return StepResult.fail(error=error, status=status, metadata=metadata)

    @staticmethod
    def rate_limited(error: str = "Rate limit exceeded") -> StepResult:
        """Create a rate-limited StepResult."""
        return StepResult.fail(error=error, status="rate_limited")

    @staticmethod
    def retryable(error: str = "Temporary error") -> StepResult:
        """Create a retryable StepResult."""
        return StepResult.fail(error=error, status="retryable")

    @staticmethod
    def bad_request(error: str = "Invalid request") -> StepResult:
        """Create a bad request StepResult."""
        return StepResult.fail(error=error, status="bad_request")


class TranscriptFactory:
    """Factory for creating Transcript objects for testing."""

    @staticmethod
    def create(
        text: str = "This is a sample transcript text.",
        language: str = "en",
        confidence: float = 0.95,
        duration: float = 300.0,
        segments: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Transcript:
        """Create a Transcript object."""
        if segments is None:
            segments = [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "This is a sample",
                    "confidence": 0.95,
                },
                {
                    "start": 5.0,
                    "end": 10.0,
                    "text": "transcript text.",
                    "confidence": 0.90,
                },
            ]

        if metadata is None:
            metadata = {
                "source": "youtube",
                "video_id": "test_video_123",
                "channel": "Test Channel",
                "upload_date": "2024-01-01",
            }

        return Transcript(
            text=text,
            language=language,
            confidence=confidence,
            duration=duration,
            segments=segments,
            metadata=metadata,
        )

    @staticmethod
    def create_youtube_transcript() -> Transcript:
        """Create a YouTube-specific transcript."""
        return TranscriptFactory.create(
            text="Welcome to my YouTube channel. Today we're discussing AI and machine learning.",
            language="en",
            confidence=0.98,
            duration=600.0,
            segments=[
                {
                    "start": 0.0,
                    "end": 10.0,
                    "text": "Welcome to my YouTube channel.",
                    "confidence": 0.98,
                },
                {
                    "start": 10.0,
                    "end": 20.0,
                    "text": "Today we're discussing AI and machine learning.",
                    "confidence": 0.97,
                },
            ],
            metadata={
                "source": "youtube",
                "video_id": "youtube_video_456",
                "channel": "AI Tech Channel",
                "upload_date": "2024-01-15",
                "views": 10000,
                "likes": 500,
            },
        )

    @staticmethod
    def create_twitch_transcript() -> Transcript:
        """Create a Twitch-specific transcript."""
        return TranscriptFactory.create(
            text="Hey everyone, welcome to the stream! Let's talk about gaming and technology.",
            language="en",
            confidence=0.92,
            duration=1800.0,
            segments=[
                {
                    "start": 0.0,
                    "end": 15.0,
                    "text": "Hey everyone, welcome to the stream!",
                    "confidence": 0.92,
                },
                {
                    "start": 15.0,
                    "end": 30.0,
                    "text": "Let's talk about gaming and technology.",
                    "confidence": 0.90,
                },
            ],
            metadata={
                "source": "twitch",
                "stream_id": "twitch_stream_789",
                "channel": "GamingTech",
                "stream_date": "2024-01-20",
                "viewers": 500,
                "followers": 1000,
            },
        )

    @staticmethod
    def create_multilingual_transcript() -> Transcript:
        """Create a multilingual transcript."""
        return TranscriptFactory.create(
            text="Bonjour tout le monde. Hello everyone. Hola a todos.",
            language="mixed",
            confidence=0.85,
            duration=120.0,
            segments=[
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "Bonjour tout le monde.",
                    "confidence": 0.85,
                    "language": "fr",
                },
                {
                    "start": 5.0,
                    "end": 10.0,
                    "text": "Hello everyone.",
                    "confidence": 0.90,
                    "language": "en",
                },
                {
                    "start": 10.0,
                    "end": 15.0,
                    "text": "Hola a todos.",
                    "confidence": 0.88,
                    "language": "es",
                },
            ],
            metadata={
                "source": "multilingual",
                "languages": ["fr", "en", "es"],
                "translation_quality": 0.88,
            },
        )


class AnalysisFactory:
    """Factory for creating Analysis objects for testing."""

    @staticmethod
    def create(
        sentiment: str = "positive",
        score: float = 0.8,
        topics: list[str] | None = None,
        entities: list[dict[str, Any]] | None = None,
        summary: str = "This is a sample analysis summary.",
        metadata: dict[str, Any] | None = None,
    ) -> Analysis:
        """Create an Analysis object."""
        if topics is None:
            topics = ["technology", "AI", "machine learning"]

        if entities is None:
            entities = [
                {
                    "text": "artificial intelligence",
                    "type": "CONCEPT",
                    "confidence": 0.95,
                },
                {"text": "machine learning", "type": "CONCEPT", "confidence": 0.90},
            ]

        if metadata is None:
            metadata = {
                "analysis_type": "content_analysis",
                "model_version": "v1.0",
                "processing_time": 2.5,
                "confidence": 0.85,
            }

        return Analysis(
            sentiment=sentiment,
            score=score,
            topics=topics,
            entities=entities,
            summary=summary,
            metadata=metadata,
        )

    @staticmethod
    def create_debate_analysis() -> Analysis:
        """Create a debate-specific analysis."""
        return AnalysisFactory.create(
            sentiment="neutral",
            score=0.6,
            topics=["politics", "debate", "policy", "government"],
            entities=[
                {"text": "president", "type": "PERSON", "confidence": 0.95},
                {"text": "congress", "type": "ORGANIZATION", "confidence": 0.90},
                {"text": "healthcare", "type": "CONCEPT", "confidence": 0.85},
            ],
            summary="This debate covers political topics including healthcare policy and government structure.",
            metadata={
                "analysis_type": "debate_analysis",
                "debate_format": "presidential",
                "participants": 2,
                "duration": 1800.0,
                "fact_check_score": 0.75,
            },
        )

    @staticmethod
    def create_educational_analysis() -> Analysis:
        """Create an educational content analysis."""
        return AnalysisFactory.create(
            sentiment="positive",
            score=0.9,
            topics=["education", "learning", "tutorial", "technology"],
            entities=[
                {"text": "Python", "type": "TECHNOLOGY", "confidence": 0.98},
                {"text": "programming", "type": "CONCEPT", "confidence": 0.95},
                {"text": "tutorial", "type": "CONTENT_TYPE", "confidence": 0.90},
            ],
            summary="This educational content provides a comprehensive tutorial on Python programming.",
            metadata={
                "analysis_type": "educational_analysis",
                "content_type": "tutorial",
                "difficulty_level": "beginner",
                "learning_objectives": ["Python basics", "Programming concepts"],
                "estimated_time": 3600.0,
            },
        )

    @staticmethod
    def create_negative_sentiment_analysis() -> Analysis:
        """Create a negative sentiment analysis."""
        return AnalysisFactory.create(
            sentiment="negative",
            score=0.2,
            topics=["complaint", "issue", "problem", "dissatisfaction"],
            entities=[
                {"text": "customer service", "type": "CONCEPT", "confidence": 0.90},
                {"text": "refund", "type": "ACTION", "confidence": 0.85},
            ],
            summary="This content expresses dissatisfaction with customer service and requests a refund.",
            metadata={
                "analysis_type": "sentiment_analysis",
                "emotion": "anger",
                "urgency": "high",
                "action_required": True,
            },
        )


class MockFactory:
    """Factory for creating mock objects for testing."""

    @staticmethod
    def create_mock_vector_store() -> Mock:
        """Create a mock vector store."""

        mock_store = Mock()
        mock_store.store.return_value = StepResultFactory.success(data={"stored": True})
        mock_store.retrieve.return_value = StepResultFactory.success(data={"content": "retrieved"})
        mock_store.search.return_value = StepResultFactory.success(data={"results": []})
        return mock_store

    @staticmethod
    def create_mock_memory_service() -> Mock:
        """Create a mock memory service."""

        mock_service = Mock()
        mock_service.store_content.return_value = StepResultFactory.success(data={"stored": True})
        mock_service.retrieve_content.return_value = StepResultFactory.success(data={"content": "retrieved"})
        mock_service.search_content.return_value = StepResultFactory.success(data={"results": []})
        return mock_service

    @staticmethod
    def create_mock_llm_client() -> Mock:
        """Create a mock LLM client."""

        mock_client = Mock()
        mock_client.generate.return_value = StepResultFactory.success(data={"text": "Generated response"})
        mock_client.embed.return_value = StepResultFactory.success(data={"embeddings": [0.1, 0.2, 0.3]})
        return mock_client

    @staticmethod
    def create_mock_discord_bot() -> Mock:
        """Create a mock Discord bot."""

        mock_bot = Mock()
        mock_bot.send_message.return_value = StepResultFactory.success(data={"sent": True})
        mock_bot.get_channel.return_value = Mock()
        mock_bot.get_user.return_value = Mock()
        return mock_bot


class TestDataFactory:
    """Factory for creating test data sets."""

    @staticmethod
    def create_sample_urls() -> list[str]:
        """Create a list of sample URLs for testing."""
        return [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.twitch.tv/videos/123456789",
            "https://www.tiktok.com/@user/video/123456789",
            "https://www.reddit.com/r/technology/comments/abc123",
            "https://www.linkedin.com/posts/activity-123456789",
        ]

    @staticmethod
    def create_sample_tenants() -> list[dict[str, str]]:
        """Create a list of sample tenant configurations."""
        return [
            {"tenant": "tenant_a", "workspace": "workspace_a"},
            {"tenant": "tenant_b", "workspace": "workspace_b"},
            {"tenant": "tenant_c", "workspace": "workspace_c"},
        ]

    @staticmethod
    def create_sample_content_types() -> list[str]:
        """Create a list of sample content types."""
        return [
            "debate",
            "tutorial",
            "news",
            "entertainment",
            "educational",
            "podcast",
            "interview",
            "review",
        ]

    @staticmethod
    def create_sample_analysis_requests() -> list[dict[str, Any]]:
        """Create a list of sample analysis requests."""
        return [
            {
                "url": "https://www.youtube.com/watch?v=test1",
                "analysis_type": "debate",
                "depth": "comprehensive",
                "tenant": "tenant_a",
                "workspace": "workspace_a",
            },
            {
                "url": "https://www.twitch.tv/videos/test2",
                "analysis_type": "sentiment",
                "depth": "basic",
                "tenant": "tenant_b",
                "workspace": "workspace_b",
            },
            {
                "url": "https://www.tiktok.com/@user/video/test3",
                "analysis_type": "fact_check",
                "depth": "detailed",
                "tenant": "tenant_c",
                "workspace": "workspace_c",
            },
        ]
