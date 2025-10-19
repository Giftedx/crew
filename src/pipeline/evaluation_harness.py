"""
Evaluation harness for multimodal content pipeline testing.

This module provides comprehensive evaluation capabilities for testing the
multimodal pipeline on real content, measuring key metrics like WER, DER,
cost, and latency.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """Container for evaluation metrics."""

    # Core metrics
    word_error_rate: float = 0.0
    diarization_error_rate: float = 0.0
    total_cost: float = 0.0
    total_latency: float = 0.0

    # Quality metrics
    transcription_quality: float = 0.0
    diarization_quality: float = 0.0
    content_analysis_quality: float = 0.0
    claim_extraction_quality: float = 0.0

    # Stage-specific metrics
    stage_metrics: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Success/failure tracking
    stages_completed: list[str] = field(default_factory=list)
    stages_failed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "word_error_rate": self.word_error_rate,
            "diarization_error_rate": self.diarization_error_rate,
            "total_cost": self.total_cost,
            "total_latency": self.total_latency,
            "transcription_quality": self.transcription_quality,
            "diarization_quality": self.diarization_quality,
            "content_analysis_quality": self.content_analysis_quality,
            "claim_extraction_quality": self.claim_extraction_quality,
            "stage_metrics": self.stage_metrics,
            "stages_completed": self.stages_completed,
            "stages_failed": self.stages_failed,
        }


@dataclass
class TestEpisode:
    """Container for test episode data."""

    url: str
    title: str
    creator: str
    platform: str
    duration_seconds: int
    expected_speakers: int
    expected_topics: list[str]
    expected_claims: list[str]
    ground_truth_transcript: str | None = None
    ground_truth_diarization: dict[str, list[tuple[float, float]]] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert episode to dictionary for serialization."""
        return {
            "url": self.url,
            "title": self.title,
            "creator": self.creator,
            "platform": self.platform,
            "duration_seconds": self.duration_seconds,
            "expected_speakers": self.expected_speakers,
            "expected_topics": self.expected_topics,
            "expected_claims": self.expected_claims,
            "ground_truth_transcript": self.ground_truth_transcript,
            "ground_truth_diarization": self.ground_truth_diarization,
        }


