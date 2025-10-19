"""Threat and risk analysis calculation utilities.

This module contains functions that calculate threat levels, behavioral risks,
and comprehensive risk assessments from CrewAI outputs and analysis data.

Extracted from analytics_calculators.py to improve maintainability and organization.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def calculate_threat_level(deception_result: Any, fallacy_result: Any, log: logging.Logger | None = None) -> str:
    """Calculate overall threat level from deception and fallacy analysis.

    Args:
        deception_result: Results from deception analysis
        fallacy_result: Results from fallacy detection
        log: Optional logger instance

    Returns:
        Threat level: "low", "medium", or "high"
    """
    try:
        if not log:
            log = logger

        # Extract scores from results
        deception_score = 0.0
        if isinstance(deception_result, dict):
            deception_score = deception_result.get("deception_score", 0.0)
        elif isinstance(deception_result, (int, float)):
            deception_score = float(deception_result)

        fallacy_score = 0.0
        if isinstance(fallacy_result, dict):
            fallacy_score = len(fallacy_result.get("fallacies_detected", []))
        elif isinstance(fallacy_result, list):
            fallacy_score = len(fallacy_result)
        elif isinstance(fallacy_result, (int, float)):
            fallacy_score = float(fallacy_result)

        # Calculate combined threat score
        threat_score = (deception_score + (fallacy_score * 0.1)) / 2

        # Determine threat level
        if threat_score > 0.7:
            return "high"
        elif threat_score > 0.4:
            return "medium"
        else:
            return "low"

    except Exception as exc:
        if log:
            log.exception("Failed to calculate threat level: %s", exc)
        return "low"


def calculate_threat_level_from_crew(crew_result: Any, log: logging.Logger | None = None) -> str:
    """Calculate threat level from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result
        log: Optional logger instance

    Returns:
        Threat level: "low", "medium", or "high"
    """
    try:
        if not log:
            log = logger

        if not crew_result:
            return "low"

        crew_output = str(crew_result).lower()

        # Threat indicators
        high_threat_words = ["dangerous", "threatening", "harmful", "malicious", "deceptive"]
        medium_threat_words = ["concerning", "suspicious", "questionable", "misleading"]
        low_threat_words = ["safe", "benign", "harmless", "neutral", "acceptable"]

        high_count = sum(1 for word in high_threat_words if word in crew_output)
        medium_count = sum(1 for word in medium_threat_words if word in crew_output)
        low_count = sum(1 for word in low_threat_words if word in crew_output)

        if high_count > medium_count and high_count > low_count:
            return "high"
        elif medium_count > low_count:
            return "medium"
        else:
            return "low"

    except Exception as exc:
        if log:
            log.exception("Failed to calculate threat level from crew result: %s", exc)
        return "low"


def calculate_behavioral_risk(behavioral_data: dict[str, Any], log: logging.Logger | None = None) -> float:
    """Calculate behavioral risk score from behavioral analysis data.

    Args:
        behavioral_data: Dictionary containing behavioral analysis results
        log: Optional logger instance

    Returns:
        Behavioral risk score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not behavioral_data:
            return 0.0

        risk_factors = []

        # Extract risk indicators
        if "manipulation_indicators" in behavioral_data:
            manipulation_count = len(behavioral_data["manipulation_indicators"])
            risk_factors.append(min(manipulation_count * 0.2, 1.0))

        if "deception_score" in behavioral_data:
            risk_factors.append(behavioral_data["deception_score"])

        if "bias_indicators" in behavioral_data:
            bias_count = len(behavioral_data["bias_indicators"])
            risk_factors.append(min(bias_count * 0.15, 1.0))

        if "psychological_threats" in behavioral_data:
            threat_level = behavioral_data["psychological_threats"].get("threat_level", "low")
            threat_scores = {"low": 0.2, "medium": 0.6, "high": 1.0}
            risk_factors.append(threat_scores.get(threat_level, 0.2))

        # Calculate average risk score
        if risk_factors:
            return sum(risk_factors) / len(risk_factors)
        else:
            return 0.0

    except Exception as exc:
        if log:
            log.exception("Failed to calculate behavioral risk: %s", exc)
        return 0.0


