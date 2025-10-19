"""Persona and agent confidence calculation utilities.

This module contains functions that calculate confidence scores for personas,
agents, and behavioral analysis data.

Extracted from confidence_calculators.py to improve maintainability and organization.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def calculate_persona_confidence(behavioral_data: dict[str, Any], log: logging.Logger | None = None) -> float:
    """Calculate persona confidence score from behavioral analysis data.

    Args:
        behavioral_data: Dictionary containing behavioral analysis results
        log: Optional logger instance

    Returns:
        Persona confidence score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not behavioral_data:
            return 0.0

        confidence_factors = []

        # Consistency factor
        if "consistency_score" in behavioral_data:
            confidence_factors.append(behavioral_data["consistency_score"])

        # Authenticity factor
        if "authenticity_score" in behavioral_data:
            confidence_factors.append(behavioral_data["authenticity_score"])

        # Reliability factor
        if "reliability_score" in behavioral_data:
            confidence_factors.append(behavioral_data["reliability_score"])

        # Calculate average confidence
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        else:
            # Fallback: analyze text for confidence indicators
            text_data = str(behavioral_data).lower()
            confidence_words = ["consistent", "authentic", "reliable", "stable", "genuine"]
            uncertainty_words = ["inconsistent", "fake", "unreliable", "unstable", "artificial"]

            confidence_count = sum(1 for word in confidence_words if word in text_data)
            uncertainty_count = sum(1 for word in uncertainty_words if word in text_data)

            total_indicators = confidence_count + uncertainty_count
            if total_indicators > 0:
                return confidence_count / total_indicators
            else:
                return 0.5  # Neutral confidence

    except Exception as exc:
        if log:
            log.exception("Failed to calculate persona confidence: %s", exc)
        return 0.0


def calculate_persona_confidence_from_crew(crew_result: Any, log: logging.Logger | None = None) -> float:
    """Calculate persona confidence from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result
        log: Optional logger instance

    Returns:
        Persona confidence score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not crew_result:
            return 0.0

        crew_output = str(crew_result).lower()

        # Persona confidence indicators
        persona_indicators = [
            "consistent personality",
            "authentic behavior",
            "reliable responses",
            "stable character",
            "genuine persona",
            "coherent identity",
        ]

        confidence_count = sum(1 for indicator in persona_indicators if indicator in crew_output)

        # Normalize by output length
        total_words = len(crew_output.split())
        if total_words > 0:
            return min(confidence_count / (total_words / 50), 1.0)
        else:
            return 0.0

    except Exception as exc:
        if log:
            log.exception("Failed to calculate persona confidence from crew result: %s", exc)
        return 0.0


def calculate_agent_confidence_from_crew(crew_result: Any, log: logging.Logger | None = None) -> float:
    """Calculate agent confidence from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result
        log: Optional logger instance

    Returns:
        Agent confidence score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not crew_result:
            return 0.0

        crew_output = str(crew_result).lower()

        # Agent confidence indicators
        agent_indicators = [
            "successful execution",
            "task completed",
            "objective achieved",
            "goal reached",
            "mission accomplished",
            "analysis complete",
            "processing finished",
            "evaluation done",
        ]

        confidence_count = sum(1 for indicator in agent_indicators if indicator in crew_output)

        # Also check for error indicators
        error_indicators = [
            "failed",
            "error",
            "exception",
            "timeout",
            "aborted",
            "cancelled",
            "incomplete",
        ]

        error_count = sum(1 for indicator in error_indicators if indicator in crew_output)

        # Calculate confidence based on success vs error indicators
        total_indicators = confidence_count + error_count
        if total_indicators > 0:
            base_confidence = confidence_count / total_indicators
            # Penalize heavily for errors
            error_penalty = error_count * 0.3
            return max(base_confidence - error_penalty, 0.0)
        else:
            return 0.5  # Neutral confidence

    except Exception as exc:
        if log:
            log.exception("Failed to calculate agent confidence from crew result: %s", exc)
        return 0.0


def calculate_contextual_relevance(content: str, context: dict[str, Any], log: logging.Logger | None = None) -> float:
    """Calculate contextual relevance score between content and context.

    Args:
        content: Content text to analyze
        context: Context dictionary with relevant information
        log: Optional logger instance

    Returns:
        Contextual relevance score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not content or not context:
            return 0.0

        content_lower = content.lower()
        context_text = str(context).lower()

        # Extract key terms from context
        context_terms = set(context_text.split())

        # Count relevant terms in content
        content_terms = content_lower.split()
        relevant_terms = [term for term in content_terms if term in context_terms]

        if len(content_terms) > 0:
            relevance_score = len(relevant_terms) / len(content_terms)
            return min(relevance_score, 1.0)
        else:
            return 0.0

    except Exception as exc:
        if log:
            log.exception("Failed to calculate contextual relevance: %s", exc)
        return 0.0
