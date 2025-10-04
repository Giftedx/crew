"""Result extraction utilities for CrewAI outputs.

This module contains pure extraction functions that parse CrewAI crew results
into structured data. All functions follow a consistent pattern:
- Accept CrewAI result objects (Any type for flexibility)
- Return typed Python structures (dict, list, float, etc.)
- Handle errors gracefully with try/except and sensible defaults
- Use simple pattern matching and text analysis

Extracted from autonomous_orchestrator.py to improve maintainability.
"""

import logging
import re
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)


def extract_timeline_from_crew(crew_result: Any) -> list[dict[str, Any]]:
    """Extract timeline anchors from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        List of timeline anchor dictionaries with type, timestamp, description
    """
    try:
        if not crew_result:
            return []

        crew_output = str(crew_result).lower()

        # Simple timeline extraction based on time patterns
        timeline_anchors = []
        if "timeline" in crew_output or "timestamp" in crew_output:
            timeline_anchors.append(
                {
                    "type": "crew_generated",
                    "timestamp": "00:00",
                    "description": "CrewAI timeline analysis available",
                }
            )

        return timeline_anchors
    except Exception as exc:
        logger.exception("Failed to extract timeline from crew result: %s", exc)
        return []


def extract_index_from_crew(crew_result: Any) -> dict[str, Any]:
    """Extract transcript index from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Index dictionary with analysis metadata and keywords
    """
    try:
        if not crew_result:
            return {}

        crew_output = str(crew_result)

        # Simple index extraction
        index = {
            "crew_analysis": True,
            "content_length": len(crew_output),
            "keywords": extract_keywords_from_text(crew_output),
            "topics": [],
        }

        return index
    except Exception as exc:
        logger.exception("Failed to extract index from crew result: %s", exc)
        return {}


def calculate_transcript_quality(crew_result: Any) -> float:
    """Calculate transcript quality from CrewAI analysis.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Quality score between 0.0 and 1.0
    """
    try:
        if not crew_result:
            return 0.0

        crew_output = str(crew_result).lower()
        quality_indicators = ["high quality", "accurate", "clear", "comprehensive", "detailed"]
        quality_count = sum(1 for indicator in quality_indicators if indicator in crew_output)

        return min(quality_count * 0.2, 1.0)
    except Exception as exc:
        logger.exception("Failed to calculate transcript quality: %s", exc)
        return 0.5


def extract_keywords_from_text(text: str) -> list[str]:
    """Extract keywords from text using simple word frequency.

    Args:
        text: Input text to analyze

    Returns:
        List of up to 10 most common keywords (4+ characters)
    """
    try:
        words = re.findall(r"[a-zA-Z]{4,}", text.lower())
        # Return most common words as keywords
        word_counts = Counter(words)
        return [word for word, count in word_counts.most_common(10)]
    except Exception as exc:
        logger.exception("Failed to extract keywords: %s", exc)
        return []


def extract_linguistic_patterns_from_crew(crew_result: Any) -> dict[str, Any]:
    """Extract linguistic patterns from CrewAI analysis.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Dictionary with complexity indicators and language features
    """
    try:
        if not crew_result:
            return {}

        crew_output = str(crew_result).lower()

        patterns = {
            "crew_detected_patterns": True,
            "complexity_indicators": analyze_text_complexity(crew_output),
            "language_features": extract_language_features(crew_output),
            "structural_elements": [],
        }

        return patterns
    except Exception as exc:
        logger.exception("Failed to extract linguistic patterns: %s", exc)
        return {}


