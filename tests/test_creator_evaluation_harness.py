from datetime import datetime

from src.ultimate_discord_intelligence_bot.services.creator_evaluation_harness import (
    CreatorEvaluationHarness,
    EvaluationEpisode,
    EvaluationMetrics,
    EvaluationReport,
)


class TestEvaluationMetrics:
    """Test the EvaluationMetrics dataclass."""

    def test_metrics_creation(self):
        """Test creating EvaluationMetrics."""
        metrics = EvaluationMetrics(
            wer=0.10,
            cer=0.12,
            der=0.18,
            jer=0.20,
            topic_seg_rouge=0.85,
            topic_seg_nmi=0.82,
            claim_extraction_f1=0.83,
            claim_extraction_precision=0.85,
            claim_extraction_recall=0.81,
            source_retrieval_r3=0.88,
            source_retrieval_ndcg=0.91,
            highlight_kendall_tau=0.76,
            highlight_precision=0.78,
            safety_classification_f1=0.94,
            dedup_precision=0.89,
            dedup_recall=0.86,
            avg_cost_usd=1.75,
            avg_latency_seconds=450.0,
            throughput_per_hour=8.5,
        )

        assert metrics.wer == 0.10
        assert metrics.der == 0.18
        assert metrics.avg_cost_usd == 1.75
        assert metrics.avg_latency_seconds == 450.0
        assert metrics.throughput_per_hour == 8.5


class TestEvaluationEpisode:
    """Test the EvaluationEpisode dataclass."""

    def test_episode_creation(self):
        """Test creating EvaluationEpisode."""
        episode = EvaluationEpisode(
            episode_id="test_episode",
            platform="youtube",
            creator="h3podcast",
            duration_seconds=3600,
            wer=0.08,
            cer=0.10,
            der=0.15,
            jer=0.17,
            topic_seg_rouge=0.87,
            topic_seg_nmi=0.84,
            claim_extraction_f1=0.85,
            claim_extraction_precision=0.87,
            claim_extraction_recall=0.83,
            source_retrieval_r3=0.90,
            source_retrieval_ndcg=0.92,
            highlight_kendall_tau=0.78,
            highlight_precision=0.80,
            safety_classification_f1=0.95,
            dedup_precision=0.91,
            dedup_recall=0.88,
            cost_usd=1.50,
            latency_seconds=420.0,
        )

        assert episode.episode_id == "test_episode"
        assert episode.platform == "youtube"
        assert episode.creator == "h3podcast"
        assert episode.duration_seconds == 3600
        assert episode.wer == 0.08
        assert episode.der == 0.15
        assert episode.cost_usd == 1.50
        assert episode.latency_seconds == 420.0


class TestEvaluationReport:
    """Test the EvaluationReport dataclass."""

    def test_report_creation(self):
        """Test creating EvaluationReport."""
        metrics = EvaluationMetrics(
            wer=0.10,
            cer=0.12,
            der=0.18,
            jer=0.20,
            topic_seg_rouge=0.85,
            topic_seg_nmi=0.82,
            claim_extraction_f1=0.83,
            claim_extraction_precision=0.85,
            claim_extraction_recall=0.81,
            source_retrieval_r3=0.88,
            source_retrieval_ndcg=0.91,
            highlight_kendall_tau=0.76,
            highlight_precision=0.78,
            safety_classification_f1=0.94,
            dedup_precision=0.89,
            dedup_recall=0.86,
            avg_cost_usd=1.75,
            avg_latency_seconds=450.0,
            throughput_per_hour=8.5,
        )

        episode = EvaluationEpisode(
            episode_id="test_episode",
            platform="youtube",
            creator="h3podcast",
            duration_seconds=3600,
            wer=0.08,
            cer=0.10,
            der=0.15,
            jer=0.17,
            topic_seg_rouge=0.87,
            topic_seg_nmi=0.84,
            claim_extraction_f1=0.85,
            claim_extraction_precision=0.87,
            claim_extraction_recall=0.83,
            source_retrieval_r3=0.90,
            source_retrieval_ndcg=0.92,
            highlight_kendall_tau=0.78,
            highlight_precision=0.80,
            safety_classification_f1=0.95,
            dedup_precision=0.91,
            dedup_recall=0.88,
            cost_usd=1.50,
            latency_seconds=420.0,
        )

        report = EvaluationReport(
            report_id="test_report_001",
            evaluation_timestamp=datetime.now(),
            dataset_version="1.0",
            episodes_evaluated=1,
            metrics=metrics,
            episode_results=[episode],
            trends={"wer_trend": "stable"},
            regression_alerts=[],
            improvement_opportunities=[],
            summary="Test evaluation summary",
            recommendations=["Test recommendation"],
        )

        assert report.report_id == "test_report_001"
        assert report.episodes_evaluated == 1
        assert len(report.episode_results) == 1
        assert report.metrics.wer == 0.10
        assert report.summary == "Test evaluation summary"


