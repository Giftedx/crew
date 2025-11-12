"""
Tests for the pipeline evaluation harness.

This module tests the comprehensive evaluation capabilities for the multimodal
pipeline, including WER, DER, cost, and latency validation.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from src.kg.creator_kg_store import CreatorKGStore
from src.pipeline.evaluation_harness import EvaluationEpisode, EvaluationMetrics, PipelineEvaluationHarness
from src.pipeline.multimodal_pipeline import MultimodalContentPipeline
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestEvaluationMetrics:
    """Test the EvaluationMetrics dataclass."""

    def test_metrics_initialization(self):
        """Test metrics initialization with default values."""
        metrics = EvaluationMetrics()
        assert metrics.word_error_rate == 0.0
        assert metrics.diarization_error_rate == 0.0
        assert metrics.total_cost == 0.0
        assert metrics.total_latency == 0.0
        assert metrics.transcription_quality == 0.0
        assert metrics.diarization_quality == 0.0
        assert metrics.content_analysis_quality == 0.0
        assert metrics.claim_extraction_quality == 0.0
        assert metrics.stage_metrics == {}
        assert metrics.stages_completed == []
        assert metrics.stages_failed == []

    def test_metrics_to_dict(self):
        """Test metrics serialization to dictionary."""
        metrics = EvaluationMetrics()
        metrics.word_error_rate = 0.1
        metrics.total_cost = 1.5
        metrics.stages_completed = ["download", "transcription"]
        result = metrics.to_dict()
        assert result["word_error_rate"] == 0.1
        assert result["total_cost"] == 1.5
        assert result["stages_completed"] == ["download", "transcription"]


class TestEvaluationEpisode:
    """Test the EvaluationEpisode dataclass."""

    def test_episode_initialization(self):
        """Test episode initialization."""
        episode = EvaluationEpisode(
            url="https://example.com/video",
            title="Test Episode",
            creator="Test Creator",
            platform="youtube",
            duration_seconds=3600,
            expected_speakers=2,
            expected_topics=["topic1", "topic2"],
            expected_claims=["claim1", "claim2"],
        )
        assert episode.url == "https://example.com/video"
        assert episode.title == "Test Episode"
        assert episode.creator == "Test Creator"
        assert episode.platform == "youtube"
        assert episode.duration_seconds == 3600
        assert episode.expected_speakers == 2
        assert episode.expected_topics == ["topic1", "topic2"]
        assert episode.expected_claims == ["claim1", "claim2"]
        assert episode.ground_truth_transcript is None
        assert episode.ground_truth_diarization is None

    def test_episode_to_dict(self):
        """Test episode serialization to dictionary."""
        episode = EvaluationEpisode(
            url="https://example.com/video",
            title="Test Episode",
            creator="Test Creator",
            platform="youtube",
            duration_seconds=3600,
            expected_speakers=2,
            expected_topics=["topic1"],
            expected_claims=["claim1"],
            ground_truth_transcript="Test transcript",
            ground_truth_diarization={"speaker1": [(0.0, 100.0)]},
        )
        result = episode.to_dict()
        assert result["url"] == "https://example.com/video"
        assert result["title"] == "Test Episode"
        assert result["ground_truth_transcript"] == "Test transcript"
        assert result["ground_truth_diarization"] == {"speaker1": [(0.0, 100.0)]}


class TestPipelineEvaluationHarness:
    """Test the PipelineEvaluationHarness class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_pipeline = Mock(spec=MultimodalContentPipeline)
        self.mock_kg_store = Mock(spec=CreatorKGStore)
        self.harness = PipelineEvaluationHarness(
            pipeline=self.mock_pipeline, kg_store=self.mock_kg_store, tenant="test_tenant", workspace="test_workspace"
        )

    def test_harness_initialization(self):
        """Test harness initialization."""
        assert self.harness.pipeline == self.mock_pipeline
        assert self.harness.kg_store == self.mock_kg_store
        assert self.harness.tenant == "test_tenant"
        assert self.harness.workspace == "test_workspace"
        assert self.harness.results == []

    def test_create_test_episodes(self):
        """Test creation of test episodes."""
        episodes = self.harness.create_test_episodes()
        assert len(episodes) == 5
        assert all(isinstance(ep, EvaluationEpisode) for ep in episodes)
        h3_episodes = [ep for ep in episodes if ep.creator == "H3 Podcast"]
        assert len(h3_episodes) == 2
        hasan_episodes = [ep for ep in episodes if ep.creator == "Hasan Piker"]
        assert len(hasan_episodes) == 3

    def test_calculate_word_error_rate(self):
        """Test WER calculation."""
        wer = self.harness.calculate_word_error_rate("hello world", "hello world")
        assert wer == 0.0
        wer = self.harness.calculate_word_error_rate("hello world", "hello there")
        assert wer == 0.5
        wer = self.harness.calculate_word_error_rate("hello world", "hi there")
        assert wer == 1.0
        wer = self.harness.calculate_word_error_rate("hello world", "")
        assert wer == 0.0
        wer = self.harness.calculate_word_error_rate("", "hello world")
        assert wer == 1.0

    def test_calculate_diarization_error_rate(self):
        """Test DER calculation."""
        predicted = {"speaker1": [(0.0, 100.0)], "speaker2": [(100.0, 200.0)]}
        ground_truth = {"speaker1": [(0.0, 100.0)], "speaker2": [(100.0, 200.0)]}
        der = self.harness.calculate_diarization_error_rate(predicted, ground_truth)
        assert der == 0.0
        predicted = {"speaker1": [(0.0, 150.0)], "speaker2": [(150.0, 200.0)]}
        ground_truth = {"speaker1": [(0.0, 100.0)], "speaker2": [(100.0, 200.0)]}
        der = self.harness.calculate_diarization_error_rate(predicted, ground_truth)
        assert der > 0.0
        der = self.harness.calculate_diarization_error_rate(predicted, {})
        assert der == 0.0

    def test_calculate_cost_estimate(self):
        """Test cost estimation."""
        stage_metrics = {
            "download": {"duration_seconds": 3600},
            "transcription": {"duration_seconds": 3600},
            "content_analysis": {"duration_seconds": 1800},
        }
        cost = self.harness.calculate_cost_estimate(stage_metrics)
        assert cost == 0.2

    def test_calculate_aggregate_metrics(self):
        """Test aggregate metrics calculation."""
        episode1 = EvaluationEpisode(
            url="url1",
            title="title1",
            creator="creator1",
            platform="youtube",
            duration_seconds=3600,
            expected_speakers=2,
            expected_topics=[],
            expected_claims=[],
        )
        episode2 = EvaluationEpisode(
            url="url2",
            title="title2",
            creator="creator2",
            platform="youtube",
            duration_seconds=1800,
            expected_speakers=1,
            expected_topics=[],
            expected_claims=[],
        )
        metrics1 = EvaluationMetrics()
        metrics1.word_error_rate = 0.1
        metrics1.diarization_error_rate = 0.2
        metrics1.total_cost = 1.0
        metrics1.total_latency = 300.0
        metrics1.stages_completed = ["download", "transcription"]
        metrics2 = EvaluationMetrics()
        metrics2.word_error_rate = 0.2
        metrics2.diarization_error_rate = 0.1
        metrics2.total_cost = 2.0
        metrics2.total_latency = 600.0
        metrics2.stages_completed = ["download", "transcription", "analysis"]
        results = [(episode1, metrics1), (episode2, metrics2)]
        aggregate = self.harness.calculate_aggregate_metrics(results)
        assert aggregate["total_episodes"] == 2
        assert aggregate["successful_episodes"] == 2
        assert aggregate["success_rate"] == 1.0
        assert abs(aggregate["average_wer"] - 0.15) < 0.001
        assert abs(aggregate["average_der"] - 0.15) < 0.001
        assert aggregate["average_cost"] == 1.5
        assert aggregate["average_latency"] == 450.0
        assert "download" in aggregate["stage_success_rates"]
        assert "transcription" in aggregate["stage_success_rates"]

    def test_generate_summary(self):
        """Test summary generation with pass/fail criteria."""
        episode = EvaluationEpisode(
            url="url1",
            title="title1",
            creator="creator1",
            platform="youtube",
            duration_seconds=3600,
            expected_speakers=2,
            expected_topics=[],
            expected_claims=[],
        )
        metrics = EvaluationMetrics()
        metrics.word_error_rate = 0.05
        metrics.diarization_error_rate = 0.1
        metrics.total_cost = 1.5
        metrics.total_latency = 300.0
        results = [(episode, metrics)]
        aggregate_metrics = self.harness.calculate_aggregate_metrics(results)
        summary = self.harness.generate_summary(results, aggregate_metrics)
        assert summary["overall_status"] == "PASS"
        assert summary["criteria_met"]["wer"] is True
        assert summary["criteria_met"]["der"] is True
        assert summary["criteria_met"]["cost"] is True
        assert summary["criteria_met"]["latency"] is True
        assert summary["criteria_failed"] == {}

    def test_generate_summary_fail_criteria(self):
        """Test summary generation with failed criteria."""
        episode = EvaluationEpisode(
            url="url1",
            title="title1",
            creator="creator1",
            platform="youtube",
            duration_seconds=3600,
            expected_speakers=2,
            expected_topics=[],
            expected_claims=[],
        )
        metrics = EvaluationMetrics()
        metrics.word_error_rate = 0.2
        metrics.diarization_error_rate = 0.3
        metrics.total_cost = 3.0
        metrics.total_latency = 900.0
        results = [(episode, metrics)]
        aggregate_metrics = self.harness.calculate_aggregate_metrics(results)
        summary = self.harness.generate_summary(results, aggregate_metrics)
        assert summary["overall_status"] == "FAIL"
        assert summary["criteria_met"]["wer"] is False
        assert summary["criteria_met"]["der"] is False
        assert summary["criteria_met"]["cost"] is False
        assert summary["criteria_met"]["latency"] is False
        assert len(summary["criteria_failed"]) == 4
        assert len(summary["recommendations"]) == 4

    def test_evaluate_episode_success(self):
        """Test successful episode evaluation."""
        from src.pipeline.multimodal_pipeline import PipelineResult

        mock_stage_results = {
            "download": {"success": True, "data": {"url": "test_url"}, "start_time": 0, "end_time": 10},
            "transcription": {
                "success": True,
                "data": {"transcript": "test transcript"},
                "start_time": 10,
                "end_time": 20,
            },
            "diarization": {
                "success": True,
                "data": {"speakers": {"speaker1": [(0.0, 100.0)]}},
                "start_time": 20,
                "end_time": 30,
            },
        }
        mock_pipeline_result = PipelineResult(
            success=True,
            stages_completed=["download", "transcription", "diarization"],
            stages_failed=[],
            total_duration=30.0,
            intermediate_results={},
            final_kg_nodes=[],
            final_kg_edges=[],
            errors=[],
            warnings=[],
            stage_results=mock_stage_results,
        )
        self.mock_pipeline.process_content = AsyncMock(return_value=StepResult.ok(data=mock_pipeline_result))
        episode = EvaluationEpisode(
            url="https://example.com/video",
            title="Test Episode",
            creator="Test Creator",
            platform="youtube",
            duration_seconds=3600,
            expected_speakers=2,
            expected_topics=["topic1"],
            expected_claims=["claim1"],
            ground_truth_transcript="test transcript",
            ground_truth_diarization={"speaker1": [(0.0, 100.0)]},
        )
        metrics = asyncio.run(self.harness.evaluate_episode(episode))
        assert metrics.word_error_rate == 0.0
        assert metrics.diarization_error_rate == 0.0
        assert metrics.total_cost > 0.0
        assert metrics.total_latency > 0.0
        assert "download" in metrics.stages_completed
        assert "transcription" in metrics.stages_completed
        assert "diarization" in metrics.stages_completed
        assert metrics.stages_failed == []

    def test_evaluate_episode_pipeline_failure(self):
        """Test episode evaluation with pipeline failure."""
        self.mock_pipeline.process_content = AsyncMock(return_value=StepResult.fail("Pipeline failed"))
        episode = EvaluationEpisode(
            url="https://example.com/video",
            title="Test Episode",
            creator="Test Creator",
            platform="youtube",
            duration_seconds=3600,
            expected_speakers=2,
            expected_topics=["topic1"],
            expected_claims=["claim1"],
        )
        metrics = asyncio.run(self.harness.evaluate_episode(episode))
        assert metrics.word_error_rate == 0.0
        assert metrics.diarization_error_rate == 0.0
        assert metrics.total_cost == 0.0
        assert metrics.total_latency > 0.0
        assert metrics.stages_completed == []
        assert "pipeline" in metrics.stages_failed

    def test_run_evaluation(self):
        """Test running evaluation on multiple episodes."""
        from src.pipeline.multimodal_pipeline import PipelineResult

        mock_stage_results = {
            "download": {"success": True, "data": {"url": "test_url"}, "start_time": 0, "end_time": 10},
            "transcription": {
                "success": True,
                "data": {"transcript": "test transcript"},
                "start_time": 10,
                "end_time": 20,
            },
        }
        mock_pipeline_result = PipelineResult(
            success=True,
            stages_completed=["download", "transcription"],
            stages_failed=[],
            total_duration=20.0,
            intermediate_results={},
            final_kg_nodes=[],
            final_kg_edges=[],
            errors=[],
            warnings=[],
            stage_results=mock_stage_results,
        )
        self.mock_pipeline.process_content = AsyncMock(return_value=StepResult.ok(data=mock_pipeline_result))
        episodes = [
            EvaluationEpisode(
                url="https://example.com/video1",
                title="Test Episode 1",
                creator="Test Creator",
                platform="youtube",
                duration_seconds=1800,
                expected_speakers=1,
                expected_topics=["topic1"],
                expected_claims=["claim1"],
            ),
            EvaluationEpisode(
                url="https://example.com/video2",
                title="Test Episode 2",
                creator="Test Creator",
                platform="youtube",
                duration_seconds=3600,
                expected_speakers=2,
                expected_topics=["topic2"],
                expected_claims=["claim2"],
            ),
        ]
        results = asyncio.run(self.harness.run_evaluation(episodes))
        assert "episodes" in results
        assert "metrics" in results
        assert "aggregate_metrics" in results
        assert "summary" in results
        assert len(results["episodes"]) == 2
        assert len(results["metrics"]) == 2
        assert results["aggregate_metrics"]["total_episodes"] == 2
        assert results["aggregate_metrics"]["successful_episodes"] == 2

    def test_save_results(self):
        """Test saving results to file."""
        episode = EvaluationEpisode(
            url="https://example.com/video",
            title="Test Episode",
            creator="Test Creator",
            platform="youtube",
            duration_seconds=3600,
            expected_speakers=2,
            expected_topics=["topic1"],
            expected_claims=["claim1"],
        )
        metrics = EvaluationMetrics()
        metrics.word_error_rate = 0.1
        metrics.total_cost = 1.5
        self.harness.results = [(episode, metrics)]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name
        try:
            result = self.harness.save_results(temp_path)
            assert result.success
            assert "data" in result.data
            assert "filepath" in result.data["data"]
            assert "results_count" in result.data["data"]
            assert result.data["data"]["results_count"] == 1
            with open(temp_path) as f:
                saved_data = json.load(f)
            assert "episodes" in saved_data
            assert "metrics" in saved_data
            assert "aggregate_metrics" in saved_data
            assert "summary" in saved_data
            assert len(saved_data["episodes"]) == 1
            assert len(saved_data["metrics"]) == 1
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_save_results_failure(self):
        """Test saving results with invalid filepath."""
        result = self.harness.save_results("/invalid/path/that/does/not/exist/results.json")
        assert not result.success
        assert "Failed to save results" in result.error
