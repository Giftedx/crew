"""Statistical confidence calculation utilities.

This module contains functions that calculate confidence intervals,
statistical measures, and mathematical confidence metrics.

Extracted from confidence_calculators.py to improve maintainability and organization.
"""

import logging
import math
from statistics import NormalDist


logger = logging.getLogger(__name__)


_NORMAL_DIST = NormalDist()
_CONFIDENCE_LEVEL_EPSILON = 1e-6


def _normalize_confidence_level(confidence_level: float, log: logging.Logger) -> float:
    """Normalize confidence level to an open interval (0, 1)."""

    default_level = 0.95

    if not 0 < confidence_level < 1:
        log.warning(
            "Invalid confidence level %.4f received; defaulting to %.2f.",
            confidence_level,
            default_level,
        )
        return default_level

    if confidence_level <= _CONFIDENCE_LEVEL_EPSILON:
        adjusted = _CONFIDENCE_LEVEL_EPSILON
        log.debug(
            "Confidence level %.6f too low; clamped to %.6f to avoid infinite z-score.",
            confidence_level,
            adjusted,
        )
        return adjusted

    if confidence_level >= 1 - _CONFIDENCE_LEVEL_EPSILON:
        adjusted = 1 - _CONFIDENCE_LEVEL_EPSILON
        log.debug(
            "Confidence level %.6f too high; clamped to %.6f to avoid infinite z-score.",
            confidence_level,
            adjusted,
        )
        return adjusted

    return confidence_level


def calculate_confidence_interval(
    data_points: list[float],
    confidence_level: float = 0.95,
    log: logging.Logger | None = None,
) -> tuple[float, float]:
    """Calculate confidence interval for a set of data points.

    Args:
        data_points: List of numeric data points
        confidence_level: Confidence level (default 0.95 for 95% confidence)
        log: Optional logger instance

    Returns:
        Tuple of (lower_bound, upper_bound) confidence interval
    """
    try:
        if not log:
            log = logger

        if not data_points or len(data_points) < 2:
            log.debug(
                "Insufficient data points for confidence interval calculation. count=%d",
                len(data_points) if data_points else 0,
            )
            return (0.0, 1.0)

        # Simple confidence interval calculation
        mean_value = sum(data_points) / len(data_points)

        # Calculate standard deviation
        variance = sum((x - mean_value) ** 2 for x in data_points) / (len(data_points) - 1)
        std_dev = math.sqrt(variance)

        # Calculate margin of error using the requested confidence level
        n = len(data_points)

        normalized_confidence = _normalize_confidence_level(confidence_level, log)
        alpha = 1.0 - normalized_confidence
        z_score = _NORMAL_DIST.inv_cdf(1.0 - alpha / 2.0)
        margin_of_error = z_score * std_dev / math.sqrt(n)

        lower_bound = max(0.0, mean_value - margin_of_error)
        upper_bound = min(1.0, mean_value + margin_of_error)

        log.debug(
            "Calculated confidence interval with confidence_level=%.4f, z_score=%.4f, n=%d, margin=%.4f.",
            normalized_confidence,
            z_score,
            n,
            margin_of_error,
        )

        return (lower_bound, upper_bound)

    except Exception as exc:
        if log:
            log.exception("Failed to calculate confidence interval: %s", exc)
        return (0.0, 1.0)


def calculate_standard_error(data_points: list[float], log: logging.Logger | None = None) -> float:
    """Calculate standard error for a set of data points.

    Args:
        data_points: List of numeric data points
        log: Optional logger instance

    Returns:
        Standard error value
    """
    try:
        if not log:
            log = logger

        if not data_points or len(data_points) < 2:
            return 0.0

        # Calculate standard deviation
        mean_value = sum(data_points) / len(data_points)
        variance = sum((x - mean_value) ** 2 for x in data_points) / (len(data_points) - 1)
        std_dev = math.sqrt(variance)

        # Standard error = standard deviation / sqrt(n)
        n = len(data_points)
        return std_dev / math.sqrt(n)

    except Exception as exc:
        if log:
            log.exception("Failed to calculate standard error: %s", exc)
        return 0.0


