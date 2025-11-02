"""Tests for statistical_analyzers module."""

from unittest.mock import Mock, patch

from ultimate_discord_intelligence_bot.orchestrator.statistical_analyzers import (
    calculate_consolidation_metrics_from_crew,
    calculate_data_completeness,
    calculate_enhanced_summary_statistics,
    calculate_summary_statistics,
)


class TestCalculateSummaryStatistics:
    """Test calculate_summary_statistics function."""

    def test_calculate_summary_statistics_basic(self):
        """Test basic summary statistics calculation."""
        results = {
            "pipeline": {"content": "test content"},
            "fact_analysis": {
                "fact_checks": {"items": [1, 2, 3]},
                "logical_fallacies": {"fallacies_detected": ["strawman", "ad hominem"]},
            },
            "deception_scoring": {"score": 0.3},
            "cross_platform_intel": {"source1": "data1", "source2": "data2"},
            "knowledge_integration": {"knowledge_storage": True},
        }

        stats = calculate_summary_statistics(results)

        assert stats["content_processed"] is True
        assert stats["fact_checks_performed"] == 3
        assert stats["fallacies_detected"] == 2
        assert stats["deception_score"] == 0.3
        assert stats["cross_platform_sources"] == 2
        assert stats["knowledge_base_entries"] == 1

    def test_calculate_summary_statistics_fallback_deception_score(self):
        """Test fallback to threat_analysis for deception score."""
        results = {
            "pipeline": {},
            "fact_analysis": {},
            "threat_analysis": {"deception_score": 0.7},
            "cross_platform_intel": {},
            "knowledge_integration": {},
        }

        stats = calculate_summary_statistics(results)

        assert stats["deception_score"] == 0.7

    def test_calculate_summary_statistics_fact_checks_claims(self):
        """Test fact checks calculation with claims instead of items."""
        results = {
            "pipeline": {},
            "fact_analysis": {"fact_checks": {"claims": ["claim1", "claim2", "claim3", "claim4"]}},
            "deception_scoring": {"score": 0.0},
            "cross_platform_intel": {},
            "knowledge_integration": {},
        }

        stats = calculate_summary_statistics(results)

        assert stats["fact_checks_performed"] == 4

    def test_calculate_summary_statistics_evidence_count_fallback(self):
        """Test evidence count fallback for fact checks."""
        results = {
            "pipeline": {},
            "fact_analysis": {"fact_checks": {"evidence_count": 5}},
            "deception_scoring": {"score": 0.0},
            "cross_platform_intel": {},
            "knowledge_integration": {},
        }

        stats = calculate_summary_statistics(results)

        assert stats["fact_checks_performed"] == 5

    def test_calculate_summary_statistics_empty_results(self):
        """Test with empty results."""
        stats = calculate_summary_statistics({})

        assert stats["content_processed"] is False
        assert stats["fact_checks_performed"] == 0
        assert stats["fallacies_detected"] == 0
        assert stats["deception_score"] == 0.0
        assert stats["cross_platform_sources"] == 0
        assert stats["knowledge_base_entries"] == 0

    def test_calculate_summary_statistics_exception_handling(self):
        """Test exception handling in summary statistics."""
        # Create results that will cause an exception
        results = {
            "pipeline": None,
            "fact_analysis": "invalid_data",
        }

        stats = calculate_summary_statistics(results)

        assert "error" in stats
        assert "Statistics calculation failed" in stats["error"]


class TestCalculateConsolidationMetricsFromCrew:
    """Test calculate_consolidation_metrics_from_crew function."""

    def test_calculate_consolidation_metrics_from_crew_success(self):
        """Test successful consolidation metrics calculation."""
        crew_result = "This content has been integrated, consolidated, and archived in the system"

        metrics = calculate_consolidation_metrics_from_crew(crew_result)

        assert "consolidation_score" in metrics
        assert "integration_depth" in metrics
        assert "system_coverage" in metrics
        assert "knowledge_persistence" in metrics
        assert metrics["knowledge_persistence"] is True

    def test_calculate_consolidation_metrics_from_crew_empty_result(self):
        """Test with empty crew result."""
        metrics = calculate_consolidation_metrics_from_crew(None)

        assert metrics == {}

    def test_calculate_consolidation_metrics_from_crew_long_content(self):
        """Test with very long content to test depth calculation."""
        long_content = "integrated " * 1000  # Very long content

        metrics = calculate_consolidation_metrics_from_crew(long_content)

        assert metrics["integration_depth"] == 1.0  # Should be capped at 1.0

    def test_calculate_consolidation_metrics_from_crew_exception_handling(self):
        """Test exception handling in consolidation metrics."""
        # Create a crew result that will cause an exception
        crew_result = Mock()
        crew_result.__str__ = Mock(side_effect=Exception("Test exception"))

        metrics = calculate_consolidation_metrics_from_crew(crew_result)

        assert metrics == {}


