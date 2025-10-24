"""Content confidence calculation utilities.

This module contains functions that calculate confidence scores for content
analysis, transcript quality, and verification metrics.

Extracted from confidence_calculators.py to improve maintainability and organization.
"""

import logging
from typing import Any


logger = logging.getLogger(__name__)


def calculate_transcript_quality(crew_result: Any, log: logging.Logger | None = None) -> float:
    """Calculate transcript quality from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result
        log: Optional logger instance

    Returns:
        Transcript quality score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not crew_result:
            return 0.0

        crew_output = str(crew_result).lower()

        # Transcript quality indicators
        quality_indicators = [
            "clear audio",
            "good transcription",
            "accurate text",
            "complete transcript",
            "high quality",
            "well transcribed",
            "clear speech",
            "good audio quality",
        ]

        quality_count = sum(1 for indicator in quality_indicators if indicator in crew_output)

        # Quality issues indicators
        issue_indicators = [
            "poor audio",
            "unclear speech",
            "transcription errors",
            "incomplete transcript",
            "low quality",
            "background noise",
            "distorted audio",
            "cut off",
        ]

        issue_count = sum(1 for indicator in issue_indicators if indicator in crew_output)

        # Calculate quality score
        total_indicators = quality_count + issue_count
        if total_indicators > 0:
            base_quality = quality_count / total_indicators
            # Penalize for issues
            issue_penalty = issue_count * 0.2
            return max(base_quality - issue_penalty, 0.0)
        else:
            return 0.5  # Neutral quality

    except Exception as exc:
        if log:
            log.exception("Failed to calculate transcript quality: %s", exc)
        return 0.0


def calculate_analysis_confidence_from_crew(crew_result: Any, log: logging.Logger | None = None) -> float:
    """Calculate analysis confidence from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result
        log: Optional logger instance

    Returns:
        Analysis confidence score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not crew_result:
            return 0.0

        crew_output = str(crew_result).lower()

        # Analysis confidence indicators
        confidence_words = [
            "confident",
            "certain",
            "definitive",
            "conclusive",
            "verified",
            "confirmed",
            "accurate",
            "reliable",
            "supported",
            "evidence",
        ]

        uncertainty_words = [
            "uncertain",
            "unclear",
            "doubtful",
            "speculative",
            "tentative",
            "preliminary",
            "inconclusive",
            "ambiguous",
        ]

        confidence_count = sum(1 for word in confidence_words if word in crew_output)
        uncertainty_count = sum(1 for word in uncertainty_words if word in crew_output)

        total_indicators = confidence_count + uncertainty_count
        if total_indicators > 0:
            return confidence_count / total_indicators
        else:
            return 0.5  # Neutral confidence

    except Exception as exc:
        if log:
            log.exception("Failed to calculate analysis confidence from crew result: %s", exc)
        return 0.0


def calculate_verification_confidence_from_crew(crew_result: Any, log: logging.Logger | None = None) -> float:
    """Calculate verification confidence from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result
        log: Optional logger instance

    Returns:
        Verification confidence score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not crew_result:
            return 0.0

        crew_output = str(crew_result).lower()

        # Verification confidence indicators
        verification_words = [
            "verified",
            "confirmed",
            "validated",
            "authenticated",
            "corroborated",
            "fact-checked",
            "peer-reviewed",
            "reliable source",
        ]

        verification_count = sum(1 for word in verification_words if word in crew_output)
        total_words = len(crew_output.split())

        if total_words > 0:
            return min(verification_count / (total_words / 100), 1.0)
        else:
            return 0.0

    except Exception as exc:
        if log:
            log.exception("Failed to calculate verification confidence from crew result: %s", exc)
        return 0.0


def calculate_content_completeness(
    content: str, expected_elements: list[str], log: logging.Logger | None = None
) -> float:
    """Calculate content completeness based on expected elements.

    Args:
        content: Content text to analyze
        expected_elements: List of expected elements to find in content
        log: Optional logger instance

    Returns:
        Content completeness score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not content or not expected_elements:
            return 0.0

        content_lower = content.lower()
        found_elements = 0

        for element in expected_elements:
            if element.lower() in content_lower:
                found_elements += 1

        return found_elements / len(expected_elements)

    except Exception as exc:
        if log:
            log.exception("Failed to calculate content completeness: %s", exc)
        return 0.0


def calculate_content_coherence(content: str, log: logging.Logger | None = None) -> float:
    """Calculate content coherence score based on text analysis.

    Args:
        content: Content text to analyze
        log: Optional logger instance

    Returns:
        Content coherence score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not content:
            return 0.0

        content_lower = content.lower()

        # Coherence indicators
        coherence_words = [
            "therefore",
            "thus",
            "consequently",
            "as a result",
            "in conclusion",
            "furthermore",
            "moreover",
            "additionally",
            "however",
            "nevertheless",
            "on the other hand",
        ]

        # Incoherence indicators
        incoherence_words = [
            "contradicts",
            "conflicts",
            "inconsistent",
            "illogical",
            "nonsensical",
            "confusing",
            "unclear",
            "disjointed",
        ]

        coherence_count = sum(1 for word in coherence_words if word in content_lower)
        incoherence_count = sum(1 for word in incoherence_words if word in content_lower)

        # Also consider sentence structure (simplified)
        sentences = content.split(".")
        sentence_count = len([s for s in sentences if s.strip()])

        # Basic coherence based on transitions and structure
        if sentence_count > 0:
            transition_score = coherence_count / sentence_count
            incoherence_penalty = incoherence_count / sentence_count

            coherence_score = max(0.0, transition_score - incoherence_penalty)
            return min(coherence_score, 1.0)
        else:
            return 0.0

    except Exception as exc:
        if log:
            log.exception("Failed to calculate content coherence: %s", exc)
        return 0.0


def calculate_source_reliability(sources: list[str], log: logging.Logger | None = None) -> float:
    """Calculate source reliability score based on source types and indicators.

    Args:
        sources: List of source URLs or identifiers
        log: Optional logger instance

    Returns:
        Source reliability score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not sources:
            return 0.0

        reliability_score = 0.0
        total_sources = len(sources)

        for source in sources:
            source_lower = str(source).lower()
            source_score = 0.5  # Default neutral score

            # High reliability indicators
            high_reliability = [
                "edu",
                "gov",
                "org",
                "peer-reviewed",
                "academic",
                "scholarly",
                "journal",
                "research",
                "study",
                "university",
            ]

            # Low reliability indicators
            low_reliability = [
                "blog",
                "forum",
                "social media",
                "opinion",
                "personal",
                "unverified",
                "rumor",
                "speculation",
            ]

            # Check for high reliability indicators
            high_count = sum(1 for indicator in high_reliability if indicator in source_lower)
            if high_count > 0:
                source_score = min(0.5 + (high_count * 0.1), 1.0)

            # Check for low reliability indicators
            low_count = sum(1 for indicator in low_reliability if indicator in source_lower)
            if low_count > 0:
                source_score = max(0.0, source_score - (low_count * 0.2))

            reliability_score += source_score

        return reliability_score / total_sources

    except Exception as exc:
        if log:
            log.exception("Failed to calculate source reliability: %s", exc)
        return 0.0
