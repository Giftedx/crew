"""
Visual content summarization tool with advanced timeline and key moment detection.

This tool provides comprehensive visual summarization including:
- Key moment identification in videos and image sequences
- Visual timeline creation with important events
- Thumbnail optimization and generation
- Visual narrative construction
- Scene flow analysis
- Multi-modal content synthesis
- Visual storytelling elements extraction
"""

from __future__ import annotations

import logging
import time
from typing import Any, TypedDict

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool


class KeyMoment(TypedDict, total=False):
    """Represents a key moment in visual content."""

    timestamp: float
    frame_id: int
    importance_score: float
    description: str
    moment_type: str  # scene_change, action, emotion, text, object_focus
    visual_elements: list[str]
    context: str
    thumbnail_quality: float


class VisualTimeline(TypedDict, total=False):
    """Visual timeline representation."""

    total_duration: float
    key_moments: list[KeyMoment]
    scene_segments: list[dict[str, Any]]
    narrative_flow: list[str]
    visual_themes: list[str]
    pacing_analysis: dict[str, Any]


class ThumbnailRecommendation(TypedDict, total=False):
    """Thumbnail optimization recommendation."""

    recommended_frame: int
    timestamp: float
    appeal_score: float
    composition_score: float
    clarity_score: float
    emotional_impact: float
    reasons: list[str]
    alternative_frames: list[dict[str, Any]]


class VisualSummary(TypedDict, total=False):
    """Complete visual summary result."""

    executive_summary: str
    key_visual_elements: list[str]
    dominant_themes: list[str]
    visual_progression: str
    emotional_arc: list[dict[str, Any]]
    technical_quality: dict[str, float]
    content_classification: str
    engagement_factors: list[str]
    accessibility_summary: str


class VisualSummaryResult(TypedDict, total=False):
    """Complete visual summary analysis result."""

    visual_summary: VisualSummary
    timeline: VisualTimeline
    thumbnail_recommendations: list[ThumbnailRecommendation]
    content_highlights: list[str]
    visual_narrative: str
    processing_time: float
    metadata: dict[str, Any]


