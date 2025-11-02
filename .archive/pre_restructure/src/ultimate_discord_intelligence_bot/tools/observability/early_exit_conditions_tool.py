"""Early Exit Conditions Tool for Week 4 Optimization.

This module implements confidence-based early exit conditions to terminate
processing when sufficient information has been gathered, avoiding unnecessary
computational overhead.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ultimate_discord_intelligence_bot.step_result import StepResult
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

            # Calculate confidence metrics
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

        # Content clarity assessment
        content_clarity = self._assess_content_clarity(transcript, title)

        # Information density assessment
        information_density = self._assess_information_density(transcript)

        # Topic coherence assessment
        topic_coherence = self._assess_topic_coherence(transcript, partial_analysis)

        # Completeness assessment based on stage
        completeness_score = self._assess_completeness(transcript, partial_analysis, processing_stage)

        # Overall confidence calculation
        overall_confidence = self._calculate_overall_confidence(
            content_clarity, information_density, topic_coherence, completeness_score
        )

        # Early exit decision
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

        # Combine title and transcript for analysis
        combined_text = f"{title} {transcript}".lower()
        words = combined_text.split()

        if len(words) < 10:
            return 0.2  # Very short content is unclear

        # Clarity indicators
        clarity_score = 0.5  # Base score

        # Positive clarity indicators
        clear_indicators = [
            r"\b(explain|definition|example|specifically|clearly|obviously)\b",
            r"\b(first|second|third|next|then|finally|in conclusion)\b",
            r"\b(because|therefore|however|although|for instance)\b",
        ]

        for pattern in clear_indicators:
            matches = len(re.findall(pattern, combined_text))
            clarity_score += min(matches * 0.1, 0.2)  # Cap each pattern contribution

        # Negative clarity indicators
        unclear_indicators = [
            r"\b(um|uh|like|you know|I guess|maybe|sort of)\b",
            r"\b(confusing|unclear|I don\'t know|not sure)\b",
        ]

        for pattern in unclear_indicators:
            matches = len(re.findall(pattern, combined_text))
            clarity_score -= min(matches * 0.05, 0.1)  # Deduct for unclear speech

        # Sentence structure assessment
        sentences = re.split(r"[.!?]+", transcript)
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if 5 <= avg_sentence_length <= 25:  # Optimal sentence length
                clarity_score += 0.1
            elif avg_sentence_length > 40:  # Very long sentences reduce clarity
                clarity_score -= 0.1

        return max(0.0, min(1.0, clarity_score))

    def _assess_information_density(self, transcript: str) -> float:
        """Assess the density of meaningful information in the transcript."""

        words = transcript.lower().split()
        if len(words) < 10:
            return 0.1

        # Information-rich word patterns
        info_patterns = [
            r"\b(data|research|study|analysis|evidence|statistics)\b",
            r"\b(important|significant|crucial|key|essential|critical)\b",
            r"\b(process|method|technique|approach|strategy|solution)\b",
            r"\b(result|conclusion|finding|discovery|insight|outcome)\b",
        ]

        info_word_count = 0
        for pattern in info_patterns:
            info_word_count += len(re.findall(pattern, transcript.lower()))

        # Calculate density ratio
        density_ratio = info_word_count / len(words)

        # Convert to 0-1 score with reasonable scaling
        density_score = min(density_ratio * 50, 1.0)  # Scale factor 50

        # Bonus for technical terms
        tech_patterns = [
            r"\b(algorithm|system|framework|architecture|implementation)\b",
            r"\b(optimize|efficient|performance|scalable|robust)\b",
        ]

        tech_count = 0
        for pattern in tech_patterns:
            tech_count += len(re.findall(pattern, transcript.lower()))

        if tech_count > 0:
            density_score += min(tech_count * 0.05, 0.2)

        return max(0.0, min(1.0, density_score))

    def _assess_topic_coherence(self, transcript: str, partial_analysis: dict) -> float:
        """Assess how coherent and focused the topic discussion is."""

        # Base coherence from partial analysis if available
        coherence_score = 0.5

        # Check if we have topic information from partial analysis
        topics = partial_analysis.get("topics", [])
        if topics:
            # More focused topics indicate higher coherence
            if len(topics) <= 3:
                coherence_score += 0.2
            elif len(topics) <= 5:
                coherence_score += 0.1
            else:
                coherence_score -= 0.1  # Too many topics may indicate lack of focus

        # Analyze transcript for topic consistency
        words = transcript.lower().split()
        if len(words) < 50:
            return max(coherence_score - 0.2, 0.1)  # Short transcripts are hard to assess

        # Look for topic transition indicators
        transition_patterns = [
            r"\b(also|additionally|furthermore|moreover|in addition)\b",
            r"\b(however|but|although|on the other hand|nevertheless)\b",
            r"\b(moving on|next topic|speaking of|regarding|concerning)\b",
        ]

        transition_count = 0
        for pattern in transition_patterns:
            transition_count += len(re.findall(pattern, transcript.lower()))

        # Moderate transitions are good, too many may indicate scattered focus
        if 1 <= transition_count <= 5:
            coherence_score += 0.1
        elif transition_count > 10:
            coherence_score -= 0.15

        # Check for repetitive patterns (may indicate strong focus)
        repetition_score = self._assess_topic_repetition(transcript)
        coherence_score += repetition_score * 0.1

        return max(0.0, min(1.0, coherence_score))

    def _assess_topic_repetition(self, transcript: str) -> float:
        """Assess repetition of key terms indicating focused discussion."""

        words = transcript.lower().split()
        word_counts = {}

        # Count significant words (exclude common words)
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
            clean_word = re.sub(r"[^\w]", "", word)
            if len(clean_word) > 3 and clean_word not in common_words:
                word_counts[clean_word] = word_counts.get(clean_word, 0) + 1

        if not word_counts:
            return 0.0

        # Find words that appear multiple times
        repeated_words = {word: count for word, count in word_counts.items() if count > 1}

        if not repeated_words:
            return 0.0

        # Calculate repetition score based on frequency distribution
        total_significant_words = sum(word_counts.values())
        repetition_weight = sum(count - 1 for count in repeated_words.values())

        return min(repetition_weight / total_significant_words, 1.0)

    def _assess_completeness(self, transcript: str, partial_analysis: dict, stage: str) -> float:
        """Assess completeness of information based on processing stage."""

        completeness_score = 0.5  # Base score

        # Stage-specific completeness assessment
        if stage in ["transcription", "initial"]:
            # Early stage - assess transcript completeness
            word_count = len(transcript.split())
            if word_count > 100:
                completeness_score += 0.2
            if word_count > 500:
                completeness_score += 0.2

        elif stage in ["analysis", "intermediate"]:
            # Mid stage - assess analysis completeness
            if partial_analysis.get("summary"):
                completeness_score += 0.2
            if partial_analysis.get("topics"):
                completeness_score += 0.2
            if partial_analysis.get("sentiment"):
                completeness_score += 0.1

        elif stage in ["final", "complete"]:
            # Late stage - comprehensive assessment
            required_components = ["summary", "topics", "sentiment", "key_points"]
            available_components = sum(1 for comp in required_components if partial_analysis.get(comp))
            completeness_score += (available_components / len(required_components)) * 0.4

        # Check for completion indicators in transcript
        completion_patterns = [
            r"\b(in conclusion|to summarize|in summary|finally|lastly)\b",
            r"\b(that\'s all|that\'s it|end of|wrapping up|to conclude)\b",
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

        # Weighted average with emphasis on clarity and completeness
        weights = {
            "clarity": 0.3,
            "density": 0.2,
            "coherence": 0.2,
            "completeness": 0.3,
        }

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

        # Get confidence threshold for current stage
        threshold = self._get_confidence_threshold(stage)

        # Basic confidence check
        if confidence >= threshold:
            return (
                True,
                f"High confidence ({confidence:.2f}) exceeds threshold ({threshold:.2f})",
            )

        # Stage-specific early exit conditions
        if stage == "transcription":
            # Very short or very clear content might not need full analysis
            word_count = len(partial_analysis.get("transcript", "").split())
            if word_count < 50 and confidence > 0.6:
                return True, "Short content with adequate confidence"

        elif stage == "analysis":
            # If we have strong indicators of content type and quality
            if confidence > 0.7 and partial_analysis.get("topics") and partial_analysis.get("summary"):
                return True, "Sufficient analysis components with good confidence"

        # Low-value content detection
        if confidence < 0.3 and stage in ["analysis", "intermediate"]:
            return True, "Low-value content detected - early termination recommended"

        return False, None

    def _get_confidence_threshold(self, stage: str) -> float:
        """Get confidence threshold for different processing stages."""

        thresholds = {
            "transcription": 0.8,  # High threshold for transcription
            "initial": 0.75,  # High threshold for initial processing
            "analysis": 0.7,  # Medium-high threshold for analysis
            "intermediate": 0.65,  # Medium threshold for intermediate
            "final": 0.6,  # Lower threshold for final stages
            "complete": 0.5,  # Lowest threshold when nearly complete
        }

        return thresholds.get(stage, 0.7)  # Default threshold

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
            return {
                "time_saved_percent": 0,
                "cost_saved_percent": 0,
                "estimated_speedup": 1.0,
            }

        # Stage-specific savings estimates
        stage_savings = {
            "transcription": {"time": 15, "cost": 10},  # Early transcription exit
            "initial": {"time": 25, "cost": 20},  # Skip heavy analysis
            "analysis": {"time": 40, "cost": 35},  # Skip advanced processing
            "intermediate": {"time": 60, "cost": 50},  # Skip final stages
            "final": {"time": 15, "cost": 10},  # Minimal savings at final
        }

        savings = stage_savings.get(stage, {"time": 30, "cost": 25})

        # Adjust based on confidence level
        confidence_multiplier = min(metrics.overall_confidence * 1.2, 1.0)

        time_saved = int(savings["time"] * confidence_multiplier)
        cost_saved = int(savings["cost"] * confidence_multiplier)
        speedup = 1.0 / (1.0 - time_saved / 100)

        return {
            "time_saved_percent": time_saved,
            "cost_saved_percent": cost_saved,
            "estimated_speedup": round(speedup, 2),
        }
