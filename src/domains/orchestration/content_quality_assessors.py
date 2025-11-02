"""Content quality assessment functions for analysis pipeline.

This module provides functions for assessing content coherence and transcript quality
in the analysis pipeline.
"""

import logging
from typing import Any


# Module-level logger
logger = logging.getLogger(__name__)


def assess_content_coherence(
    analysis_data: dict[str, Any],
    logger_instance: logging.Logger | None = None,
) -> float:
    """Assess the coherence of analyzed content based on transcript structure and logical flow.

    Args:
        analysis_data: Dictionary containing analysis results
        logger_instance: Optional logger instance

    Returns:
        Coherence score between 0.0 and 1.0
    """
    _logger = logger_instance or logger
    try:
        # Extract transcript and analysis data
        transcript = analysis_data.get("transcript", "")
        linguistic_patterns = analysis_data.get("linguistic_patterns", {})
        sentiment_analysis = analysis_data.get("sentiment_analysis", {})
        content_metadata = analysis_data.get("content_metadata", {})

        coherence_score = 0.5  # Base neutral score

        # Factor 1: Transcript length and structure
        if transcript:
            word_count = len(transcript.split())
            if word_count > 100:
                coherence_score += 0.1
            elif word_count < 20:
                coherence_score -= 0.2

            # Check for structured content (paragraphs, sentences)
            sentences = transcript.split(".")
            if len(sentences) > 3:
                coherence_score += 0.1

        # Factor 2: Linguistic patterns consistency
        if linguistic_patterns and isinstance(linguistic_patterns, dict):
            coherence_score += 0.1

        # Factor 3: Sentiment consistency
        if sentiment_analysis and isinstance(sentiment_analysis, dict):
            coherence_score += 0.05

        # Factor 4: Content metadata completeness
        metadata_completeness = sum(
            1 for key in ["title", "platform", "word_count", "quality_score"] if content_metadata.get(key) is not None
        )
        metadata_bonus = (metadata_completeness / 4) * 0.1
        coherence_score += metadata_bonus

        # Ensure score is within valid range
        return max(0.0, min(1.0, coherence_score))

    except Exception as exc:
        _logger.debug("Content coherence assessment failed: %s", exc)
        return 0.5


def assess_transcript_quality(
    transcript: str,
    logger_instance: logging.Logger | None = None,
) -> float:
    """Assess the quality of a transcript based on various metrics.

    Args:
        transcript: Transcript text to assess
        logger_instance: Optional logger instance

    Returns:
        Quality score between 0.0 and 1.0
    """
    _logger = logger_instance or logger
    try:
        if not transcript:
            return 0.0

        # Basic quality metrics
        word_count = len(transcript.split())
        char_count = len(transcript)

        # Quality factors
        quality_score = 0.0

        # Length factor (longer transcripts are generally better)
        if word_count > 100:
            quality_score += 0.3
        elif word_count > 50:
            quality_score += 0.2
        elif word_count > 10:
            quality_score += 0.1

        # Character density (reasonable character to word ratio)
        if word_count > 0:
            char_per_word = char_count / word_count
            if 4 <= char_per_word <= 8:  # Reasonable range
                quality_score += 0.2

        # Sentence structure (presence of punctuation)
        punctuation_count = sum(1 for char in transcript if char in ".!?")
        if punctuation_count > word_count / 20:  # At least one sentence marker per 20 words
            quality_score += 0.2

        # Capitalization (proper nouns, sentence starts)
        capital_count = sum(1 for char in transcript if char.isupper())
        if capital_count > word_count / 30:  # Some capitals expected
            quality_score += 0.1

        # Coherence factor (not too many repeated words)
        words = transcript.lower().split()
        unique_words = set(words)
        if len(words) > 0:
            uniqueness_ratio = len(unique_words) / len(words)
            if uniqueness_ratio > 0.3:  # At least 30% unique words
                quality_score += 0.2

        return min(quality_score, 1.0)  # Cap at 1.0
    except Exception as exc:
        _logger.debug("Transcript quality assessment failed: %s", exc)
        return 0.5  # Default moderate quality if assessment fails
