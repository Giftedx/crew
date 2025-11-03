"""Quality calculation functions for analysis pipeline.

This module provides utility functions for calculating overall quality metrics,
trends, and confidence scores in the analysis pipeline.
"""

import logging


# Module-level logger
logger = logging.getLogger(__name__)


def clamp_score(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Clamp helper to keep quality metrics within expected bounds.

    Args:
        value: Value to clamp
        minimum: Minimum allowed value
        maximum: Maximum allowed value

    Returns:
        Clamped value between minimum and maximum
    """
    try:
        return max(minimum, min(maximum, float(value)))
    except Exception:
        return minimum


def assess_quality_trend(ai_quality_score: float) -> str:
    """Assess the quality trend based on AI quality score.

    Args:
        ai_quality_score: Quality score from 0.0 to 1.0

    Returns:
        Trend description ("improving", "stable", "declining")
    """
    try:
        if ai_quality_score >= 0.75:
            return "improving"
        elif ai_quality_score >= 0.5:
            return "stable"
        else:
            return "declining"
    except Exception:
        return "stable"


def calculate_overall_confidence(
    *data_sources,
    logger_instance: logging.Logger | None = None,
) -> float:
    """Calculate overall confidence across all data sources.

    Args:
        *data_sources: Variable number of data dictionaries
        logger_instance: Optional logger instance

    Returns:
        Confidence score between 0.0 and 1.0
    """
    _logger = logger_instance or logger
    try:
        valid_sources = sum(1 for source in data_sources if source and isinstance(source, dict))
        return min(valid_sources * 0.15, 0.9)
    except Exception as exc:
        _logger.debug("Overall confidence calculation failed: %s", exc)
        return 0.5