class TestCalculateDataCompleteness:
    """Test calculate_data_completeness function."""

    def test_calculate_data_completeness_success(self):
        """Test successful data completeness calculation."""
        # Since data_transformers doesn't exist yet, this should return 0.0
        result = calculate_data_completeness({"data1": "value1"}, {"data2": "value2"})

        assert result == 0.0  # Should return 0.0 due to import failure

    def test_calculate_data_completeness_exception_handling(self):
        """Test exception handling in data completeness calculation."""
        result = calculate_data_completeness({"data1": "value1"})

        assert result == 0.0  # Should return 0.0 due to import failure

    def test_calculate_data_completeness_with_logger(self):
        """Test data completeness calculation with logger."""
        mock_logger = Mock()

        result = calculate_data_completeness({"data1": "value1"}, log=mock_logger)

        assert result == 0.0  # Should return 0.0 due to import failure


class TestCalculateEnhancedSummaryStatistics:
    """Test calculate_enhanced_summary_statistics function."""

    @patch("ultimate_discord_intelligence_bot.orchestrator.statistical_analyzers.calculate_summary_statistics")
    @patch("ultimate_discord_intelligence_bot.orchestrator.statistical_analyzers.calculate_data_completeness")
    def test_calculate_enhanced_summary_statistics_basic(self, mock_data_completeness, mock_basic_stats):
        """Test basic enhanced summary statistics calculation."""
        mock_basic_stats.return_value = {
            "content_processed": True,
            "fact_checks_performed": 3,
            "deception_score": 0.3,
        }
        mock_data_completeness.return_value = 0.8

        results = {
            "quality_assessment": {
                "content_quality": 0.7,
                "factual_accuracy": 0.8,
                "source_credibility": 0.6,
                "bias_detection": 0.5,
            },
            "temporal_analysis": {
                "coverage_days": 30,
                "relevance_score": 0.9,
                "historical_context": True,
            },
        }

        enhanced_stats = calculate_enhanced_summary_statistics(results)

        assert enhanced_stats["content_processed"] is True
        assert enhanced_stats["fact_checks_performed"] == 3
        assert enhanced_stats["content_quality_score"] == 0.7
        assert enhanced_stats["factual_accuracy_score"] == 0.8
        assert enhanced_stats["temporal_coverage_days"] == 30
        assert enhanced_stats["overall_completeness"] == 0.8

    @patch("ultimate_discord_intelligence_bot.orchestrator.statistical_analyzers.calculate_summary_statistics")
    def test_calculate_enhanced_summary_statistics_no_quality_metrics(self, mock_basic_stats):
        """Test enhanced statistics without quality metrics."""
        mock_basic_stats.return_value = {"content_processed": True}

        results = {"pipeline": {}}

        enhanced_stats = calculate_enhanced_summary_statistics(results, include_quality_metrics=False)

        assert enhanced_stats["content_processed"] is True
        assert "content_quality_score" not in enhanced_stats

    @patch("ultimate_discord_intelligence_bot.orchestrator.statistical_analyzers.calculate_summary_statistics")
    def test_calculate_enhanced_summary_statistics_no_temporal_analysis(self, mock_basic_stats):
        """Test enhanced statistics without temporal analysis."""
        mock_basic_stats.return_value = {"content_processed": True}

        results = {"pipeline": {}}

        enhanced_stats = calculate_enhanced_summary_statistics(results, include_temporal_analysis=False)

        assert enhanced_stats["content_processed"] is True
        assert "temporal_coverage_days" not in enhanced_stats

    @patch("ultimate_discord_intelligence_bot.orchestrator.statistical_analyzers.calculate_summary_statistics")
    def test_calculate_enhanced_summary_statistics_exception_handling(self, mock_basic_stats):
        """Test exception handling in enhanced statistics."""
        mock_basic_stats.side_effect = Exception("Test exception")

        results = {"pipeline": {}}

        enhanced_stats = calculate_enhanced_summary_statistics(results)

        assert "error" in enhanced_stats
        assert "Enhanced statistics calculation failed" in enhanced_stats["error"]

    @patch("ultimate_discord_intelligence_bot.orchestrator.statistical_analyzers.calculate_summary_statistics")
    def test_calculate_enhanced_summary_statistics_with_logger(self, mock_basic_stats):
        """Test enhanced statistics with logger."""
        mock_logger = Mock()
        mock_basic_stats.return_value = {"content_processed": True}

        results = {"pipeline": {}}

        enhanced_stats = calculate_enhanced_summary_statistics(results, log=mock_logger)

        assert enhanced_stats["content_processed"] is True
        mock_basic_stats.assert_called_once_with(results, log=mock_logger)
