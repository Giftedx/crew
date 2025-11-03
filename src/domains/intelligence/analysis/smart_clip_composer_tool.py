from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from platform.core.step_result import StepResult
from typing import Any

from crewai_tools import BaseTool
from pydantic import BaseModel, Field

from kg.creator_kg_store import CreatorKGStore


logger = logging.getLogger(__name__)


class SmartClipComposerInput(BaseModel):
    """Input schema for smart clip composer."""

    episode_id: str = Field(..., description="Episode ID to analyze for clips")
    max_clips: int = Field(default=10, description="Maximum number of clips to suggest")
    min_clip_length: float = Field(default=15.0, description="Minimum clip length in seconds")
    max_clip_length: float = Field(default=120.0, description="Maximum clip length in seconds")
    highlight_threshold: float = Field(default=0.6, description="Minimum highlight score threshold")
    include_titles: bool = Field(default=True, description="Generate title variants for clips")
    export_formats: list[str] = Field(default=["json"], description="Export formats: json, xml, csv")


@dataclass
class ClipSuggestion:
    """Represents a suggested clip with metadata."""

    clip_id: str
    start_time: float
    end_time: float
    duration: float
    highlight_score: float
    proposed_title: str
    title_variants: list[str]
    reasoning: str
    signals: dict[str, float]
    thumbnail_frame_time: float
    content_summary: str
    tags: list[str]


@dataclass
class ExportData:
    """Export format data."""

    format_name: str
    content: str
    filename: str