def extract_sentiment_from_crew(crew_result: Any) -> dict[str, Any]:
    """Extract sentiment analysis from CrewAI results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Sentiment dictionary with overall sentiment, confidence, and scores
    """
    try:
        if not crew_result:
            return {}

        crew_output = str(crew_result).lower()

        # Simple sentiment indicators
        positive_indicators = ["positive", "good", "excellent", "successful", "effective"]
        negative_indicators = ["negative", "bad", "poor", "unsuccessful", "problematic"]
        neutral_indicators = ["neutral", "balanced", "moderate", "average"]

        pos_count = sum(1 for word in positive_indicators if word in crew_output)
        neg_count = sum(1 for word in negative_indicators if word in crew_output)
        neu_count = sum(1 for word in neutral_indicators if word in crew_output)

        sentiment = {
            "overall_sentiment": "positive"
            if pos_count > neg_count
            else "negative"
            if neg_count > pos_count
            else "neutral",
            "confidence": min(
                (max(pos_count, neg_count, neu_count) / max(1, pos_count + neg_count + neu_count)) * 1.0, 1.0
            ),
            "positive_score": pos_count,
            "negative_score": neg_count,
            "neutral_score": neu_count,
        }

        return sentiment
    except Exception as exc:
        logger.exception("Failed to extract sentiment: %s", exc)
        return {"overall_sentiment": "unknown", "confidence": 0.0}


def extract_themes_from_crew(crew_result: Any) -> list[dict[str, Any]]:
    """Extract thematic insights from CrewAI analysis.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        List of theme dictionaries with confidence and keywords
    """
    try:
        if not crew_result:
            return []

        crew_output = str(crew_result)

        # Simple theme extraction
        themes = []
        if len(crew_output) > 100:
            themes.append(
                {
                    "theme": "crew_analysis",
                    "confidence": 0.8,
                    "description": "Comprehensive analysis performed by CrewAI agent",
                    "keywords": extract_keywords_from_text(crew_output)[:5],
                }
            )

        return themes
    except Exception as exc:
        logger.exception("Failed to extract themes: %s", exc)
        return []


def calculate_analysis_confidence_from_crew(crew_result: Any) -> float:
    """Calculate analysis confidence from CrewAI results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Confidence score between 0.0 and 0.9
    """
    try:
        if not crew_result:
            return 0.0

        crew_output = str(crew_result)

        # Base confidence on analysis depth and quality indicators
        confidence_indicators = ["analysis", "detailed", "comprehensive", "thorough", "insights"]
        confidence_count = sum(1 for indicator in confidence_indicators if indicator in crew_output.lower())

        base_confidence = min(len(crew_output) / 1000, 0.7)  # Length factor
        indicator_confidence = min(confidence_count * 0.1, 0.3)  # Quality indicator factor

        return min(base_confidence + indicator_confidence, 0.9)
    except Exception as exc:
        logger.exception("Failed to calculate analysis confidence: %s", exc)
        return 0.5


def analyze_text_complexity(text: str) -> dict[str, Any]:
    """Analyze text complexity metrics.

    Args:
        text: Input text to analyze

    Returns:
        Dictionary with word count, sentence count, and complexity score
    """
    try:
        words = text.split()
        sentences = text.split(".")

        complexity = {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_words_per_sentence": len(words) / max(1, len(sentences)),
            "complexity_score": min(len(words) / 100, 1.0),
        }

        return complexity
    except Exception as exc:
        logger.exception("Failed to analyze text complexity: %s", exc)
        return {}


def extract_language_features(text: str) -> dict[str, Any]:
    """Extract language features from text.

    Args:
        text: Input text to analyze

    Returns:
        Dictionary with boolean feature flags
    """
    try:
        features = {
            "has_questions": "?" in text,
            "has_exclamations": "!" in text,
            "formal_language": any(word in text.lower() for word in ["furthermore", "however", "therefore"]),
            "technical_language": any(word in text.lower() for word in ["analysis", "system", "process", "data"]),
        }

        return features
    except Exception as exc:
        logger.exception("Failed to extract language features: %s", exc)
        return {}