class PipelineEvaluationHarness:
    """
    Comprehensive evaluation harness for multimodal content pipeline.

    This class provides end-to-end testing capabilities for the multimodal
    pipeline, measuring key performance metrics and validating quality.
    """

    def __init__(self, pipeline, kg_store, tenant: str = "evaluation", workspace: str = "testing"):
        """Initialize the evaluation harness."""
        self.pipeline = pipeline
        self.kg_store = kg_store
        self.tenant = tenant
        self.workspace = workspace
        self.results: list[tuple[TestEpisode, EvaluationMetrics]] = []

    def create_test_episodes(self) -> list[TestEpisode]:
        """Create test episodes for evaluation."""
        return [
            # H3 Podcast episodes
            TestEpisode(
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Mock URL
                title="H3 Podcast #123 - Tech Talk with Guest",
                creator="H3 Podcast",
                platform="youtube",
                duration_seconds=3600,  # 1 hour
                expected_speakers=3,
                expected_topics=["technology", "podcasting", "entertainment"],
                expected_claims=["AI will revolutionize content creation", "Podcasting is the future of media"],
                ground_truth_transcript="Welcome to the H3 Podcast. Today we're discussing technology trends...",
                ground_truth_diarization={
                    "Ethan": [(0.0, 300.0), (600.0, 900.0)],
                    "Hila": [(300.0, 600.0), (900.0, 1200.0)],
                    "Guest": [(1200.0, 1800.0)],
                },
            ),
            TestEpisode(
                url="https://www.youtube.com/watch?v=example2",
                title="H3 Podcast #124 - Gaming Discussion",
                creator="H3 Podcast",
                platform="youtube",
                duration_seconds=2700,  # 45 minutes
                expected_speakers=2,
                expected_topics=["gaming", "streaming", "entertainment"],
                expected_claims=["Streaming platforms are changing gaming", "Mobile gaming is the future"],
                ground_truth_transcript="Today we're talking about the gaming industry and how streaming has changed everything...",
                ground_truth_diarization={"Ethan": [(0.0, 1350.0)], "Hila": [(1350.0, 2700.0)]},
            ),
            # Hasan Piker episodes
            TestEpisode(
                url="https://www.twitch.tv/videos/example1",
                title="Hasan Reacts to Political News",
                creator="Hasan Piker",
                platform="twitch",
                duration_seconds=7200,  # 2 hours
                expected_speakers=1,
                expected_topics=["politics", "news", "reaction"],
                expected_claims=["Current political system needs reform", "Media bias affects public opinion"],
                ground_truth_transcript="Welcome back to the stream. Today we're reacting to the latest political news...",
                ground_truth_diarization={"Hasan": [(0.0, 7200.0)]},
            ),
            TestEpisode(
                url="https://www.twitch.tv/videos/example2",
                title="Hasan Gaming Stream - Valorant",
                creator="Hasan Piker",
                platform="twitch",
                duration_seconds=5400,  # 1.5 hours
                expected_speakers=1,
                expected_topics=["gaming", "valorant", "streaming"],
                expected_claims=["Valorant is the best tactical shooter", "Streaming improves gaming skills"],
                ground_truth_transcript="Alright, let's jump into some Valorant. I've been practicing my aim...",
                ground_truth_diarization={"Hasan": [(0.0, 5400.0)]},
            ),
            TestEpisode(
                url="https://www.youtube.com/watch?v=example3",
                title="Hasan Reacts to Drama",
                creator="Hasan Piker",
                platform="youtube",
                duration_seconds=1800,  # 30 minutes
                expected_speakers=1,
                expected_topics=["drama", "reaction", "entertainment"],
                expected_claims=["Drama content is harmful to creators", "Reaction content adds value"],
                ground_truth_transcript="Today we're reacting to some drama that's been going around...",
                ground_truth_diarization={"Hasan": [(0.0, 1800.0)]},
            ),
        ]

    def calculate_word_error_rate(self, predicted: str, ground_truth: str) -> float:
        """Calculate Word Error Rate (WER) between predicted and ground truth transcript."""
        if not ground_truth:
            return 0.0

        # Simple WER calculation using edit distance
        predicted_words = predicted.lower().split()
        ground_truth_words = ground_truth.lower().split()

        if not ground_truth_words:
            return 0.0

        # Calculate edit distance
        m, n = len(predicted_words), len(ground_truth_words)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if predicted_words[i - 1] == ground_truth_words[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

        return dp[m][n] / n

    def calculate_diarization_error_rate(
        self, predicted: dict[str, list[tuple[float, float]]], ground_truth: dict[str, list[tuple[float, float]]]
    ) -> float:
        """Calculate Diarization Error Rate (DER) between predicted and ground truth."""
        if not ground_truth:
            return 0.0

        # Simple DER calculation based on speaker overlap
        total_time = 0.0
        error_time = 0.0

        # Calculate total duration from ground truth
        for speaker_segments in ground_truth.values():
            for start, end in speaker_segments:
                total_time += end - start

        if total_time == 0:
            return 0.0

        # Calculate error time based on speaker mismatches
        # This is a simplified calculation - in practice, you'd use more sophisticated algorithms
        for speaker, segments in ground_truth.items():
            for start, end in segments:
                segment_duration = end - start

                # Check if predicted diarization matches
                if speaker in predicted:
                    predicted_segments = predicted[speaker]
                    overlap_time = 0.0

                    for pred_start, pred_end in predicted_segments:
                        overlap_start = max(start, pred_start)
                        overlap_end = min(end, pred_end)
                        if overlap_start < overlap_end:
                            overlap_time += overlap_end - overlap_start

                    # Error is the non-overlapping time
                    error_time += segment_duration - overlap_time
                else:
                    # Speaker not found in prediction
                    error_time += segment_duration

        return error_time / total_time

    def calculate_cost_estimate(self, stage_metrics: dict[str, dict[str, Any]]) -> float:
        """Calculate estimated cost based on stage metrics."""
        total_cost = 0.0

        # Cost estimates per stage (in USD)
        cost_estimates = {
            "download": 0.0,  # Free
            "diarization": 0.05,  # $0.05 per hour
            "transcription": 0.10,  # $0.10 per hour
            "visual_analysis": 0.15,  # $0.15 per hour
            "content_analysis": 0.20,  # $0.20 per hour
            "claim_extraction": 0.10,  # $0.10 per hour
            "kg_ingestion": 0.05,  # $0.05 per hour
        }

        for stage, metrics in stage_metrics.items():
            if stage in cost_estimates:
                duration_hours = metrics.get("duration_seconds", 0) / 3600.0
                total_cost += cost_estimates[stage] * duration_hours

        return total_cost

    async def evaluate_episode(self, episode: TestEpisode) -> EvaluationMetrics:
        """Evaluate a single episode through the pipeline."""
        logger.info(f"Evaluating episode: {episode.title}")

        metrics = EvaluationMetrics()
        start_time = time.time()

        try:
            # Process episode through pipeline
            result = await self.pipeline.process_content(url=episode.url, tenant=self.tenant, workspace=self.workspace)

            if not result.success:
                logger.error(f"Pipeline failed for episode {episode.title}: {result.error}")
                metrics.stages_failed.append("pipeline")
                metrics.total_latency = time.time() - start_time
                return metrics

            # Extract pipeline result
            pipeline_result = result.data["data"]
            stage_results = pipeline_result.stage_results

            # Calculate stage-specific metrics
            for stage_name, stage_data in stage_results.items():
                stage_start = stage_data.get("start_time", 0)
                stage_end = stage_data.get("end_time", 0)
                stage_duration = stage_end - stage_start

                metrics.stage_metrics[stage_name] = {
                    "duration_seconds": stage_duration,
                    "success": stage_data.get("success", False),
                    "data_size": len(str(stage_data.get("data", {}))),
                }

                if stage_data.get("success", False):
                    metrics.stages_completed.append(stage_name)
                else:
                    metrics.stages_failed.append(stage_name)

            # Calculate WER if ground truth is available
            if episode.ground_truth_transcript and "transcription" in stage_results:
                transcript_data = stage_results["transcription"].get("data", {})
                predicted_transcript = transcript_data.get("transcript", "")
                metrics.word_error_rate = self.calculate_word_error_rate(
                    predicted_transcript, episode.ground_truth_transcript
                )

            # Calculate DER if ground truth is available
            if episode.ground_truth_diarization and "diarization" in stage_results:
                diarization_data = stage_results["diarization"].get("data", {})
                predicted_diarization = diarization_data.get("speakers", {})
                metrics.diarization_error_rate = self.calculate_diarization_error_rate(
                    predicted_diarization, episode.ground_truth_diarization
                )

            # Calculate total cost
            metrics.total_cost = self.calculate_cost_estimate(metrics.stage_metrics)

            # Calculate total latency
            metrics.total_latency = time.time() - start_time

            # Calculate quality metrics (simplified)
            metrics.transcription_quality = 1.0 - metrics.word_error_rate
            metrics.diarization_quality = 1.0 - metrics.diarization_error_rate
            metrics.content_analysis_quality = 0.8 if "content_analysis" in metrics.stages_completed else 0.0
            metrics.claim_extraction_quality = 0.8 if "claim_extraction" in metrics.stages_completed else 0.0

        except Exception as e:
            logger.error(f"Evaluation failed for episode {episode.title}: {str(e)}")
            metrics.stages_failed.append("evaluation")

        return metrics

    async def run_evaluation(self, episodes: list[TestEpisode] | None = None) -> dict[str, Any]:
        """Run evaluation on all test episodes."""
        if episodes is None:
            episodes = self.create_test_episodes()

        logger.info(f"Starting evaluation of {len(episodes)} episodes")

        results = []
        for episode in episodes:
            metrics = await self.evaluate_episode(episode)
            results.append((episode, metrics))
            self.results.append((episode, metrics))

        # Calculate aggregate metrics
        aggregate_metrics = self.calculate_aggregate_metrics(results)

        return {
            "episodes": [ep.to_dict() for ep, _ in results],
            "metrics": [m.to_dict() for _, m in results],
            "aggregate_metrics": aggregate_metrics,
            "summary": self.generate_summary(results, aggregate_metrics),
        }

    def calculate_aggregate_metrics(self, results: list[tuple[TestEpisode, EvaluationMetrics]]) -> dict[str, Any]:
        """Calculate aggregate metrics across all episodes."""
        if not results:
            return {}

        total_episodes = len(results)
        successful_episodes = sum(1 for _, m in results if not m.stages_failed)

        # Calculate averages
        avg_wer = sum(m.word_error_rate for _, m in results) / total_episodes
        avg_der = sum(m.diarization_error_rate for _, m in results) / total_episodes
        avg_cost = sum(m.total_cost for _, m in results) / total_episodes
        avg_latency = sum(m.total_latency for _, m in results) / total_episodes

        # Calculate success rates
        stage_success_rates = {}
        all_stages = set()
        for _, metrics in results:
            all_stages.update(metrics.stages_completed + metrics.stages_failed)

        for stage in all_stages:
            completed = sum(1 for _, m in results if stage in m.stages_completed)
            stage_success_rates[stage] = completed / total_episodes

        return {
            "total_episodes": total_episodes,
            "successful_episodes": successful_episodes,
            "success_rate": successful_episodes / total_episodes,
            "average_wer": avg_wer,
            "average_der": avg_der,
            "average_cost": avg_cost,
            "average_latency": avg_latency,
            "stage_success_rates": stage_success_rates,
        }

    def generate_summary(
        self, results: list[tuple[TestEpisode, EvaluationMetrics]], aggregate_metrics: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate evaluation summary with pass/fail criteria."""
        summary = {
            "overall_status": "PASS",
            "criteria_met": {},
            "criteria_failed": {},
            "recommendations": [],
        }

        # Check WER criteria (≤12%)
        wer_criteria = aggregate_metrics.get("average_wer", 1.0) <= 0.12
        summary["criteria_met"]["wer"] = wer_criteria
        if not wer_criteria:
            summary["criteria_failed"]["wer"] = (
                f"WER {aggregate_metrics.get('average_wer', 0):.1%} exceeds 12% threshold"
            )
            summary["overall_status"] = "FAIL"

        # Check DER criteria (≤20%)
        der_criteria = aggregate_metrics.get("average_der", 1.0) <= 0.20
        summary["criteria_met"]["der"] = der_criteria
        if not der_criteria:
            summary["criteria_failed"]["der"] = (
                f"DER {aggregate_metrics.get('average_der', 0):.1%} exceeds 20% threshold"
            )
            summary["overall_status"] = "FAIL"

        # Check cost criteria (≤$2.00/episode)
        cost_criteria = aggregate_metrics.get("average_cost", 100.0) <= 2.00
        summary["criteria_met"]["cost"] = cost_criteria
        if not cost_criteria:
            summary["criteria_failed"]["cost"] = (
                f"Cost ${aggregate_metrics.get('average_cost', 0):.2f} exceeds $2.00 threshold"
            )
            summary["overall_status"] = "FAIL"

        # Check latency criteria (≤10min)
        latency_criteria = aggregate_metrics.get("average_latency", 1000.0) <= 600.0  # 10 minutes in seconds
        summary["criteria_met"]["latency"] = latency_criteria
        if not latency_criteria:
            summary["criteria_failed"]["latency"] = (
                f"Latency {aggregate_metrics.get('average_latency', 0):.1f}s exceeds 10min threshold"
            )
            summary["overall_status"] = "FAIL"

        # Generate recommendations
        if not wer_criteria:
            summary["recommendations"].append("Improve transcription accuracy with better ASR models")
        if not der_criteria:
            summary["recommendations"].append("Enhance diarization with speaker embedding models")
        if not cost_criteria:
            summary["recommendations"].append("Optimize cost by using cheaper models for non-critical stages")
        if not latency_criteria:
            summary["recommendations"].append("Reduce latency with parallel processing and caching")

        return summary

    def save_results(self, filepath: str) -> StepResult:
        """Save evaluation results to file."""
        try:
            results_data = {
                "episodes": [ep.to_dict() for ep, _ in self.results],
                "metrics": [m.to_dict() for _, m in self.results],
                "aggregate_metrics": self.calculate_aggregate_metrics(self.results),
                "summary": self.generate_summary(self.results, self.calculate_aggregate_metrics(self.results)),
            }

            with open(filepath, "w") as f:
                json.dump(results_data, f, indent=2)

            return StepResult.ok(data={"filepath": filepath, "results_count": len(self.results)})

        except Exception as e:
            return StepResult.fail(f"Failed to save results: {str(e)}")
