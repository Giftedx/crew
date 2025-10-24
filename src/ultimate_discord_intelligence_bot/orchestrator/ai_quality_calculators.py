"""AI quality and enhancement calculation utilities.

This module contains functions that calculate AI quality scores,
enhancement levels, and related metrics.

Extracted from confidence_calculators.py to improve maintainability and organization.
"""

import logging
from typing import Any


logger = logging.getLogger(__name__)


def calculate_ai_quality_score(quality_dimensions: dict[str, float], log: logging.Logger | None = None) -> float:
    """Calculate overall AI quality score from quality dimensions.

    Args:
        quality_dimensions: Dictionary with quality dimension scores
        log: Optional logger instance

    Returns:
        Overall AI quality score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not quality_dimensions:
            return 0.0

        # Weight different quality dimensions
        dimension_weights = {
            "accuracy": 0.3,
            "completeness": 0.2,
            "consistency": 0.2,
            "clarity": 0.15,
            "relevance": 0.15,
        }

        weighted_score = 0.0
        total_weight = 0.0

        for dimension, weight in dimension_weights.items():
            if dimension in quality_dimensions:
                score = quality_dimensions[dimension]
                weighted_score += score * weight
                total_weight += weight

        if total_weight > 0:
            return weighted_score / total_weight
        else:
            # Fallback: average of available scores
            scores = [score for score in quality_dimensions.values() if isinstance(score, (int, float))]
            return sum(scores) / len(scores) if scores else 0.0

    except Exception as exc:
        if log:
            log.exception("Failed to calculate AI quality score: %s", exc)
        return 0.0


def calculate_ai_enhancement_level(depth: str, log: logging.Logger | None = None) -> float:
    """Calculate AI enhancement level based on analysis depth.

    Args:
        depth: Analysis depth level ("shallow", "standard", "deep", "experimental")
        log: Optional logger instance

    Returns:
        AI enhancement level between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        depth_levels = {
            "shallow": 0.25,
            "standard": 0.5,
            "deep": 0.75,
            "experimental": 1.0,
        }

        return depth_levels.get(depth.lower(), 0.5)

    except Exception as exc:
        if log:
            log.exception("Failed to calculate AI enhancement level: %s", exc)
        return 0.5


def calculate_synthesis_confidence(research_results: dict[str, Any], log: logging.Logger | None = None) -> float:
    """Calculate synthesis confidence from research results.

    Args:
        research_results: Dictionary containing research analysis results
        log: Optional logger instance

    Returns:
        Synthesis confidence score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not research_results:
            return 0.0

        confidence_factors = []

        # Source diversity factor
        if "source_diversity" in research_results:
            confidence_factors.append(research_results["source_diversity"])

        # Evidence strength factor
        if "evidence_strength" in research_results:
            confidence_factors.append(research_results["evidence_strength"])

        # Cross-validation factor
        if "cross_validation" in research_results:
            confidence_factors.append(research_results["cross_validation"])

        # Calculate average confidence
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        else:
            # Fallback: analyze text for synthesis indicators
            text_data = str(research_results).lower()
            synthesis_words = [
                "synthesis",
                "integration",
                "consolidation",
                "unified",
                "comprehensive",
                "cohesive",
            ]
            uncertainty_words = [
                "fragmented",
                "disjointed",
                "inconsistent",
                "contradictory",
            ]

            synthesis_count = sum(1 for word in synthesis_words if word in text_data)
            uncertainty_count = sum(1 for word in uncertainty_words if word in text_data)

            total_indicators = synthesis_count + uncertainty_count
            if total_indicators > 0:
                return synthesis_count / total_indicators
            else:
                return 0.5  # Neutral confidence

    except Exception as exc:
        if log:
            log.exception("Failed to calculate synthesis confidence: %s", exc)
        return 0.0


def calculate_synthesis_confidence_from_crew(crew_result: Any, log: logging.Logger | None = None) -> float:
    """Calculate synthesis confidence from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result
        log: Optional logger instance

    Returns:
        Synthesis confidence score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not crew_result:
            return 0.0

        crew_output = str(crew_result).lower()

        # Synthesis confidence indicators
        synthesis_indicators = [
            "synthesis complete",
            "integration successful",
            "consolidation achieved",
            "unified analysis",
            "comprehensive overview",
            "cohesive summary",
        ]

        confidence_count = sum(1 for indicator in synthesis_indicators if indicator in crew_output)

        # Normalize by output length
        total_words = len(crew_output.split())
        if total_words > 0:
            return min(confidence_count / (total_words / 100), 1.0)
        else:
            return 0.0

    except Exception as exc:
        if log:
            log.exception("Failed to calculate synthesis confidence from crew result: %s", exc)
        return 0.0


def calculate_overall_confidence(*data_sources, log: logging.Logger | None = None) -> float:
    """Calculate overall confidence from multiple data sources.

    Args:
        *data_sources: Variable number of data sources (dicts, strings, or numbers)
        log: Optional logger instance

    Returns:
        Overall confidence score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not data_sources:
            return 0.0

        confidence_scores = []

        for source in data_sources:
            if isinstance(source, dict):
                # Extract confidence from dict if available
                if "confidence" in source:
                    confidence_scores.append(source["confidence"])
                elif "quality_score" in source:
                    confidence_scores.append(source["quality_score"])
                else:
                    # Analyze text content for confidence indicators
                    text = str(source).lower()
                    confidence_words = [
                        "high",
                        "excellent",
                        "strong",
                        "reliable",
                        "accurate",
                    ]
                    uncertainty_words = [
                        "low",
                        "poor",
                        "weak",
                        "unreliable",
                        "inaccurate",
                    ]

                    conf_count = sum(1 for word in confidence_words if word in text)
                    unc_count = sum(1 for word in uncertainty_words if word in text)

                    total_indicators = conf_count + unc_count
                    if total_indicators > 0:
                        confidence_scores.append(conf_count / total_indicators)
                    else:
                        confidence_scores.append(0.5)  # Neutral

            elif isinstance(source, (int, float)):
                # Normalize numeric values to 0-1 range
                normalized = min(max(source, 0.0), 1.0)
                confidence_scores.append(normalized)

            elif isinstance(source, str):
                # Analyze string content for confidence indicators
                source_lower = source.lower()
                confidence_words = [
                    "confident",
                    "certain",
                    "sure",
                    "definitive",
                    "conclusive",
                ]
                uncertainty_words = [
                    "uncertain",
                    "doubtful",
                    "speculative",
                    "tentative",
                ]

                conf_count = sum(1 for word in confidence_words if word in source_lower)
                unc_count = sum(1 for word in uncertainty_words if word in source_lower)

                total_indicators = conf_count + unc_count
                if total_indicators > 0:
                    confidence_scores.append(conf_count / total_indicators)
                else:
                    confidence_scores.append(0.5)  # Neutral

        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        else:
            return 0.0

    except Exception as exc:
        if log:
            log.exception("Failed to calculate overall confidence: %s", exc)
        return 0.0
