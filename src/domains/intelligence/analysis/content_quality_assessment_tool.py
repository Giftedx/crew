"""Content Quality Assessment Tool for Week 4 Optimization.

This module implements transcript quality scoring to enable quality threshold filtering,
allowing the system to skip full analysis for low-quality content.
"""
from __future__ import annotations
import logging
import os
import re
from dataclasses import dataclass
from typing import Any
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool
logger = logging.getLogger(__name__)

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
        return {'word_count': self.word_count, 'sentence_count': self.sentence_count, 'avg_sentence_length': self.avg_sentence_length, 'coherence_score': self.coherence_score, 'topic_clarity_score': self.topic_clarity_score, 'language_quality_score': self.language_quality_score, 'overall_quality_score': self.overall_quality_score}

class ContentQualityAssessmentTool(BaseTool[dict[str, Any]]):
    """Tool for assessing transcript quality to enable threshold filtering."""
    name: str = 'content_quality_assessment'
    description: str = 'Assess transcript quality for threshold-based processing decisions'
    MIN_WORD_COUNT = int(os.getenv('QUALITY_MIN_WORD_COUNT', '500'))
    MIN_SENTENCE_COUNT = int(os.getenv('QUALITY_MIN_SENTENCE_COUNT', '10'))
    MIN_COHERENCE_SCORE = float(os.getenv('QUALITY_MIN_COHERENCE', '0.6'))
    MIN_OVERALL_SCORE = float(os.getenv('QUALITY_MIN_OVERALL', '0.65'))

    def __init__(self):
        """Initialize the content quality assessment tool."""
        super().__init__()
        self._metrics = get_metrics()

    def run(self, input_data: dict) -> StepResult:
        """
        Assess transcript quality and return quality metrics.

        Args:
            input_data: Dictionary containing transcript, metadata, and optional custom thresholds

        Returns:
            StepResult containing quality metrics and processing recommendation
        """
        try:
            transcript = input_data.get('transcript', '')
            if not transcript or not isinstance(transcript, str):
                return StepResult.fail(error='Invalid transcript provided for quality assessment', error_category='input_validation')
            custom_thresholds = input_data.get('thresholds', {})
            metrics = self._calculate_quality_metrics(transcript)
            should_process_fully = self._should_process_fully(metrics, custom_thresholds)
            result = {'quality_metrics': metrics.to_dict(), 'should_process_fully': should_process_fully, 'should_process': should_process_fully, 'overall_score': metrics.overall_quality_score, 'recommendation': self._get_processing_recommendation(metrics), 'recommendation_details': self._get_processing_recommendation(metrics), 'bypass_reason': None if should_process_fully else self._get_bypass_reason(metrics)}
            try:
                self._metrics.counter('tool_runs_total', labels={'tool': self.name or 'content_quality_assessment', 'outcome': 'success'}).inc()
            except Exception as exc:
                logger.debug('metrics increment failed: %s', exc)
            return StepResult.ok(result=result)
        except Exception as e:
            try:
                self._metrics.counter('tool_runs_total', labels={'tool': self.name or 'content_quality_assessment', 'outcome': 'error'}).inc()
            except Exception as exc:
                logger.debug('metrics increment failed (error path): %s', exc)
            return StepResult.fail(error=f'Quality assessment failed: {e!s}', error_category='processing_error')

    def _calculate_quality_metrics(self, transcript: str) -> QualityMetrics:
        """Calculate comprehensive quality metrics for the transcript."""
        words = self._extract_words(transcript)
        sentences = self._extract_sentences(transcript)
        word_count = len(words)
        sentence_count = len(sentences)
        avg_sentence_length = word_count / max(sentence_count, 1)
        coherence_score = self._calculate_coherence_score(words, sentences)
        topic_clarity_score = self._calculate_topic_clarity_score(words)
        language_quality_score = self._calculate_language_quality_score(transcript, words)
        overall_quality_score = self._calculate_overall_score(word_count, sentence_count, avg_sentence_length, coherence_score, topic_clarity_score, language_quality_score)
        return QualityMetrics(word_count=word_count, sentence_count=sentence_count, avg_sentence_length=avg_sentence_length, coherence_score=coherence_score, topic_clarity_score=topic_clarity_score, language_quality_score=language_quality_score, overall_quality_score=overall_quality_score)

    def _extract_words(self, text: str) -> list[str]:
        """Extract meaningful words from text."""
        words = re.findall('\\b[a-zA-Z]{2,}\\b', text.lower())
        filler_words = {'um', 'uh', 'like', 'you', 'know', 'so', 'well', 'yeah', 'okay', 'right', 'actually', 'basically', 'literally', 'just', 'really'}
        meaningful_words = [word for word in words if word not in filler_words]
        return meaningful_words

    def _extract_sentences(self, text: str) -> list[str]:
        """Extract sentences from text."""
        sentences = re.split('[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        return sentences

    def _calculate_coherence_score(self, words: list[str], sentences: list[str]) -> float:
        """Calculate coherence score based on word repetition and sentence structure."""
        if not words or not sentences:
            return 0.0
        unique_words = set(words)
        word_diversity = len(unique_words) / len(words) if words else 0
        sentence_lengths = [len(s.split()) for s in sentences]
        if len(sentence_lengths) > 1:
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            variance = sum(((length - avg_length) ** 2 for length in sentence_lengths)) / len(sentence_lengths)
            length_consistency = max(0, 1 - variance / avg_length ** 2)
        else:
            length_consistency = 0.5
        coherence_score = word_diversity * 0.6 + length_consistency * 0.4
        return min(1.0, coherence_score)

    def _calculate_topic_clarity_score(self, words: list[str]) -> float:
        """Calculate topic clarity based on word frequency and distribution."""
        if not words:
            return 0.0
        from collections import Counter
        word_freq = Counter(words)
        repeated_words = {word: count for word, count in word_freq.items() if count > 1}
        if not repeated_words:
            return 0.3
        max_frequency = max(repeated_words.values())
        total_words = len(words)
        dominance_penalty = max_frequency / total_words
        dominance_penalty = dominance_penalty * 2 if dominance_penalty > 0.2 else 0
        repetition_score = min(1.0, len(repeated_words) / 10)
        topic_clarity = max(0.0, repetition_score - dominance_penalty)
        return min(1.0, topic_clarity)

    def _calculate_language_quality_score(self, transcript: str, words: list[str]) -> float:
        """Calculate language quality based on grammar and structure indicators."""
        if not transcript or not words:
            return 0.0
        punctuation_count = len(re.findall('[.!?;:,]', transcript))
        punctuation_ratio = punctuation_count / len(words) if words else 0
        punctuation_score = min(1.0, punctuation_ratio * 10)
        capital_count = len(re.findall('[A-Z]', transcript))
        capital_ratio = capital_count / len(transcript) if transcript else 0
        capital_score = min(1.0, capital_ratio * 20)
        complete_words = len([w for w in words if len(w) >= 3])
        complete_ratio = complete_words / len(words) if words else 0
        language_quality = punctuation_score * 0.4 + capital_score * 0.3 + complete_ratio * 0.3
        return min(1.0, language_quality)

    def _calculate_overall_score(self, word_count: int, sentence_count: int, avg_sentence_length: float, coherence_score: float, topic_clarity_score: float, language_quality_score: float) -> float:
        """Calculate weighted overall quality score."""
        if word_count < 100:
            length_score = word_count / 100
        elif word_count > 2000:
            length_score = max(0.5, 1 - (word_count - 2000) / 2000)
        else:
            length_score = 1.0
        if sentence_count == 0:
            structure_score = 0.0
        elif avg_sentence_length < 3:
            structure_score = 0.3
        elif avg_sentence_length > 30:
            structure_score = 0.6
        else:
            structure_score = 1.0
        overall_score = length_score * 0.25 + structure_score * 0.15 + coherence_score * 0.25 + topic_clarity_score * 0.2 + language_quality_score * 0.15
        return min(1.0, overall_score)

    def _should_process_fully(self, metrics: QualityMetrics, custom_thresholds: dict | None=None) -> bool:
        """Determine if content should receive full processing based on quality metrics.

        Args:
            metrics: Quality metrics calculated from transcript
            custom_thresholds: Optional content-type specific thresholds (Week 4 Phase 2)

        Returns:
            True if content should receive full processing
        """
        if custom_thresholds:
            min_overall = custom_thresholds.get('quality_threshold', self.MIN_OVERALL_SCORE)
            min_coherence = custom_thresholds.get('coherence_threshold', self.MIN_COHERENCE_SCORE)
            min_word_count = custom_thresholds.get('min_word_count', self.MIN_WORD_COUNT)
            min_sentence_count = custom_thresholds.get('min_sentence_count', self.MIN_SENTENCE_COUNT)
        else:
            min_overall = self.MIN_OVERALL_SCORE
            min_coherence = self.MIN_COHERENCE_SCORE
            min_word_count = self.MIN_WORD_COUNT
            min_sentence_count = self.MIN_SENTENCE_COUNT
        checks = [metrics.word_count >= min_word_count, metrics.sentence_count >= min_sentence_count, metrics.coherence_score >= min_coherence, metrics.overall_quality_score >= min_overall]
        return sum(checks) >= 3

    def _get_processing_recommendation(self, metrics: QualityMetrics) -> str:
        """Get processing recommendation based on quality metrics."""
        if metrics.overall_quality_score >= 0.8:
            return 'full_analysis'
        elif metrics.overall_quality_score >= 0.65:
            return 'standard_analysis'
        elif metrics.overall_quality_score >= 0.4:
            return 'basic_analysis'
        else:
            return 'minimal_processing'

    def _get_bypass_reason(self, metrics: QualityMetrics) -> str:
        """Get reason for bypassing full processing."""
        reasons = []
        if metrics.word_count < self.MIN_WORD_COUNT:
            reasons.append(f'insufficient_content (words: {metrics.word_count} < {self.MIN_WORD_COUNT})')
        if metrics.sentence_count < self.MIN_SENTENCE_COUNT:
            reasons.append(f'fragmented_content (sentences: {metrics.sentence_count} < {self.MIN_SENTENCE_COUNT})')
        if metrics.coherence_score < self.MIN_COHERENCE_SCORE:
            reasons.append(f'low_coherence (score: {metrics.coherence_score:.2f} < {self.MIN_COHERENCE_SCORE})')
        if metrics.overall_quality_score < self.MIN_OVERALL_SCORE:
            reasons.append(f'low_overall_quality (score: {metrics.overall_quality_score:.2f} < {self.MIN_OVERALL_SCORE})')
        return '; '.join(reasons) if reasons else 'unknown'