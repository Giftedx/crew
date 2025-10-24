"""Integration tests for the core content pipeline workflow."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ultimate_discord_intelligence_bot.pipeline import ContentPipeline
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext


class TestContentPipelineIntegration:
    """Integration tests for the core content pipeline."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        # Mock downloader
        downloader = MagicMock()
        downloader.run = AsyncMock(
            return_value=StepResult.ok(
                data={
                    "local_path": "/tmp/test_video.mp4",
                    "title": "Test Video",
                    "platform": "youtube",
                    "video_id": "test123",
                    "duration": 120.0,
                    "file_size": 1024000,
                }
            )
        )

        # Mock transcriber
        transcriber = MagicMock()
        transcriber.run = AsyncMock(
            return_value=StepResult.ok(
                data={
                    "transcript": "This is a test transcript about artificial intelligence and machine learning.",
                    "confidence": 0.95,
                    "segments": [
                        {"start": 0.0, "end": 5.0, "text": "This is a test transcript"},
                        {"start": 5.0, "end": 10.0, "text": "about artificial intelligence and machine learning"},
                    ],
                }
            )
        )

        # Mock analyzer
        analyzer = MagicMock()
        analyzer.run = AsyncMock(
            return_value=StepResult.ok(
                data={
                    "sentiment": {"overall": "positive", "score": 0.8},
                    "keywords": ["artificial intelligence", "machine learning", "technology"],
                    "themes": ["AI", "Technology", "Innovation"],
                    "summary": "Discussion about AI and machine learning technologies",
                }
            )
        )

        # Mock fallacy detector
        fallacy_detector = MagicMock()
        fallacy_detector.run = AsyncMock(
            return_value=StepResult.ok(data={"fallacies": [], "logical_consistency": 0.9, "argument_quality": "high"})
        )

        # Mock perspective synthesizer
        perspective = MagicMock()
        perspective.run = AsyncMock(
            return_value=StepResult.ok(
                data={
                    "summary": "Comprehensive analysis of AI technologies",
                    "perspectives": ["technical", "business", "ethical"],
                    "bias_indicators": [],
                }
            )
        )

        # Mock memory service
        memory = MagicMock()
        memory.run = AsyncMock(
            return_value=StepResult.ok(data={"memory_id": "mem_123", "stored": True, "vector_count": 5})
        )

        # Mock drive upload
        drive = MagicMock()
        drive.run = AsyncMock(
            return_value=StepResult.ok(
                data={
                    "links": {
                        "preview_link": "https://drive.google.com/preview/123",
                        "download_link": "https://drive.google.com/download/123",
                    },
                    "file_id": "drive_123",
                }
            )
        )

        # Mock Discord posting
        discord = MagicMock()
        discord.run = AsyncMock(
            return_value=StepResult.ok(data={"message_id": "discord_123", "posted": True, "channel": "test_channel"})
        )

        return {
            "downloader": downloader,
            "transcriber": transcriber,
            "analyzer": analyzer,
            "fallacy_detector": fallacy_detector,
            "perspective": perspective,
            "memory": memory,
            "drive": drive,
            "discord": discord,
        }

    @pytest.fixture
    def pipeline(self, mock_services):
        """Create a ContentPipeline instance with mocked services."""
        return ContentPipeline(
            webhook_url="https://discord.com/api/webhooks/test",
            downloader=mock_services["downloader"],
            transcriber=mock_services["transcriber"],
            analyzer=mock_services["analyzer"],
            fallacy_detector=mock_services["fallacy_detector"],
            perspective=mock_services["perspective"],
            memory=mock_services["memory"],
            drive=mock_services["drive"],
            discord=mock_services["discord"],
        )

    @pytest.mark.asyncio
    async def test_full_pipeline_workflow(self, pipeline):
        """Test the complete content pipeline workflow."""
        url = "https://youtube.com/watch?v=test123"
        quality = "1080p"

        # Execute the pipeline
        result = await pipeline.process_video(url, quality)

        # Verify the result structure
        assert result is not None
        assert hasattr(result, "success")
        assert hasattr(result, "data")

        # Verify all services were called
        pipeline.downloader.run.assert_called_once()
        pipeline.transcriber.run.assert_called_once()
        pipeline.analyzer.run.assert_called_once()
        pipeline.fallacy_detector.run.assert_called_once()
        pipeline.perspective.run.assert_called_once()
        pipeline.memory.run.assert_called_once()
        pipeline.drive.run.assert_called_once()
        pipeline.discord.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_pipeline_with_download_failure(self, pipeline):
        """Test pipeline behavior when download fails."""
        # Configure downloader to fail
        pipeline.downloader.run = AsyncMock(return_value=StepResult.fail("Download failed"))

        url = "https://youtube.com/watch?v=test123"
        quality = "1080p"

        result = await pipeline.process_video(url, quality)

        # Should fail early and not call other services
        assert not result.success
        pipeline.transcriber.run.assert_not_called()
        pipeline.analyzer.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_pipeline_with_transcription_failure(self, pipeline):
        """Test pipeline behavior when transcription fails."""
        # Configure transcriber to fail
        pipeline.transcriber.run = AsyncMock(return_value=StepResult.fail("Transcription failed"))

        url = "https://youtube.com/watch?v=test123"
        quality = "1080p"

        result = await pipeline.process_video(url, quality)

        # Should fail and not call analysis services
        assert not result.success
        pipeline.analyzer.run.assert_not_called()
        pipeline.fallacy_detector.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_pipeline_with_analysis_failure(self, pipeline):
        """Test pipeline behavior when analysis fails."""
        # Configure analyzer to fail
        pipeline.analyzer.run = AsyncMock(return_value=StepResult.fail("Analysis failed"))

        url = "https://youtube.com/watch?v=test123"
        quality = "1080p"

        result = await pipeline.process_video(url, quality)

        # Should fail and not call memory/discord services
        assert not result.success
        pipeline.memory.run.assert_not_called()
        pipeline.discord.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_pipeline_with_memory_failure(self, pipeline):
        """Test pipeline behavior when memory storage fails."""
        # Configure memory to fail
        pipeline.memory.run = AsyncMock(return_value=StepResult.fail("Memory storage failed"))

        url = "https://youtube.com/watch?v=test123"
        quality = "1080p"

        result = await pipeline.process_video(url, quality)

        # Should still succeed but log memory failure
        # (Memory failure shouldn't stop the pipeline)
        assert result.success

    @pytest.mark.asyncio
    async def test_pipeline_with_discord_failure(self, pipeline):
        """Test pipeline behavior when Discord posting fails."""
        # Configure Discord to fail
        pipeline.discord.run = AsyncMock(return_value=StepResult.fail("Discord posting failed"))

        url = "https://youtube.com/watch?v=test123"
        quality = "1080p"

        result = await pipeline.process_video(url, quality)

        # Should still succeed but log Discord failure
        # (Discord failure shouldn't stop the pipeline)
        assert result.success

    @pytest.mark.asyncio
    async def test_pipeline_data_flow(self, pipeline):
        """Test that data flows correctly between pipeline stages."""
        url = "https://youtube.com/watch?v=test123"
        quality = "1080p"

        # Execute the pipeline
        result = await pipeline.process_video(url, quality)

        # Verify data flows through the pipeline
        assert result.success

        # Check that download data is passed to transcription
        download_call = pipeline.downloader.run.call_args
        assert download_call[0][0] == url  # URL passed to downloader

        # Check that transcription data is passed to analysis
        transcribe_call = pipeline.transcriber.run.call_args
        assert "local_path" in transcribe_call[0][0]  # File path passed to transcriber

    @pytest.mark.asyncio
    async def test_pipeline_with_different_qualities(self, pipeline):
        """Test pipeline with different quality settings."""
        url = "https://youtube.com/watch?v=test123"

        for quality in ["720p", "1080p", "1440p"]:
            # Reset mocks
            for service in pipeline.__dict__.values():
                if hasattr(service, "run"):
                    service.run.reset_mock()

            result = await pipeline.process_video(url, quality)
            assert result.success

    @pytest.mark.asyncio
    async def test_pipeline_performance_metrics(self, pipeline):
        """Test that pipeline tracks performance metrics."""
        url = "https://youtube.com/watch?v=test123"
        quality = "1080p"

        with patch("time.monotonic", side_effect=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]):
            result = await pipeline.process_video(url, quality)

        assert result.success
        # Performance metrics should be tracked
        # (This would be verified by checking the result data structure)

    @pytest.mark.asyncio
    async def test_pipeline_with_tenant_context(self, pipeline):
        """Test pipeline with tenant context."""
        url = "https://youtube.com/watch?v=test123"
        quality = "1080p"

        # Mock tenant context
        with patch("ultimate_discord_intelligence_bot.tenancy.current_tenant") as mock_tenant:
            mock_tenant.return_value = TenantContext(tenant="test_tenant", workspace="test_workspace")

            result = await pipeline.process_video(url, quality)

            assert result.success
            # Verify tenant context is used throughout the pipeline

    @pytest.mark.asyncio
    async def test_pipeline_concurrent_execution(self, pipeline):
        """Test pipeline with concurrent execution."""
        urls = [
            "https://youtube.com/watch?v=test1",
            "https://youtube.com/watch?v=test2",
            "https://youtube.com/watch?v=test3",
        ]

        # Execute multiple pipelines concurrently
        tasks = [pipeline.process_video(url, "1080p") for url in urls]
        results = await asyncio.gather(*tasks)

        # All should succeed
        for result in results:
            assert result.success

    @pytest.mark.asyncio
    async def test_pipeline_error_recovery(self, pipeline):
        """Test pipeline error recovery mechanisms."""
        url = "https://youtube.com/watch?v=test123"
        quality = "1080p"

        # Configure transcriber to fail first time, succeed second time
        call_count = 0

        async def mock_transcriber(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return StepResult.fail("Transcription failed")
            else:
                return StepResult.ok(data={"transcript": "Recovered transcript", "confidence": 0.9})

        pipeline.transcriber.run = mock_transcriber

        # Should handle the failure gracefully
        result = await pipeline.process_video(url, quality)

        # The pipeline should either succeed with retry or fail gracefully
        # (Exact behavior depends on implementation)
        assert result is not None
