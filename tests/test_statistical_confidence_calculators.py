"""Tests for statistical confidence calculators module."""

from unittest.mock import Mock

from ultimate_discord_intelligence_bot.orchestrator.statistical_confidence_calculators import (
    calculate_confidence_interval,
    calculate_confidence_score,
    calculate_reliability_score,
    calculate_standard_error,
    calculate_statistical_significance,
)


class TestCalculateConfidenceInterval:
    """Test confidence interval calculation."""

    def test_calculate_confidence_interval_normal_data(self):
        """Test confidence interval with normal data."""
        data_points = [0.1, 0.2, 0.3, 0.4, 0.5]

        lower, upper = calculate_confidence_interval(data_points)

        assert lower >= 0.0
        assert upper <= 1.0
        assert lower < upper

    def test_calculate_confidence_interval_empty_data(self):
        """Test confidence interval with empty data."""
        lower, upper = calculate_confidence_interval([])

        assert lower == 0.0
        assert upper == 1.0

    def test_calculate_confidence_interval_single_point(self):
        """Test confidence interval with single data point."""
        lower, upper = calculate_confidence_interval([0.5])

        assert lower == 0.0
        assert upper == 1.0

    def test_calculate_confidence_interval_two_points(self):
        """Test confidence interval with two data points."""
        data_points = [0.3, 0.7]

        lower, upper = calculate_confidence_interval(data_points)

        assert lower >= 0.0
        assert upper <= 1.0
        assert lower < upper

    def test_calculate_confidence_interval_exception_handling(self):
        """Test confidence interval exception handling."""
        data_points = Mock()
        data_points.__iter__ = Mock(side_effect=Exception("Test error"))

        lower, upper = calculate_confidence_interval(data_points)

        assert lower == 0.0
        assert upper == 1.0


class TestCalculateStandardError:
    """Test standard error calculation."""

    def test_calculate_standard_error_normal_data(self):
        """Test standard error with normal data."""
        data_points = [0.1, 0.2, 0.3, 0.4, 0.5]

        result = calculate_standard_error(data_points)

        assert result >= 0.0

    def test_calculate_standard_error_empty_data(self):
        """Test standard error with empty data."""
        result = calculate_standard_error([])
        assert result == 0.0

    def test_calculate_standard_error_single_point(self):
        """Test standard error with single data point."""
        result = calculate_standard_error([0.5])
        assert result == 0.0

    def test_calculate_standard_error_two_points(self):
        """Test standard error with two data points."""
        data_points = [0.3, 0.7]

        result = calculate_standard_error(data_points)

        assert result >= 0.0

    def test_calculate_standard_error_exception_handling(self):
        """Test standard error exception handling."""
        data_points = Mock()
        data_points.__iter__ = Mock(side_effect=Exception("Test error"))

        result = calculate_standard_error(data_points)
        assert result == 0.0


class TestCalculateConfidenceScore:
    """Test confidence score calculation."""

    def test_calculate_confidence_score_consistent_data(self):
        """Test confidence score with consistent data."""
        data_points = [0.5, 0.5, 0.5, 0.5]

        result = calculate_confidence_score(data_points)

        assert result > 0.0  # High consistency should give good confidence

    def test_calculate_confidence_score_inconsistent_data(self):
        """Test confidence score with inconsistent data."""
        data_points = [0.1, 0.9, 0.2, 0.8]

        result = calculate_confidence_score(data_points)

        assert result < 1.0  # Low consistency should give lower confidence

    def test_calculate_confidence_score_with_target(self):
        """Test confidence score with target value."""
        data_points = [0.5, 0.6, 0.4, 0.5]
        target_value = 0.5

        result = calculate_confidence_score(data_points, target_value)

        assert 0.0 <= result <= 1.0

    def test_calculate_confidence_score_empty_data(self):
        """Test confidence score with empty data."""
        result = calculate_confidence_score([])
        assert result == 0.0

    def test_calculate_confidence_score_single_point(self):
        """Test confidence score with single data point."""
        result = calculate_confidence_score([0.5])
        assert result == 1.0

    def test_calculate_confidence_score_zero_mean(self):
        """Test confidence score with zero mean."""
        data_points = [0.0, 0.0, 0.0]

        result = calculate_confidence_score(data_points)

        assert result == 0.0

    def test_calculate_confidence_score_exception_handling(self):
        """Test confidence score exception handling."""
        data_points = Mock()
        data_points.__iter__ = Mock(side_effect=Exception("Test error"))

        result = calculate_confidence_score(data_points)
        assert result == 0.0