class VisualSummaryTool(BaseTool[StepResult]):
    """Advanced visual content summarization and key moment detection."""

    name: str = "Visual Summary Tool"
    description: str = (
        "Generates visual summaries, timelines, key moments, and thumbnail recommendations from video frame analysis."
    )

    def __init__(
        self,
        key_moment_threshold: float = 0.6,
        max_key_moments: int = 10,
        thumbnail_count: int = 3,
        enable_narrative_analysis: bool = True,
    ):
        super().__init__()
        self._key_moment_threshold = key_moment_threshold
        self._max_key_moments = max_key_moments
        self._thumbnail_count = thumbnail_count
        self._enable_narrative_analysis = enable_narrative_analysis
        self._metrics = get_metrics()

    def _run(
        self,
        frame_analysis_data: dict[str, Any],
        content_metadata: dict[str, Any] | None = None,
        tenant: str = "default",
        workspace: str = "default",
        summary_type: str = "comprehensive",
    ) -> StepResult:
        """
        Generate visual summary from frame analysis data.

        Args:
            frame_analysis_data: Results from VideoFrameAnalysisTool
            content_metadata: Additional content metadata
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier
            summary_type: Type of summary (basic, comprehensive, narrative_focused)

        Returns:
            StepResult with visual summary and recommendations
        """
        start_time = time.monotonic()

        try:
            # Input validation
            if not frame_analysis_data:
                return StepResult.fail("Frame analysis data cannot be empty")

            key_frames = frame_analysis_data.get("key_frames", [])
            if not key_frames:
                return StepResult.fail("No key frames found in analysis data")

            if tenant and workspace:
                self.note(f"Generating visual summary for {len(key_frames)} frames")

            # Generate visual summary components
            visual_summary = self._generate_visual_summary(frame_analysis_data, summary_type)
            timeline = self._create_visual_timeline(frame_analysis_data)
            thumbnail_recommendations = self._generate_thumbnail_recommendations(frame_analysis_data)

            # Extract content highlights
            content_highlights = self._extract_content_highlights(frame_analysis_data)

            # Generate visual narrative
            visual_narrative = self._construct_visual_narrative(frame_analysis_data, visual_summary)

            processing_time = time.monotonic() - start_time

            result: VisualSummaryResult = {
                "visual_summary": visual_summary,
                "timeline": timeline,
                "thumbnail_recommendations": thumbnail_recommendations,
                "content_highlights": content_highlights,
                "visual_narrative": visual_narrative,
                "processing_time": processing_time,
                "metadata": {
                    "summary_type": summary_type,
                    "frame_count": len(key_frames),
                    "tenant": tenant,
                    "workspace": workspace,
                },
            }

            self._metrics.counter("tool_runs_total", labels={"tool": self.name, "outcome": "success"}).inc()
            self._metrics.histogram("tool_run_seconds", processing_time, labels={"tool": self.name})

            return StepResult.ok(data=result)

        except Exception as e:
            processing_time = time.monotonic() - start_time
            self._metrics.counter("tool_runs_total", labels={"tool": self.name, "outcome": "error"}).inc()
            logging.exception("Visual summary generation failed")
            return StepResult.fail(f"Visual summary generation failed: {e!s}")

    def _generate_visual_summary(self, frame_analysis_data: dict[str, Any], summary_type: str) -> VisualSummary:
        """Generate comprehensive visual summary."""
        key_frames = frame_analysis_data.get("key_frames", [])
        duration = frame_analysis_data.get("duration_seconds", 0.0)
        scene_transitions = frame_analysis_data.get("scene_transitions", [])

        # Extract visual elements across all frames
        all_objects = []
        all_sentiments = []
        all_scenes = []
        text_content = []

        for frame in key_frames:
            objects = frame.get("objects", [])
            if isinstance(objects, list):
                all_objects.extend([str(obj) for obj in objects])

            sentiment = frame.get("visual_sentiment", "neutral")
            all_sentiments.append(sentiment)

            scene_type = frame.get("scene_type", "unknown")
            all_scenes.append(scene_type)

            text = frame.get("text_content", "")
            if text:
                text_content.append(text)

        # Identify key visual elements
        from collections import Counter

        object_counts = Counter(all_objects)
        key_visual_elements = [obj for obj, count in object_counts.most_common(10)]

        # Determine dominant themes
        scene_counts = Counter(all_scenes)
        dominant_themes = [scene for scene, count in scene_counts.most_common(3)]

        # Analyze emotional progression
        emotional_arc = self._analyze_emotional_arc(key_frames)

        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            key_visual_elements,
            dominant_themes,
            emotional_arc,
            duration,
            len(key_frames),
        )

        # Analyze visual progression
        visual_progression = self._analyze_visual_progression(key_frames, scene_transitions)

        # Assess technical quality
        technical_quality = self._assess_technical_quality(frame_analysis_data)

        # Classify content
        content_classification = self._classify_content(dominant_themes, emotional_arc)

        # Identify engagement factors
        engagement_factors = self._identify_engagement_factors(key_frames, scene_transitions)

        # Generate accessibility summary
        accessibility_summary = self._generate_accessibility_summary(key_frames, text_content)

        return {
            "executive_summary": executive_summary,
            "key_visual_elements": key_visual_elements,
            "dominant_themes": dominant_themes,
            "visual_progression": visual_progression,
            "emotional_arc": emotional_arc,
            "technical_quality": technical_quality,
            "content_classification": content_classification,
            "engagement_factors": engagement_factors,
            "accessibility_summary": accessibility_summary,
        }

    def _create_visual_timeline(self, frame_analysis_data: dict[str, Any]) -> VisualTimeline:
        """Create detailed visual timeline with key moments."""
        key_frames = frame_analysis_data.get("key_frames", [])
        scene_transitions = frame_analysis_data.get("scene_transitions", [])
        duration = frame_analysis_data.get("duration_seconds", 0.0)

        # Identify key moments
        key_moments = self._identify_key_moments(key_frames)

        # Create scene segments
        scene_segments = self._create_scene_segments(key_frames, scene_transitions)

        # Analyze narrative flow
        narrative_flow = self._analyze_narrative_flow(key_frames, scene_segments)

        # Extract visual themes
        visual_themes = self._extract_visual_themes(key_frames)

        # Analyze pacing
        pacing_analysis = self._analyze_pacing(key_frames, scene_transitions, duration)

        return {
            "total_duration": duration,
            "key_moments": key_moments,
            "scene_segments": scene_segments,
            "narrative_flow": narrative_flow,
            "visual_themes": visual_themes,
            "pacing_analysis": pacing_analysis,
        }

    def _identify_key_moments(self, key_frames: list[dict[str, Any]]) -> list[KeyMoment]:
        """Identify the most important visual moments."""
        key_moments = []

        for i, frame in enumerate(key_frames):
            importance_score = self._calculate_importance_score(frame, i, key_frames)

            if importance_score >= self._key_moment_threshold:
                moment_type = self._classify_moment_type(frame, key_frames)

                key_moment: KeyMoment = {
                    "timestamp": frame.get("timestamp", 0.0),
                    "frame_id": frame.get("frame_id", i),
                    "importance_score": importance_score,
                    "description": self._generate_moment_description(frame),
                    "moment_type": moment_type,
                    "visual_elements": self._extract_visual_elements(frame),
                    "context": self._generate_moment_context(frame, i, key_frames),
                    "thumbnail_quality": self._assess_thumbnail_quality(frame),
                }

                key_moments.append(key_moment)

        # Sort by importance and limit count
        key_moments.sort(key=lambda x: x["importance_score"], reverse=True)
        return key_moments[: self._max_key_moments]

    def _calculate_importance_score(self, frame: dict[str, Any], index: int, all_frames: list[dict[str, Any]]) -> float:
        """Calculate importance score for a frame."""
        score = 0.0

        # Object diversity factor
        objects = frame.get("objects", [])
        if objects:
            score += min(0.3, len(objects) * 0.1)

        # Text content factor
        text_content = frame.get("text_content", "")
        if text_content:
            score += 0.2

        # Emotional intensity factor
        sentiment = frame.get("visual_sentiment", "neutral")
        if sentiment in ["positive", "negative"]:
            score += 0.2

        # Scene change factor (check if different from previous)
        if index > 0:
            prev_scene = all_frames[index - 1].get("scene_type", "")
            curr_scene = frame.get("scene_type", "")
            if prev_scene != curr_scene:
                score += 0.3

        # Confidence factor
        confidence_scores = frame.get("confidence_scores", {})
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0
        score += avg_confidence * 0.2

        return min(1.0, score)

    def _classify_moment_type(self, frame: dict[str, Any], all_frames: list[dict[str, Any]]) -> str:
        """Classify the type of key moment."""
        if frame.get("text_content"):
            return "text"

        objects = frame.get("objects", [])
        if any("face" in str(obj).lower() for obj in objects):
            return "emotion"

        if len(objects) > 3:
            return "action"

        return "scene_change"

    def _generate_moment_description(self, frame: dict[str, Any]) -> str:
        """Generate description for a key moment."""
        scene_type = frame.get("scene_type", "scene")
        objects = frame.get("objects", [])
        sentiment = frame.get("visual_sentiment", "neutral")

        desc_parts = []

        if scene_type != "unknown":
            desc_parts.append(f"{scene_type} scene")

        if objects:
            main_objects = [str(obj) for obj in objects[:3]]
            desc_parts.append(f"featuring {', '.join(main_objects)}")

        if sentiment != "neutral":
            desc_parts.append(f"with {sentiment} tone")

        return " ".join(desc_parts) if desc_parts else "Key visual moment"

    def _extract_visual_elements(self, frame: dict[str, Any]) -> list[str]:
        """Extract key visual elements from a frame."""
        elements = []

        objects = frame.get("objects", [])
        if objects:
            elements.extend([str(obj) for obj in objects[:5]])

        scene_type = frame.get("scene_type")
        if scene_type and scene_type != "unknown":
            elements.append(f"scene:{scene_type}")

        sentiment = frame.get("visual_sentiment")
        if sentiment and sentiment != "neutral":
            elements.append(f"mood:{sentiment}")

        return elements

    def _generate_moment_context(self, frame: dict[str, Any], index: int, all_frames: list[dict[str, Any]]) -> str:
        """Generate contextual information for a moment."""
        context_parts = []

        # Temporal context
        timestamp = frame.get("timestamp", 0.0)
        if timestamp > 0:
            context_parts.append(f"at {timestamp:.1f}s")

        # Positional context
        total_frames = len(all_frames)
        position = "beginning" if index < total_frames * 0.25 else "middle" if index < total_frames * 0.75 else "end"
        context_parts.append(f"in the {position} of content")

        return " ".join(context_parts)

    def _assess_thumbnail_quality(self, frame: dict[str, Any]) -> float:
        """Assess how good this frame would be as a thumbnail."""
        quality_score = 0.5  # Base score

        # Object presence
        objects = frame.get("objects", [])
        if objects:
            quality_score += min(0.2, len(objects) * 0.05)

        # Face presence (good for thumbnails)
        if any("face" in str(obj).lower() for obj in objects):
            quality_score += 0.2

        # Text content (can be good or bad)
        text_content = frame.get("text_content", "")
        if text_content:
            quality_score += 0.1 if len(text_content) < 50 else -0.1

        # Emotional content
        sentiment = frame.get("visual_sentiment", "neutral")
        if sentiment in ["positive", "negative"]:
            quality_score += 0.1

        return min(1.0, quality_score)

    def _generate_thumbnail_recommendations(self, frame_analysis_data: dict[str, Any]) -> list[ThumbnailRecommendation]:
        """Generate thumbnail recommendations."""
        key_frames = frame_analysis_data.get("key_frames", [])

        # Score all frames for thumbnail quality
        scored_frames = []
        for i, frame in enumerate(key_frames):
            appeal_score = self._calculate_thumbnail_appeal(frame)
            composition_score = self._assess_composition_quality(frame)
            clarity_score = self._assess_frame_clarity(frame)
            emotional_impact = self._assess_emotional_impact(frame)

            overall_score = (appeal_score + composition_score + clarity_score + emotional_impact) / 4

            scored_frames.append(
                {
                    "frame_id": frame.get("frame_id", i),
                    "timestamp": frame.get("timestamp", 0.0),
                    "overall_score": overall_score,
                    "appeal_score": appeal_score,
                    "composition_score": composition_score,
                    "clarity_score": clarity_score,
                    "emotional_impact": emotional_impact,
                    "frame": frame,
                }
            )

        # Sort by overall score and create recommendations
        scored_frames.sort(key=lambda x: x["overall_score"], reverse=True)

        recommendations = []
        for i, scored_frame in enumerate(scored_frames[: self._thumbnail_count]):
            reasons = self._generate_thumbnail_reasons(scored_frame)

            recommendation: ThumbnailRecommendation = {
                "recommended_frame": scored_frame["frame_id"],
                "timestamp": scored_frame["timestamp"],
                "appeal_score": scored_frame["appeal_score"],
                "composition_score": scored_frame["composition_score"],
                "clarity_score": scored_frame["clarity_score"],
                "emotional_impact": scored_frame["emotional_impact"],
                "reasons": reasons,
                "alternative_frames": [
                    {
                        "frame_id": alt["frame_id"],
                        "timestamp": alt["timestamp"],
                        "score": alt["overall_score"],
                    }
                    for alt in scored_frames[i + 1 : i + 3]
                ],
            }

            recommendations.append(recommendation)

        return recommendations

    def _calculate_thumbnail_appeal(self, frame: dict[str, Any]) -> float:
        """Calculate thumbnail visual appeal."""
        score = 0.5

        objects = frame.get("objects", [])

        # People boost appeal
        if any("person" in str(obj).lower() or "face" in str(obj).lower() for obj in objects):
            score += 0.3

        # Clear objects
        if len(objects) >= 2:
            score += 0.2

        # Emotional content
        sentiment = frame.get("visual_sentiment", "neutral")
        if sentiment != "neutral":
            score += 0.2

        return min(1.0, score)

    def _assess_composition_quality(self, frame: dict[str, Any]) -> float:
        """Assess visual composition quality."""
        # Simplified composition assessment
        objects = frame.get("objects", [])

        # Good object count (not too empty, not too cluttered)
        if 2 <= len(objects) <= 5:
            return 0.8
        elif 1 <= len(objects) <= 6:
            return 0.6
        else:
            return 0.4

    def _assess_frame_clarity(self, frame: dict[str, Any]) -> float:
        """Assess frame clarity and sharpness."""
        # Use confidence scores as proxy for clarity
        confidence_scores = frame.get("confidence_scores", {})
        if confidence_scores:
            return sum(confidence_scores.values()) / len(confidence_scores)
        return 0.5

    def _assess_emotional_impact(self, frame: dict[str, Any]) -> float:
        """Assess emotional impact of frame."""
        sentiment = frame.get("visual_sentiment", "neutral")

        if sentiment == "positive":
            return 0.8
        elif sentiment == "negative":
            return 0.7  # Negative can be impactful but less appealing
        else:
            return 0.4

    def _generate_thumbnail_reasons(self, scored_frame: dict[str, Any]) -> list[str]:
        """Generate reasons why this frame makes a good thumbnail."""
        reasons = []
        frame = scored_frame["frame"]

        if scored_frame["appeal_score"] > 0.7:
            reasons.append("High visual appeal")

        if scored_frame["emotional_impact"] > 0.7:
            reasons.append("Strong emotional content")

        objects = frame.get("objects", [])
        if any("person" in str(obj).lower() for obj in objects):
            reasons.append("Contains people")

        if len(objects) >= 3:
            reasons.append("Rich visual content")

        if frame.get("text_content"):
            reasons.append("Contains readable text")

        return reasons or ["Good overall composition"]

    def _create_scene_segments(
        self, key_frames: list[dict[str, Any]], scene_transitions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Create scene segments from frames and transitions."""
        segments = []

        if not key_frames:
            return segments

        current_segment_start = 0
        current_scene_type = key_frames[0].get("scene_type", "unknown")

        for i, frame in enumerate(key_frames[1:], 1):
            frame_scene_type = frame.get("scene_type", "unknown")

            # Check if scene changed
            if frame_scene_type != current_scene_type:
                # Close current segment
                segments.append(
                    {
                        "start_timestamp": key_frames[current_segment_start].get("timestamp", 0.0),
                        "end_timestamp": key_frames[i - 1].get("timestamp", 0.0),
                        "scene_type": current_scene_type,
                        "frame_count": i - current_segment_start,
                        "dominant_objects": self._get_dominant_objects_in_range(key_frames[current_segment_start:i]),
                    }
                )

                # Start new segment
                current_segment_start = i
                current_scene_type = frame_scene_type

        # Close final segment
        segments.append(
            {
                "start_timestamp": key_frames[current_segment_start].get("timestamp", 0.0),
                "end_timestamp": key_frames[-1].get("timestamp", 0.0),
                "scene_type": current_scene_type,
                "frame_count": len(key_frames) - current_segment_start,
                "dominant_objects": self._get_dominant_objects_in_range(key_frames[current_segment_start:]),
            }
        )

        return segments

    def _get_dominant_objects_in_range(self, frames: list[dict[str, Any]]) -> list[str]:
        """Get dominant objects in a range of frames."""
        from collections import Counter

        all_objects = []

        for frame in frames:
            objects = frame.get("objects", [])
            all_objects.extend([str(obj) for obj in objects])

        object_counts = Counter(all_objects)
        return [obj for obj, count in object_counts.most_common(3)]

    def _analyze_narrative_flow(
        self, key_frames: list[dict[str, Any]], scene_segments: list[dict[str, Any]]
    ) -> list[str]:
        """Analyze the narrative flow of the visual content."""
        flow = []

        if scene_segments:
            for segment in scene_segments:
                scene_type = segment.get("scene_type", "unknown")
                dominant_objects = segment.get("dominant_objects", [])

                if scene_type != "unknown":
                    flow_description = f"{scene_type}"
                    if dominant_objects:
                        flow_description += f" with {', '.join(dominant_objects[:2])}"
                    flow.append(flow_description)

        return flow

    def _extract_visual_themes(self, key_frames: list[dict[str, Any]]) -> list[str]:
        """Extract recurring visual themes."""
        from collections import Counter

        all_scenes = [frame.get("scene_type", "") for frame in key_frames]
        all_objects = []
        for frame in key_frames:
            objects = frame.get("objects", [])
            all_objects.extend([str(obj) for obj in objects])

        scene_counts = Counter(all_scenes)
        object_counts = Counter(all_objects)

        themes = []

        # Add dominant scenes as themes
        for scene, count in scene_counts.most_common(3):
            if scene and scene != "unknown":
                themes.append(f"{scene}_scenes")

        # Add common objects as themes
        for obj, count in object_counts.most_common(5):
            if count >= len(key_frames) * 0.3:  # Appears in 30%+ of frames
                themes.append(f"recurring_{obj}")

        return themes

    def _analyze_pacing(
        self,
        key_frames: list[dict[str, Any]],
        scene_transitions: list[dict[str, Any]],
        duration: float,
    ) -> dict[str, Any]:
        """Analyze visual pacing."""
        pacing = {
            "average_scene_length": 0.0,
            "transition_frequency": 0.0,
            "pacing_assessment": "moderate",
            "rhythm_pattern": "steady",
        }

        if scene_transitions and duration > 0:
            pacing["transition_frequency"] = len(scene_transitions) / duration
            pacing["average_scene_length"] = duration / len(scene_transitions) if scene_transitions else duration

            # Assess pacing
            if pacing["transition_frequency"] > 0.3:
                pacing["pacing_assessment"] = "fast"
                pacing["rhythm_pattern"] = "dynamic"
            elif pacing["transition_frequency"] < 0.1:
                pacing["pacing_assessment"] = "slow"
                pacing["rhythm_pattern"] = "contemplative"

        return pacing

    def _analyze_emotional_arc(self, key_frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Analyze emotional progression through the content."""
        arc = []

        for i, frame in enumerate(key_frames):
            sentiment = frame.get("visual_sentiment", "neutral")
            timestamp = frame.get("timestamp", 0.0)

            # Map sentiment to emotional intensity
            intensity = {"positive": 0.7, "negative": 0.6, "neutral": 0.3}.get(sentiment, 0.3)

            arc.append(
                {
                    "timestamp": timestamp,
                    "emotion": sentiment,
                    "intensity": intensity,
                    "position": i / len(key_frames) if key_frames else 0,
                }
            )

        return arc

    def _generate_executive_summary(
        self,
        visual_elements: list[str],
        themes: list[str],
        emotional_arc: list[dict[str, Any]],
        duration: float,
        frame_count: int,
    ) -> str:
        """Generate executive summary of visual content."""
        summary_parts = []

        # Duration and scope
        if duration > 0:
            summary_parts.append(f"Visual content spanning {duration:.1f} seconds")

        # Key themes
        if themes:
            theme_text = ", ".join(themes[:3])
            summary_parts.append(f"featuring {theme_text}")

        # Visual elements
        if visual_elements:
            element_text = ", ".join(visual_elements[:5])
            summary_parts.append(f"with prominent visual elements including {element_text}")

        # Emotional tone
        if emotional_arc:
            dominant_emotion = max(
                {point["emotion"] for point in emotional_arc},
                key=lambda x: sum(1 for p in emotional_arc if p["emotion"] == x),
            )
            if dominant_emotion != "neutral":
                summary_parts.append(f"maintaining a predominantly {dominant_emotion} emotional tone")

        return ". ".join(summary_parts) + "." if summary_parts else "Visual content analyzed."

    def _analyze_visual_progression(
        self, key_frames: list[dict[str, Any]], scene_transitions: list[dict[str, Any]]
    ) -> str:
        """Analyze how visual content progresses."""
        if not key_frames:
            return "No visual progression data available"

        # Analyze scene changes
        if scene_transitions:
            transition_count = len(scene_transitions)
            if transition_count > len(key_frames) * 0.5:
                return "Dynamic visual progression with frequent scene changes"
            elif transition_count > 2:
                return "Moderate visual progression with structured scene development"
            else:
                return "Steady visual progression with minimal scene changes"

        return "Consistent visual presentation throughout"

    def _assess_technical_quality(self, frame_analysis_data: dict[str, Any]) -> dict[str, float]:
        """Assess overall technical quality metrics."""
        key_frames = frame_analysis_data.get("key_frames", [])

        if not key_frames:
            return {"overall": 0.0, "clarity": 0.0, "composition": 0.0}

        # Average confidence scores as proxy for technical quality
        all_confidence_scores = []
        for frame in key_frames:
            confidence_scores = frame.get("confidence_scores", {})
            if confidence_scores:
                all_confidence_scores.extend(confidence_scores.values())

        avg_confidence = sum(all_confidence_scores) / len(all_confidence_scores) if all_confidence_scores else 0.5

        return {
            "overall": avg_confidence,
            "clarity": avg_confidence,
            "composition": avg_confidence * 0.9,  # Slightly lower for composition
            "technical_assessment": avg_confidence,
        }

    def _classify_content(self, themes: list[str], emotional_arc: list[dict[str, Any]]) -> str:
        """Classify the type of visual content."""
        if not themes:
            return "general_content"

        # Check for specific content types based on themes
        educational_indicators = ["presentation", "lecture", "studio"]
        entertainment_indicators = ["performance", "show", "music"]
        documentary_indicators = ["outdoor", "nature", "interview"]

        theme_text = " ".join(themes).lower()

        if any(indicator in theme_text for indicator in educational_indicators):
            return "educational_content"
        elif any(indicator in theme_text for indicator in entertainment_indicators):
            return "entertainment_content"
        elif any(indicator in theme_text for indicator in documentary_indicators):
            return "documentary_content"
        else:
            return "mixed_content"

    def _identify_engagement_factors(
        self, key_frames: list[dict[str, Any]], scene_transitions: list[dict[str, Any]]
    ) -> list[str]:
        """Identify factors that contribute to viewer engagement."""
        factors = []

        # Visual variety
        unique_scenes = {frame.get("scene_type", "unknown") for frame in key_frames}
        if len(unique_scenes) > 2:
            factors.append("Visual variety with multiple scene types")

        # Dynamic pacing
        if len(scene_transitions) > len(key_frames) * 0.3:
            factors.append("Dynamic pacing with frequent scene changes")

        # Emotional content
        emotional_frames = [frame for frame in key_frames if frame.get("visual_sentiment", "neutral") != "neutral"]
        if len(emotional_frames) > len(key_frames) * 0.4:
            factors.append("Strong emotional content")

        # Text presence
        text_frames = [frame for frame in key_frames if frame.get("text_content")]
        if text_frames:
            factors.append("Informational text elements")

        # Rich object content
        avg_objects = sum(len(frame.get("objects", [])) for frame in key_frames) / len(key_frames) if key_frames else 0
        if avg_objects > 3:
            factors.append("Rich visual detail")

        return factors or ["Standard visual presentation"]

    def _generate_accessibility_summary(self, key_frames: list[dict[str, Any]], text_content: list[str]) -> str:
        """Generate accessibility summary for the visual content."""
        summary_parts = []

        # Text content availability
        if text_content:
            summary_parts.append(f"Contains {len(text_content)} text elements for screen readers")
        else:
            summary_parts.append("Limited text content - may require additional audio description")

        # Visual complexity
        avg_objects = sum(len(frame.get("objects", [])) for frame in key_frames) / len(key_frames) if key_frames else 0
        if avg_objects > 4:
            summary_parts.append("High visual complexity - detailed descriptions recommended")
        elif avg_objects < 2:
            summary_parts.append("Simple visual presentation - basic descriptions sufficient")

        # Scene variety
        unique_scenes = {frame.get("scene_type", "unknown") for frame in key_frames}
        if len(unique_scenes) > 3:
            summary_parts.append("Multiple scene types require context switching descriptions")

        return ". ".join(summary_parts) + "." if summary_parts else "Standard accessibility considerations apply."

    def _extract_content_highlights(self, frame_analysis_data: dict[str, Any]) -> list[str]:
        """Extract key content highlights."""
        highlights = []
        key_frames = frame_analysis_data.get("key_frames", [])

        # Find frames with text content
        text_highlights = []
        for frame in key_frames:
            text = frame.get("text_content", "")
            if text and len(text) > 10:  # Meaningful text
                text_highlights.append(text[:100])  # Truncate long text

        if text_highlights:
            highlights.extend(text_highlights[:3])  # Top 3 text highlights

        # Find emotional peaks
        emotional_frames = [frame for frame in key_frames if frame.get("visual_sentiment", "neutral") != "neutral"]
        if emotional_frames:
            highlights.append(f"Strong emotional moments with {emotional_frames[0].get('visual_sentiment')} sentiment")

        # Find object-rich scenes
        max_objects_frame = max(key_frames, key=lambda x: len(x.get("objects", [])), default=None)
        if max_objects_frame:
            objects = max_objects_frame.get("objects", [])
            if len(objects) > 3:
                highlights.append(f"Rich visual scene featuring {', '.join([str(obj) for obj in objects[:3]])}")

        return highlights

    def _construct_visual_narrative(self, frame_analysis_data: dict[str, Any], visual_summary: VisualSummary) -> str:
        """Construct a coherent visual narrative."""
        if not self._enable_narrative_analysis:
            return "Narrative analysis disabled"

        narrative_parts = []

        # Opening
        key_frames = frame_analysis_data.get("key_frames", [])
        if key_frames:
            first_frame = key_frames[0]
            scene_type = first_frame.get("scene_type", "scene")
            objects = first_frame.get("objects", [])

            if scene_type != "unknown":
                narrative_parts.append(f"The visual content opens with a {scene_type}")

            if objects:
                main_objects = [str(obj) for obj in objects[:2]]
                narrative_parts.append(f"introducing {', '.join(main_objects)}")

        # Development
        visual_progression = visual_summary.get("visual_progression", "")
        if visual_progression:
            narrative_parts.append(f"The content {visual_progression.lower()}")

        # Emotional journey
        emotional_arc = visual_summary.get("emotional_arc", [])
        if emotional_arc:
            dominant_emotions = [point["emotion"] for point in emotional_arc]
            emotion_summary = max(set(dominant_emotions), key=dominant_emotions.count)
            if emotion_summary != "neutral":
                narrative_parts.append(f"maintaining a {emotion_summary} emotional tone throughout")

        # Conclusion
        dominant_themes = visual_summary.get("dominant_themes", [])
        if dominant_themes:
            theme = dominant_themes[0]
            narrative_parts.append(f"concluding as a cohesive {theme} presentation")

        return ". ".join(narrative_parts) + "." if narrative_parts else "Visual narrative analysis complete."

    def run(
        self,
        frame_analysis_data: dict[str, Any],
        content_metadata: dict[str, Any] | None = None,
        tenant: str = "default",
        workspace: str = "default",
        summary_type: str = "comprehensive",
    ) -> StepResult:
        """Public interface for visual summary generation."""
        return self._run(frame_analysis_data, content_metadata, tenant, workspace, summary_type)
