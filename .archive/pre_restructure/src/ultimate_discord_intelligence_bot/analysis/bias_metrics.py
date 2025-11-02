"""Bias metrics system with comprehensive scoring.

This module implements multi-dimensional bias measurement including
political leaning, partisan intensity, viewpoint diversity, evidence balance,
framing neutrality, source diversity, and temporal consistency.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


@dataclass
class BiasMetrics:
    """Comprehensive bias metrics for content analysis."""

    political_leaning: float = 0.0  # -1.0 (left) to +1.0 (right)
    partisan_intensity: float = 0.0  # 0.0 (balanced) to 1.0 (extreme)
    viewpoint_diversity: float = 0.0  # 0.0 (single view) to 1.0 (multiple)
    evidence_balance: float = 0.0  # 0.0 (one-sided) to 1.0 (balanced)
    framing_neutrality: float = 0.0  # 0.0 (biased) to 1.0 (neutral)
    source_diversity: float = 0.0  # 0.0 (single source) to 1.0 (diverse)
    temporal_consistency: float = 0.0  # Track bias over time
    overall_bias_score: float = 0.0  # Composite bias score

    def __post_init__(self) -> None:
        """Calculate overall bias score after initialization."""
        self.overall_bias_score = self._calculate_overall_bias()

    def _calculate_overall_bias(self) -> float:
        """Calculate overall bias score from individual metrics."""
        # Weight different metrics based on importance
        weights = {
            "partisan_intensity": 0.25,
            "viewpoint_diversity": 0.20,
            "evidence_balance": 0.20,
            "framing_neutrality": 0.15,
            "source_diversity": 0.10,
            "temporal_consistency": 0.10,
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for metric, weight in weights.items():
            value = getattr(self, metric)
            weighted_sum += value * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight


class BiasAnalyzer:
    """Analyzer for comprehensive bias measurement.

    This class implements multiple approaches to bias detection:
    1. Lexical analysis (partisan vocabulary)
    2. Source diversity analysis
    3. Claim balance assessment
    4. Perspective representation
    5. Emotional language detection
    6. Evidence selectivity scoring
    """

    def __init__(self) -> None:
        """Initialize the bias analyzer."""
        self.logger = logging.getLogger(__name__)
        self._initialize_analysis_patterns()

    def _initialize_analysis_patterns(self) -> None:
        """Initialize patterns for bias analysis."""
        # Political leaning indicators
        self.left_indicators = [
            "progressive",
            "liberal",
            "leftist",
            "socialist",
            "democrat",
            "woke",
            "social justice",
            "equity",
            "inclusion",
            "diversity",
            "climate change",
            "environmental",
            "sustainable",
            "renewable",
            "universal healthcare",
            "public education",
            "social safety net",
        ]

        self.right_indicators = [
            "conservative",
            "republican",
            "right-wing",
            "traditional",
            "patriot",
            "freedom",
            "liberty",
            "individual",
            "merit",
            "hard work",
            "free market",
            "capitalism",
            "entrepreneurship",
            "self-reliance",
            "law and order",
            "national security",
            "family values",
        ]

        # Partisan intensity indicators
        self.extreme_indicators = [
            "radical",
            "extreme",
            "fanatic",
            "zealot",
            "militant",
            "revolutionary",
            "counter-revolutionary",
            "subversive",
            "treasonous",
            "unpatriotic",
            "anti-American",
        ]

        # Emotional language indicators
        self.emotional_indicators = [
            "outrage",
            "shocking",
            "devastating",
            "terrifying",
            "appalling",
            "inspiring",
            "heartbreaking",
            "unbelievable",
            "incredible",
            "disgusting",
            "revolting",
            "nauseating",
            "sickening",
        ]

        # Source diversity indicators
        self.source_indicators = [
            "according to",
            "studies show",
            "research indicates",
            "experts say",
            "data suggests",
            "findings show",
            "reports indicate",
            "analysis reveals",
            "investigation shows",
        ]

    def analyze_bias(self, content: str, context: dict[str, Any] | None = None) -> StepResult:
        """Analyze bias in content using comprehensive metrics.

        Args:
            content: The content to analyze
            context: Optional context information

        Returns:
            StepResult with bias metrics
        """
        try:
            content_lower = content.lower()

            # Analyze political leaning
            political_leaning = self._analyze_political_leaning(content_lower)

            # Analyze partisan intensity
            partisan_intensity = self._analyze_partisan_intensity(content_lower)

            # Analyze viewpoint diversity
            viewpoint_diversity = self._analyze_viewpoint_diversity(content)

            # Analyze evidence balance
            evidence_balance = self._analyze_evidence_balance(content)

            # Analyze framing neutrality
            framing_neutrality = self._analyze_framing_neutrality(content_lower)

            # Analyze source diversity
            source_diversity = self._analyze_source_diversity(content)

            # Analyze temporal consistency
            temporal_consistency = self._analyze_temporal_consistency(content, context)

            metrics = BiasMetrics(
                political_leaning=political_leaning,
                partisan_intensity=partisan_intensity,
                viewpoint_diversity=viewpoint_diversity,
                evidence_balance=evidence_balance,
                framing_neutrality=framing_neutrality,
                source_diversity=source_diversity,
                temporal_consistency=temporal_consistency,
            )

            return StepResult.ok(data={"bias_metrics": metrics, "analysis_complete": True})

        except Exception as e:
            self.logger.error(f"Bias analysis failed: {e}")
            return StepResult.fail(f"Bias analysis failed: {e}")

    def _analyze_political_leaning(self, content: str) -> float:
        """Analyze political leaning of content."""
        left_count = sum(1 for indicator in self.left_indicators if indicator in content)
        right_count = sum(1 for indicator in self.right_indicators if indicator in content)

        total_indicators = left_count + right_count
        if total_indicators == 0:
            return 0.0  # Neutral

        # Calculate leaning (-1.0 for left, +1.0 for right)
        if left_count > right_count:
            return -(left_count - right_count) / total_indicators
        elif right_count > left_count:
            return (right_count - left_count) / total_indicators
        else:
            return 0.0  # Balanced

    def _analyze_partisan_intensity(self, content: str) -> float:
        """Analyze partisan intensity of content."""
        extreme_count = sum(1 for indicator in self.extreme_indicators if indicator in content)
        emotional_count = sum(1 for indicator in self.emotional_indicators if indicator in content)

        total_words = len(content.split())
        if total_words == 0:
            return 0.0

        # Calculate intensity based on extreme and emotional language
        intensity = (extreme_count + emotional_count) / total_words
        return min(intensity * 10, 1.0)  # Scale to 0-1

    def _analyze_viewpoint_diversity(self, content: str) -> float:
        """Analyze viewpoint diversity in content."""
        # Look for perspective indicators
        perspective_indicators = [
            "some believe",
            "others argue",
            "proponents say",
            "critics claim",
            "supporters argue",
            "opponents say",
            "advocates believe",
            "on one hand",
            "on the other hand",
            "different perspectives",
        ]

        perspective_count = sum(1 for indicator in perspective_indicators if indicator in content)

        # Look for balanced language
        balanced_indicators = [
            "both sides",
            "different views",
            "various opinions",
            "multiple perspectives",
            "diverse viewpoints",
        ]

        balanced_count = sum(1 for indicator in balanced_indicators if indicator in content)

        # Calculate diversity score
        total_sentences = len([s for s in content.split(".") if s.strip()])
        if total_sentences == 0:
            return 0.0

        diversity_ratio = (perspective_count + balanced_count) / total_sentences
        return min(diversity_ratio * 5, 1.0)  # Scale to 0-1

    def _analyze_evidence_balance(self, content: str) -> float:
        """Analyze evidence balance in content."""
        # Look for supporting evidence
        supporting_indicators = [
            "proves",
            "demonstrates",
            "shows",
            "confirms",
            "validates",
            "supports",
            "evidence",
            "data",
            "research",
            "studies",
        ]

        # Look for opposing evidence
        opposing_indicators = [
            "refutes",
            "contradicts",
            "disproves",
            "challenges",
            "questions",
            "undermines",
            "disputes",
            "rejects",
            "denies",
            "opposes",
        ]

        supporting_count = sum(1 for indicator in supporting_indicators if indicator in content)
        opposing_count = sum(1 for indicator in opposing_indicators if indicator in content)

        total_evidence = supporting_count + opposing_count
        if total_evidence == 0:
            return 1.0  # No evidence bias if no evidence

        # Calculate balance (closer to 0.5 is more balanced)
        balance_ratio = min(supporting_count, opposing_count) / max(supporting_count, opposing_count)
        return balance_ratio

    def _analyze_framing_neutrality(self, content: str) -> float:
        """Analyze framing neutrality of content."""
        # Look for loaded language
        loaded_indicators = [
            "radical",
            "extreme",
            "dangerous",
            "threat",
            "crisis",
            "heroic",
            "brave",
            "courageous",
            "noble",
            "righteous",
            "shocking",
            "devastating",
            "terrifying",
            "appalling",
        ]

        loaded_count = sum(1 for indicator in loaded_indicators if indicator in content)

        # Look for neutral language
        neutral_indicators = [
            "according to",
            "research shows",
            "data indicates",
            "studies suggest",
            "evidence points to",
            "findings reveal",
        ]

        neutral_count = sum(1 for indicator in neutral_indicators if indicator in content)

        total_words = len(content.split())
        if total_words == 0:
            return 1.0  # Neutral if no content

        # Calculate neutrality (higher neutral ratio = more neutral)
        loaded_ratio = loaded_count / total_words
        neutral_ratio = neutral_count / total_words

        # Neutrality score (1.0 = completely neutral, 0.0 = highly loaded)
        neutrality = max(0.0, 1.0 - (loaded_ratio * 10) + (neutral_ratio * 5))
        return min(neutrality, 1.0)

    def _analyze_source_diversity(self, content: str) -> float:
        """Analyze source diversity in content."""
        source_count = sum(1 for indicator in self.source_indicators if indicator in content)

        # Look for multiple source types
        source_types = [
            "study",
            "research",
            "survey",
            "poll",
            "report",
            "analysis",
            "investigation",
            "interview",
            "testimony",
        ]

        type_count = sum(1 for source_type in source_types if source_type in content)

        # Calculate diversity
        if source_count == 0:
            return 0.0  # No sources

        diversity = min(type_count / source_count, 1.0)
        return diversity

    def _analyze_temporal_consistency(self, content: str, context: dict[str, Any] | None = None) -> float:
        """Analyze temporal consistency of bias over time."""
        # This is a simplified implementation
        # In practice, this would require historical analysis

        if context and "historical_bias" in context:
            # Compare with historical bias scores
            current_bias = self._analyze_political_leaning(content.lower())
            historical_bias = context["historical_bias"]

            # Calculate consistency (1.0 = consistent, 0.0 = inconsistent)
            consistency = 1.0 - abs(current_bias - historical_bias)
            return max(0.0, consistency)

        # Default to neutral if no historical context
        return 0.5

    def compare_bias_metrics(self, metrics1: BiasMetrics, metrics2: BiasMetrics) -> StepResult:
        """Compare two sets of bias metrics.

        Args:
            metrics1: First set of bias metrics
            metrics2: Second set of bias metrics

        Returns:
            StepResult with comparison results
        """
        try:
            comparison = {
                "political_leaning_diff": abs(metrics1.political_leaning - metrics2.political_leaning),
                "partisan_intensity_diff": abs(metrics1.partisan_intensity - metrics2.partisan_intensity),
                "viewpoint_diversity_diff": abs(metrics1.viewpoint_diversity - metrics2.viewpoint_diversity),
                "evidence_balance_diff": abs(metrics1.evidence_balance - metrics2.evidence_balance),
                "framing_neutrality_diff": abs(metrics1.framing_neutrality - metrics2.framing_neutrality),
                "source_diversity_diff": abs(metrics1.source_diversity - metrics2.source_diversity),
                "temporal_consistency_diff": abs(metrics1.temporal_consistency - metrics2.temporal_consistency),
                "overall_bias_diff": abs(metrics1.overall_bias_score - metrics2.overall_bias_score),
            }

            # Calculate overall similarity
            similarity_scores = list(comparison.values())
            overall_similarity = 1.0 - (sum(similarity_scores) / len(similarity_scores))

            return StepResult.ok(
                data={"comparison": comparison, "overall_similarity": overall_similarity, "analysis_complete": True}
            )

        except Exception as e:
            self.logger.error(f"Bias metrics comparison failed: {e}")
            return StepResult.fail(f"Bias metrics comparison failed: {e}")

    def generate_bias_report(self, content: str, context: dict[str, Any] | None = None) -> StepResult:
        """Generate a comprehensive bias report.

        Args:
            content: The content to analyze
            context: Optional context information

        Returns:
            StepResult with detailed bias report
        """
        try:
            # Analyze bias metrics
            analysis_result = self.analyze_bias(content, context)
            if not analysis_result.success:
                return analysis_result

            metrics = analysis_result.data["bias_metrics"]

            # Generate report sections
            report = {
                "content_analysis": {
                    "political_leaning": self._interpret_political_leaning(metrics.political_leaning),
                    "partisan_intensity": self._interpret_partisan_intensity(metrics.partisan_intensity),
                    "viewpoint_diversity": self._interpret_viewpoint_diversity(metrics.viewpoint_diversity),
                    "evidence_balance": self._interpret_evidence_balance(metrics.evidence_balance),
                    "framing_neutrality": self._interpret_framing_neutrality(metrics.framing_neutrality),
                    "source_diversity": self._interpret_source_diversity(metrics.source_diversity),
                },
                "overall_assessment": {
                    "bias_level": self._assess_bias_level(metrics.overall_bias_score),
                    "recommendations": self._generate_recommendations(metrics),
                    "human_review_required": metrics.overall_bias_score > 0.7,
                },
                "metrics": metrics,
            }

            return StepResult.ok(data={"bias_report": report})

        except Exception as e:
            self.logger.error(f"Bias report generation failed: {e}")
            return StepResult.fail(f"Bias report generation failed: {e}")

    def _interpret_political_leaning(self, leaning: float) -> str:
        """Interpret political leaning score."""
        if leaning < -0.5:
            return "Strongly left-leaning"
        elif leaning < -0.2:
            return "Moderately left-leaning"
        elif leaning < 0.2:
            return "Politically neutral"
        elif leaning < 0.5:
            return "Moderately right-leaning"
        else:
            return "Strongly right-leaning"

    def _interpret_partisan_intensity(self, intensity: float) -> str:
        """Interpret partisan intensity score."""
        if intensity < 0.2:
            return "Low partisan intensity"
        elif intensity < 0.5:
            return "Moderate partisan intensity"
        elif intensity < 0.8:
            return "High partisan intensity"
        else:
            return "Extreme partisan intensity"

    def _interpret_viewpoint_diversity(self, diversity: float) -> str:
        """Interpret viewpoint diversity score."""
        if diversity < 0.2:
            return "Single viewpoint"
        elif diversity < 0.5:
            return "Limited diversity"
        elif diversity < 0.8:
            return "Moderate diversity"
        else:
            return "High diversity"

    def _interpret_evidence_balance(self, balance: float) -> str:
        """Interpret evidence balance score."""
        if balance < 0.3:
            return "Highly unbalanced"
        elif balance < 0.6:
            return "Moderately unbalanced"
        elif balance < 0.8:
            return "Reasonably balanced"
        else:
            return "Well balanced"

    def _interpret_framing_neutrality(self, neutrality: float) -> str:
        """Interpret framing neutrality score."""
        if neutrality < 0.3:
            return "Highly biased framing"
        elif neutrality < 0.6:
            return "Moderately biased framing"
        elif neutrality < 0.8:
            return "Reasonably neutral framing"
        else:
            return "Neutral framing"

    def _interpret_source_diversity(self, diversity: float) -> str:
        """Interpret source diversity score."""
        if diversity < 0.2:
            return "Single source"
        elif diversity < 0.5:
            return "Limited sources"
        elif diversity < 0.8:
            return "Moderate diversity"
        else:
            return "High diversity"

    def _assess_bias_level(self, bias_score: float) -> str:
        """Assess overall bias level."""
        if bias_score < 0.2:
            return "Low bias"
        elif bias_score < 0.4:
            return "Moderate bias"
        elif bias_score < 0.6:
            return "High bias"
        else:
            return "Extreme bias"

    def _generate_recommendations(self, metrics: BiasMetrics) -> list[str]:
        """Generate recommendations based on bias metrics."""
        recommendations = []

        if metrics.partisan_intensity > 0.7:
            recommendations.append("Consider reducing partisan language and emotional appeals")

        if metrics.viewpoint_diversity < 0.3:
            recommendations.append("Include more diverse perspectives and viewpoints")

        if metrics.evidence_balance < 0.4:
            recommendations.append("Present more balanced evidence from multiple sides")

        if metrics.framing_neutrality < 0.5:
            recommendations.append("Use more neutral language and avoid loaded terms")

        if metrics.source_diversity < 0.3:
            recommendations.append("Include sources from a wider range of perspectives")

        if not recommendations:
            recommendations.append("Content appears reasonably balanced")

        return recommendations
