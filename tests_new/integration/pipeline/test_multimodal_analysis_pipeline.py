"""Tests for Multimodal Analysis Pipeline."""

from __future__ import annotations

from pipeline.multimodal_analysis_pipeline import (
    MultimodalAnalysisPipeline,
    PipelineConfig,
    get_multimodal_analysis_pipeline,
)


class TestMultimodalAnalysisPipeline:
    """Test multimodal analysis pipeline functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.pipeline = MultimodalAnalysisPipeline()

    def test_initialization(self) -> None:
        """Test pipeline initialization."""
        assert self.pipeline._services_initialized is True
        assert hasattr(self.pipeline, "_asr_service")

    def test_analyze_content_basic(self) -> None:
        """Test basic content analysis pipeline."""
        config = PipelineConfig(
            enable_asr=False,  # Disable ASR for faster testing
            enable_speaker_diarization=False,
            enable_visual_parsing=False,
            enable_topic_segmentation=False,
            enable_claim_extraction=False,
            enable_highlight_detection=False,
            enable_sentiment_analysis=False,
            enable_safety_analysis=False,
            enable_deduplication=False,
            enable_publishing=False,
        )

        result = self.pipeline.analyze_content(
            content_url="https://example.com/video.mp4",
            platform="youtube",
            config=config,
        )

        # Should succeed with minimal configuration
        assert result.success
        assert result.data is not None
        assert "analysis_results" in result.data
        assert "published_reports" in result.data
        assert result.data["total_processing_time"] > 0

    def test_analyze_content_full_pipeline(self) -> None:
        """Test full pipeline execution."""
        config = PipelineConfig(
            # Enable only basic services for testing
            enable_asr=True,
            enable_speaker_diarization=False,  # Requires audio
            enable_visual_parsing=False,  # Requires video
            enable_topic_segmentation=True,
            enable_claim_extraction=False,  # Requires speaker data
            enable_highlight_detection=True,
            enable_sentiment_analysis=True,
            enable_safety_analysis=True,
            enable_deduplication=True,
            enable_publishing=False,  # Disable for testing
        )

        result = self.pipeline.analyze_content(
            content_url="https://example.com/video.mp4",
            platform="youtube",
            config=config,
        )

        # Should succeed with enabled services
        assert result.success
        assert "analysis_results" in result.data

        # Check that expected services ran
        analysis_results = result.data["analysis_results"]
        assert "ingestion" in analysis_results

        # Some services might succeed, others might fail gracefully
        # The pipeline should continue even if individual services fail

    def test_pipeline_with_custom_config(self) -> None:
        """Test pipeline with custom configuration."""
        config = PipelineConfig(
            model_quality="fast",
            max_processing_time=60,
            enable_caching=False,
        )

        result = self.pipeline.analyze_content(
            content_url="https://example.com/video.mp4",
            config=config,
        )

        assert result.success
        assert result.data["metadata"]["config"]["model_quality"] == "fast"
        assert result.data["metadata"]["config"]["max_processing_time"] == 60

    def test_pipeline_status_check(self) -> None:
        """Test pipeline status checking."""
        result = self.pipeline.get_pipeline_status()

        assert result.success
        assert result.data is not None
        assert "services_initialized" in result.data
        assert "available_services" in result.data
        assert "service_health" in result.data

        # Should have initialized services
        assert result.data["services_initialized"] is True


class TestMultimodalAnalysisPipelineSingleton:
    """Test singleton instance management."""

    def test_get_multimodal_analysis_pipeline(self) -> None:
        """Test getting singleton instance."""
        pipeline1 = get_multimodal_analysis_pipeline()
        pipeline2 = get_multimodal_analysis_pipeline()

        # Should return same instance
        assert pipeline1 is pipeline2
        assert isinstance(pipeline1, MultimodalAnalysisPipeline)


class TestPipelineConfig:
    """Test pipeline configuration data structure."""

    def test_create_pipeline_config(self) -> None:
        """Test creating pipeline configuration."""
        config = PipelineConfig(
            enable_asr=True,
            model_quality="quality",
            max_processing_time=600,
            enable_caching=True,
            publish_reports=True,
        )

        assert config.enable_asr is True
        assert config.model_quality == "quality"
        assert config.max_processing_time == 600
        assert config.enable_caching is True
        assert config.publish_reports is True

    def test_pipeline_config_defaults(self) -> None:
        """Test pipeline configuration with default values."""
        config = PipelineConfig()

        assert config.enable_asr is True  # Default enabled
        assert config.model_quality == "balanced"  # Default quality
        assert config.max_processing_time == 300  # Default timeout
        assert config.enable_caching is True  # Default caching
        assert config.publish_reports is True  # Default publishing


class TestPipelineResult:
    """Test pipeline result data structure."""

    def test_create_pipeline_result(self) -> None:
        """Test creating pipeline result."""
        from pipeline.multimodal_analysis_pipeline import PipelineResult

        result = PipelineResult(
            success=True,
            total_processing_time=45.2,
            analysis_results={"asr": {"text": "transcript"}},
            published_reports=["report_1", "report_2"],
            errors=[],
            warnings=["warning1"],
            metadata={"platform": "youtube"},
        )

        assert result.success is True
        assert result.total_processing_time == 45.2
        assert "asr" in result.analysis_results
        assert len(result.published_reports) == 2
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert result.metadata["platform"] == "youtube"

    def test_pipeline_result_with_errors(self) -> None:
        """Test pipeline result with errors."""
        from pipeline.multimodal_analysis_pipeline import PipelineResult

        result = PipelineResult(
            success=False,
            total_processing_time=30.1,
            analysis_results={},
            published_reports=[],
            errors=["ASR failed", "Speaker analysis failed"],
            warnings=[],
            metadata={"platform": "twitch"},
        )

        assert result.success is False
        assert len(result.errors) == 2
        assert len(result.published_reports) == 0


class TestMultimodalPipelineIntegration:
    """Test pipeline integration with mocked services."""

    def test_pipeline_with_minimal_services(self) -> None:
        """Test pipeline execution with minimal service configuration."""
        config = PipelineConfig(
            enable_asr=False,
            enable_speaker_diarization=False,
            enable_visual_parsing=False,
            enable_topic_segmentation=False,
            enable_claim_extraction=False,
            enable_highlight_detection=False,
            enable_sentiment_analysis=False,
            enable_safety_analysis=False,
            enable_deduplication=False,
            enable_publishing=False,
        )

        result = self.pipeline.analyze_content(
            content_url="https://example.com/video.mp4",
            platform="youtube",
            config=config,
        )

        assert result.success
        # Should only have ingestion results
        assert "ingestion" in result.data["analysis_results"]
        assert len(result.data["analysis_results"]) == 1

    def test_pipeline_error_handling(self) -> None:
        """Test pipeline error handling when services fail."""
        config = PipelineConfig(
            enable_asr=True,  # Enable ASR which might fail
            enable_speaker_diarization=True,
            enable_visual_parsing=True,
            enable_topic_segmentation=True,
            enable_claim_extraction=True,
            enable_highlight_detection=True,
            enable_sentiment_analysis=True,
            enable_safety_analysis=True,
            enable_deduplication=True,
            enable_publishing=False,  # Disable publishing for cleaner testing
        )

        result = self.pipeline.analyze_content(
            content_url="https://example.com/video.mp4",
            platform="youtube",
            config=config,
        )

        # Should succeed even if some services fail
        assert result.success
        assert "analysis_results" in result.data
        assert "errors" in result.data
        assert "warnings" in result.data

        # Should have some results even if some services failed
        analysis_results = result.data["analysis_results"]
        assert len(analysis_results) >= 1  # At least ingestion should work

    def test_pipeline_metadata_preservation(self) -> None:
        """Test that pipeline preserves metadata correctly."""
        config = PipelineConfig(model_quality="fast", max_processing_time=120)

        result = self.pipeline.analyze_content(
            content_url="https://example.com/video.mp4",
            platform="twitch",
            config=config,
        )

        assert result.success
        metadata = result.data["metadata"]

        assert metadata["content_url"] == "https://example.com/video.mp4"
        assert metadata["platform"] == "twitch"
        assert metadata["config"]["model_quality"] == "fast"
        assert metadata["config"]["max_processing_time"] == 120
