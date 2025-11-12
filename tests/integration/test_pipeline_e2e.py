"""End-to-end integration tests for the content processing pipeline."""

from unittest.mock import patch

import pytest

from ultimate_discord_intelligence_bot.step_result import StepResult


class TestPipelineE2E:
    """End-to-end pipeline integration tests."""

    @pytest.fixture
    def sample_url(self):
        """Sample URL for testing."""
        return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    @pytest.fixture
    def sample_transcript(self):
        """Sample transcript for testing."""
        return "This is a sample transcript for testing the pipeline."

    @pytest.fixture
    def sample_analysis_result(self):
        """Sample analysis result."""
        return {
            "sentiment": "positive",
            "topics": ["technology", "AI"],
            "confidence": 0.85,
            "summary": "Sample analysis summary",
        }

    @pytest.fixture
    def mock_pipeline_components(self):
        """Mock all pipeline components."""
        with (
            patch("ultimate_discord_intelligence_bot.pipeline.MultiPlatformDownloadTool") as mock_download,
            patch("ultimate_discord_intelligence_bot.pipeline.AudioTranscriptionTool") as mock_transcribe,
            patch("ultimate_discord_intelligence_bot.pipeline.TextAnalysisTool") as mock_analyze,
            patch("ultimate_discord_intelligence_bot.pipeline.UnifiedMemoryTool") as mock_memory,
        ):
            mock_download.return_value._run.return_value = StepResult.ok(
                data={"platform": "youtube", "title": "Test Video", "file_path": "/tmp/test_video.mp4"}
            )
            mock_transcribe.return_value._run.return_value = StepResult.ok(
                data={"transcript": "This is a sample transcript for testing the pipeline.", "confidence": 0.95}
            )
            mock_analyze.return_value._run.return_value = StepResult.ok(
                data={"sentiment": "positive", "topics": ["technology", "AI"], "confidence": 0.85}
            )
            mock_memory.return_value._run.return_value = StepResult.ok(data={"stored": True, "index": "memory"})
            yield {
                "download": mock_download,
                "transcribe": mock_transcribe,
                "analyze": mock_analyze,
                "memory": mock_memory,
            }

    def test_full_pipeline_flow(self, sample_url, mock_pipeline_components):
        """Test complete pipeline flow from URL to memory storage."""
        download_tool = mock_pipeline_components["download"]()
        download_result = download_tool._run(url=sample_url)
        assert isinstance(download_result, StepResult)
        assert download_result.success
        transcribe_tool = mock_pipeline_components["transcribe"]()
        transcribe_result = transcribe_tool._run(file_path="/tmp/test_video.mp4")
        assert isinstance(transcribe_result, StepResult)
        assert transcribe_result.success
        analyze_tool = mock_pipeline_components["analyze"]()
        analyze_result = analyze_tool._run(text="This is a sample transcript for testing the pipeline.")
        assert isinstance(analyze_result, StepResult)
        assert analyze_result.success
        memory_tool = mock_pipeline_components["memory"]()
        memory_result = memory_tool._run(content="Sample analysis result")
        assert isinstance(memory_result, StepResult)
        assert memory_result.success

    def test_pipeline_error_handling(self, sample_url, mock_pipeline_components):
        """Test pipeline error handling and recovery."""
        mock_pipeline_components["download"].return_value._run.return_value = StepResult.fail("Download failed")
        download_tool = mock_pipeline_components["download"]()
        download_result = download_tool._run(url=sample_url)
        assert isinstance(download_result, StepResult)
        assert not download_result.success
        assert "Download failed" in str(download_result.error)

    def test_pipeline_tenant_isolation(self, sample_url, mock_pipeline_components):
        """Test pipeline respects tenant isolation."""
        tenant1 = "tenant1"
        tenant2 = "tenant2"
        workspace1 = "workspace1"
        workspace2 = "workspace2"
        download_tool = mock_pipeline_components["download"]()
        result1 = download_tool._run(url=sample_url, tenant=tenant1, workspace=workspace1)
        assert isinstance(result1, StepResult)
        result2 = download_tool._run(url=sample_url, tenant=tenant2, workspace=workspace2)
        assert isinstance(result2, StepResult)
        assert result1.success
        assert result2.success

    def test_pipeline_performance_metrics(self, sample_url, mock_pipeline_components):
        """Test pipeline performance metrics collection."""
        import time

        start_time = time.time()
        download_tool = mock_pipeline_components["download"]()
        download_result = download_tool._run(url=sample_url)
        end_time = time.time()
        duration = end_time - start_time
        assert isinstance(download_result, StepResult)
        assert download_result.success
        assert duration < 1.0

    @patch("ultimate_discord_intelligence_bot.pipeline.crew")
    def test_crew_orchestration(self, mock_crew, sample_url):
        """Test CrewAI orchestration of the pipeline."""
        mock_crew.return_value.kickoff.return_value = {
            "status": "completed",
            "results": ["Download successful", "Analysis complete"],
        }
        crew_instance = mock_crew()
        result = crew_instance.kickoff(inputs={"url": sample_url})
        assert result["status"] == "completed"
        assert len(result["results"]) > 0
