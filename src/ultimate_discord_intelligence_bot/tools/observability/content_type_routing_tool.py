"""Content Type Routing Tool for Week 4 Optimization.

This module implements content classification and routing to enable specialized
processing pipelines for different content types (educational, entertainment, news, etc).

Supports both LLM-based classification (via Instructor) and pattern-matching fallback.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from platform.config.configuration import get_config
from platform.core.step_result import ErrorCategory, StepResult
from platform.observability.metrics import get_metrics

from ultimate_discord_intelligence_bot.tools._base import BaseTool


try:
    from platform.rl.response_models import ContentTypeClassification
    from platform.rl.structured_outputs import InstructorClientFactory

    INSTRUCTOR_AVAILABLE = True
except ImportError:
    INSTRUCTOR_AVAILABLE = False
logger = logging.getLogger(__name__)


@dataclass
class ContentClassification:
    """Container for content type classification results."""

    primary_type: str
    confidence: float
    secondary_types: list[str]
    routing_decision: str
    processing_flags: dict[str, bool]


class ContentTypeRoutingTool(BaseTool[dict]):
    """Classifies content and determines optimal processing pipeline.

    Supports two analysis methods:
    1. LLM-based classification (via Instructor) - when enabled and available
    2. Pattern-matching fallback - always available, used when LLM fails or disabled
    """

    name: str = "content_type_routing_tool"
    description: str = "Analyzes content to determine type and route to appropriate processing pipeline"

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()
        self._config = get_config()

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
                return StepResult.fail(
                    error="No transcript provided for content classification",
                    error_category=ErrorCategory.MISSING_REQUIRED_FIELD,
                )
            llm_result = self._try_llm_classification(transcript, title, description)
            if llm_result is not None:
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": self.name, "method": "llm_instructor", "outcome": "success"}
                ).inc()
                return llm_result
            classification = self._classify_content(transcript, title, description, metadata)
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
                "analysis_method": "pattern_matching",
            }
            self._metrics.counter(
                "tool_runs_total", labels={"tool": self.name, "method": "pattern_matching", "outcome": "success"}
            ).inc()
            return StepResult.ok(result=result)
        except Exception as e:
            self._metrics.counter(
                "tool_runs_total", labels={"tool": self.name, "method": "unknown", "outcome": "error"}
            ).inc()
            return StepResult.fail(error=f"Content type routing failed: {e!s}", error_category=ErrorCategory.PROCESSING)

    def _try_llm_classification(self, transcript: str, title: str, description: str) -> StepResult | None:
        """Attempt LLM-based content classification using Instructor.

        Returns:
            StepResult with classification if successful, None to trigger fallback
        """
        if not INSTRUCTOR_AVAILABLE:
            return None
        if not InstructorClientFactory.is_enabled():
            return None
        try:
            client = InstructorClientFactory.create_openrouter_client()
            if client is None:
                logger.warning("Failed to create Instructor client for content routing")
                return None
            combined_text = (
                f"Title: {title}\n\nDescription: {description}\n\nTranscript (first 3000 chars): {transcript[:3000]}"
            )
            prompt = f"Analyze the following content and classify it into appropriate content types.\n\nProvide:\n1. Primary content type (e.g., educational, entertainment, news, technology, discussion, general)\n2. Confidence level (0.0-1.0)\n3. Secondary content types if applicable\n4. Recommended processing pipeline\n5. Processing flags for optimization\n6. Recommendations for analysis\n\nContent to analyze:\n{combined_text}\n"
            response = client.chat.completions.create(
                model=self._config.openrouter_llm_model,
                response_model=ContentTypeClassification,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content classifier. Analyze content and provide structured classification results.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
                temperature=0.3,
            )
            decision = response.parsed if hasattr(response, "parsed") else response
            result = {
                "classification": {
                    "primary_type": decision.primary_type.value,
                    "confidence": decision.confidence,
                    "secondary_types": [t.value for t in decision.secondary_types],
                },
                "routing": {
                    "pipeline": decision.recommended_pipeline,
                    "processing_flags": decision.processing_flags,
                    "estimated_speedup": decision.estimated_processing_time / 100.0,
                },
                "recommendations": decision.recommendations,
                "analysis_method": "llm_instructor",
                "quality_score": decision.quality_score,
            }
            return StepResult.ok(result=result)
        except Exception as e:
            logger.warning(f"LLM classification failed, falling back to pattern matching: {e}")
            self._metrics.counter(
                "tool_runs_total", labels={"tool": self.name, "method": "llm_instructor", "outcome": "error"}
            ).inc()
            return None

    def _classify_content(self, transcript: str, title: str, description: str, metadata: dict) -> ContentClassification:
        """Classify content based on multiple signals."""
        educational_indicators = [
            "\\b(learn|tutorial|explain|how\\s+to|lesson|course|teach|study)\\b",
            "\\b(university|school|professor|student|lecture|class)\\b",
            "\\b(definition|theory|concept|principle|method|technique)\\b",
        ]
        entertainment_indicators = [
            "\\b(funny|comedy|humor|joke|laugh|entertainment|fun)\\b",
            "\\b(movie|film|show|series|episode|actor|actress)\\b",
            "\\b(game|gaming|play|player|level|score)\\b",
        ]
        news_indicators = [
            "\\b(news|report|breaking|update|journalist|reporter)\\b",
            "\\b(politics|government|election|vote|policy|law)\\b",
            "\\b(economy|market|business|company|industry)\\b",
        ]
        tech_indicators = [
            "\\b(technology|software|programming|code|developer|engineer)\\b",
            "\\b(computer|internet|digital|cyber|online|web)\\b",
            "\\b(AI|artificial\\s+intelligence|machine\\s+learning|data)\\b",
        ]
        discussion_indicators = [
            "\\b(debate|discuss|opinion|argument|perspective|viewpoint)\\b",
            "\\b(interview|conversation|talk|dialogue|panel)\\b",
            "\\b(think|believe|feel|agree|disagree)\\b",
        ]
        combined_text = f"{title} {description} {transcript[:2000]}".lower()
        scores = {}
        edu_score = sum(len(re.findall(pattern, combined_text)) for pattern in educational_indicators)
        scores["educational"] = edu_score / len(combined_text.split()) * 1000
        ent_score = sum(len(re.findall(pattern, combined_text)) for pattern in entertainment_indicators)
        scores["entertainment"] = ent_score / len(combined_text.split()) * 1000
        news_score = sum(len(re.findall(pattern, combined_text)) for pattern in news_indicators)
        scores["news"] = news_score / len(combined_text.split()) * 1000
        tech_score = sum(len(re.findall(pattern, combined_text)) for pattern in tech_indicators)
        scores["technology"] = tech_score / len(combined_text.split()) * 1000
        disc_score = sum(len(re.findall(pattern, combined_text)) for pattern in discussion_indicators)
        scores["discussion"] = disc_score / len(combined_text.split()) * 1000
        primary_type = max(scores.keys(), key=lambda k: scores[k])
        confidence = min(scores[primary_type] / 10, 1.0)
        if confidence < 0.1:
            primary_type = "general"
            confidence = 0.5
        secondary_types = [
            content_type for content_type, score in scores.items() if score > 0.5 and content_type != primary_type
        ]
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
            "educational": "deep_analysis",
            "technology": "deep_analysis",
            "news": "fast_summary",
            "entertainment": "light_analysis",
            "discussion": "deep_analysis",
            "general": "standard_pipeline",
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
        if "discussion" in secondary_types:
            flags["enable_fallacy_detection"] = True
        if "entertainment" in secondary_types:
            flags["enable_sentiment_analysis"] = True
        return flags

    def _determine_routing(self, classification: ContentClassification) -> dict:
        """Determine routing configuration and performance estimates."""
        routing_config = {"pipeline": classification.routing_decision, "estimated_speedup": 1.0}
        speedup_estimates = {"fast_summary": 2.5, "light_analysis": 1.8, "standard_pipeline": 1.0, "deep_analysis": 0.9}
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