def extract_fact_checks_from_crew(crew_result: Any) -> dict[str, Any]:
    """Extract fact-checking results from CrewAI verification analysis.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Dictionary with verified/disputed claims and credibility assessment
    """
    try:
        if not crew_result:
            return {}

        crew_output = str(crew_result).lower()

        # Extract fact-checking indicators from crew analysis
        fact_indicators = ["verified", "factual", "accurate", "confirmed", "disputed", "false", "misleading"]
        detected_indicators = [indicator for indicator in fact_indicators if indicator in crew_output]

        fact_checks = {
            "verified_claims": len(
                [i for i in detected_indicators if i in ["verified", "factual", "accurate", "confirmed"]]
            ),
            "disputed_claims": len([i for i in detected_indicators if i in ["disputed", "false", "misleading"]]),
            "fact_indicators": detected_indicators,
            "overall_credibility": "high"
            if "verified" in crew_output
            else "medium"
            if "factual" in crew_output
            else "low",
            "crew_analysis_available": True,
        }

        return fact_checks
    except Exception as exc:
        logger.exception("Failed to extract fact checks: %s", exc)
        return {"error": "extraction_failed", "crew_analysis_available": False}


def extract_logical_analysis_from_crew(crew_result: Any) -> dict[str, Any]:
    """Extract logical analysis results from CrewAI verification.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Dictionary with detected fallacies and consistency assessment
    """
    try:
        if not crew_result:
            return {}

        crew_output = str(crew_result).lower()

        # Identify logical fallacy indicators
        fallacy_indicators = [
            "fallacy",
            "bias",
            "logical error",
            "flawed reasoning",
            "contradiction",
            "inconsistency",
        ]
        detected_fallacies = [indicator for indicator in fallacy_indicators if indicator in crew_output]

        logical_analysis = {
            "fallacies_detected": detected_fallacies,
            "fallacy_count": len(detected_fallacies),
            "logical_consistency": "low"
            if len(detected_fallacies) > 2
            else "medium"
            if len(detected_fallacies) > 0
            else "high",
            "reasoning_quality": "strong" if not detected_fallacies else "weak",
            "crew_analysis_depth": len(crew_output),
        }

        return logical_analysis
    except Exception as exc:
        logger.exception("Failed to extract logical analysis: %s", exc)
        return {"fallacies_detected": [], "error": "analysis_failed"}


def extract_credibility_from_crew(crew_result: Any) -> dict[str, Any]:
    """Extract credibility assessment from CrewAI verification.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Dictionary with credibility score, factors, and assessment
    """
    try:
        if not crew_result:
            return {"score": 0.0, "factors": []}

        crew_output = str(crew_result).lower()

        # Credibility indicators
        high_cred = ["authoritative", "reliable", "credible", "trustworthy", "verified source"]
        low_cred = ["unreliable", "questionable", "dubious", "unverified", "biased source"]

        high_count = sum(1 for indicator in high_cred if indicator in crew_output)
        low_count = sum(1 for indicator in low_cred if indicator in crew_output)

        credibility_score = max(0.0, min(1.0, (high_count - low_count + 2) / 4))

        credibility = {
            "score": credibility_score,
            "factors": {
                "positive_indicators": high_count,
                "negative_indicators": low_count,
                "analysis_depth": len(crew_output),
            },
            "assessment": "high" if credibility_score > 0.7 else "medium" if credibility_score > 0.4 else "low",
        }

        return credibility
    except Exception as exc:
        logger.exception("Failed to extract credibility: %s", exc)
        return {"score": 0.5, "factors": [], "error": "assessment_failed"}


def extract_bias_indicators_from_crew(crew_result: Any) -> list[dict[str, Any]]:
    """Extract bias indicators from CrewAI verification.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        List of detected bias dictionaries with type, confidence, and indicators
    """
    try:
        if not crew_result:
            return []

        crew_output = str(crew_result).lower()

        bias_types = {
            "confirmation_bias": ["confirmation bias", "selective information"],
            "selection_bias": ["cherry picking", "selective evidence"],
            "cognitive_bias": ["cognitive bias", "mental shortcut"],
            "political_bias": ["political bias", "partisan", "ideological"],
        }

        detected_biases = []
        for bias_type, indicators in bias_types.items():
            if any(indicator in crew_output for indicator in indicators):
                detected_biases.append(
                    {
                        "type": bias_type,
                        "confidence": 0.8,
                        "indicators": [ind for ind in indicators if ind in crew_output],
                    }
                )

        return detected_biases
    except Exception as exc:
        logger.exception("Failed to extract bias indicators: %s", exc)
        return []


