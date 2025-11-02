"""Fact-checking and verification extraction utilities for CrewAI outputs.

This module contains functions that extract fact-checking, credibility,
and verification data from CrewAI crew results.

Extracted from extractors.py to improve maintainability and organization.
"""

import logging
import re
from typing import Any


logger = logging.getLogger(__name__)


def extract_fact_checks_from_crew(crew_result: Any) -> dict[str, Any]:
    """Extract fact-checking results from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Dictionary with fact-checking analysis and results
    """
    try:
        if not crew_result:
            return {"verified_claims": [], "disputed_claims": [], "confidence": 0.0}

        crew_output = str(crew_result).lower()

        # Look for fact-checking indicators
        verified_keywords = [
            "verified",
            "confirmed",
            "accurate",
            "correct",
            "true",
            "factual",
        ]
        disputed_keywords = [
            "disputed",
            "false",
            "inaccurate",
            "misleading",
            "unverified",
            "doubtful",
        ]

        verified_count = sum(1 for keyword in verified_keywords if keyword in crew_output)
        disputed_count = sum(1 for keyword in disputed_keywords if keyword in crew_output)

        total_indicators = verified_count + disputed_count
        confidence = verified_count / total_indicators if total_indicators > 0 else 0.5

        return {
            "verified_claims": ["CrewAI fact-checking analysis completed"],
            "disputed_claims": [],
            "confidence": confidence,
            "verification_method": "crew_analysis",
            "sources_checked": 1 if "source" in crew_output else 0,
        }
    except Exception as exc:
        logger.exception("Failed to extract fact checks from crew result: %s", exc)
        return {"verified_claims": [], "disputed_claims": [], "confidence": 0.0}


def extract_logical_analysis_from_crew(crew_result: Any) -> dict[str, Any]:
    """Extract logical analysis from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Dictionary with logical fallacy analysis
    """
    try:
        if not crew_result:
            return {"fallacies_detected": [], "logical_strength": 0.0}

        crew_output = str(crew_result).lower()

        # Common logical fallacies to detect
        fallacy_patterns = {
            "ad_hominem": ["personal attack", "attacking the person", "ad hominem"],
            "straw_man": ["straw man", "misrepresenting", "distorting"],
            "false_dilemma": ["either or", "black and white", "false choice"],
            "appeal_to_emotion": ["emotional appeal", "playing on emotions"],
            "circular_reasoning": ["circular reasoning", "begging the question"],
        }

        detected_fallacies = []
        for fallacy_type, patterns in fallacy_patterns.items():
            for pattern in patterns:
                if pattern in crew_output:
                    detected_fallacies.append(
                        {
                            "type": fallacy_type,
                            "description": f"Potential {fallacy_type} detected",
                            "confidence": 0.7,
                        }
                    )

        # Calculate logical strength (inverse of fallacy count)
        logical_strength = max(0.0, 1.0 - (len(detected_fallacies) * 0.2))

        return {
            "fallacies_detected": detected_fallacies,
            "logical_strength": logical_strength,
            "argument_structure": "analyzed" if "argument" in crew_output else "not_detected",
            "evidence_quality": "assessed" if "evidence" in crew_output else "not_assessed",
        }
    except Exception as exc:
        logger.exception("Failed to extract logical analysis from crew result: %s", exc)
        return {"fallacies_detected": [], "logical_strength": 0.0}


