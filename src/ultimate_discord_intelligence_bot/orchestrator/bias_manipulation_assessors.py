"""Bias and manipulation assessment functions for content analysis.

This module provides functions for assessing bias levels, emotional manipulation,
and logical consistency in the analysis pipeline.
"""

import logging
from typing import Any

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


def assess_bias_levels(
    analysis_data: dict[str, Any] | None,
    verification_data: dict[str, Any] | None,
    logger_instance: logging.Logger | None = None,
) -> float:
    """Score how balanced the content is based on bias indicators and sentiment spread.

    Args:
        analysis_data: Content analysis results
        verification_data: Verification analysis results
        logger_instance: Optional logger instance

    Returns:
        Bias score between 0.0 (highly biased) and 1.0 (balanced)
    """
    _logger = logger_instance or logger
    try:
        base_score = 0.7
        bias_signals = []

        if isinstance(verification_data, dict):
            indicators = verification_data.get("bias_indicators")
            if isinstance(indicators, list):
                bias_signals = indicators
            elif isinstance(indicators, dict):
                extracted = indicators.get("signals")
                if isinstance(extracted, list):
                    bias_signals = extracted

        bias_penalty = min(0.5, len(bias_signals) * 0.1)

        sentiment = analysis_data.get("sentiment_analysis") if isinstance(analysis_data, dict) else {}
        if isinstance(sentiment, dict):
            positive = sentiment.get("positive") or sentiment.get("positives")
            negative = sentiment.get("negative") or sentiment.get("negatives")
            if isinstance(positive, (int, float)) and isinstance(negative, (int, float)):
                total = positive + negative
                if total:
                    swing = abs(positive - negative) / total
                    bias_penalty += min(0.3, swing * 0.3)
            if sentiment.get("overall_sentiment") == "neutral":
                bias_penalty = max(0.0, bias_penalty - 0.05)

        score = base_score - bias_penalty
        return clamp_score(round(score, 3))
    except Exception as exc:
        _logger.debug("Bias assessment fallback due to error: %s", exc)
        return 0.5


def assess_emotional_manipulation(
    analysis_data: dict[str, Any] | None,
    logger_instance: logging.Logger | None = None,
) -> float:
    """Estimate the level of emotional manipulation present in the content.

    Args:
        analysis_data: Content analysis results
        logger_instance: Optional logger instance

    Returns:
        Manipulation resistance score between 0.0 (high manipulation) and 1.0 (low manipulation)
    """
    _logger = logger_instance or logger
    try:
        sentiment = analysis_data.get("sentiment_analysis") if isinstance(analysis_data, dict) else {}
        if not isinstance(sentiment, dict) or not sentiment:
            return 0.6

        intensity = sentiment.get("intensity")
        if isinstance(intensity, (int, float)):
            score = 1.0 - min(0.8, float(intensity) * 0.5)
        else:
            positive = sentiment.get("positive") or sentiment.get("positives") or 0.0
            negative = sentiment.get("negative") or sentiment.get("negatives") or 0.0
            if not isinstance(positive, (int, float)):
                positive = 0.0
            if not isinstance(negative, (int, float)):
                negative = 0.0

            total = positive + negative
            if total > 0:
                swing = abs(positive - negative) / total
                score = 1.0 - min(0.8, swing * 0.5)
            else:
                score = 0.7

        return clamp_score(round(score, 3))
    except Exception as exc:
        _logger.debug("Emotional manipulation assessment failed: %s", exc)
        return 0.6


def assess_logical_consistency(
    verification_data: dict[str, Any] | None,
    logical_analysis: dict[str, Any] | None = None,
    logger_instance: logging.Logger | None = None,
) -> float:
    """Evaluate logical consistency based on verification and logical analysis.

    Args:
        verification_data: Verification analysis results
        logical_analysis: Optional logical analysis results
        logger_instance: Optional logger instance

    Returns:
        Logical consistency score between 0.0 and 1.0
    """
    _logger = logger_instance or logger
    try:
        score = 0.6  # Base score

        # Check logical analysis
        if isinstance(logical_analysis, dict):
            fallacies = logical_analysis.get("fallacies", [])
            if isinstance(fallacies, list):
                # More fallacies = lower consistency
                fallacy_penalty = min(0.4, len(fallacies) * 0.1)
                score -= fallacy_penalty

            reasoning_quality = logical_analysis.get("reasoning_quality")
            if isinstance(reasoning_quality, (int, float)):
                score = (score * 0.5) + (clamp_score(float(reasoning_quality)) * 0.5)

        # Check verification data
        if isinstance(verification_data, dict):
            logical_check = verification_data.get("logical_consistency")
            if isinstance(logical_check, dict):
                consistency_score = logical_check.get("score")
                if isinstance(consistency_score, (int, float)):
                    score = (score * 0.5) + (clamp_score(float(consistency_score)) * 0.5)

        return clamp_score(round(score, 3))
    except Exception as exc:
        _logger.debug("Logical consistency assessment failed: %s", exc)
        return 0.6
