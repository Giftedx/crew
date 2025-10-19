"""Content analysis extraction utilities for CrewAI outputs.

This module contains functions that extract content analysis data from CrewAI
crew results, including timeline, indexing, keywords, sentiment, and themes.

Extracted from extractors.py to improve maintainability and organization.
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


def extract_keywords_from_text(text: str) -> list[str]:
    """Extract keywords from text using simple frequency analysis.

    Args:
        text: Text to analyze

    Returns:
        List of top keywords
    """
    try:
        # Simple keyword extraction - remove common words and count frequency
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())

        # Remove common stop words
        stop_words = {
            "that",
            "this",
            "with",
            "have",
            "will",
            "from",
            "they",
            "been",
            "said",
            "each",
            "which",
            "their",
            "time",
            "would",
            "there",
            "could",
        }

        filtered_words = [w for w in words if w not in stop_words]

        # Count frequency and return top words
        word_counts = Counter(filtered_words)
        return [word for word, count in word_counts.most_common(10) if count > 1]

    except Exception as exc:
        logger.exception("Failed to extract keywords from text: %s", exc)
        return []


def extract_linguistic_patterns_from_crew(crew_result: Any) -> dict[str, Any]:
    """Extract linguistic patterns from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Dictionary with linguistic analysis patterns
    """
    try:
        if not crew_result:
            return {}

        crew_output = str(crew_result)
        patterns = {
            "sentence_length_avg": 0.0,
            "complex_sentences": 0,
            "question_count": 0,
            "exclamation_count": 0,
            "repetitive_phrases": [],
        }

        # Analyze sentence patterns
        sentences = re.split(r"[.!?]+", crew_output)
        if sentences:
            total_words = sum(len(s.split()) for s in sentences)
            patterns["sentence_length_avg"] = total_words / len(sentences)

        # Count complex sentence indicators
        patterns["complex_sentences"] = crew_output.count(";") + crew_output.count(":")
        patterns["question_count"] = crew_output.count("?")
        patterns["exclamation_count"] = crew_output.count("!")

        return patterns
    except Exception as exc:
        logger.exception("Failed to extract linguistic patterns from crew result: %s", exc)
        return {}


def extract_sentiment_from_crew(crew_result: Any) -> dict[str, Any]:
    """Extract sentiment analysis from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        Dictionary with sentiment scores and analysis
    """
    try:
        if not crew_result:
            return {"sentiment": "neutral", "confidence": 0.0, "scores": {}}

        crew_output = str(crew_result).lower()

        # Simple sentiment analysis using keyword matching
        positive_words = [
            "good",
            "great",
            "excellent",
            "positive",
            "beneficial",
            "effective",
            "successful",
            "improved",
            "better",
            "outstanding",
            "impressive",
        ]
        negative_words = [
            "bad",
            "terrible",
            "negative",
            "harmful",
            "ineffective",
            "failed",
            "worse",
            "poor",
            "disappointing",
            "concerning",
            "problematic",
        ]

        positive_count = sum(1 for word in positive_words if word in crew_output)
        negative_count = sum(1 for word in negative_words if word in crew_output)

        total_words = len(crew_output.split())
        if total_words > 0:
            positive_score = positive_count / total_words
            negative_score = negative_count / total_words

            if positive_score > negative_score:
                sentiment = "positive"
                confidence = positive_score
            elif negative_score > positive_score:
                sentiment = "negative"
                confidence = negative_score
            else:
                sentiment = "neutral"
                confidence = 0.5
        else:
            sentiment = "neutral"
            confidence = 0.0

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "scores": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": max(0, total_words - positive_count - negative_count),
            },
        }
    except Exception as exc:
        logger.exception("Failed to extract sentiment from crew result: %s", exc)
        return {"sentiment": "neutral", "confidence": 0.0, "scores": {}}


def extract_themes_from_crew(crew_result: Any) -> list[dict[str, Any]]:
    """Extract themes from CrewAI crew results.

    Args:
        crew_result: CrewAI crew execution result

    Returns:
        List of theme dictionaries with relevance scores
    """
    try:
        if not crew_result:
            return []

        crew_output = str(crew_result).lower()

        # Define theme categories and their keywords
        theme_keywords = {
            "politics": ["political", "government", "policy", "election", "democracy", "republican", "democrat"],
            "technology": ["technology", "digital", "software", "internet", "ai", "computer", "tech"],
            "economics": ["economy", "economic", "financial", "market", "business", "trade", "money"],
            "health": ["health", "medical", "healthcare", "disease", "treatment", "medicine"],
            "education": ["education", "school", "university", "learning", "teaching", "student"],
            "environment": ["environment", "climate", "nature", "pollution", "green", "sustainability"],
        }

        themes = []
        for theme, keywords in theme_keywords.items():
            keyword_count = sum(1 for keyword in keywords if keyword in crew_output)
            if keyword_count > 0:
                relevance = min(keyword_count / len(keywords), 1.0)
                themes.append({"theme": theme, "relevance": relevance, "keyword_matches": keyword_count})

        # Sort by relevance
        themes.sort(key=lambda x: x["relevance"], reverse=True)
        return themes[:5]  # Return top 5 themes

    except Exception as exc:
        logger.exception("Failed to extract themes from crew result: %s", exc)
        return []


def extract_language_features(text: str) -> dict[str, Any]:
    """Extract language features from text.

    Args:
        text: Text to analyze

    Returns:
        Dictionary with language feature analysis
    """
    try:
        features = {
            "readability_score": 0.0,
            "formality_level": "neutral",
            "technical_terms": 0,
            "emotional_language": 0,
        }

        # Calculate basic readability (simplified Flesch score)
        sentences = re.split(r"[.!?]+", text)
        words = text.split()

        if sentences and words:
            avg_sentence_length = len(words) / len(sentences)
            avg_syllables = sum(len(word) for word in words) / len(words)
            features["readability_score"] = max(0, 100 - (avg_sentence_length * 1.015) - (avg_syllables * 0.846))

        # Detect formality level
        formal_indicators = ["therefore", "furthermore", "however", "consequently", "nevertheless"]
        informal_indicators = ["yeah", "okay", "cool", "awesome", "totally"]

        formal_count = sum(1 for indicator in formal_indicators if indicator.lower() in text.lower())
        informal_count = sum(1 for indicator in informal_indicators if indicator.lower() in text.lower())

        if formal_count > informal_count:
            features["formality_level"] = "formal"
        elif informal_count > formal_count:
            features["formality_level"] = "informal"

        # Count technical terms (words with specific patterns)
        technical_patterns = [r"\b[A-Z]{2,}\b", r"\b\w+ology\b", r"\b\w+tion\b"]
        for pattern in technical_patterns:
            features["technical_terms"] += len(re.findall(pattern, text))

        # Count emotional language
        emotional_words = ["feel", "believe", "think", "love", "hate", "excited", "worried", "angry"]
        features["emotional_language"] = sum(1 for word in emotional_words if word in text.lower())

        return features

    except Exception as exc:
        logger.exception("Failed to extract language features from text: %s", exc)
        return {"readability_score": 0.0, "formality_level": "neutral", "technical_terms": 0, "emotional_language": 0}


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
        return 0.0