def calculate_confidence_score(
    data_points: list[float],
    target_value: float | None = None,
    log: logging.Logger | None = None,
) -> float:
    """Calculate confidence score based on data consistency.

    Args:
        data_points: List of numeric data points
        target_value: Optional target value to compare against
        log: Optional logger instance

    Returns:
        Confidence score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not data_points:
            return 0.0

        if len(data_points) == 1:
            return 1.0  # Perfect confidence with single data point

        # Calculate coefficient of variation (CV) as inverse confidence measure
        mean_value = sum(data_points) / len(data_points)

        if mean_value == 0:
            return 0.0

        variance = sum((x - mean_value) ** 2 for x in data_points) / (len(data_points) - 1)
        std_dev = math.sqrt(variance)

        cv = std_dev / mean_value

        # Convert CV to confidence score (lower CV = higher confidence)
        confidence = max(0.0, 1.0 - cv)

        # If target value provided, factor in proximity to target
        if target_value is not None:
            proximity_score = 1.0 - abs(mean_value - target_value)
            confidence = (confidence + proximity_score) / 2.0

        return min(confidence, 1.0)

    except Exception as exc:
        if log:
            log.exception("Failed to calculate confidence score: %s", exc)
        return 0.0


def calculate_reliability_score(data_points: list[float], log: logging.Logger | None = None) -> float:
    """Calculate reliability score based on data consistency over time.

    Args:
        data_points: List of numeric data points (chronologically ordered)
        log: Optional logger instance

    Returns:
        Reliability score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not data_points or len(data_points) < 2:
            return 0.0

        # Calculate trend consistency
        differences = [data_points[i] - data_points[i - 1] for i in range(1, len(data_points))]

        if not differences:
            return 1.0

        # Check for consistent direction (all positive, all negative, or stable)
        positive_count = sum(1 for diff in differences if diff > 0.01)
        negative_count = sum(1 for diff in differences if diff < -0.01)
        stable_count = len(differences) - positive_count - negative_count

        # Calculate consistency score
        max_direction = max(positive_count, negative_count, stable_count)
        consistency_score = max_direction / len(differences)

        # Factor in variance (lower variance = higher reliability)
        mean_diff = sum(differences) / len(differences)
        variance = sum((diff - mean_diff) ** 2 for diff in differences) / len(differences)

        # Normalize variance to 0-1 range (inverse relationship)
        variance_score = max(0.0, 1.0 - variance)

        # Combine consistency and variance scores
        reliability = (consistency_score + variance_score) / 2.0

        return min(reliability, 1.0)

    except Exception as exc:
        if log:
            log.exception("Failed to calculate reliability score: %s", exc)
        return 0.0


def calculate_statistical_significance(
    group1: list[float], group2: list[float], log: logging.Logger | None = None
) -> float:
    """Calculate statistical significance between two groups (simplified t-test).

    Args:
        group1: First group of data points
        group2: Second group of data points
        log: Optional logger instance

    Returns:
        Statistical significance score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not group1 or not group2:
            return 0.0

        if len(group1) < 2 or len(group2) < 2:
            return 0.5  # Insufficient data for reliable significance test

        # Calculate means
        mean1 = sum(group1) / len(group1)
        mean2 = sum(group2) / len(group2)

        # Calculate standard deviations
        var1 = sum((x - mean1) ** 2 for x in group1) / (len(group1) - 1)
        var2 = sum((x - mean2) ** 2 for x in group2) / (len(group2) - 1)

        math.sqrt(var1)
        math.sqrt(var2)

        # Calculate pooled standard error
        n1, n2 = len(group1), len(group2)
        pooled_se = math.sqrt((var1 / n1) + (var2 / n2))

        if pooled_se == 0:
            return 0.0

        # Calculate t-statistic
        t_stat = abs(mean1 - mean2) / pooled_se

        # Simplified significance calculation (not exact p-value)
        # Higher t-statistic = higher significance
        significance = min(t_stat / 3.0, 1.0)  # Normalize to 0-1 range

        return significance

    except Exception as exc:
        if log:
            log.exception("Failed to calculate statistical significance: %s", exc)
        return 0.0
