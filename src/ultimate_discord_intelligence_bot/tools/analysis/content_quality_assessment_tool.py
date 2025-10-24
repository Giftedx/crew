"""Content Quality Assessment Tool for Week 4 Optimization.

This module implements transcript quality scoring to enable quality threshold filtering,
allowing the system to skip full analysis for low-quality content.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


@dataclass
class QualityMetrics:
    """Container for transcript quality metrics."""

    word_count: int
    sentence_count: int
    avg_sentence_length: float
    coherence_score: float
    topic_clarity_score: float
    language_quality_score: float
    overall_quality_score: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "avg_sentence_length": self.avg_sentence_length,
            "coherence_score": self.coherence_score,
            "topic_clarity_score": self.topic_clarity_score,
            "language_quality_score": self.language_quality_score,
            "overall_quality_score": self.overall_quality_score,
        }


class ContentQualityAssessmentTool(BaseTool[dict[str, Any]]):
    """Tool for assessing transcript quality to enable threshold filtering."""

    name: str = "content_quality_assessment"
    description: str = "Assess transcript quality for threshold-based processing decisions"

    # Quality thresholds (configurable)
    MIN_WORD_COUNT = int(os.getenv("QUALITY_MIN_WORD_COUNT", "500"))
    MIN_SENTENCE_COUNT = int(os.getenv("QUALITY_MIN_SENTENCE_COUNT", "10"))
    MIN_COHERENCE_SCORE = float(os.getenv("QUALITY_MIN_COHERENCE", "0.6"))
    MIN_OVERALL_SCORE = float(os.getenv("QUALITY_MIN_OVERALL", "0.65"))

    def run(self, input_data: dict) -> StepResult:
        """
        Assess transcript quality and return quality metrics.

        Args:
            input_data: Dictionary containing transcript, metadata, and optional custom thresholds

        Returns:
            StepResult containing quality metrics and processing recommendation
        """
        try:
            transcript = input_data.get("transcript", "")
            if not transcript or not isinstance(transcript, str):
                return StepResult.fail(
                    error="Invalid transcript provided for quality assessment",
                    error_category="input_validation",
                )

            # Get custom thresholds if provided (Week 4 Phase 2: content-type aware)
            custom_thresholds = input_data.get("thresholds", {})

            # Calculate quality metrics
            metrics = self._calculate_quality_metrics(transcript)

            # Determine processing recommendation (with custom thresholds if provided)
            should_process_fully = self._should_process_fully(metrics, custom_thresholds)

            result = {
                "quality_metrics": metrics.to_dict(),
                "should_process_fully": should_process_fully,
                "should_process": should_process_fully,  # Pipeline compatibility
                "overall_score": metrics.overall_quality_score,  # Pipeline compatibility
                "recommendation": self._get_processing_recommendation(metrics),
                "recommendation_details": self._get_processing_recommendation(metrics),  # Pipeline compatibility
                "bypass_reason": None if should_process_fully else self._get_bypass_reason(metrics),
            }

            return StepResult.ok(result=result)

        except Exception as e:
            return StepResult.fail(
                error=f"Quality assessment failed: {e!s}",
                error_category="processing_error",
            )

    def _calculate_quality_metrics(self, transcript: str) -> QualityMetrics:
        """Calculate comprehensive quality metrics for the transcript."""
        # Basic text metrics
        words = self._extract_words(transcript)
        sentences = self._extract_sentences(transcript)

        word_count = len(words)
        sentence_count = len(sentences)
        avg_sentence_length = word_count / max(sentence_count, 1)

        # Advanced quality scores
        coherence_score = self._calculate_coherence_score(words, sentences)
        topic_clarity_score = self._calculate_topic_clarity_score(words)
        language_quality_score = self._calculate_language_quality_score(transcript, words)

        # Overall quality score (weighted combination)
        overall_quality_score = self._calculate_overall_score(
            word_count,
            sentence_count,
            avg_sentence_length,
            coherence_score,
            topic_clarity_score,
            language_quality_score,
        )

        return QualityMetrics(
            word_count=word_count,
            sentence_count=sentence_count,
            avg_sentence_length=avg_sentence_length,
            coherence_score=coherence_score,
            topic_clarity_score=topic_clarity_score,
            language_quality_score=language_quality_score,
            overall_quality_score=overall_quality_score,
        )

    def _extract_words(self, text: str) -> list[str]:
        """Extract meaningful words from text."""
        # Remove filler words and normalize
        words = re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())

        # Filter out common filler words that don't contribute to quality
        filler_words = {
            "um",
            "uh",
            "like",
            "you",
            "know",
            "so",
            "well",
            "yeah",
            "okay",
            "right",
            "actually",
            "basically",
            "literally",
            "just",
            "really",
        }

        meaningful_words = [word for word in words if word not in filler_words]
        return meaningful_words

    def _extract_sentences(self, text: str) -> list[str]:
        """Extract sentences from text."""
        # Split on sentence boundaries
        sentences = re.split(r"[.!?]+", text)

        # Filter out very short fragments
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        return sentences

    def _calculate_coherence_score(self, words: list[str], sentences: list[str]) -> float:
        """Calculate coherence score based on word repetition and sentence structure."""
        if not words or not sentences:
            return 0.0

        # Word diversity (higher is better)
        unique_words = set(words)
        word_diversity = len(unique_words) / len(words) if words else 0

        # Sentence length consistency (moderate variance is good)
        sentence_lengths = [len(s.split()) for s in sentences]
        if len(sentence_lengths) > 1:
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            variance = sum((length - avg_length) ** 2 for length in sentence_lengths) / len(sentence_lengths)
            length_consistency = max(0, 1 - (variance / (avg_length**2)))
        else:
            length_consistency = 0.5

        # Combine metrics (weighted average)
        coherence_score = (word_diversity * 0.6) + (length_consistency * 0.4)
        return min(1.0, coherence_score)

    def _calculate_topic_clarity_score(self, words: list[str]) -> float:
        """Calculate topic clarity based on word frequency and distribution."""
        if not words:
            return 0.0

        from collections import Counter

        word_freq = Counter(words)

        # Topic words should appear multiple times but not dominate
        repeated_words = {word: count for word, count in word_freq.items() if count > 1}

        if not repeated_words:
            return 0.3  # No repeated words = poor topic clarity

        # Good topic clarity: some words repeated but not excessive
        max_frequency = max(repeated_words.values())
        total_words = len(words)

        # Penalize if any single word dominates too much
        dominance_penalty = max_frequency / total_words
        if dominance_penalty > 0.2:  # Single word >20% of content
            dominance_penalty = dominance_penalty * 2
        else:
            dominance_penalty = 0

        # Reward reasonable repetition
        repetition_score = min(1.0, len(repeated_words) / 10)  # Up to 10 repeated words is good

        topic_clarity = max(0.0, repetition_score - dominance_penalty)
        return min(1.0, topic_clarity)

    def _calculate_language_quality_score(self, transcript: str, words: list[str]) -> float:
        """Calculate language quality based on grammar and structure indicators."""
        if not transcript or not words:
            return 0.0

        # Punctuation usage (indicates structured speech)
        punctuation_count = len(re.findall(r"[.!?;:,]", transcript))
        punctuation_ratio = punctuation_count / len(words) if words else 0
        punctuation_score = min(1.0, punctuation_ratio * 10)  # Normalize to 0-1

        # Capitalization usage
        capital_count = len(re.findall(r"[A-Z]", transcript))
        capital_ratio = capital_count / len(transcript) if transcript else 0
        capital_score = min(1.0, capital_ratio * 20)  # Normalize to 0-1

        # Complete word ratio (vs fragments)
        complete_words = len([w for w in words if len(w) >= 3])
        complete_ratio = complete_words / len(words) if words else 0

        # Combine indicators
        language_quality = (punctuation_score * 0.4) + (capital_score * 0.3) + (complete_ratio * 0.3)
        return min(1.0, language_quality)

    def _calculate_overall_score(
        self,
        word_count: int,
        sentence_count: int,
        avg_sentence_length: float,
        coherence_score: float,
        topic_clarity_score: float,
        language_quality_score: float,
    ) -> float:
        """Calculate weighted overall quality score."""
        # Length score (sigmoid curve - too short or too long is bad)
        if word_count < 100:
            length_score = word_count / 100
        elif word_count > 2000:
            length_score = max(0.5, 1 - ((word_count - 2000) / 2000))
        else:
            length_score = 1.0

        # Sentence structure score
        if sentence_count == 0:
            structure_score = 0.0
        elif avg_sentence_length < 3:
            structure_score = 0.3  # Very short sentences
        elif avg_sentence_length > 30:
            structure_score = 0.6  # Very long sentences
        else:
            structure_score = 1.0  # Good sentence length

        # Weighted combination
        overall_score = (
            length_score * 0.25
            + structure_score * 0.15
            + coherence_score * 0.25
            + topic_clarity_score * 0.20
            + language_quality_score * 0.15
        )

        return min(1.0, overall_score)

    def _should_process_fully(self, metrics: QualityMetrics, custom_thresholds: dict | None = None) -> bool:
        """Determine if content should receive full processing based on quality metrics.

        Args:
            metrics: Quality metrics calculated from transcript
            custom_thresholds: Optional content-type specific thresholds (Week 4 Phase 2)

        Returns:
            True if content should receive full processing
        """
        # Use custom thresholds if provided, otherwise use defaults
        if custom_thresholds:
            min_overall = custom_thresholds.get("quality_threshold", self.MIN_OVERALL_SCORE)
            min_coherence = custom_thresholds.get("coherence_threshold", self.MIN_COHERENCE_SCORE)
            min_word_count = custom_thresholds.get("min_word_count", self.MIN_WORD_COUNT)
            min_sentence_count = custom_thresholds.get("min_sentence_count", self.MIN_SENTENCE_COUNT)
        else:
            min_overall = self.MIN_OVERALL_SCORE
            min_coherence = self.MIN_COHERENCE_SCORE
            min_word_count = self.MIN_WORD_COUNT
            min_sentence_count = self.MIN_SENTENCE_COUNT

        # Multiple threshold checks
        checks = [
            metrics.word_count >= min_word_count,
            metrics.sentence_count >= min_sentence_count,
            metrics.coherence_score >= min_coherence,
            metrics.overall_quality_score >= min_overall,
        ]

        # Require majority of checks to pass
        return sum(checks) >= 3

    def _get_processing_recommendation(self, metrics: QualityMetrics) -> str:
        """Get processing recommendation based on quality metrics."""
        if metrics.overall_quality_score >= 0.8:
            return "full_analysis"
        elif metrics.overall_quality_score >= 0.65:
            return "standard_analysis"
        elif metrics.overall_quality_score >= 0.4:
            return "basic_analysis"
        else:
            return "minimal_processing"

    def _get_bypass_reason(self, metrics: QualityMetrics) -> str:
        """Get reason for bypassing full processing."""
        reasons = []

        if metrics.word_count < self.MIN_WORD_COUNT:
            reasons.append(f"insufficient_content (words: {metrics.word_count} < {self.MIN_WORD_COUNT})")

        if metrics.sentence_count < self.MIN_SENTENCE_COUNT:
            reasons.append(f"fragmented_content (sentences: {metrics.sentence_count} < {self.MIN_SENTENCE_COUNT})")

        if metrics.coherence_score < self.MIN_COHERENCE_SCORE:
            reasons.append(f"low_coherence (score: {metrics.coherence_score:.2f} < {self.MIN_COHERENCE_SCORE})")

        if metrics.overall_quality_score < self.MIN_OVERALL_SCORE:
            reasons.append(
                f"low_overall_quality (score: {metrics.overall_quality_score:.2f} < {self.MIN_OVERALL_SCORE})"
            )

        return "; ".join(reasons) if reasons else "unknown"


# Quality assessment tool implementation complete