def extract_source_validation_from_crew(crew_result: Any) -> dict[str, Any]:
    """Extract source validation results from CrewAI verification.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Dictionary with validation status, confidence, and quality
    """
    try:
        if not crew_result:
            return {"validated": False, "reason": "no_analysis"}

        crew_output = str(crew_result).lower()

        # Source validation indicators
        valid_indicators = ["verified source", "authoritative", "primary source", "credible publication"]
        invalid_indicators = ["unverified", "questionable source", "unreliable", "no source"]

        valid_count = sum(1 for indicator in valid_indicators if indicator in crew_output)
        invalid_count = sum(1 for indicator in invalid_indicators if indicator in crew_output)

        validation = {
            "validated": valid_count > invalid_count,
            "confidence": min(max(valid_count - invalid_count, 0) / 3, 1.0),
            "validation_factors": {"positive_signals": valid_count, "negative_signals": invalid_count},
            "source_quality": "high" if valid_count > 2 else "medium" if valid_count > 0 else "unknown",
        }

        return validation
    except Exception as exc:
        logger.exception("Failed to extract source validation: %s", exc)
        return {"validated": False, "reason": "validation_failed"}


def calculate_verification_confidence_from_crew(crew_result: Any) -> float:
    """Calculate overall verification confidence from CrewAI analysis.

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
        high_conf = ["verified", "confirmed", "certain", "definitive", "clear evidence"]
        medium_conf = ["likely", "probable", "suggests", "indicates"]
        low_conf = ["uncertain", "unclear", "insufficient evidence", "questionable"]

        high_count = sum(1 for indicator in high_conf if indicator in crew_output)
        medium_count = sum(1 for indicator in medium_conf if indicator in crew_output)
        low_count = sum(1 for indicator in low_conf if indicator in crew_output)

        # Calculate weighted confidence
        confidence = (high_count * 0.9 + medium_count * 0.6 - low_count * 0.3) / max(
            1, high_count + medium_count + low_count
        )

        return max(0.0, min(1.0, confidence))
    except Exception as exc:
        logger.exception("Failed to calculate verification confidence: %s", exc)
        return 0.5


def calculate_agent_confidence_from_crew(crew_result: Any) -> float:
    """Calculate agent confidence from CrewAI analysis quality.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Confidence score between 0.0 and 0.9
    """
    try:
        if not crew_result:
            return 0.0

        crew_output = str(crew_result)

        # Quality indicators for agent performance
        quality_indicators = ["comprehensive", "thorough", "detailed", "analysis", "assessment"]
        quality_count = sum(1 for indicator in quality_indicators if indicator in crew_output.lower())

        # Base confidence on analysis depth and quality
        length_factor = min(len(crew_output) / 500, 0.5)  # Up to 0.5 for length
        quality_factor = min(quality_count * 0.1, 0.4)  # Up to 0.4 for quality indicators

        return min(length_factor + quality_factor, 0.9)
    except Exception as exc:
        logger.exception("Failed to calculate agent confidence: %s", exc)
        return 0.5


# Public API - all extraction functions
__all__ = [
    "extract_timeline_from_crew",
    "extract_index_from_crew",
    "calculate_transcript_quality",
    "extract_keywords_from_text",
    "extract_linguistic_patterns_from_crew",
    "extract_sentiment_from_crew",
    "extract_themes_from_crew",
    "calculate_analysis_confidence_from_crew",
    "analyze_text_complexity",
    "extract_language_features",
    "extract_fact_checks_from_crew",
    "extract_logical_analysis_from_crew",
    "extract_credibility_from_crew",
    "extract_bias_indicators_from_crew",
    "extract_source_validation_from_crew",
    "calculate_verification_confidence_from_crew",
    "calculate_agent_confidence_from_crew",
]
