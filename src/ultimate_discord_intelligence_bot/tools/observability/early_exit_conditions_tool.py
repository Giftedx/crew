"""Early Exit Conditions Tool for Week 4 Optimization.

This module implements confidence-based early exit conditions to terminate
processing when sufficient information has been gathered, avoiding unnecessary
computational overhead.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


@dataclass
class ConfidenceMetrics:
    """Container for confidence assessment metrics."""

    content_clarity: float
    information_density: float
    topic_coherence: float
    completeness_score: float
    overall_confidence: float
    should_exit_early: bool
    exit_reason: str | None = None


class EarlyExitConditionsTool(BaseTool[dict]):
    """Evaluates processing confidence to determine early exit conditions."""

    name: str = "early_exit_conditions_tool"
    description: str = (
        "Assesses processing confidence to enable early exit when sufficient information has been gathered"
    )

    def run(self, input_data: dict) -> StepResult:
        """Run confidence assessment for early exit determination.

        Args:
            input_data: Dict containing transcript, analysis results, and metadata

        Returns:
            StepResult with confidence metrics and exit recommendation
        """
        try:
            transcript = input_data.get("transcript", "")
            title = input_data.get("title", "")
            partial_analysis = input_data.get("partial_analysis", {})
            processing_stage = input_data.get("processing_stage", "unknown")
            if not transcript:
                return StepResult.fail(error="No transcript provided for confidence assessment")
            confidence_metrics = self._calculate_confidence_metrics(
                transcript, title, partial_analysis, processing_stage
            )
            result = {
                "confidence_metrics": {
                    "content_clarity": confidence_metrics.content_clarity,
                    "information_density": confidence_metrics.information_density,
                    "topic_coherence": confidence_metrics.topic_coherence,
                    "completeness_score": confidence_metrics.completeness_score,
                    "overall_confidence": confidence_metrics.overall_confidence,
                },
                "exit_decision": {
                    "should_exit_early": confidence_metrics.should_exit_early,
                    "exit_reason": confidence_metrics.exit_reason,
                    "confidence_threshold": self._get_confidence_threshold(processing_stage),
                    "stage": processing_stage,
                },
                "recommendations": self._generate_exit_recommendations(confidence_metrics),
                "estimated_savings": self._estimate_processing_savings(confidence_metrics, processing_stage),
            }
            return StepResult.ok(result=result)
        except Exception as e:
            return StepResult.fail(error=f"Early exit evaluation failed: {e!s}")

    def _calculate_confidence_metrics(
        self, transcript: str, title: str, partial_analysis: dict, processing_stage: str
    ) -> ConfidenceMetrics:
        """Calculate confidence metrics for early exit decision."""
        content_clarity = self._assess_content_clarity(transcript, title)
        information_density = self._assess_information_density(transcript)
        topic_coherence = self._assess_topic_coherence(transcript, partial_analysis)
        completeness_score = self._assess_completeness(transcript, partial_analysis, processing_stage)
        overall_confidence = self._calculate_overall_confidence(
            content_clarity, information_density, topic_coherence, completeness_score
        )
        should_exit_early, exit_reason = self._evaluate_exit_conditions(
            overall_confidence, processing_stage, partial_analysis
        )
        return ConfidenceMetrics(
            content_clarity=content_clarity,
            information_density=information_density,
            topic_coherence=topic_coherence,
            completeness_score=completeness_score,
            overall_confidence=overall_confidence,
            should_exit_early=should_exit_early,
            exit_reason=exit_reason,
        )

    def _assess_content_clarity(self, transcript: str, title: str) -> float:
        """Assess how clear and understandable the content is."""
        combined_text = f"{title} {transcript}".lower()
        words = combined_text.split()
        if len(words) < 10:
            return 0.2
        clarity_score = 0.5
        clear_indicators = [
            "\\b(explain|definition|example|specifically|clearly|obviously)\\b",
            "\\b(first|second|third|next|then|finally|in conclusion)\\b",
            "\\b(because|therefore|however|although|for instance)\\b",
        ]
        for pattern in clear_indicators:
            matches = len(re.findall(pattern, combined_text))
            clarity_score += min(matches * 0.1, 0.2)
        unclear_indicators = [
            "\\b(um|uh|like|you know|I guess|maybe|sort of)\\b",
            "\\b(confusing|unclear|I don\\'t know|not sure)\\b",
        ]
        for pattern in unclear_indicators:
            matches = len(re.findall(pattern, combined_text))
            clarity_score -= min(matches * 0.05, 0.1)
        sentences = re.split("[.!?]+", transcript)
        if sentences:
            avg_sentence_length = sum((len(s.split()) for s in sentences)) / len(sentences)
            if 5 <= avg_sentence_length <= 25:
                clarity_score += 0.1
            elif avg_sentence_length > 40:
                clarity_score -= 0.1
        return max(0.0, min(1.0, clarity_score))

    def _assess_information_density(self, transcript: str) -> float:
        """Assess the density of meaningful information in the transcript."""
        words = transcript.lower().split()
        if len(words) < 10:
            return 0.1
        info_patterns = [
            "\\b(data|research|study|analysis|evidence|statistics)\\b",
            "\\b(important|significant|crucial|key|essential|critical)\\b",
            "\\b(process|method|technique|approach|strategy|solution)\\b",
            "\\b(result|conclusion|finding|discovery|insight|outcome)\\b",
        ]
        info_word_count = 0
        for pattern in info_patterns:
            info_word_count += len(re.findall(pattern, transcript.lower()))
        density_ratio = info_word_count / len(words)
        density_score = min(density_ratio * 50, 1.0)
        tech_patterns = [
            "\\b(algorithm|system|framework|architecture|implementation)\\b",
            "\\b(optimize|efficient|performance|scalable|robust)\\b",
        ]
        tech_count = 0
        for pattern in tech_patterns:
            tech_count += len(re.findall(pattern, transcript.lower()))
        if tech_count > 0:
            density_score += min(tech_count * 0.05, 0.2)
        return max(0.0, min(1.0, density_score))

    def _assess_topic_coherence(self, transcript: str, partial_analysis: dict) -> float:
        """Assess how coherent and focused the topic discussion is."""
        coherence_score = 0.5
        topics = partial_analysis.get("topics", [])
        if topics:
            if len(topics) <= 3:
                coherence_score += 0.2
            elif len(topics) <= 5:
                coherence_score += 0.1
            else:
                coherence_score -= 0.1
        words = transcript.lower().split()
        if len(words) < 50:
            return max(coherence_score - 0.2, 0.1)
        transition_patterns = [
            "\\b(also|additionally|furthermore|moreover|in addition)\\b",
            "\\b(however|but|although|on the other hand|nevertheless)\\b",
            "\\b(moving on|next topic|speaking of|regarding|concerning)\\b",
        ]
        transition_count = 0
        for pattern in transition_patterns:
            transition_count += len(re.findall(pattern, transcript.lower()))
        if 1 <= transition_count <= 5:
            coherence_score += 0.1
        elif transition_count > 10:
            coherence_score -= 0.15
        repetition_score = self._assess_topic_repetition(transcript)
        coherence_score += repetition_score * 0.1
        return max(0.0, min(1.0, coherence_score))

    def _assess_topic_repetition(self, transcript: str) -> float:
        """Assess repetition of key terms indicating focused discussion."""
        words = transcript.lower().split()
        word_counts = {}
        common_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
        }
        for word in words:
            clean_word = re.sub("[^\\w]", "", word)
            if len(clean_word) > 3 and clean_word not in common_words:
                word_counts[clean_word] = word_counts.get(clean_word, 0) + 1
        if not word_counts:
            return 0.0
        repeated_words = {word: count for word, count in word_counts.items() if count > 1}
        if not repeated_words:
            return 0.0
        total_significant_words = sum(word_counts.values())
        repetition_weight = sum((count - 1 for count in repeated_words.values()))
        return min(repetition_weight / total_significant_words, 1.0)

    def _assess_completeness(self, transcript: str, partial_analysis: dict, stage: str) -> float:
        """Assess completeness of information based on processing stage."""
        completeness_score = 0.5
        if stage in ["transcription", "initial"]:
            word_count = len(transcript.split())
            if word_count > 100:
                completeness_score += 0.2
            if word_count > 500:
                completeness_score += 0.2
        elif stage in ["analysis", "intermediate"]:
            if partial_analysis.get("summary"):
                completeness_score += 0.2
            if partial_analysis.get("topics"):
                completeness_score += 0.2
            if partial_analysis.get("sentiment"):
                completeness_score += 0.1
        elif stage in ["final", "complete"]:
            required_components = ["summary", "topics", "sentiment", "key_points"]
            available_components = sum((1 for comp in required_components if partial_analysis.get(comp)))
            completeness_score += available_components / len(required_components) * 0.4
        completion_patterns = [
            "\\b(in conclusion|to summarize|in summary|finally|lastly)\\b",
            "\\b(that\\'s all|that\\'s it|end of|wrapping up|to conclude)\\b",
        ]
        for pattern in completion_patterns:
            if re.search(pattern, transcript.lower()):
                completeness_score += 0.1
                break
        return max(0.0, min(1.0, completeness_score))

    def _calculate_overall_confidence(
        self, clarity: float, density: float, coherence: float, completeness: float
    ) -> float:
        """Calculate weighted overall confidence score."""
        weights = {"clarity": 0.3, "density": 0.2, "coherence": 0.2, "completeness": 0.3}
        overall = (
            clarity * weights["clarity"]
            + density * weights["density"]
            + coherence * weights["coherence"]
            + completeness * weights["completeness"]
        )
        return max(0.0, min(1.0, overall))

    def _evaluate_exit_conditions(
        self, confidence: float, stage: str, partial_analysis: dict
    ) -> tuple[bool, str | None]:
        """Evaluate whether early exit conditions are met."""
        threshold = self._get_confidence_threshold(stage)
        if confidence >= threshold:
            return (True, f"High confidence ({confidence:.2f}) exceeds threshold ({threshold:.2f})")
        if stage == "transcription":
            word_count = len(partial_analysis.get("transcript", "").split())
            if word_count < 50 and confidence > 0.6:
                return (True, "Short content with adequate confidence")
        elif stage == "analysis":
            if confidence > 0.7 and partial_analysis.get("topics") and partial_analysis.get("summary"):
                return (True, "Sufficient analysis components with good confidence")
        if confidence < 0.3 and stage in ["analysis", "intermediate"]:
            return (True, "Low-value content detected - early termination recommended")
        return (False, None)

    def _get_confidence_threshold(self, stage: str) -> float:
        """Get confidence threshold for different processing stages."""
        thresholds = {
            "transcription": 0.8,
            "initial": 0.75,
            "analysis": 0.7,
            "intermediate": 0.65,
            "final": 0.6,
            "complete": 0.5,
        }
        return thresholds.get(stage, 0.7)

    def _should_exit_early(self, metrics: ConfidenceMetrics, stage: str) -> bool:
        """Determine if early exit should be triggered."""
        return metrics.should_exit_early

    def _generate_exit_recommendations(self, metrics: ConfidenceMetrics) -> list[str]:
        """Generate recommendations based on confidence assessment."""
        recommendations = []
        if metrics.should_exit_early:
            recommendations.append(f"Early exit recommended: {metrics.exit_reason}")
            if metrics.overall_confidence > 0.8:
                recommendations.append("High confidence - minimal additional processing needed")
            elif metrics.overall_confidence < 0.4:
                recommendations.append("Low confidence - content may not warrant full analysis")
        else:
            recommendations.append("Continue processing - confidence below threshold")
            if metrics.content_clarity < 0.5:
                recommendations.append("Consider additional clarity analysis")
            if metrics.information_density < 0.4:
                recommendations.append("Content appears low-density - consider lighter processing")
            if metrics.topic_coherence < 0.5:
                recommendations.append("Topic coherence is low - may need focused analysis")
        return recommendations

    def _estimate_processing_savings(self, metrics: ConfidenceMetrics, stage: str) -> dict:
        """Estimate potential processing time and cost savings from early exit."""
        if not metrics.should_exit_early:
            return {"time_saved_percent": 0, "cost_saved_percent": 0, "estimated_speedup": 1.0}
        stage_savings = {
            "transcription": {"time": 15, "cost": 10},
            "initial": {"time": 25, "cost": 20},
            "analysis": {"time": 40, "cost": 35},
            "intermediate": {"time": 60, "cost": 50},
            "final": {"time": 15, "cost": 10},
        }
        savings = stage_savings.get(stage, {"time": 30, "cost": 25})
        confidence_multiplier = min(metrics.overall_confidence * 1.2, 1.0)
        time_saved = int(savings["time"] * confidence_multiplier)
        cost_saved = int(savings["cost"] * confidence_multiplier)
        speedup = 1.0 / (1.0 - time_saved / 100)
        return {
            "time_saved_percent": time_saved,
            "cost_saved_percent": cost_saved,
            "estimated_speedup": round(speedup, 2),
        }
