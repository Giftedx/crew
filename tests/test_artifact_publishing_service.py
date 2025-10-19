"""Tests for Artifact Publishing Service."""

from __future__ import annotations

import pytest

from publishing.artifact_publishing_service import (
    ArtifactPublishingService,
    PublishingArtifact,
    get_artifact_publishing_service,
)


class TestArtifactPublishingService:
    """Test artifact publishing service functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = ArtifactPublishingService(cache_size=100)

    def test_initialization(self) -> None:
        """Test service initialization."""
        assert self.service.cache_size == 100
        assert len(self.service._publishing_cache) == 0
        assert self.service._discord_webhook_url is None
        assert self.service._discord_bot_token is None

    def test_publish_fallback(self) -> None:
        """Test publishing with fallback method."""
        artifact = PublishingArtifact(
            artifact_type="test",
            title="Test Artifact",
            content="This is test content for publishing.",
            metadata={"test": True},
        )

        result = self.service.publish_artifact(artifact, use_cache=False)

        # Should succeed with webhook fallback
        assert result.success
        assert result.data is not None
        assert "success" in result.data

    def test_publish_empty_artifact(self) -> None:
        """Test handling of empty artifact."""
        result = self.service.publish_artifact(None, use_cache=False)  # type: ignore[arg-type]

        assert not result.success
        assert result.status == "bad_request"
        assert "must have" in result.error.lower()

    def test_publish_artifact_without_content(self) -> None:
        """Test handling of artifact without content."""
        artifact = PublishingArtifact(
            artifact_type="test",
            title="Test Artifact",
            content="",  # Empty content
            metadata={},
        )

        result = self.service.publish_artifact(artifact, use_cache=False)

        assert not result.success
        assert result.status == "bad_request"
        assert "must have" in result.error.lower()

    def test_publishing_cache_hit(self) -> None:
        """Test publishing cache functionality."""
        artifact = PublishingArtifact(
            artifact_type="test",
            title="Cached Artifact",
            content="This content will be cached.",
            metadata={},
        )

        # First publish - cache miss
        result1 = self.service.publish_artifact(artifact, use_cache=True)
        assert result1.success
        assert result1.data["cache_hit"] is False

        # Second publish - should be cache hit
        result2 = self.service.publish_artifact(artifact, use_cache=True)
        assert result2.success
        assert result2.data["cache_hit"] is True

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        # Add some cached publishing results
        artifact = PublishingArtifact(
            artifact_type="test",
            title="Test",
            content="Content",
            metadata={},
        )
        self.service.publish_artifact(artifact, use_cache=True)

        assert len(self.service._publishing_cache) > 0

        # Clear cache
        result = self.service.clear_cache()

        assert result.success
        assert result.data["cleared_entries"] > 0
        assert len(self.service._publishing_cache) == 0

    def test_get_cache_stats(self) -> None:
        """Test cache statistics."""
        # Add some cached publishing results
        artifact = PublishingArtifact(
            artifact_type="test",
            title="Test",
            content="Content",
            metadata={},
        )
        self.service.publish_artifact(artifact, use_cache=True)

        result = self.service.get_cache_stats()

        assert result.success
        assert result.data is not None
        assert "total_cached" in result.data
        assert "cache_size_limit" in result.data
        assert "platforms_cached" in result.data

        assert result.data["total_cached"] >= 1
        assert result.data["cache_size_limit"] == 100

    def test_publish_report(self) -> None:
        """Test report publishing."""
        report_data = {
            "episode_title": "Test Episode",
            "platform": "youtube",
            "duration": 1800.0,
            "sentiment": {"sentiment": "positive", "confidence": 0.8},
        }

        result = self.service.publish_report(report_data, report_type="analysis")

        assert result.success
        assert result.data is not None
        assert "success" in result.data

    def test_publish_highlight_summary(self) -> None:
        """Test highlight summary publishing."""
        highlights = [
            {
                "start_time": 0.0,
                "end_time": 30.0,
                "highlight_score": 0.9,
                "transcript_text": "This is an exciting moment!",
            },
            {
                "start_time": 60.0,
                "end_time": 90.0,
                "highlight_score": 0.8,
                "transcript_text": "Amazing discussion here.",
            },
        ]

        episode_info = {
            "title": "Test Episode",
            "platform": "youtube",
        }

        result = self.service.publish_highlight_summary(highlights, episode_info)

        assert result.success
        assert result.data is not None

    def test_publish_claim_summary(self) -> None:
        """Test claim and quote summary publishing."""
        claims = [
            {
                "text": "AI will change everything",
                "speaker": "Host",
                "confidence": 0.85,
            }
        ]

        quotes = [
            {
                "text": "This is a memorable quote",
                "speaker": "Guest",
                "confidence": 0.9,
            }
        ]

        episode_info = {
            "title": "Test Episode",
            "platform": "youtube",
        }

        result = self.service.publish_claim_summary(claims, quotes, episode_info)

        assert result.success
        assert result.data is not None

    def test_discord_embed_formatting(self) -> None:
        """Test Discord embed formatting."""
        artifact = PublishingArtifact(
            artifact_type="highlight_summary",
            title="Test Highlights",
            content="This is test highlight content",
            metadata={"highlight_count": 5},
        )

        embed = self.service._format_discord_embed(artifact)

        assert "title" in embed
        assert "description" in embed
        assert "color" in embed
        assert "footer" in embed
        assert embed["title"] == "Test Highlights"

    def test_content_truncation(self) -> None:
        """Test content truncation for Discord limits."""
        long_content = "A" * 3000  # Longer than Discord limit

        truncated = self.service._truncate_content(long_content, 2000)

        assert len(truncated) <= 2003  # 2000 + "..."
        assert truncated.endswith("...")

    def test_title_generation(self) -> None:
        """Test automatic title generation."""
        report_data = {
            "episode_title": "Amazing Episode",
            "platform": "youtube",
        }

        title = self.service._generate_report_title(report_data, "analysis")

        assert "Amazing Episode" in title
        assert "analysis" in title.lower()


class TestArtifactPublishingServiceSingleton:
    """Test singleton instance management."""

    def test_get_artifact_publishing_service(self) -> None:
        """Test getting singleton instance."""
        service1 = get_artifact_publishing_service()
        service2 = get_artifact_publishing_service()

        # Should return same instance
        assert service1 is service2
        assert isinstance(service1, ArtifactPublishingService)


class TestPublishingArtifact:
    """Test publishing artifact data structure."""

    def test_create_publishing_artifact(self) -> None:
        """Test creating publishing artifact."""
        artifact = PublishingArtifact(
            artifact_type="report",
            title="Test Report",
            content="This is test report content",
            metadata={"test": True},
            platform="discord",
            priority=5,
            created_at=1234567890.0,
        )

        assert artifact.artifact_type == "report"
        assert artifact.title == "Test Report"
        assert artifact.content == "This is test report content"
        assert artifact.metadata == {"test": True}
        assert artifact.platform == "discord"
        assert artifact.priority == 5
        assert artifact.created_at == 1234567890.0

    def test_publishing_artifact_defaults(self) -> None:
        """Test publishing artifact with default values."""
        import time

        artifact = PublishingArtifact(
            artifact_type="report",
            title="Test Report",
            content="Content",
            metadata={},
        )

        assert artifact.platform == "discord"  # Default platform
        assert artifact.priority == 1  # Default priority
        assert artifact.created_at > time.time() - 60  # Should be recent


class TestArtifactPublishingWithMocking:
    """Test publishing service with mocked dependencies."""

    def test_publish_to_discord_webhook_mock(self) -> None:
        """Test Discord webhook publishing with mocking."""
        artifact = PublishingArtifact(
            artifact_type="test",
            title="Test Artifact",
            content="Test content",
            metadata={},
        )

        # Mock requests.post
        with pytest.importorskip("unittest.mock").patch("requests.post") as mock_post:
            mock_response = pytest.importorskip("unittest.mock").MagicMock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            # Set webhook URL
            self.service._discord_webhook_url = "https://discord.com/api/webhooks/test"

            result = self.service._publish_to_discord_webhook(artifact)

            assert result.success is True
            assert result.published_at > 0
            mock_post.assert_called_once()

    def test_publish_report_formatting(self) -> None:
        """Test report content formatting."""
        report_data = {
            "episode_title": "Test Episode",
            "platform": "youtube",
            "duration": 1800.0,
            "sentiment": {"sentiment": "positive", "confidence": 0.8},
        }

        formatted_content = self.service._format_report_content(report_data, "analysis")

        assert "Analysis Summary" in formatted_content
        assert "Sentiment: positive" in formatted_content
        assert "Duration: 1800.0s" in formatted_content
        assert "Platform: youtube" in formatted_content

    def test_highlight_summary_formatting(self) -> None:
        """Test highlight summary formatting."""
        highlights = [
            {
                "start_time": 0.0,
                "end_time": 30.0,
                "highlight_score": 0.9,
                "transcript_text": "This is an exciting moment!",
            }
        ]

        episode_info = {"title": "Test Episode"}

        formatted_summary = self.service._format_highlight_summary(highlights, episode_info)

        assert "Highlight Summary: Test Episode" in formatted_summary
        assert "exciting moment" in formatted_summary
        assert "Score: 0.90" in formatted_summary

    def test_claim_quote_summary_formatting(self) -> None:
        """Test claim and quote summary formatting."""
        claims = [
            {
                "text": "AI will change everything",
                "speaker": "Host",
                "confidence": 0.85,
            }
        ]

        quotes = [
            {
                "text": "This is a memorable quote",
                "speaker": "Guest",
                "confidence": 0.9,
            }
        ]

        episode_info = {"title": "Test Episode"}

        formatted_summary = self.service._format_claim_quote_summary(claims, quotes, episode_info)

        assert "Claims & Quotes: Test Episode" in formatted_summary
        assert "AI will change everything" in formatted_summary
        assert "memorable quote" in formatted_summary
        assert "Host:" in formatted_summary
        assert "Guest:" in formatted_summary