class TestCalculateReliabilityScore:
    """Test reliability score calculation."""

    def test_calculate_reliability_score_increasing_trend(self):
        """Test reliability score with increasing trend."""
        data_points = [0.1, 0.2, 0.3, 0.4, 0.5]

        result = calculate_reliability_score(data_points)

        assert 0.0 <= result <= 1.0

    def test_calculate_reliability_score_decreasing_trend(self):
        """Test reliability score with decreasing trend."""
        data_points = [0.5, 0.4, 0.3, 0.2, 0.1]

        result = calculate_reliability_score(data_points)

        assert 0.0 <= result <= 1.0

    def test_calculate_reliability_score_stable_trend(self):
        """Test reliability score with stable trend."""
        data_points = [0.5, 0.5, 0.5, 0.5, 0.5]

        result = calculate_reliability_score(data_points)

        assert result > 0.0  # Stable data should be reliable

    def test_calculate_reliability_score_empty_data(self):
        """Test reliability score with empty data."""
        result = calculate_reliability_score([])
        assert result == 0.0

    def test_calculate_reliability_score_single_point(self):
        """Test reliability score with single data point."""
        result = calculate_reliability_score([0.5])
        assert result == 0.0

    def test_calculate_reliability_score_two_points(self):
        """Test reliability score with two data points."""
        data_points = [0.3, 0.7]

        result = calculate_reliability_score(data_points)

        assert 0.0 <= result <= 1.0

    def test_calculate_reliability_score_exception_handling(self):
        """Test reliability score exception handling."""
        data_points = Mock()
        data_points.__iter__ = Mock(side_effect=Exception("Test error"))

        result = calculate_reliability_score(data_points)
        assert result == 0.0


class TestCalculateStatisticalSignificance:
    """Test statistical significance calculation."""

    def test_calculate_statistical_significance_different_groups(self):
        """Test statistical significance with clearly different groups."""
        group1 = [0.1, 0.2, 0.3]
        group2 = [0.8, 0.9, 1.0]

        result = calculate_statistical_significance(group1, group2)

        assert result > 0.0  # Should detect significant difference

    def test_calculate_statistical_significance_similar_groups(self):
        """Test statistical significance with similar groups."""
        group1 = [0.4, 0.5, 0.6]
        group2 = [0.45, 0.55, 0.65]

        result = calculate_statistical_significance(group1, group2)

        assert 0.0 <= result <= 1.0

    def test_calculate_statistical_significance_empty_group1(self):
        """Test statistical significance with empty group1."""
        result = calculate_statistical_significance([], [0.1, 0.2])
        assert result == 0.0

    def test_calculate_statistical_significance_empty_group2(self):
        """Test statistical significance with empty group2."""
        result = calculate_statistical_significance([0.1, 0.2], [])
        assert result == 0.0

    def test_calculate_statistical_significance_insufficient_data(self):
        """Test statistical significance with insufficient data."""
        result = calculate_statistical_significance([0.5], [0.6])
        assert result == 0.5  # Fallback for insufficient data

    def test_calculate_statistical_significance_zero_pooled_se(self):
        """Test statistical significance with zero pooled standard error."""
        group1 = [0.5, 0.5, 0.5]
        group2 = [0.5, 0.5, 0.5]

        result = calculate_statistical_significance(group1, group2)

        assert result == 0.0

    def test_calculate_statistical_significance_exception_handling(self):
        """Test statistical significance exception handling."""
        group1 = Mock()
        group1.__iter__ = Mock(side_effect=Exception("Test error"))

        result = calculate_statistical_significance(group1, [0.1, 0.2])
        assert result == 0.0
