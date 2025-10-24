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

        # Mock transcriber - Use a longer transcript to pass quality filtering (needs 500+ words, 10+ sentences)
        transcriber = MagicMock()
        long_transcript = (
            "This is a comprehensive test transcript with substantial content to analyze. "
            "The speaker discusses various important topics in great detail throughout the presentation. "
            "First, they introduce the main theme and provide essential background context. "
            "Then, they explore multiple perspectives on the subject matter, offering nuanced insights. "
            "The analysis includes both theoretical frameworks and practical applications. "
            "Several key points are emphasized to help the audience understand the core concepts. "
            "The presenter also addresses common misconceptions and clarifies complex ideas. "
            "Throughout the discussion, evidence is provided to support the main arguments. "
            "Multiple examples illustrate the principles being explained in the presentation. "
            "The speaker connects these ideas to real-world scenarios and current events. "
            "Additional context is provided about the historical development of these concepts. "
            "The presentation builds upon foundational knowledge while introducing new insights. "
            "Critical thinking is encouraged as the speaker explores different viewpoints. "
            "The audience is guided through a logical progression of interconnected ideas. "
            "Key terminology is defined clearly to ensure common understanding. "
            "The speaker acknowledges limitations and areas requiring further research. "
            "Practical implications are discussed for implementing these concepts effectively. "
            "The presentation maintains academic rigor while remaining accessible to the audience. "
            "Various stakeholders and their perspectives are considered in the analysis. "
            "The speaker concludes by summarizing the main points and suggesting next steps. "
            "This comprehensive approach ensures that the content meets quality standards for processing. "
            "The transcript demonstrates coherent structure, topical clarity, and substantive depth. "
            "All quality metrics should indicate this is high-quality content worthy of full analysis. "
            "The word count exceeds the minimum threshold of five hundred words required. "
            "Sentence count also surpasses the minimum of ten sentences needed for processing. "
            "Language quality is maintained throughout with proper grammar and vocabulary. "
            "Coherence between sentences creates a logical flow of information. "
            "Topic clarity is evident as the speaker maintains focus on the central theme. "
            "This ensures the content will bypass the lightweight processing path. "
            "Instead, it will proceed through the complete pipeline for thorough analysis. "
            "All downstream tools will receive this rich content for processing. "
            "The analysis phase will extract sentiment, keywords, and generate insights. "
            "Fallacy detection will examine the logical structure of the arguments. "
            "Perspective synthesis will identify alternative viewpoints and considerations. "
            "Memory storage will preserve this valuable content for future retrieval. "
            "Graph memory will map relationships between concepts and entities. "
            "Discord posting will share the complete analysis with the community. "
            "Every pipeline stage will contribute to comprehensive content understanding. "
            "This test validates the full end-to-end integration of all components. "
            "The quality filtering mechanism correctly identifies this as high-quality content. "
            "Processing continues through all stages without triggering lightweight bypass. "
            "This ensures the test accurately reflects production pipeline behavior. "
            "All assertions will verify the expected behavior of each pipeline component. "
            "The test demonstrates the system's ability to handle substantial content effectively. "
            "Integration between components is validated through this comprehensive test case. "
            "The final result will include outputs from all pipeline stages as expected. "
            "This transcript provides the foundation for thorough integration testing. "
            "Quality thresholds are exceeded, ensuring full pipeline execution occurs. "
            "The content is sufficiently rich to warrant complete analytical processing. "
            "All quality metrics indicate this material deserves comprehensive treatment."
        )
        transcriber.run.return_value = {
            "status": "success",
            "transcript": long_transcript,
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
    async def test_complete_pipeline_success(self, pipeline, monkeypatch):
        """Test successful execution of the complete pipeline."""
        # Disable quality filtering for this test to focus on pipeline integration
        monkeypatch.setenv("ENABLE_QUALITY_FILTERING", "0")

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
    async def test_pipeline_graph_memory_enabled(self, mock_tools, monkeypatch):
        # Disable quality filtering for this test to focus on graph memory integration
        monkeypatch.setenv("ENABLE_QUALITY_FILTERING", "0")

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
    async def test_pipeline_tenant_isolation(self, pipeline, monkeypatch):
        """Test that pipeline operations respect tenant isolation."""
        # Disable quality filtering for this test to focus on tenant isolation
        monkeypatch.setenv("ENABLE_QUALITY_FILTERING", "0")

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
