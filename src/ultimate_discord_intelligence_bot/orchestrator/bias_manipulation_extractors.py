"""Bias and manipulation detection extraction utilities for CrewAI outputs.

This module contains functions that extract bias indicators, deception analysis,
and manipulation detection from CrewAI crew results.

Extracted from extractors.py to improve maintainability and organization.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def extract_bias_indicators_from_crew(crew_result: Any) -> list[dict[str, Any]]:
    """Extract bias indicators from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        List of bias indicator dictionaries
    """
    try:
        if not crew_result:
            return []

        crew_output = str(crew_result).lower()

        # Define bias types and their indicators
        bias_types = {
            "political_bias": ["liberal", "conservative", "republican", "democrat", "left", "right"],
            "confirmation_bias": ["confirms", "supports", "validates", "proves"],
            "selection_bias": ["cherry-pick", "selective", "chosen examples"],
            "cultural_bias": ["western", "eastern", "cultural", "traditional"],
            "gender_bias": ["gender", "male", "female", "masculine", "feminine"],
            "racial_bias": ["race", "ethnic", "minority", "majority"],
        }

        detected_biases = []
        for bias_type, indicators in bias_types.items():
            matches = sum(1 for indicator in indicators if indicator in crew_output)
            if matches > 0:
                confidence = min(matches / len(indicators), 1.0)
                detected_biases.append(
                    {
                        "type": bias_type,
                        "confidence": confidence,
                        "indicators_found": matches,
                        "severity": "high" if confidence > 0.7 else "medium" if confidence > 0.4 else "low",
                    }
                )

        return detected_biases
    except Exception as exc:
        logger.exception("Failed to extract bias indicators from crew result: %s", exc)
        return []


def extract_deception_analysis_from_crew(crew_result: Any) -> dict[str, Any]:
    """Extract deception analysis from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Dictionary with deception analysis and indicators
    """
    try:
        if not crew_result:
            return {"deception_score": 0.0, "indicators": [], "confidence": 0.0}

        crew_output = str(crew_result).lower()

        # Deception indicators
        deception_indicators = {
            "evasiveness": ["avoid", "evade", "dodge", "sidestep", "deflect"],
            "contradiction": ["contradict", "inconsistent", "conflicting", "opposite"],
            "exaggeration": ["exaggerate", "overstate", "inflate", "amplify"],
            "omission": ["omitted", "withheld", "concealed", "hidden", "missing"],
            "manipulation": ["manipulate", "influence", "control", "coerce"],
        }

        total_indicators = 0
        detected_indicators = []

        for category, words in deception_indicators.items():
            count = sum(1 for word in words if word in crew_output)
            if count > 0:
                total_indicators += count
                detected_indicators.append(
                    {
                        "category": category,
                        "count": count,
                        "severity": "high" if count > 2 else "medium" if count > 0 else "low",
                    }
                )

        # Calculate deception score
        total_possible = sum(len(words) for words in deception_indicators.values())
        deception_score = total_indicators / total_possible if total_possible > 0 else 0.0

        # Calculate confidence based on indicator diversity
        confidence = min(len(detected_indicators) / len(deception_indicators), 1.0)

        return {
            "deception_score": deception_score,
            "indicators": detected_indicators,
            "confidence": confidence,
            "risk_level": "high" if deception_score > 0.7 else "medium" if deception_score > 0.4 else "low",
        }
    except Exception as exc:
        logger.exception("Failed to extract deception analysis from crew result: %s", exc)
        return {"deception_score": 0.0, "indicators": [], "confidence": 0.0}


def extract_manipulation_indicators_from_crew(crew_result: Any) -> list[dict[str, Any]]:
    """Extract manipulation indicators from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        List of manipulation indicator dictionaries
    """
    try:
        if not crew_result:
            return []

        crew_output = str(crew_result).lower()

        # Manipulation techniques
        manipulation_techniques = {
            "emotional_manipulation": ["guilt", "fear", "anger", "emotional", "heartstrings"],
            "gaslighting": ["gaslight", "deny", "question reality", "make doubt"],
            "projection": ["project", "accuse", "blame", "deflect responsibility"],
            "love_bombing": ["love bomb", "excessive praise", "overwhelming affection"],
            "triangulation": ["triangulate", "third party", "divide", "pitting"],
            "isolation": ["isolate", "cut off", "separate", "alienate"],
        }

        detected_techniques = []
        for technique, indicators in manipulation_techniques.items():
            matches = sum(1 for indicator in indicators if indicator in crew_output)
            if matches > 0:
                confidence = min(matches / len(indicators), 1.0)
                detected_techniques.append(
                    {
                        "technique": technique,
                        "confidence": confidence,
                        "indicators_found": matches,
                        "description": f"Potential {technique.replace('_', ' ')} detected",
                    }
                )

        return detected_techniques
    except Exception as exc:
        logger.exception("Failed to extract manipulation indicators from crew result: %s", exc)
        return []


def extract_narrative_integrity_from_crew(crew_result: Any) -> dict[str, Any]:
    """Extract narrative integrity analysis from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Dictionary with narrative integrity assessment
    """
    try:
        if not crew_result:
            return {"integrity_score": 0.5, "coherence": 0.0, "consistency": 0.0}

        crew_output = str(crew_result).lower()

        # Narrative integrity indicators
        positive_indicators = [
            "consistent",
            "coherent",
            "logical",
            "clear",
            "transparent",
            "honest",
            "accurate",
            "reliable",
            "trustworthy",
        ]
        negative_indicators = [
            "inconsistent",
            "contradictory",
            "confusing",
            "unclear",
            "misleading",
            "deceptive",
            "unreliable",
            "suspicious",
        ]

        positive_count = sum(1 for indicator in positive_indicators if indicator in crew_output)
        negative_count = sum(1 for indicator in negative_indicators if indicator in crew_output)

        total_indicators = positive_count + negative_count
        if total_indicators == 0:
            integrity_score = 0.5
        else:
            integrity_score = positive_count / total_indicators

        # Assess coherence (how well the narrative flows)
        coherence_indicators = ["flow", "structure", "organization", "sequence"]
        coherence_score = sum(1 for indicator in coherence_indicators if indicator in crew_output) / len(
            coherence_indicators
        )

        # Assess consistency (how consistent the narrative is)
        consistency_indicators = ["consistent", "matches", "aligns", "agrees"]
        consistency_score = sum(1 for indicator in consistency_indicators if indicator in crew_output) / len(
            consistency_indicators
        )

        return {
            "integrity_score": integrity_score,
            "coherence": coherence_score,
            "consistency": consistency_score,
            "overall_assessment": "high" if integrity_score > 0.7 else "medium" if integrity_score > 0.4 else "low",
            "red_flags": negative_count,
            "green_flags": positive_count,
        }
    except Exception as exc:
        logger.exception("Failed to extract narrative integrity from crew result: %s", exc)
        return {"integrity_score": 0.5, "coherence": 0.0, "consistency": 0.0}


def extract_psychological_threats_from_crew(crew_result: Any) -> dict[str, Any]:
    """Extract psychological threat analysis from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Dictionary with psychological threat assessment
    """
    try:
        if not crew_result:
            return {"threat_level": "low", "threats_detected": [], "risk_score": 0.0}

        crew_output = str(crew_result).lower()

        # Psychological threat categories
        threat_categories = {
            "manipulation": ["manipulate", "control", "influence", "coerce"],
            "intimidation": ["intimidate", "threaten", "fear", "scare"],
            "exploitation": ["exploit", "take advantage", "use", "leverage"],
            "isolation": ["isolate", "alienate", "separate", "exclude"],
            "gaslighting": ["gaslight", "deny", "question", "make doubt"],
            "emotional_abuse": ["abuse", "hurt", "harm", "damage", "emotional pain"],
        }

        threats_detected = []
        total_threat_score = 0.0

        for category, indicators in threat_categories.items():
            matches = sum(1 for indicator in indicators if indicator in crew_output)
            if matches > 0:
                threat_score = min(matches / len(indicators), 1.0)
                total_threat_score += threat_score
                threats_detected.append(
                    {
                        "category": category,
                        "score": threat_score,
                        "indicators_found": matches,
                        "severity": "high" if threat_score > 0.7 else "medium" if threat_score > 0.4 else "low",
                    }
                )

        # Calculate overall risk score
        risk_score = total_threat_score / len(threat_categories) if threat_categories else 0.0

        # Determine threat level
        if risk_score > 0.7:
            threat_level = "high"
        elif risk_score > 0.4:
            threat_level = "medium"
        else:
            threat_level = "low"

        return {
            "threat_level": threat_level,
            "threats_detected": threats_detected,
            "risk_score": risk_score,
            "recommendation": "immediate_attention"
            if threat_level == "high"
            else "monitor"
            if threat_level == "medium"
            else "low_priority",
            "confidence": min(len(threats_detected) / len(threat_categories), 1.0) if threat_categories else 0.0,
        }
    except Exception as exc:
        logger.exception("Failed to extract psychological threats from crew result: %s", exc)
        return {"threat_level": "low", "threats_detected": [], "risk_score": 0.0}


def calculate_comprehensive_threat_score_from_crew(crew_result: Any) -> float:
    """Calculate comprehensive threat score from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Comprehensive threat score between 0.0 and 1.0
    """
    try:
        if not crew_result:
            return 0.0

        str(crew_result).lower()

        # Weight different threat indicators
        threat_weights = {
            "manipulation": 0.3,
            "deception": 0.25,
            "bias": 0.2,
            "psychological": 0.15,
            "narrative_integrity": 0.1,
        }

        total_score = 0.0
        total_weight = 0.0

        # Extract individual threat scores
        deception_analysis = extract_deception_analysis_from_crew(crew_result)
        bias_indicators = extract_bias_indicators_from_crew(crew_result)
        psych_threats = extract_psychological_threats_from_crew(crew_result)
        narrative_integrity = extract_narrative_integrity_from_crew(crew_result)

        # Weight and combine scores
        total_score += deception_analysis.get("deception_score", 0.0) * threat_weights["deception"]
        total_weight += threat_weights["deception"]

        if bias_indicators:
            bias_score = sum(bias["confidence"] for bias in bias_indicators) / len(bias_indicators)
            total_score += bias_score * threat_weights["bias"]
            total_weight += threat_weights["bias"]

        total_score += psych_threats.get("risk_score", 0.0) * threat_weights["psychological"]
        total_weight += threat_weights["psychological"]

        # Narrative integrity is inverse (lower integrity = higher threat)
        integrity_score = 1.0 - narrative_integrity.get("integrity_score", 0.5)
        total_score += integrity_score * threat_weights["narrative_integrity"]
        total_weight += threat_weights["narrative_integrity"]

        # Calculate final weighted score
        if total_weight > 0:
            return min(total_score / total_weight, 1.0)
        else:
            return 0.0

    except Exception as exc:
        logger.exception("Failed to calculate comprehensive threat score: %s", exc)
        return 0.0