def extract_credibility_from_crew(crew_result: Any) -> dict[str, Any]:
    """Extract credibility assessment from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Dictionary with credibility scores and factors
    """
    try:
        if not crew_result:
            return {"overall_credibility": 0.5, "factors": [], "confidence": 0.0}

        crew_output = str(crew_result).lower()

        # Credibility indicators
        credibility_indicators = {
            "source_reputation": ["reputable", "authoritative", "expert", "scholar"],
            "evidence_quality": ["evidence", "data", "research", "study", "statistics"],
            "transparency": ["transparent", "clear", "open", "honest"],
            "bias_level": ["unbiased", "objective", "neutral", "balanced"],
            "accuracy": ["accurate", "precise", "correct", "verified"],
        }

        credibility_scores = {}
        for factor, indicators in credibility_indicators.items():
            score = sum(1 for indicator in indicators if indicator in crew_output)
            credibility_scores[factor] = min(score / len(indicators), 1.0)

        # Calculate overall credibility
        overall_credibility = sum(credibility_scores.values()) / len(credibility_scores) if credibility_scores else 0.5

        # Extract specific factors mentioned
        factors = []
        for factor, score in credibility_scores.items():
            if score > 0.3:
                factors.append(
                    {
                        "factor": factor,
                        "score": score,
                        "impact": "positive" if score > 0.6 else "neutral",
                    }
                )

        return {
            "overall_credibility": overall_credibility,
            "factors": factors,
            "confidence": 0.8 if overall_credibility > 0.7 else 0.6,
            "assessment_method": "crew_analysis",
        }
    except Exception as exc:
        logger.exception("Failed to extract credibility from crew result: %s", exc)
        return {"overall_credibility": 0.5, "factors": [], "confidence": 0.0}


def extract_source_validation_from_crew(crew_result: Any) -> dict[str, Any]:
    """Extract source validation from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Dictionary with source validation results
    """
    try:
        if not crew_result:
            return {
                "sources_validated": 0,
                "validation_method": "none",
                "reliability": 0.0,
            }

        crew_output = str(crew_result)

        # Look for source indicators
        source_patterns = [
            r"https?://[^\s]+",  # URLs
            r"\[.*?\]",  # Citations in brackets
            r"\(.*?\d{4}.*?\)",  # Parenthetical citations with years
        ]

        sources_found = 0
        for pattern in source_patterns:
            sources_found += len(re.findall(pattern, crew_output))

        # Determine validation method
        validation_method = "none"
        if "peer-reviewed" in crew_output.lower():
            validation_method = "peer_review"
        elif "fact-check" in crew_output.lower():
            validation_method = "fact_checking"
        elif "verification" in crew_output.lower():
            validation_method = "verification"

        # Calculate reliability based on validation method and source count
        reliability_factors = {
            "peer_review": 0.9,
            "fact_checking": 0.8,
            "verification": 0.7,
            "none": 0.3,
        }
        base_reliability = reliability_factors.get(validation_method, 0.5)
        source_bonus = min(sources_found * 0.1, 0.3)
        reliability = min(base_reliability + source_bonus, 1.0)

        return {
            "sources_validated": sources_found,
            "validation_method": validation_method,
            "reliability": reliability,
            "source_types": ["web", "academic"] if sources_found > 0 else [],
            "last_updated": "unknown",
        }
    except Exception as exc:
        logger.exception("Failed to extract source validation from crew result: %s", exc)
        return {"sources_validated": 0, "validation_method": "none", "reliability": 0.0}


def calculate_verification_confidence_from_crew(crew_result: Any) -> float:
    """Calculate verification confidence from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Confidence score between 0.0 and 1.0
    """
    try:
        if not crew_result:
            return 0.0

        crew_output = str(crew_result).lower()

        # Confidence indicators
        high_confidence_words = [
            "confirmed",
            "verified",
            "certain",
            "definite",
            "proven",
        ]
        medium_confidence_words = [
            "likely",
            "probably",
            "suggests",
            "indicates",
            "appears",
        ]
        low_confidence_words = [
            "uncertain",
            "unclear",
            "doubtful",
            "speculative",
            "unknown",
        ]

        high_count = sum(1 for word in high_confidence_words if word in crew_output)
        medium_count = sum(1 for word in medium_confidence_words if word in crew_output)
        low_count = sum(1 for word in low_confidence_words if word in crew_output)

        total_indicators = high_count + medium_count + low_count
        if total_indicators == 0:
            return 0.5  # Default neutral confidence

        # Weighted confidence calculation
        confidence = (high_count * 0.9 + medium_count * 0.6 + low_count * 0.2) / total_indicators
        return min(max(confidence, 0.0), 1.0)

    except Exception as exc:
        logger.exception("Failed to calculate verification confidence: %s", exc)
        return 0.0
