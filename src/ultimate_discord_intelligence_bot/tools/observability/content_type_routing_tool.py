"""Content Type Routing Tool for Week 4 Optimization.

This module implements content classification and routing to enable specialized
processing pipelines for different content types (educational, entertainment, news, etc).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


@dataclass
class ContentClassification:
    """Container for content type classification results."""

    primary_type: str
    confidence: float
    secondary_types: list[str]
    routing_decision: str
    processing_flags: dict[str, bool]


class ContentTypeRoutingTool(BaseTool[dict]):
    """Classifies content and determines optimal processing pipeline."""

    name: str = "content_type_routing_tool"
    description: str = "Analyzes content to determine type and route to appropriate processing pipeline"

    def run(self, input_data: dict) -> StepResult:
        """Run content type classification and routing.

        Args:
            input_data: Dict containing transcript and metadata

        Returns:
            StepResult with classification and routing recommendations
        """
        try:
            transcript = input_data.get("transcript", "")
            title = input_data.get("title", "")
            description = input_data.get("description", "")
            metadata = input_data.get("metadata", {})

            if not transcript:
                return StepResult.fail(error="No transcript provided for content classification")

            # Perform content classification
            classification = self._classify_content(transcript, title, description, metadata)

            # Determine routing decision
            routing_config = self._determine_routing(classification)

            result = {
                "classification": {
                    "primary_type": classification.primary_type,
                    "confidence": classification.confidence,
                    "secondary_types": classification.secondary_types,
                },
                "routing": {
                    "pipeline": classification.routing_decision,
                    "processing_flags": classification.processing_flags,
                    "estimated_speedup": routing_config.get("estimated_speedup", 1.0),
                },
                "recommendations": self._generate_recommendations(classification),
            }

            return StepResult.ok(result=result)

        except Exception as e:
            return StepResult.fail(error=f"Content type routing failed: {e!s}")

    def _classify_content(self, transcript: str, title: str, description: str, metadata: dict) -> ContentClassification:
        """Classify content based on multiple signals."""

        # Content type indicators
        educational_indicators = [
            r"\b(learn|tutorial|explain|how\s+to|lesson|course|teach|study)\b",
            r"\b(university|school|professor|student|lecture|class)\b",
            r"\b(definition|theory|concept|principle|method|technique)\b",
        ]

        entertainment_indicators = [
            r"\b(funny|comedy|humor|joke|laugh|entertainment|fun)\b",
            r"\b(movie|film|show|series|episode|actor|actress)\b",
            r"\b(game|gaming|play|player|level|score)\b",
        ]

        news_indicators = [
            r"\b(news|report|breaking|update|journalist|reporter)\b",
            r"\b(politics|government|election|vote|policy|law)\b",
            r"\b(economy|market|business|company|industry)\b",
        ]

        tech_indicators = [
            r"\b(technology|software|programming|code|developer|engineer)\b",
            r"\b(computer|internet|digital|cyber|online|web)\b",
            r"\b(AI|artificial\s+intelligence|machine\s+learning|data)\b",
        ]

        discussion_indicators = [
            r"\b(debate|discuss|opinion|argument|perspective|viewpoint)\b",
            r"\b(interview|conversation|talk|dialogue|panel)\b",
            r"\b(think|believe|feel|agree|disagree)\b",
        ]

        # Combine all text for analysis
        combined_text = f"{title} {description} {transcript[:2000]}".lower()

        # Score each category
        scores = {}

        # Educational content
        edu_score = sum(len(re.findall(pattern, combined_text)) for pattern in educational_indicators)
        scores["educational"] = edu_score / len(combined_text.split()) * 1000

        # Entertainment content
        ent_score = sum(len(re.findall(pattern, combined_text)) for pattern in entertainment_indicators)
        scores["entertainment"] = ent_score / len(combined_text.split()) * 1000

        # News content
        news_score = sum(len(re.findall(pattern, combined_text)) for pattern in news_indicators)
        scores["news"] = news_score / len(combined_text.split()) * 1000

        # Tech content
        tech_score = sum(len(re.findall(pattern, combined_text)) for pattern in tech_indicators)
        scores["technology"] = tech_score / len(combined_text.split()) * 1000

        # Discussion content
        disc_score = sum(len(re.findall(pattern, combined_text)) for pattern in discussion_indicators)
        scores["discussion"] = disc_score / len(combined_text.split()) * 1000

        # Determine primary type
        primary_type = max(scores.keys(), key=lambda k: scores[k])
        confidence = min(scores[primary_type] / 10, 1.0)  # Cap at 1.0

        # If confidence is very low, classify as general
        if confidence < 0.1:
            primary_type = "general"
            confidence = 0.5

        # Get secondary types (scores > 0.5 but not primary)
        secondary_types = [
            content_type for content_type, score in scores.items() if score > 0.5 and content_type != primary_type
        ]

        # Determine routing decision based on classification
        routing_decision = self._map_type_to_pipeline(primary_type)
        processing_flags = self._get_processing_flags(primary_type, secondary_types)

        return ContentClassification(
            primary_type=primary_type,
            confidence=confidence,
            secondary_types=secondary_types,
            routing_decision=routing_decision,
            processing_flags=processing_flags,
        )

    def _map_type_to_pipeline(self, content_type: str) -> str:
        """Map content type to processing pipeline."""
        pipeline_mapping = {
            "educational": "deep_analysis",  # Full analysis for learning content
            "technology": "deep_analysis",  # Full analysis for tech content
            "news": "fast_summary",  # Quick summary for news
            "entertainment": "light_analysis",  # Light analysis for entertainment
            "discussion": "deep_analysis",  # Full analysis for discussions
            "general": "standard_pipeline",  # Standard processing
        }
        return pipeline_mapping.get(content_type, "standard_pipeline")

    def _get_processing_flags(self, primary_type: str, secondary_types: list[str]) -> dict[str, bool]:
        """Determine processing flags based on content classification."""
        flags = {
            "enable_deep_analysis": False,
            "enable_fallacy_detection": False,
            "enable_sentiment_analysis": False,
            "enable_topic_extraction": False,
            "skip_perspective_api": False,
            "use_fast_transcription": False,
        }

        # Set flags based on primary type
        if primary_type in ["educational", "technology", "discussion"]:
            flags["enable_deep_analysis"] = True
            flags["enable_fallacy_detection"] = True
            flags["enable_topic_extraction"] = True
        elif primary_type == "entertainment":
            flags["enable_sentiment_analysis"] = True
            flags["skip_perspective_api"] = True
            flags["use_fast_transcription"] = True
        elif primary_type == "news":
            flags["enable_sentiment_analysis"] = True
            flags["enable_topic_extraction"] = True
            flags["use_fast_transcription"] = True

        # Adjust based on secondary types
        if "discussion" in secondary_types:
            flags["enable_fallacy_detection"] = True
        if "entertainment" in secondary_types:
            flags["enable_sentiment_analysis"] = True

        return flags

    def _determine_routing(self, classification: ContentClassification) -> dict:
        """Determine routing configuration and performance estimates."""
        routing_config = {
            "pipeline": classification.routing_decision,
            "estimated_speedup": 1.0,
        }

        # Estimate speedup based on pipeline choice
        speedup_estimates = {
            "fast_summary": 2.5,  # 60% faster
            "light_analysis": 1.8,  # 44% faster
            "standard_pipeline": 1.0,  # No change
            "deep_analysis": 0.9,  # 10% slower but more thorough
        }

        routing_config["estimated_speedup"] = speedup_estimates.get(classification.routing_decision, 1.0)

        return routing_config

    def _generate_recommendations(self, classification: ContentClassification) -> list[str]:
        """Generate processing recommendations based on classification."""
        recommendations = []

        if classification.confidence < 0.3:
            recommendations.append("Low confidence classification - consider manual review")

        if classification.primary_type == "educational":
            recommendations.append("Enable comprehensive analysis for educational content")
        elif classification.primary_type == "entertainment":
            recommendations.append("Use lighter processing to optimize for speed")
        elif classification.primary_type == "news":
            recommendations.append("Focus on quick summarization and fact extraction")

        if "discussion" in classification.secondary_types:
            recommendations.append("Enable fallacy detection for discussion content")

        return recommendations