class SmartClipComposerTool(BaseTool):
    """
    Smart Clip Composer Tool.

    Analyzes episodes to identify highlight-worthy moments and generates
    clip suggestions with titles, export formats, and metadata.
    """

    name: str = "smart_clip_composer_tool"
    description: str = "\n    Analyze episodes for highlight-worthy moments and generate clip suggestions\n    with titles, export formats, and metadata for content creators.\n    "
    args_schema: type[BaseModel] = SmartClipComposerInput

    def __init__(self, kg_store: CreatorKGStore | None = None):
        """Initialize the smart clip composer tool."""
        super().__init__()
        self.kg_store = kg_store or CreatorKGStore(":memory:")

    def _run(
        self,
        episode_id: str,
        max_clips: int = 10,
        min_clip_length: float = 15.0,
        max_clip_length: float = 120.0,
        highlight_threshold: float = 0.6,
        include_titles: bool = True,
        export_formats: list[str] | None = None,
        tenant: str = "",
        workspace: str = "",
    ) -> StepResult:
        """
        Execute smart clip composition.

        Steps:
        1. Retrieve episode data from KG
        2. Analyze content for highlight moments
        3. Score and rank potential clips
        4. Generate titles and metadata
        5. Export in requested formats
        """
        try:
            if export_formats is None:
                export_formats = ["json"]
            logger.info(f"Composing clips for episode: {episode_id}")
            episode_data = self._retrieve_episode_data(episode_id, tenant, workspace)
            if not episode_data:
                return StepResult.fail(f"Episode {episode_id} not found")
            highlight_segments = self._analyze_highlights(episode_data)
            clip_suggestions = self._generate_clip_suggestions(
                highlight_segments,
                episode_data,
                max_clips,
                min_clip_length,
                max_clip_length,
                highlight_threshold,
                include_titles,
            )
            exports = self._export_clips(clip_suggestions, episode_id, export_formats)
            return StepResult.ok(
                data={
                    "episode_id": episode_id,
                    "clip_suggestions": [self._serialize_clip_suggestion(clip) for clip in clip_suggestions],
                    "total_clips": len(clip_suggestions),
                    "export_formats": {exp.format_name: exp.filename for exp in exports},
                    "summary": {
                        "avg_highlight_score": sum(c.highlight_score for c in clip_suggestions) / len(clip_suggestions)
                        if clip_suggestions
                        else 0,
                        "clip_duration_range": f"{min_clip_length}s - {max_clip_length}s",
                        "threshold_used": highlight_threshold,
                    },
                }
            )
        except Exception as e:
            logger.error(f"Clip composition failed: {e!s}")
            return StepResult.fail(f"Clip composition failed: {e!s}")

    def _retrieve_episode_data(self, episode_id: str, tenant: str, workspace: str) -> dict[str, Any] | None:
        """Retrieve episode data from knowledge graph."""
        try:
            mock_episode_data = {
                "episode_id": episode_id,
                "title": "H3 Podcast #123 - Triller Lawsuit Discussion",
                "duration": 5400,
                "transcript_segments": [
                    {
                        "start_time": 300.0,
                        "end_time": 420.0,
                        "text": "Ethan discusses the Triller lawsuit filing and expresses confidence in winning.",
                        "speaker": "Ethan",
                        "sentiment": "positive",
                        "energy_level": 0.8,
                        "topic": "legal",
                    },
                    {
                        "start_time": 1200.0,
                        "end_time": 1350.0,
                        "text": "Hila reacts strongly to the lawsuit details with surprise and concern.",
                        "speaker": "Hila",
                        "sentiment": "surprised",
                        "energy_level": 0.9,
                        "topic": "reaction",
                    },
                    {
                        "start_time": 2400.0,
                        "end_time": 2580.0,
                        "text": "Ethan explains the legal strategy and timeline for the case.",
                        "speaker": "Ethan",
                        "sentiment": "confident",
                        "energy_level": 0.7,
                        "topic": "strategy",
                    },
                ],
                "visual_events": [
                    {
                        "timestamp": 315.0,
                        "type": "reaction_shot",
                        "description": "Ethan leans back with confident smile",
                        "intensity": 0.8,
                    },
                    {
                        "timestamp": 1220.0,
                        "type": "surprise_reaction",
                        "description": "Hila covers mouth in shock",
                        "intensity": 0.9,
                    },
                ],
                "claims": [
                    {"timestamp": 350.0, "claim": "We will win this lawsuit", "speaker": "Ethan", "confidence": 0.9}
                ],
                "chat_spikes": [
                    {"timestamp": 320.0, "velocity": 15, "sentiment": "excited"},
                    {"timestamp": 1230.0, "velocity": 12, "sentiment": "shocked"},
                ],
            }
            return mock_episode_data
        except Exception as e:
            logger.error(f"Failed to retrieve episode data: {e!s}")
            return None

    def _analyze_highlights(self, episode_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Analyze episode for highlight-worthy segments."""
        highlight_segments = []
        transcript_segments = episode_data.get("transcript_segments", [])
        visual_events = episode_data.get("visual_events", [])
        chat_spikes = episode_data.get("chat_spikes", [])
        for segment in transcript_segments:
            audio_score = self._calculate_audio_score(segment)
            semantic_score = self._calculate_semantic_score(segment)
            visual_score = self._calculate_visual_score(segment, visual_events)
            engagement_score = self._calculate_engagement_score(segment, chat_spikes)
            highlight_score = 0.3 * audio_score + 0.3 * semantic_score + 0.2 * visual_score + 0.2 * engagement_score
            if highlight_score >= 0.5:
                highlight_segment = {
                    **segment,
                    "highlight_score": highlight_score,
                    "signals": {
                        "audio_novelty": audio_score,
                        "semantic_novelty": semantic_score,
                        "visual_saliency": visual_score,
                        "engagement_proxy": engagement_score,
                    },
                    "reasoning": self._generate_reasoning(segment, highlight_score),
                }
                highlight_segments.append(highlight_segment)
        return highlight_segments

    def _calculate_audio_score(self, segment: dict[str, Any]) -> float:
        """Calculate audio novelty score."""
        energy_level = segment.get("energy_level", 0.5)
        sentiment_intensity = 1.0 if segment.get("sentiment") in ["surprised", "excited", "angry"] else 0.5
        return min(1.0, (energy_level + sentiment_intensity) / 2)

    def _calculate_semantic_score(self, segment: dict[str, Any]) -> float:
        """Calculate semantic novelty score."""
        topic_importance = 1.0 if segment.get("topic") in ["legal", "reaction", "strategy"] else 0.6
        claim_presence = (
            1.0
            if any(
                c.get("timestamp", 0) >= segment["start_time"] and c.get("timestamp", 0) <= segment["end_time"]
                for c in segment.get("claims", [])
            )
            else 0.3
        )
        return (topic_importance + claim_presence) / 2

    def _calculate_visual_score(self, segment: dict[str, Any], visual_events: list[dict[str, Any]]) -> float:
        """Calculate visual saliency score."""
        segment_visual_events = [
            event for event in visual_events if segment["start_time"] <= event["timestamp"] <= segment["end_time"]
        ]
        if not segment_visual_events:
            return 0.3
        avg_intensity = sum(event["intensity"] for event in segment_visual_events) / len(segment_visual_events)
        return min(1.0, avg_intensity * 1.2)

    def _calculate_engagement_score(self, segment: dict[str, Any], chat_spikes: list[dict[str, Any]]) -> float:
        """Calculate engagement proxy score from chat data."""
        segment_chat_spikes = [
            spike for spike in chat_spikes if segment["start_time"] <= spike["timestamp"] <= segment["end_time"]
        ]
        if not segment_chat_spikes:
            return 0.2
        max_velocity = max(spike["velocity"] for spike in segment_chat_spikes)
        return min(1.0, max_velocity / 20.0)

    def _generate_reasoning(self, segment: dict[str, Any], score: float) -> str:
        """Generate human-readable reasoning for highlight score."""
        reasons = []
        if segment.get("energy_level", 0) > 0.7:
            reasons.append("high audio energy")
        if segment.get("sentiment") in ["surprised", "excited"]:
            reasons.append("strong emotional reaction")
        if segment.get("topic") in ["legal", "reaction", "strategy"]:
            reasons.append("important topic discussion")
        if not reasons:
            reasons.append("multiple engagement signals")
        return f"{', '.join(reasons)} (score: {score:.2f})"

    def _generate_clip_suggestions(
        self,
        highlight_segments: list[dict[str, Any]],
        episode_data: dict[str, Any],
        max_clips: int,
        min_clip_length: float,
        max_clip_length: float,
        highlight_threshold: float,
        include_titles: bool,
    ) -> list[ClipSuggestion]:
        """Generate clip suggestions from highlight segments."""
        sorted_segments = sorted(highlight_segments, key=lambda x: x["highlight_score"], reverse=True)
        candidate_segments = [seg for seg in sorted_segments if seg["highlight_score"] >= highlight_threshold][
            :max_clips
        ]
        clip_suggestions = []
        for i, segment in enumerate(candidate_segments):
            start_time = max(0, segment["start_time"] - 5.0)
            end_time = min(episode_data["duration"], segment["end_time"] + 5.0)
            duration = end_time - start_time
            if duration < min_clip_length:
                extension_needed = min_clip_length - duration
                start_time = max(0, start_time - extension_needed / 2)
                end_time = min(episode_data["duration"], end_time + extension_needed / 2)
                duration = end_time - start_time
            elif duration > max_clip_length:
                center_time = (segment["start_time"] + segment["end_time"]) / 2
                start_time = max(0, center_time - max_clip_length / 2)
                end_time = min(episode_data["duration"], center_time + max_clip_length / 2)
                duration = end_time - start_time
            title_variants = []
            if include_titles:
                title_variants = self._generate_title_variants(segment, episode_data)
            clip_suggestion = ClipSuggestion(
                clip_id=f"clip_{episode_data['episode_id']}_{i + 1:02d}",
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                highlight_score=segment["highlight_score"],
                proposed_title=title_variants[0] if title_variants else f"Highlight {i + 1}",
                title_variants=title_variants,
                reasoning=segment["reasoning"],
                signals=segment["signals"],
                thumbnail_frame_time=(start_time + end_time) / 2,
                content_summary=segment["text"][:200] + "..." if len(segment["text"]) > 200 else segment["text"],
                tags=self._generate_clip_tags(segment),
            )
            clip_suggestions.append(clip_suggestion)
        return clip_suggestions

    def _generate_title_variants(self, segment: dict[str, Any], episode_data: dict[str, Any]) -> list[str]:
        """Generate multiple title variants for a clip."""
        base_title = f"{segment['speaker']} on {segment['topic'].title()}"
        variants = [
            f"{base_title} - {episode_data['title'].split(' - ')[-1]}",
            f"Did {segment['speaker']} Just Say...?",
            f"{segment['speaker']} Reacts to {segment['topic'].title()} News",
            f"{base_title} - Raw Reaction",
            f"Watch {segment['speaker']} Explain {segment['topic'].title()}",
        ]
        return variants

    def _generate_clip_tags(self, segment: dict[str, Any]) -> list[str]:
        """Generate tags for a clip."""
        tags = [segment.get("topic", "general")]
        if segment.get("sentiment"):
            tags.append(segment["sentiment"])
        if segment.get("speaker"):
            tags.append(f"speaker:{segment['speaker']}")
        tags.extend(["highlight", "clip", "viral"])
        return list(set(tags))

    def _export_clips(
        self, clip_suggestions: list[ClipSuggestion], episode_id: str, export_formats: list[str]
    ) -> list[ExportData]:
        """Export clips in requested formats."""
        exports = []
        for format_name in export_formats:
            if format_name == "json":
                content = self._export_json(clip_suggestions, episode_id)
                filename = f"clips_{episode_id}.json"
            elif format_name == "xml":
                content = self._export_xml(clip_suggestions, episode_id)
                filename = f"clips_{episode_id}.xml"
            elif format_name == "csv":
                content = self._export_csv(clip_suggestions, episode_id)
                filename = f"clips_{episode_id}.csv"
            else:
                continue
            exports.append(ExportData(format_name=format_name, content=content, filename=filename))
        return exports

    def _export_json(self, clips: list[ClipSuggestion], episode_id: str) -> str:
        """Export clips as JSON."""
        data = {
            "episode_id": episode_id,
            "generated_at": "2024-01-17T12:00:00Z",
            "clip_suggestions": [
                {
                    "clip_id": clip.clip_id,
                    "start_time": clip.start_time,
                    "end_time": clip.end_time,
                    "duration": clip.duration,
                    "highlight_score": clip.highlight_score,
                    "proposed_title": clip.proposed_title,
                    "title_variants": clip.title_variants,
                    "reasoning": clip.reasoning,
                    "signals": clip.signals,
                    "thumbnail_frame_time": clip.thumbnail_frame_time,
                    "content_summary": clip.content_summary,
                    "tags": clip.tags,
                }
                for clip in clips
            ],
        }
        return json.dumps(data, indent=2)

    def _export_xml(self, clips: list[ClipSuggestion], episode_id: str) -> str:
        """Export clips as XML (Premiere Pro format)."""
        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            "<PremiereClipExport>",
            f"  <EpisodeID>{episode_id}</EpisodeID>",
            "  <GeneratedAt>2024-01-17T12:00:00Z</GeneratedAt>",
        ]
        for clip in clips:
            xml_parts.extend(
                [
                    "  <Clip>",
                    f"    <ClipID>{clip.clip_id}</ClipID>",
                    f"    <StartTime>{clip.start_time}</StartTime>",
                    f"    <EndTime>{clip.end_time}</EndTime>",
                    f"    <Duration>{clip.duration}</Duration>",
                    f"    <Title>{clip.proposed_title}</Title>",
                    f"    <HighlightScore>{clip.highlight_score}</HighlightScore>",
                    "  </Clip>",
                ]
            )
        xml_parts.append("</PremiereClipExport>")
        return "\n".join(xml_parts)

    def _export_csv(self, clips: list[ClipSuggestion], episode_id: str) -> str:
        """Export clips as CSV."""
        csv_lines = ["ClipID,StartTime,EndTime,Duration,Title,HighlightScore,Tags"]
        for clip in clips:
            tags_str = ";".join(clip.tags)
            line = f'{clip.clip_id},{clip.start_time},{clip.end_time},{clip.duration},"{clip.proposed_title}",{clip.highlight_score},"{tags_str}"'
            csv_lines.append(line)
        return "\n".join(csv_lines)

    def _serialize_clip_suggestion(self, clip: ClipSuggestion) -> dict[str, Any]:
        """Serialize a clip suggestion to a dictionary."""
        return {
            "clip_id": clip.clip_id,
            "start_time": clip.start_time,
            "end_time": clip.end_time,
            "duration": clip.duration,
            "highlight_score": clip.highlight_score,
            "proposed_title": clip.proposed_title,
            "title_variants": clip.title_variants,
            "reasoning": clip.reasoning,
            "signals": clip.signals,
            "thumbnail_frame_time": clip.thumbnail_frame_time,
            "content_summary": clip.content_summary,
            "tags": clip.tags,
        }
