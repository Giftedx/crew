"""Tests for the multimodal content processing pipeline."""

import asyncio
from platform.core.step_result import StepResult
from unittest.mock import patch

import pytest

from src.kg.creator_kg_store import CreatorKGStore
from src.pipeline.multimodal_pipeline import MultimodalContentPipeline, PipelineConfig, PipelineResult, PipelineStage


class TestPipelineConfig:
    """Test pipeline configuration."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = PipelineConfig()
        assert config.enable_download is True
        assert config.enable_diarization is True
        assert config.enable_transcription is True
        assert config.enable_visual_analysis is True
        assert config.enable_content_analysis is True
        assert config.enable_claim_extraction is True
        assert config.enable_kg_ingestion is True
        assert config.min_transcription_confidence == 0.7
        assert config.min_diarization_confidence == 0.6
        assert config.min_visual_analysis_confidence == 0.5
        assert config.max_processing_time == 600
        assert config.max_file_size_mb == 500
        assert config.max_audio_duration_hours == 3
        assert config.save_intermediate_results is True
        assert config.cleanup_temp_files is True

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = PipelineConfig(enable_visual_analysis=False, min_transcription_confidence=0.8, max_processing_time=300)
        assert config.enable_visual_analysis is False
        assert config.min_transcription_confidence == 0.8
        assert config.max_processing_time == 300


class TestPipelineStage:
    """Test pipeline stage definition."""

    def test_pipeline_stage_creation(self) -> None:
        """Test pipeline stage creation."""
        stage = PipelineStage(
            name="test_stage",
            description="Test stage description",
            required=True,
            estimated_duration=60,
            dependencies=["stage1", "stage2"],
        )
        assert stage.name == "test_stage"
        assert stage.description == "Test stage description"
        assert stage.required is True
        assert stage.estimated_duration == 60
        assert stage.dependencies == ["stage1", "stage2"]


class TestMultimodalContentPipeline:
    """Test multimodal content pipeline."""

    @pytest.fixture
    def pipeline(self) -> MultimodalContentPipeline:
        """Create a pipeline instance for testing."""
        config = PipelineConfig(max_processing_time=60, save_intermediate_results=True)
        kg_store = CreatorKGStore(":memory:")
        return MultimodalContentPipeline(config, kg_store)

    def test_pipeline_initialization(self, pipeline: MultimodalContentPipeline) -> None:
        """Test pipeline initialization."""
        assert pipeline.config is not None
        assert pipeline.kg_store is not None
        assert len(pipeline.stages) == 7
        stage_names = [stage.name for stage in pipeline.stages]
        expected_stages = [
            "download",
            "diarization",
            "transcription",
            "visual_analysis",
            "content_analysis",
            "claim_extraction",
            "kg_ingestion",
        ]
        assert stage_names == expected_stages

    def test_get_pipeline_status(self, pipeline: MultimodalContentPipeline) -> None:
        """Test getting pipeline status."""
        status = pipeline.get_pipeline_status()
        assert "stages" in status
        assert "config" in status
        assert len(status["stages"]) == 7
        download_stage = status["stages"][0]
        assert download_stage["name"] == "download"
        assert download_stage["enabled"] is True
        assert download_stage["required"] is True
        assert download_stage["dependencies"] == []

    def test_validate_inputs_success(self, pipeline: MultimodalContentPipeline) -> None:
        """Test successful input validation."""
        result = asyncio.run(
            pipeline._validate_inputs("https://youtube.com/watch?v=test", "test_tenant", "test_workspace")
        )
        assert result.success
        assert result.data["data"]["validated"] is True

    @pytest.mark.asyncio
    async def test_validate_inputs_invalid_url(self, pipeline: MultimodalContentPipeline) -> None:
        """Test input validation with invalid URL."""
        result = await pipeline._validate_inputs("invalid_url", "test_tenant", "test_workspace")
        assert not result.success
        assert "Invalid URL format" in result.error

    @pytest.mark.asyncio
    async def test_validate_inputs_missing_tenant(self, pipeline: MultimodalContentPipeline) -> None:
        """Test input validation with missing tenant."""
        result = await pipeline._validate_inputs("https://youtube.com/watch?v=test", "", "test_workspace")
        assert not result.success
        assert "Tenant and workspace are required" in result.error

    def test_is_stage_enabled(self, pipeline: MultimodalContentPipeline) -> None:
        """Test stage enabled checking."""
        assert pipeline._is_stage_enabled("download") is True
        assert pipeline._is_stage_enabled("diarization") is True
        assert pipeline._is_stage_enabled("nonexistent") is True

    def test_check_dependencies(self, pipeline: MultimodalContentPipeline) -> None:
        """Test dependency checking."""
        download_stage = pipeline.stages[0]
        assert pipeline._check_dependencies(download_stage, []) is True
        assert pipeline._check_dependencies(download_stage, ["other"]) is True
        diarization_stage = pipeline.stages[1]
        assert pipeline._check_dependencies(diarization_stage, []) is False
        assert pipeline._check_dependencies(diarization_stage, ["download"]) is True
        assert pipeline._check_dependencies(diarization_stage, ["other"]) is False

    def test_stage_download(self, pipeline: MultimodalContentPipeline) -> None:
        """Test download stage execution."""
        result = asyncio.run(
            pipeline._stage_download("https://youtube.com/watch?v=test", "test_tenant", "test_workspace")
        )
        assert result.success
        assert "url" in result.data["data"]
        assert "file_path" in result.data["data"]
        assert "duration" in result.data["data"]
        assert result.data["data"]["url"] == "https://youtube.com/watch?v=test"

    @pytest.mark.asyncio
    async def test_stage_diarization(self, pipeline: MultimodalContentPipeline) -> None:
        """Test diarization stage execution."""
        download_result = {"url": "https://youtube.com/watch?v=test", "file_path": "/tmp/test.mp4", "duration": 3600}
        result = await pipeline._stage_diarization(download_result, "test_tenant", "test_workspace")
        assert result.success
        assert "speakers" in result.data
        assert "segments" in result.data
        assert "total_speakers" in result.data
        assert result.data["total_speakers"] == 2

    @pytest.mark.asyncio
    async def test_stage_transcription(self, pipeline: MultimodalContentPipeline) -> None:
        """Test transcription stage execution."""
        diarization_result = {
            "speakers": [{"id": "speaker_1", "name": "Host"}],
            "segments": [{"start": 0, "end": 300, "speaker": "speaker_1"}],
        }
        result = await pipeline._stage_transcription(diarization_result, "test_tenant", "test_workspace")
        assert result.success
        assert "segments" in result.data
        assert "full_text" in result.data
        assert "language" in result.data
        assert result.data["language"] == "en"

    @pytest.mark.asyncio
    async def test_stage_visual_analysis(self, pipeline: MultimodalContentPipeline) -> None:
        """Test visual analysis stage execution."""
        download_result = {"url": "https://youtube.com/watch?v=test", "file_path": "/tmp/test.mp4", "duration": 3600}
        result = await pipeline._stage_visual_analysis(download_result, "test_tenant", "test_workspace")
        assert result.success
        assert "frames_analyzed" in result.data
        assert "objects_detected" in result.data
        assert "scenes" in result.data

    @pytest.mark.asyncio
    async def test_stage_content_analysis(self, pipeline: MultimodalContentPipeline) -> None:
        """Test content analysis stage execution."""
        transcription_result = {
            "segments": [{"start": 0, "end": 300, "text": "Test content"}],
            "full_text": "Test content",
        }
        visual_result = {
            "objects_detected": [{"object": "person", "confidence": 0.9}],
            "scenes": [{"start": 0, "end": 300, "type": "interview"}],
        }
        result = await pipeline._stage_content_analysis(
            transcription_result, visual_result, "test_tenant", "test_workspace"
        )
        assert result.success
        assert "topics" in result.data
        assert "sentiment" in result.data
        assert "key_phrases" in result.data
        assert "summary" in result.data

    @pytest.mark.asyncio
    async def test_stage_claim_extraction(self, pipeline: MultimodalContentPipeline) -> None:
        """Test claim extraction stage execution."""
        content_result = {
            "topics": [{"name": "Politics", "confidence": 0.9}],
            "sentiment": {"overall": "neutral"},
            "key_phrases": ["politics", "election"],
        }
        result = await pipeline._stage_claim_extraction(content_result, "test_tenant", "test_workspace")
        assert result.success
        assert "claims" in result.data
        assert "quotes" in result.data
        assert "highlights" in result.data

    @pytest.mark.asyncio
    async def test_stage_kg_ingestion(self, pipeline: MultimodalContentPipeline) -> None:
        """Test KG ingestion stage execution."""
        stage_results = {
            "download": {
                "title": "Test Episode",
                "duration": 3600,
                "upload_date": "2024-01-15",
                "platform": "youtube",
                "view_count": 100000,
                "like_count": 5000,
                "comment_count": 500,
            },
            "content_analysis": {"topics": [{"name": "Politics", "confidence": 0.9, "mentions": 5}]},
            "claim_extraction": {
                "claims": [
                    {
                        "text": "Test claim",
                        "speaker": "speaker_1",
                        "timestamp": 300,
                        "confidence": 0.8,
                        "verification_status": "unverified",
                    }
                ],
                "highlights": [
                    {"start_time": 300, "end_time": 600, "description": "Test highlight", "confidence": 0.8}
                ],
            },
        }
        result = await pipeline._stage_kg_ingestion(
            stage_results,
            "https://youtube.com/watch?v=test",
            "test_tenant",
            "test_workspace",
            "Test Creator",
            "Test Episode",
        )
        assert result.success
        assert "episode_id" in result.data
        assert "creator_id" in result.data
        assert "topic_ids" in result.data
        assert "claim_ids" in result.data
        assert "highlight_ids" in result.data
        assert result.data["total_nodes_created"] > 0
        assert result.data["total_edges_created"] > 0

    def test_process_content_success(self, pipeline: MultimodalContentPipeline) -> None:
        """Test successful content processing."""
        result = asyncio.run(
            pipeline.process_content(
                url="https://youtube.com/watch?v=test",
                tenant="test_tenant",
                workspace="test_workspace",
                creator_name="Test Creator",
                episode_title="Test Episode",
            )
        )
        assert result.success
        pipeline_result = result.data["data"]
        assert isinstance(pipeline_result, PipelineResult)
        assert pipeline_result.success is True
        assert len(pipeline_result.stages_completed) > 0
        assert len(pipeline_result.stages_failed) == 0
        assert pipeline_result.total_duration > 0

    @pytest.mark.asyncio
    async def test_process_content_invalid_url(self, pipeline: MultimodalContentPipeline) -> None:
        """Test content processing with invalid URL."""
        result = await pipeline.process_content(url="invalid_url", tenant="test_tenant", workspace="test_workspace")
        assert not result.success
        assert "Pipeline failed" in result.error

    @pytest.mark.asyncio
    async def test_process_content_missing_tenant(self, pipeline: MultimodalContentPipeline) -> None:
        """Test content processing with missing tenant."""
        result = await pipeline.process_content(
            url="https://youtube.com/watch?v=test", tenant="", workspace="test_workspace"
        )
        assert not result.success
        assert "Pipeline failed" in result.error

    @pytest.mark.asyncio
    async def test_process_content_with_disabled_stage(self, pipeline: MultimodalContentPipeline) -> None:
        """Test content processing with disabled stage."""
        pipeline.config.enable_visual_analysis = False
        result = await pipeline.process_content(
            url="https://youtube.com/watch?v=test", tenant="test_tenant", workspace="test_workspace"
        )
        assert result.success
        assert isinstance(result.data, PipelineResult)
        assert result.data.success is True
        assert "visual_analysis" not in result.data.stages_completed

    @pytest.mark.asyncio
    async def test_process_content_stage_failure(self, pipeline: MultimodalContentPipeline) -> None:
        """Test content processing with stage failure."""
        with patch.object(pipeline, "_stage_download", return_value=StepResult.fail("Download failed")):
            result = await pipeline.process_content(
                url="https://youtube.com/watch?v=test", tenant="test_tenant", workspace="test_workspace"
            )
            assert not result.success
            assert isinstance(result.data, PipelineResult)
            assert result.data.success is False
            assert "download" in result.data.stages_failed
            assert len(result.data.errors) > 0


class TestPipelineResult:
    """Test pipeline result data structure."""

    def test_pipeline_result_creation(self) -> None:
        """Test pipeline result creation."""
        result = PipelineResult(
            success=True,
            stages_completed=["download", "transcription"],
            stages_failed=[],
            total_duration=120.5,
            intermediate_results={"download": {"file": "test.mp4"}},
            final_kg_nodes=[1, 2, 3],
            final_kg_edges=[1, 2],
            errors=[],
            warnings=["Minor warning"],
        )
        assert result.success is True
        assert len(result.stages_completed) == 2
        assert len(result.stages_failed) == 0
        assert result.total_duration == 120.5
        assert len(result.intermediate_results) == 1
        assert len(result.final_kg_nodes) == 3
        assert len(result.final_kg_edges) == 2
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