class TestCreatorEvaluationHarness:
    """Test the CreatorEvaluationHarness class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.harness = CreatorEvaluationHarness()

    def test_initialization(self):
        """Test harness initialization."""
        assert self.harness.gold_dataset_path == "gold_dataset.json"
        assert "wer_max" in self.harness.metrics_thresholds
        assert "der_max" in self.harness.metrics_thresholds
        assert "cost_max_usd" in self.harness.metrics_thresholds

    def test_load_gold_dataset(self):
        """Test loading gold dataset."""
        # Use the existing gold dataset file for testing
        annotations = self.harness._load_gold_dataset()
        # Should load the existing gold dataset (10 episodes)
        assert len(annotations) == 10
        assert all("episode_id" in annotation for annotation in annotations)

    def test_evaluate_episode(self):
        """Test evaluating a single episode."""
        annotation = {
            "episode_id": "test_episode",
            "platform": "youtube",
            "creator": "h3podcast",
            "duration_seconds": 3600,
        }

        result = self.harness._evaluate_episode(annotation)

        assert isinstance(result, EvaluationEpisode)
        assert result.episode_id == "test_episode"
        assert result.success is True
        assert result.wer >= 0.0
        assert result.der >= 0.0
        assert result.cost_usd >= 0.0
        assert result.latency_seconds >= 0.0

    def test_calculate_aggregate_metrics(self):
        """Test aggregate metrics calculation."""
        episodes = [
            EvaluationEpisode(
                episode_id="episode_1",
                platform="youtube",
                creator="h3podcast",
                duration_seconds=3600,
                wer=0.08,
                cer=0.10,
                der=0.15,
                jer=0.17,
                topic_seg_rouge=0.87,
                topic_seg_nmi=0.84,
                claim_extraction_f1=0.85,
                claim_extraction_precision=0.87,
                claim_extraction_recall=0.83,
                source_retrieval_r3=0.90,
                source_retrieval_ndcg=0.92,
                highlight_kendall_tau=0.78,
                highlight_precision=0.80,
                safety_classification_f1=0.95,
                dedup_precision=0.91,
                dedup_recall=0.88,
                cost_usd=1.50,
                latency_seconds=420.0,
            ),
            EvaluationEpisode(
                episode_id="episode_2",
                platform="twitch",
                creator="hasanabi",
                duration_seconds=5400,
                wer=0.10,
                cer=0.12,
                der=0.17,
                jer=0.19,
                topic_seg_rouge=0.85,
                topic_seg_nmi=0.82,
                claim_extraction_f1=0.83,
                claim_extraction_precision=0.85,
                claim_extraction_recall=0.81,
                source_retrieval_r3=0.88,
                source_retrieval_ndcg=0.90,
                highlight_kendall_tau=0.76,
                highlight_precision=0.78,
                safety_classification_f1=0.93,
                dedup_precision=0.89,
                dedup_recall=0.86,
                cost_usd=2.00,
                latency_seconds=480.0,
            ),
        ]

        metrics = self.harness._calculate_aggregate_metrics(episodes)

        assert isinstance(metrics, EvaluationMetrics)
        assert metrics.wer == 0.09  # Average of 0.08 and 0.10
        assert metrics.der == 0.16  # Average of 0.15 and 0.17
        assert metrics.avg_cost_usd == 1.75  # Average of 1.50 and 2.00
        assert metrics.avg_latency_seconds == 450.0  # Average of 420 and 480

    def test_analyze_trends(self):
        """Test trend analysis."""
        episodes = [
            EvaluationEpisode(
                episode_id="episode_1",
                platform="youtube",
                creator="h3podcast",
                duration_seconds=3600,
                wer=0.08,
                cer=0.10,
                der=0.15,
                jer=0.17,
                topic_seg_rouge=0.87,
                topic_seg_nmi=0.84,
                claim_extraction_f1=0.85,
                claim_extraction_precision=0.87,
                claim_extraction_recall=0.83,
                source_retrieval_r3=0.90,
                source_retrieval_ndcg=0.92,
                highlight_kendall_tau=0.78,
                highlight_precision=0.80,
                safety_classification_f1=0.95,
                dedup_precision=0.91,
                dedup_recall=0.88,
                cost_usd=1.50,
                latency_seconds=420.0,
            ),
            EvaluationEpisode(
                episode_id="episode_2",
                platform="twitch",
                creator="hasanabi",
                duration_seconds=5400,
                wer=0.10,
                cer=0.12,
                der=0.17,
                jer=0.19,
                topic_seg_rouge=0.85,
                topic_seg_nmi=0.82,
                claim_extraction_f1=0.83,
                claim_extraction_precision=0.85,
                claim_extraction_recall=0.81,
                source_retrieval_r3=0.88,
                source_retrieval_ndcg=0.90,
                highlight_kendall_tau=0.76,
                highlight_precision=0.78,
                safety_classification_f1=0.93,
                dedup_precision=0.89,
                dedup_recall=0.86,
                cost_usd=2.00,
                latency_seconds=480.0,
            ),
        ]

        trends = self.harness._analyze_trends(episodes)

        assert "wer_trend" in trends
        assert "der_trend" in trends
        assert "cost_trend" in trends
        assert "latency_trend" in trends
        assert trends["wer_trend"] == "stable"

    def test_generate_regression_alerts(self):
        """Test regression alert generation."""
        metrics = EvaluationMetrics(
            wer=0.15,
            cer=0.18,
            der=0.25,
            jer=0.27,
            topic_seg_rouge=0.85,
            topic_seg_nmi=0.82,
            claim_extraction_f1=0.83,
            claim_extraction_precision=0.85,
            claim_extraction_recall=0.81,
            source_retrieval_r3=0.88,
            source_retrieval_ndcg=0.91,
            highlight_kendall_tau=0.76,
            highlight_precision=0.78,
            safety_classification_f1=0.94,
            dedup_precision=0.89,
            dedup_recall=0.86,
            avg_cost_usd=2.50,
            avg_latency_seconds=720.0,
            throughput_per_hour=5.0,
        )

        trends = {"wer_trend": "degrading", "cost_trend": "increasing"}

        alerts = self.harness._generate_regression_alerts(metrics, trends)

        assert len(alerts) > 0
        assert any("WER" in alert for alert in alerts)
        assert any("DER" in alert for alert in alerts)
        assert any("cost" in alert.lower() for alert in alerts)

    def test_check_overall_acceptance(self):
        """Test overall acceptance criteria checking."""
        # Test passing metrics
        passing_metrics = EvaluationMetrics(
            wer=0.10,
            cer=0.12,
            der=0.18,
            jer=0.20,
            topic_seg_rouge=0.85,
            topic_seg_nmi=0.82,
            claim_extraction_f1=0.85,
            claim_extraction_precision=0.87,
            claim_extraction_recall=0.83,
            source_retrieval_r3=0.90,
            source_retrieval_ndcg=0.92,
            highlight_kendall_tau=0.76,
            highlight_precision=0.78,
            safety_classification_f1=0.94,
            dedup_precision=0.89,
            dedup_recall=0.86,
            avg_cost_usd=1.75,
            avg_latency_seconds=450.0,
            throughput_per_hour=8.5,
        )

        assert self.harness._check_overall_acceptance(passing_metrics) is True

        # Test failing metrics
        failing_metrics = EvaluationMetrics(
            wer=0.15,
            cer=0.18,
            der=0.25,
            jer=0.27,
            topic_seg_rouge=0.85,
            topic_seg_nmi=0.82,
            claim_extraction_f1=0.75,
            claim_extraction_precision=0.77,
            claim_extraction_recall=0.73,
            source_retrieval_r3=0.70,
            source_retrieval_ndcg=0.72,
            highlight_kendall_tau=0.76,
            highlight_precision=0.78,
            safety_classification_f1=0.94,
            dedup_precision=0.89,
            dedup_recall=0.86,
            avg_cost_usd=2.50,
            avg_latency_seconds=720.0,
            throughput_per_hour=5.0,
        )

        assert self.harness._check_overall_acceptance(failing_metrics) is False

    def test_serialize_metrics(self):
        """Test metrics serialization."""
        metrics = EvaluationMetrics(
            wer=0.10,
            cer=0.12,
            der=0.18,
            jer=0.20,
            topic_seg_rouge=0.85,
            topic_seg_nmi=0.82,
            claim_extraction_f1=0.83,
            claim_extraction_precision=0.85,
            claim_extraction_recall=0.81,
            source_retrieval_r3=0.88,
            source_retrieval_ndcg=0.91,
            highlight_kendall_tau=0.76,
            highlight_precision=0.78,
            safety_classification_f1=0.94,
            dedup_precision=0.89,
            dedup_recall=0.86,
            avg_cost_usd=1.75,
            avg_latency_seconds=450.0,
            throughput_per_hour=8.5,
        )

        serialized = self.harness._serialize_metrics(metrics)

        assert isinstance(serialized, dict)
        assert "wer" in serialized
        assert "der" in serialized
        assert "avg_cost_usd" in serialized
        assert "avg_latency_seconds" in serialized
        assert serialized["wer"] == 0.10
        assert serialized["der"] == 0.18
        assert serialized["avg_cost_usd"] == 1.75

    def test_run_evaluation_with_mock_data(self):
        """Test running evaluation with mock data."""
        # Use the existing gold dataset for testing
        result = self.harness.run_evaluation()

        assert result.success
        data = result.data["data"]
        assert "report_id" in data
        assert "episodes_evaluated" in data
        assert "overall_passed" in data
        assert "metrics" in data
        assert "report_path" in data

        # Check that metrics are reasonable
        metrics = data["metrics"]
        assert 0.0 <= metrics["wer"] <= 1.0
        assert 0.0 <= metrics["der"] <= 1.0
        assert metrics["avg_cost_usd"] >= 0.0
        assert metrics["avg_latency_seconds"] >= 0.0

    def test_evaluate_episode_with_error(self):
        """Test episode evaluation with error."""
        # Create annotation that will cause an error
        annotation = {
            "episode_id": "error_episode",
            "platform": "youtube",
            "creator": "h3podcast",
            "duration_seconds": "invalid_duration",  # This should cause an error
        }

        result = self.harness._evaluate_episode(annotation)

        assert result.success is False
        assert result.error_message is not None