def calculate_behavioral_risk_from_crew(crew_result: Any, log: logging.Logger | None = None) -> float:
    """Calculate behavioral risk from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result
        log: Optional logger instance

    Returns:
        Behavioral risk score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not crew_result:
            return 0.0

        crew_output = str(crew_result).lower()

        # Behavioral risk indicators
        risk_indicators = [
            "manipulative",
            "deceptive",
            "coercive",
            "controlling",
            "exploitative",
            "abusive",
            "threatening",
            "intimidating",
        ]

        risk_count = sum(1 for indicator in risk_indicators if indicator in crew_output)
        total_words = len(crew_output.split())

        if total_words > 0:
            risk_score = min(risk_count / (total_words / 100), 1.0)
        else:
            risk_score = 0.0

        return risk_score

    except Exception as exc:
        if log:
            log.exception("Failed to calculate behavioral risk from crew result: %s", exc)
        return 0.0


def calculate_composite_deception_score(
    deception_indicators: list[dict[str, Any]], log: logging.Logger | None = None
) -> float:
    """Calculate composite deception score from multiple indicators.

    Args:
        deception_indicators: List of deception indicator dictionaries
        log: Optional logger instance

    Returns:
        Composite deception score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not deception_indicators:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for indicator in deception_indicators:
            if isinstance(indicator, dict):
                confidence = indicator.get("confidence", 0.0)
                severity = indicator.get("severity", "low")

                # Weight by severity
                severity_weights = {"low": 0.3, "medium": 0.6, "high": 1.0}
                weight = severity_weights.get(severity, 0.5)

                total_score += confidence * weight
                total_weight += weight

        if total_weight > 0:
            return min(total_score / total_weight, 1.0)
        else:
            return 0.0

    except Exception as exc:
        if log:
            log.exception("Failed to calculate composite deception score: %s", exc)
        return 0.0


def calculate_comprehensive_threat_score(threat_data: dict[str, Any], log: logging.Logger | None = None) -> float:
    """Calculate comprehensive threat score from multiple threat dimensions.

    Args:
        threat_data: Dictionary containing various threat analysis results
        log: Optional logger instance

    Returns:
        Comprehensive threat score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not threat_data:
            return 0.0

        threat_components = []

        # Deception threat
        if "deception_score" in threat_data:
            threat_components.append(threat_data["deception_score"] * 0.3)

        # Bias threat
        if "bias_indicators" in threat_data:
            bias_count = len(threat_data["bias_indicators"])
            threat_components.append(min(bias_count * 0.1, 0.2))

        # Manipulation threat
        if "manipulation_indicators" in threat_data:
            manipulation_count = len(threat_data["manipulation_indicators"])
            threat_components.append(min(manipulation_count * 0.15, 0.25))

        # Psychological threat
        if "psychological_threats" in threat_data:
            psych_threats = threat_data["psychological_threats"]
            if isinstance(psych_threats, dict):
                risk_score = psych_threats.get("risk_score", 0.0)
                threat_components.append(risk_score * 0.25)

        # Calculate weighted average
        if threat_components:
            return min(sum(threat_components), 1.0)
        else:
            return 0.0

    except Exception as exc:
        if log:
            log.exception("Failed to calculate comprehensive threat score: %s", exc)
        return 0.0


def calculate_basic_threat_from_data(analysis_data: dict[str, Any], log: logging.Logger | None = None) -> float:
    """Calculate basic threat score from analysis data.

    Args:
        analysis_data: Dictionary containing analysis results
        log: Optional logger instance

    Returns:
        Basic threat score between 0.0 and 1.0
    """
    try:
        if not log:
            log = logger

        if not analysis_data:
            return 0.0

        threat_score = 0.0

        # Check for threat indicators in the data
        threat_keywords = ["threat", "danger", "risk", "harm", "deception", "manipulation"]

        for key, value in analysis_data.items():
            if isinstance(value, str):
                text_value = value.lower()
                keyword_count = sum(1 for keyword in threat_keywords if keyword in text_value)
                threat_score += keyword_count * 0.1
            elif isinstance(value, (int, float)):
                # If it's a numeric threat score
                if "threat" in key.lower() or "risk" in key.lower():
                    threat_score += min(value, 1.0)

        return min(threat_score, 1.0)

    except Exception as exc:
        if log:
            log.exception("Failed to calculate basic threat from data: %s", exc)
        return 0.0
