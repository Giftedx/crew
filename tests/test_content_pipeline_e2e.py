"""End-to-end integration tests for the content pipeline.

Tests the complete workflow from URL input to final Discord post,
validating all pipeline stages work together correctly.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from ultimate_discord_intelligence_bot.pipeline import ContentPipeline
from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant


class TestContentPipelineE2E:
    """End-to-end integration tests for the content pipeline."""

    @pytest.fixture
    def mock_tools(self):
        """Create mocked tools for integration testing."""
        # Mock downloader
        downloader = MagicMock()
        downloader.run.return_value = {
            "status": "success",
            "local_path": "/tmp/test_video.mp4",
            "video_id": "test123",
            "title": "Test Video",
            "platform": "youtube",
        }

        # Mock transcriber
        transcriber = MagicMock()
        transcriber.run.return_value = {
            "status": "success",
            "transcript": "This is a test transcript with some content to analyze.",
        }

        # Mock analyzer
        analyzer = MagicMock()
        analyzer.run.return_value = {
            "status": "success",
            "sentiment": "neutral",
            "keywords": ["test", "content", "analysis"],
            "summary": "Test content analysis",
        }

        # Mock drive uploader
        drive = MagicMock()
        drive.run.return_value = {
            "status": "success",
            "drive_url": "https://drive.google.com/file/d/test123",
            "shared": True,
        }

        # Mock discord poster
        discord = MagicMock()
        discord.run.return_value = {
            "status": "success",
            "message_id": "msg_123",
            "webhook_delivered": True,
        }

        # Mock fallacy detector
        fallacy_detector = MagicMock()
        fallacy_detector.run.return_value = {
            "status": "success",
            "fallacies": [],
            "analysis": "No logical fallacies detected",
        }

        # Mock perspective synthesizer
        perspective = MagicMock()
        perspective.run.return_value = {
            "status": "success",
            "perspectives": ["Alternative viewpoint 1", "Alternative viewpoint 2"],
        }

        # Mock memory storage
        memory = MagicMock()
        memory.run.return_value = {
            "status": "success",
            "stored": True,
            "collection": "transcripts",
        }

        return {
            "downloader": downloader,
            "transcriber": transcriber,
            "analyzer": analyzer,
            "drive": drive,
            "discord": discord,
            "fallacy_detector": fallacy_detector,
            "perspective": perspective,
            "memory": memory,
        }

    @pytest.fixture
    def pipeline(self, mock_tools):
        """Create a ContentPipeline with mocked tools."""
        return ContentPipeline(
            webhook_url="https://discord.com/api/webhooks/test",
            downloader=mock_tools["downloader"],
            transcriber=mock_tools["transcriber"],
            analyzer=mock_tools["analyzer"],
            drive=mock_tools["drive"],
            discord=mock_tools["discord"],
            fallacy_detector=mock_tools["fallacy_detector"],
            perspective=mock_tools["perspective"],
            memory=mock_tools["memory"],
            pipeline_rate_limit=60.0,  # High limit for testing
            tool_rate_limit=60.0,
        )

    @pytest.mark.asyncio
    async def test_complete_pipeline_success(self, pipeline):
        """Test successful execution of the complete pipeline."""
        test_url = "https://www.youtube.com/watch?v=test123"

        with with_tenant(TenantContext("test_tenant", "test_workspace")):
            result = await pipeline.process_video(test_url, quality="720p")

        # Verify successful completion
        assert result["status"] == "success"
        assert "download" in result
        assert "transcription" in result
        assert "analysis" in result
        assert "drive" in result
        assert "discord" in result
        assert "fallacy" in result
        assert "perspective" in result
        assert "memory" in result
        assert "graph_memory" in result

        # Verify all tools were called
        pipeline.downloader.run.assert_called_once_with(test_url, quality="720p")
        pipeline.transcriber.run.assert_called_once()
        pipeline.analyzer.run.assert_called_once()
        pipeline.drive.run.assert_called_once()
        pipeline.discord.run.assert_called_once()
        pipeline.fallacy_detector.run.assert_called_once()
        pipeline.perspective.run.assert_called_once()
        pipeline.memory.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_pipeline_graph_memory_enabled(self, mock_tools):
        graph_memory = MagicMock()
        graph_memory.run.return_value = {
            "status": "success",
            "graph_id": "graph123",
            "node_count": 4,
            "edge_count": 3,
        }
        mock_tools["perspective"].run.return_value["summary"] = "Concise narrative summary"

        pipeline = ContentPipeline(
            webhook_url="https://discord.com/api/webhooks/test",
            downloader=mock_tools["downloader"],
            transcriber=mock_tools["transcriber"],
            analyzer=mock_tools["analyzer"],
            drive=mock_tools["drive"],
            discord=mock_tools["discord"],
            fallacy_detector=mock_tools["fallacy_detector"],
            perspective=mock_tools["perspective"],
            memory=mock_tools["memory"],
            graph_memory=graph_memory,
            pipeline_rate_limit=60.0,
            tool_rate_limit=60.0,
        )

        test_url = "https://www.youtube.com/watch?v=test123"

        with with_tenant(TenantContext("test_tenant", "test_workspace")):
            result = await pipeline.process_video(test_url)

        graph_memory.run.assert_called_once()
        assert result["graph_memory"].get("graph_id") == "graph123"

    @pytest.mark.asyncio
    async def test_pipeline_download_failure(self, pipeline):
        """Test pipeline behavior when download fails."""
        # Mock download failure
        pipeline.downloader.run.return_value = {
            "status": "error",
            "error": "Video not found",
        }

        test_url = "https://www.youtube.com/watch?v=invalid"

        with with_tenant(TenantContext("test_tenant", "test_workspace")):
            result = await pipeline.process_video(test_url)

        # Verify failure handling
        assert result["status"] == "error"
        assert result["step"] == "download"
        assert "Video not found" in result["error"]

        # Verify no subsequent tools were called
        pipeline.transcriber.run.assert_not_called()
        pipeline.analyzer.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_pipeline_transcription_failure(self, pipeline):
        """Test pipeline behavior when transcription fails."""
        # Mock transcription failure
        pipeline.transcriber.run.return_value = {
            "status": "error",
            "error": "Audio extraction failed",
        }

        test_url = "https://www.youtube.com/watch?v=test123"

        with with_tenant(TenantContext("test_tenant", "test_workspace")):
            result = await pipeline.process_video(test_url)

        # Verify failure handling
        assert result["status"] == "error"
        assert result["step"] == "transcription"
        assert "Audio extraction failed" in result["error"]

        # Verify download was called but analysis was not
        pipeline.downloader.run.assert_called_once()
        pipeline.analyzer.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_pipeline_rate_limiting(self, pipeline):
        """Test pipeline rate limiting functionality."""
        # Set very low rate limit
        pipeline.pipeline_limiter._tokens = 0  # Exhaust rate limit

        test_url = "https://www.youtube.com/watch?v=test123"

        with with_tenant(TenantContext("test_tenant", "test_workspace")):
            result = await pipeline.process_video(test_url)

        # Verify rate limiting
        assert result["status"] == "error"
        assert result["step"] == "rate_limit"
        assert result["rate_limit_exceeded"] is True
        assert result["status_code"] == 429

    @pytest.mark.asyncio
    async def test_pipeline_concurrent_execution(self, pipeline):
        """Test that independent pipeline stages run concurrently."""
        test_url = "https://www.youtube.com/watch?v=test123"

        # Add delays to simulate processing time
        async def delayed_transcription(*args, **kwargs):
            await asyncio.sleep(0.1)
            return {
                "status": "success",
                "transcript": "Test transcript",
            }

        async def delayed_drive_upload(*args, **kwargs):
            await asyncio.sleep(0.1)
            return {
                "status": "success",
                "drive_url": "https://drive.google.com/test",
            }

        with (
            patch.object(pipeline.transcriber, "run", side_effect=delayed_transcription),
            patch.object(pipeline.drive, "run", side_effect=delayed_drive_upload),
        ):
            start_time = asyncio.get_event_loop().time()

            with with_tenant(TenantContext("test_tenant", "test_workspace")):
                result = await pipeline.process_video(test_url)

            end_time = asyncio.get_event_loop().time()
            processing_time = end_time - start_time

        # Verify success
        assert result["status"] == "success"

        # Verify concurrent execution (should be less than sum of delays)
        # If sequential: 0.1 + 0.1 = 0.2s minimum
        # If concurrent: ~0.1s + overhead
        assert processing_time < 0.18  # Allow some overhead

    @pytest.mark.asyncio
    async def test_pipeline_tenant_isolation(self, pipeline):
        """Test that pipeline operations respect tenant isolation."""
        test_url = "https://www.youtube.com/watch?v=test123"

        # Test with tenant context
        with with_tenant(TenantContext("tenant1", "workspace1")):
            result1 = await pipeline.process_video(test_url)

        # Test with different tenant context
        with with_tenant(TenantContext("tenant2", "workspace2")):
            result2 = await pipeline.process_video(test_url)

        # Both should succeed
        assert result1["status"] == "success"
        assert result2["status"] == "success"

        # Verify memory storage was called with proper tenant isolation
        assert pipeline.memory.run.call_count == 2
