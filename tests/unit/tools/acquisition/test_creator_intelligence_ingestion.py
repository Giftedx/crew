"""Tests for Creator Intelligence Ingestion Tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ingest.providers.twitch import ClipMetadata
from ingest.providers.youtube import VideoMetadata
from mcp_server.tools.creator_intelligence_ingestion import (
    CreatorIntelligenceIngestionTools,
    IngestedContent,
    get_ingestion_tools,
)


class TestIngestedContent:
    """Test ingested content data structure."""

    def test_create_ingested_content(self) -> None:
        """Test creating ingested content object."""
        content = IngestedContent(
            platform="youtube",
            content_id="abc123",
            content_type="episode",
            creator_id="channel_id",
            title="Test Video",
            url="https://youtube.com/watch?v=abc123",
            published_at="2025-01-17T12:00:00Z",
            duration_seconds=600,
            transcript="This is a test transcript.",
            metadata={"channel": "Test Channel"},
        )
        assert content.platform == "youtube"
        assert content.content_id == "abc123"
        assert content.duration_seconds == 600
        assert content.transcript is not None


class TestCreatorIntelligenceIngestionTools:
    """Test ingestion tools functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.tools = CreatorIntelligenceIngestionTools(sqlite_path=":memory:", enable_vector_storage=False)

    @patch("ingest.providers.youtube.fetch_metadata")
    @patch("ingest.providers.youtube.fetch_transcript")
    def test_ingest_youtube_video_success(
        self, mock_fetch_transcript: MagicMock, mock_fetch_metadata: MagicMock
    ) -> None:
        """Test successful YouTube video ingestion."""
        mock_fetch_metadata.return_value = VideoMetadata(
            id="test_video_id",
            title="Test Video Title",
            channel="Test Channel",
            channel_id="test_channel_id",
            published_at="2025-01-17T12:00:00Z",
            duration=600.0,
            url="https://youtube.com/watch?v=test_video_id",
            thumbnails=["https://img.youtube.com/vi/test_video_id/maxresdefault.jpg"],
        )
        mock_fetch_transcript.return_value = "This is a test transcript of the video content."
        result = self.tools.ingest_youtube_video(
            url="https://youtube.com/watch?v=test_video_id",
            tenant="test_tenant",
            workspace="test_workspace",
            fetch_transcript=True,
        )
        assert result.success
        assert result.data is not None
        assert result.data["platform"] == "youtube"
        assert result.data["content_id"] == "test_video_id"
        assert result.data["title"] == "Test Video Title"
        assert result.data["has_transcript"] is True
        assert result.data["transcript_length"] > 0

    @patch("ingest.providers.youtube.fetch_metadata")
    def test_ingest_youtube_video_metadata_failure(self, mock_fetch_metadata: MagicMock) -> None:
        """Test YouTube ingestion with metadata fetch failure."""
        mock_fetch_metadata.side_effect = Exception("API rate limit exceeded")
        result = self.tools.ingest_youtube_video(
            url="https://youtube.com/watch?v=test_video_id", tenant="test_tenant", workspace="test_workspace"
        )
        assert not result.success
        assert result.status == "retryable"
        assert "Failed to fetch YouTube metadata" in result.error

    @patch("ingest.providers.youtube.fetch_metadata")
    @patch("ingest.providers.youtube.fetch_transcript")
    def test_ingest_youtube_video_without_transcript(
        self, mock_fetch_transcript: MagicMock, mock_fetch_metadata: MagicMock
    ) -> None:
        """Test YouTube ingestion without transcript."""
        mock_fetch_metadata.return_value = VideoMetadata(
            id="test_id",
            title="Test",
            channel="Channel",
            channel_id="ch123",
            published_at=None,
            duration=None,
            url="https://youtube.com/watch?v=test_id",
            thumbnails=[],
        )
        result = self.tools.ingest_youtube_video(
            url="https://youtube.com/watch?v=test_id",
            tenant="test_tenant",
            workspace="test_workspace",
            fetch_transcript=False,
        )
        mock_fetch_transcript.assert_not_called()
        assert result.success
        assert result.data["has_transcript"] is False

    @patch("ingest.providers.twitch.fetch_metadata")
    @patch("ingest.providers.twitch.fetch_transcript")
    def test_ingest_twitch_clip_success(self, mock_fetch_transcript: MagicMock, mock_fetch_metadata: MagicMock) -> None:
        """Test successful Twitch clip ingestion."""
        mock_fetch_metadata.return_value = ClipMetadata(
            id="test_clip_id",
            title="Amazing Clip",
            streamer="test_streamer",
            published_at="2025-01-17T12:00:00Z",
            duration=30.0,
            url="https://clips.twitch.tv/test_clip_id",
        )
        mock_fetch_transcript.return_value = "clip"
        result = self.tools.ingest_twitch_clip(
            url="https://clips.twitch.tv/test_clip_id", tenant="test_tenant", workspace="test_workspace"
        )
        assert result.success
        assert result.data is not None
        assert result.data["platform"] == "twitch"
        assert result.data["content_type"] == "clip"
        assert result.data["creator_id"] == "test_streamer"

    @patch("ingest.providers.twitch.fetch_metadata")
    def test_ingest_twitch_clip_failure(self, mock_fetch_metadata: MagicMock) -> None:
        """Test Twitch ingestion failure."""
        mock_fetch_metadata.side_effect = Exception("Network error")
        result = self.tools.ingest_twitch_clip(
            url="https://clips.twitch.tv/test_clip_id", tenant="test_tenant", workspace="test_workspace"
        )
        assert not result.success
        assert result.status == "retryable"

    def test_batch_ingest_not_implemented(self) -> None:
        """Test batch ingestion returns not_implemented status."""
        result = self.tools.batch_ingest_youtube_channel(
            channel_url="https://youtube.com/@test_channel",
            tenant="test_tenant",
            workspace="test_workspace",
            max_videos=10,
        )
        assert not result.success
        assert result.status == "not_implemented"
        assert "YouTube Data API" in result.error

    def test_compute_content_hash(self) -> None:
        """Test content hash computation for provenance."""
        content = IngestedContent(
            platform="youtube",
            content_id="abc123",
            content_type="episode",
            creator_id="creator",
            title="Test",
            url="https://youtube.com/test",
            published_at=None,
            duration_seconds=None,
            transcript=None,
            metadata={},
        )
        hash1 = self.tools._compute_content_hash(content)
        hash2 = self.tools._compute_content_hash(content)
        assert hash1 == hash2
        assert len(hash1) == 64

    def test_get_platform_tos_url(self) -> None:
        """Test platform TOS URL retrieval."""
        youtube_tos = self.tools._get_platform_tos_url("youtube")
        twitch_tos = self.tools._get_platform_tos_url("twitch")
        unknown_tos = self.tools._get_platform_tos_url("unknown_platform")
        assert "youtube.com" in youtube_tos
        assert "twitch.tv" in twitch_tos
        assert unknown_tos == ""


