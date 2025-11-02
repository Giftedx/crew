"""
DEPRECATED: This file is deprecated and will be removed in a future version.
Please use ultimate_discord_intelligence_bot.crew_core instead.

Migration guide:
- Import from crew_core instead of this module
- Use UnifiedCrewExecutor for crew execution
- Use CrewErrorHandler for error handling
- Use CrewInsightGenerator for insight generation

Example:
    from ultimate_discord_intelligence_bot.crew_core import (
        UnifiedCrewExecutor,
        CrewConfig,
        CrewTask,
    )
"""

import warnings


warnings.warn(
    "This module is deprecated. Use ultimate_discord_intelligence_bot.crew_core instead.",
    DeprecationWarning,
    stacklevel=2,
)


"""Helper methods for extracting insights from CrewAI agent execution results.

These methods parse and structure outputs from various specialized agents to provide
consistent, structured data for downstream processing and synthesis.
"""

import re  # noqa: E402
from typing import Any  # noqa: E402


class CrewInsightExtractor:
    """Extract structured insights from CrewAI agent execution results."""

    @staticmethod
    def _extract_pattern_insights(crew_result: Any) -> dict[str, Any]:
        """Extract pattern recognition insights from crew result."""
        result_text = str(crew_result).lower()

        patterns: dict[str, list[str]] = {
            "linguistic_patterns": [],
            "behavioral_patterns": [],
            "recurring_themes": [],
            "anomaly_indicators": [],
        }

        # Extract linguistic patterns
        if "linguistic" in result_text or "language" in result_text:
            patterns["linguistic_patterns"].extend(
                [
                    "repetitive_phrasing" if "repeat" in result_text else "",
                    "emotional_language" if "emotion" in result_text else "",
                    "formal_language" if "formal" in result_text else "",
                    "persuasive_language" if "persuasive" in result_text else "",
                ]
            )

        # Extract behavioral patterns
        if "behavior" in result_text or "pattern" in result_text:
            patterns["behavioral_patterns"].extend(
                [
                    "consistency_indicators" if "consistent" in result_text else "",
                    "deception_signals" if "deception" in result_text else "",
                    "authority_claims" if "authority" in result_text else "",
                    "social_proof" if "social" in result_text else "",
                ]
            )

        # Clean empty values
        patterns = {k: [x for x in v if x] for k, v in patterns.items()}

        return patterns

    @staticmethod
    def _extract_behavioral_correlations(crew_result: Any) -> dict[str, Any]:
        """Extract behavioral correlations from crew result."""
        result_text = str(crew_result).lower()

        correlations = {
            "language_behavior_correlation": 0.7,  # Default moderate correlation
            "sentiment_action_correlation": 0.6,
            "consistency_reliability_correlation": 0.8,
        }

        # Adjust based on detected patterns
        if "strong correlation" in result_text:
            correlations = {k: min(1.0, v + 0.2) for k, v in correlations.items()}
        elif "weak correlation" in result_text:
            correlations = {k: max(0.0, v - 0.2) for k, v in correlations.items()}

        return correlations

    @staticmethod
    def _extract_anomaly_indicators(crew_result: Any) -> list[dict[str, Any]]:
        """Extract anomaly indicators from crew result."""
        result_text = str(crew_result).lower()

        indicators = []

        if "anomaly" in result_text or "unusual" in result_text:
            indicators.append(
                {
                    "type": "behavioral_anomaly",
                    "severity": "medium",
                    "confidence": 0.7,
                    "description": "Unusual behavioral patterns detected",
                }
            )

        if "inconsistent" in result_text:
            indicators.append(
                {
                    "type": "consistency_anomaly",
                    "severity": "high",
                    "confidence": 0.8,
                    "description": "Inconsistent patterns detected",
                }
            )

        return indicators

    @staticmethod
    def _extract_predictive_signals(crew_result: Any) -> list[dict[str, Any]]:
        """Extract predictive signals from crew result."""
        result_text = str(crew_result).lower()

        signals = []

        if "future" in result_text or "predict" in result_text:
            signals.append(
                {
                    "signal_type": "trend_indicator",
                    "probability": 0.6,
                    "timeframe": "short_term",
                    "description": "Predictive trend indicators identified",
                }
            )

        if "escalation" in result_text or "increase" in result_text:
            signals.append(
                {
                    "signal_type": "escalation_risk",
                    "probability": 0.7,
                    "timeframe": "medium_term",
                    "description": "Risk escalation patterns detected",
                }
            )

        return signals

    @staticmethod
    def _extract_network_intelligence(crew_result: Any) -> dict[str, Any]:
        """Extract network intelligence from crew result."""
        result_text = str(crew_result).lower()

        network_data = {
            "node_count": 0,
            "connection_strength": {},
            "cluster_analysis": {},
            "information_flow": {},
        }

        # Extract numeric indicators where possible
        numbers = re.findall(r"\d+", result_text)
        if numbers:
            network_data["node_count"] = int(numbers[0]) if numbers else 5

        if "strong connection" in result_text:
            network_data["connection_strength"] = {"average": 0.8}
        elif "weak connection" in result_text:
            network_data["connection_strength"] = {"average": 0.3}
        else:
            network_data["connection_strength"] = {"average": 0.5}

        return network_data

    @staticmethod
    def _extract_relationship_mappings(crew_result: Any) -> dict[str, list[str]]:
        """Extract relationship mappings from crew result."""
        result_text = str(crew_result).lower()

        mappings: dict[str, list[str]] = {
            "entity_relationships": [],
            "source_relationships": [],
            "topic_relationships": [],
            "temporal_relationships": [],
        }

        # Simple pattern matching for common relationship indicators
        if "related" in result_text or "connect" in result_text:
            mappings["entity_relationships"] = ["primary_entity", "secondary_entity"]

        if "source" in result_text:
            mappings["source_relationships"] = [
                "primary_source",
                "corroborating_source",
            ]

        return mappings

    @staticmethod
    def _extract_source_clusters(crew_result: Any) -> list[dict[str, Any]]:
        """Extract source clusters from crew result."""
        result_text = str(crew_result).lower()

        clusters = []

        if "cluster" in result_text or "group" in result_text:
            clusters.append(
                {
                    "cluster_id": "primary_cluster",
                    "reliability_score": 0.8,
                    "source_count": 3,
                    "coherence_level": "high",
                }
            )

        return clusters

    @staticmethod
    def _extract_corroboration_matrix(crew_result: Any) -> dict[str, Any]:
        """Extract fact corroboration matrix from crew result."""
        result_text = str(crew_result).lower()

        matrix = {
            "corroboration_score": 0.7,
            "supporting_sources": 2,
            "contradicting_sources": 0,
            "neutral_sources": 1,
        }

        if "strong support" in result_text:
            matrix["corroboration_score"] = 0.9
            matrix["supporting_sources"] = 4
        elif "weak support" in result_text:
            matrix["corroboration_score"] = 0.4
            matrix["contradicting_sources"] = 1

        return matrix

    @staticmethod
    def _extract_contradiction_analysis(crew_result: Any) -> dict[str, Any]:
        """Extract contradiction analysis from crew result."""
        result_text = str(crew_result).lower()

        analysis = {
            "contradiction_detected": False,
            "contradiction_severity": "none",
            "contradiction_count": 0,
            "resolution_strategy": "none_needed",
        }

        if "contradict" in result_text or "conflict" in result_text:
            analysis["contradiction_detected"] = True
            analysis["contradiction_severity"] = "medium"
            analysis["contradiction_count"] = 1
            analysis["resolution_strategy"] = "further_investigation"

        return analysis

    @staticmethod
    def _extract_predictive_insights(crew_result: Any) -> dict[str, Any]:
        """Extract predictive insights from crew result."""
        result_text = str(crew_result).lower()

        insights = {
            "prediction_confidence": 0.6,
            "prediction_timeframe": "medium_term",
            "key_indicators": [],
            "uncertainty_factors": [],
        }

        if "high confidence" in result_text:
            insights["prediction_confidence"] = 0.9
        elif "low confidence" in result_text:
            insights["prediction_confidence"] = 0.3

        if "immediate" in result_text:
            insights["prediction_timeframe"] = "immediate"
        elif "long term" in result_text:
            insights["prediction_timeframe"] = "long_term"

        return insights

    @staticmethod
    def _extract_risk_trajectories(crew_result: Any) -> list[dict[str, Any]]:
        """Extract risk trajectories from crew result."""
        result_text = str(crew_result).lower()

        trajectories = []

        if "increasing risk" in result_text or "escalating" in result_text:
            trajectories.append(
                {
                    "trajectory_type": "escalating",
                    "current_level": "medium",
                    "projected_level": "high",
                    "timeline": "short_term",
                }
            )
        elif "decreasing risk" in result_text:
            trajectories.append(
                {
                    "trajectory_type": "declining",
                    "current_level": "medium",
                    "projected_level": "low",
                    "timeline": "medium_term",
                }
            )

        return trajectories

    @staticmethod
    def _extract_escalation_probabilities(crew_result: Any) -> dict[str, float]:
        """Extract escalation probabilities from crew result."""
        result_text = str(crew_result).lower()

        probabilities = {
            "immediate_escalation": 0.2,
            "short_term_escalation": 0.4,
            "medium_term_escalation": 0.6,
            "long_term_escalation": 0.3,
        }

        if "high probability" in result_text:
            probabilities = {k: min(1.0, v + 0.3) for k, v in probabilities.items()}
        elif "low probability" in result_text:
            probabilities = {k: max(0.0, v - 0.3) for k, v in probabilities.items()}

        return probabilities

    @staticmethod
    def _extract_early_warnings(crew_result: Any) -> list[dict[str, Any]]:
        """Extract early warning indicators from crew result."""
        result_text = str(crew_result).lower()

        warnings = []

        if "warning" in result_text or "alert" in result_text:
            warnings.append(
                {
                    "warning_type": "behavioral_change",
                    "severity": "medium",
                    "confidence": 0.7,
                    "monitoring_recommended": True,
                }
            )

        if "urgent" in result_text:
            warnings.append(
                {
                    "warning_type": "immediate_attention",
                    "severity": "high",
                    "confidence": 0.9,
                    "monitoring_recommended": True,
                }
            )

        return warnings

    @staticmethod
    def _extract_mitigation_strategies(crew_result: Any) -> list[dict[str, Any]]:
        """Extract mitigation strategies from crew result."""
        result_text = str(crew_result).lower()

        strategies = []

        if "monitor" in result_text:
            strategies.append(
                {
                    "strategy_type": "enhanced_monitoring",
                    "priority": "high",
                    "implementation_complexity": "low",
                    "expected_effectiveness": 0.7,
                }
            )

        if "intervention" in result_text:
            strategies.append(
                {
                    "strategy_type": "direct_intervention",
                    "priority": "medium",
                    "implementation_complexity": "medium",
                    "expected_effectiveness": 0.8,
                }
            )

        return strategies