class TestIngestionToolsFactory:
    """Test ingestion tools factory function."""

    def test_get_ingestion_tools(self) -> None:
        """Test factory function."""
        tools = get_ingestion_tools(sqlite_path=":memory:", enable_vector_storage=False)
        assert isinstance(tools, CreatorIntelligenceIngestionTools)
        assert tools.sqlite_path == ":memory:"
        assert tools.enable_vector_storage is False


class TestIngestionWithVectorStorage:
    """Test ingestion with vector storage enabled."""

    def setup_method(self) -> None:
        """Set up test fixtures with vector storage."""
        self.tools = CreatorIntelligenceIngestionTools(sqlite_path=":memory:", enable_vector_storage=True)

    def test_vector_storage_initialization(self) -> None:
        """Test that vector storage components are initialized."""
        assert self.tools.collection_manager is not None
        assert self.tools.embedding_service is not None

    @patch("ingest.providers.youtube.fetch_metadata")
    @patch("ingest.providers.youtube.fetch_transcript")
    def test_ingest_with_vector_storage(self, mock_fetch_transcript: MagicMock, mock_fetch_metadata: MagicMock) -> None:
        """Test ingestion stores content in vector DB."""
        mock_fetch_metadata.return_value = VideoMetadata(
            id="vec_test_id",
            title="Vector Test",
            channel="Test Channel",
            channel_id="ch123",
            published_at="2025-01-17T12:00:00Z",
            duration=300.0,
            url="https://youtube.com/watch?v=vec_test_id",
            thumbnails=[],
        )
        mock_fetch_transcript.return_value = "This is a transcript for vector embedding testing."
        result = self.tools.ingest_youtube_video(
            url="https://youtube.com/watch?v=vec_test_id",
            tenant="test_tenant",
            workspace="test_workspace",
            fetch_transcript=True,
        )
        assert result.success
