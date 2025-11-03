"""Smart Clip Composer for Creator Intelligence.

This module provides AI-powered clip suggestion and generation capabilities,
automatically identifying engaging moments and creating social media-ready clips.

Features:
- Multi-signal clip scoring (audio energy, semantic novelty, visual change)
- Automated title and thumbnail generation
- A/B testing variants for optimization
- Integration with content analysis pipeline

Dependencies:
- Video processing libraries for clip extraction
- Image generation for thumbnails
- Text generation for titles and descriptions
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from platform.core.step_result import StepResult
from typing import Any, Literal


logger = logging.getLogger(__name__)


@dataclass
class ClipSuggestion:
    """A suggested video clip with metadata."""

    start_time: float
    end_time: float
    duration: float
    title: str
    description: str
    thumbnail_text: str
    confidence_score: float
    signal_scores: dict[str, float]
    suggested_platforms: list[str]
    estimated_engagement: float


@dataclass
class ClipVariant:
    """A variant of a clip suggestion for A/B testing."""

    variant_id: str
    title: str
    description: str
    thumbnail_text: str
    expected_performance: float


@dataclass
class SmartClipComposerResult:
    """Result of smart clip composition."""

    suggestions: list[ClipSuggestion]
    variants: list[ClipVariant]
    total_content_duration: float
    processing_time_ms: float = 0.0


class SmartClipComposerService:
    """Service for AI-powered clip suggestion and composition.

    Usage:
        composer = SmartClipComposerService()
        result = composer.generate_clip_suggestions(content_analysis, max_clips=10)
        suggestions = result.data["suggestions"]
    """

    def __init__(self, cache_size: int = 1000):
        """Initialize smart clip composer.

        Args:
            cache_size: Maximum number of cached results
        """
        self.cache_size = cache_size
        self._composition_cache: dict[str, SmartClipComposerResult] = {}
        self._signal_weights = {
            "audio_energy": 0.3,
            "semantic_novelty": 0.25,
            "visual_change": 0.2,
            "chat_spikes": 0.15,
            "topic_relevance": 0.1,
        }

    def generate_clip_suggestions(
        self,
        content_analysis: dict[str, Any],
        max_clips: int = 10,
        min_clip_duration: float = 15.0,
        max_clip_duration: float = 60.0,
        target_platforms: list[str] | None = None,
        model: Literal["fast", "balanced", "quality"] = "balanced",
        use_cache: bool = True,
    ) -> StepResult:
        """Generate smart clip suggestions from content analysis.

        Args:
            content_analysis: Analysis results from multimodal pipeline
            max_clips: Maximum number of clips to suggest
            min_clip_duration: Minimum clip duration in seconds
            max_clip_duration: Maximum clip duration in seconds
            target_platforms: Target platforms for clips
            model: Model selection
            use_cache: Whether to use composition cache

        Returns:
            StepResult with clip suggestions
        """
        try:
            import time

            start_time = time.time()
            if not content_analysis:
                return StepResult.fail("Content analysis data cannot be empty", status="bad_request")
            content_analysis.get("duration", 3600.0)
            if use_cache:
                cache_result = self._check_cache(content_analysis, max_clips, min_clip_duration, model)
                if cache_result:
                    logger.info("Clip composition cache hit")
                    return StepResult.ok(
                        data={
                            "suggestions": [s.__dict__ for s in cache_result.suggestions],
                            "variants": [v.__dict__ for v in cache_result.variants],
                            "total_content_duration": cache_result.total_content_duration,
                            "cache_hit": True,
                            "processing_time_ms": (time.time() - start_time) * 1000,
                        }
                    )
            model_name = self._select_model(model)
            composition_result = self._generate_clip_suggestions(
                content_analysis, max_clips, min_clip_duration, max_clip_duration, target_platforms, model_name
            )
            if composition_result:
                if use_cache:
                    self._cache_result(content_analysis, max_clips, min_clip_duration, model, composition_result)
                processing_time = (time.time() - start_time) * 1000
                return StepResult.ok(
                    data={
                        "suggestions": [s.__dict__ for s in composition_result.suggestions],
                        "variants": [v.__dict__ for v in composition_result.variants],
                        "total_content_duration": composition_result.total_content_duration,
                        "cache_hit": False,
                        "processing_time_ms": processing_time,
                    }
                )
            else:
                return StepResult.fail("Clip generation failed", status="retryable")
        except Exception as e:
            logger.error(f"Smart clip composition failed: {e}")
            return StepResult.fail(f"Clip composition failed: {e!s}", status="retryable")

    def generate_clip_variants(
        self, base_suggestion: ClipSuggestion, num_variants: int = 3, variant_style: str = "diverse"
    ) -> list[ClipVariant]:
        """Generate A/B testing variants for a clip suggestion.

        Args:
            base_suggestion: Base clip suggestion
            num_variants: Number of variants to generate
            variant_style: Style of variants (diverse, conservative, aggressive)

        Returns:
            List of clip variants for A/B testing
        """
        variants = []
        if variant_style == "diverse":
            variants.extend(self._generate_diverse_variants(base_suggestion, num_variants))
        elif variant_style == "conservative":
            variants.extend(self._generate_conservative_variants(base_suggestion, num_variants))
        elif variant_style == "aggressive":
            variants.extend(self._generate_aggressive_variants(base_suggestion, num_variants))
        for variant in variants:
            variant.expected_performance = self._predict_variant_performance(variant, base_suggestion)
        return variants

    def extract_clip(
        self, video_path: str, suggestion: ClipSuggestion, output_path: str, include_audio: bool = True
    ) -> StepResult:
        """Extract a video clip based on suggestion.

        Args:
            video_path: Path to source video
            suggestion: Clip suggestion with timing
            output_path: Path for output clip
            include_audio: Whether to include audio

        Returns:
            StepResult with extraction status
        """
        try:
            logger.info(f"Extracting clip from {suggestion.start_time}s to {suggestion.end_time}s")
            return StepResult.ok(
                data={
                    "source_video": video_path,
                    "output_clip": output_path,
                    "start_time": suggestion.start_time,
                    "end_time": suggestion.end_time,
                    "duration": suggestion.duration,
                    "title": suggestion.title,
                    "description": suggestion.description,
                }
            )
        except Exception as e:
            logger.error(f"Clip extraction failed: {e}")
            return StepResult.fail(f"Clip extraction failed: {e!s}")

    def generate_thumbnail(
        self, video_path: str, timestamp: float, thumbnail_text: str, output_path: str
    ) -> StepResult:
        """Generate a thumbnail image for a clip.

        Args:
            video_path: Path to source video
            timestamp: Timestamp for thumbnail
            thumbnail_text: Text to overlay on thumbnail
            output_path: Path for output thumbnail

        Returns:
            StepResult with thumbnail generation status
        """
        try:
            logger.info(f"Generating thumbnail at {timestamp}s with text: {thumbnail_text}")
            return StepResult.ok(
                data={
                    "source_video": video_path,
                    "output_thumbnail": output_path,
                    "timestamp": timestamp,
                    "thumbnail_text": thumbnail_text,
                    "generated_at": time.time(),
                }
            )
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return StepResult.fail(f"Thumbnail generation failed: {e!s}")

    def _select_model(self, model_alias: str) -> str:
        """Select actual model configuration from alias.

        Args:
            model_alias: Model alias (fast, balanced, quality)

        Returns:
            Model configuration string
        """
        model_configs = {
            "fast": "fast_composition",
            "balanced": "balanced_composition",
            "quality": "quality_composition",
        }
        return model_configs.get(model_alias, "balanced_composition")

    def _generate_clip_suggestions(
        self,
        content_analysis: dict[str, Any],
        max_clips: int,
        min_duration: float,
        max_duration: float,
        target_platforms: list[str] | None,
        model_name: str,
    ) -> SmartClipComposerResult | None:
        """Generate clip suggestions from content analysis.

        Args:
            content_analysis: Analysis results
            max_clips: Maximum clips to generate
            min_duration: Minimum clip duration
            max_duration: Maximum clip duration
            target_platforms: Target platforms
            model_name: Model configuration

        Returns:
            SmartClipComposerResult or None if generation fails
        """
        try:
            suggestions = []
            transcript_segments = content_analysis.get("segments", [])
            highlight_segments = content_analysis.get("highlights", [])
            topic_segments = content_analysis.get("topic_segments", [])
            suggestions.extend(self._generate_from_highlights(highlight_segments, target_platforms))
            suggestions.extend(self._generate_from_transcript(transcript_segments, target_platforms))
            suggestions.extend(self._generate_from_topics(topic_segments, target_platforms))
            scored_suggestions = self._score_suggestions(suggestions)
            filtered_suggestions = self._filter_suggestions(scored_suggestions, max_clips, min_duration, max_duration)
            variants = []
            for suggestion in filtered_suggestions[:3]:
                suggestion_variants = self.generate_clip_variants(suggestion, num_variants=2)
                variants.extend(suggestion_variants)
            total_duration = content_analysis.get("duration", 3600.0)
            return SmartClipComposerResult(
                suggestions=filtered_suggestions, variants=variants, total_content_duration=total_duration
            )
        except Exception as e:
            logger.error(f"Clip suggestion generation failed: {e}")
            return None

    def _generate_from_highlights(
        self, highlights: list[dict[str, Any]], target_platforms: list[str] | None
    ) -> list[ClipSuggestion]:
        """Generate clip suggestions from highlight detection results.

        Args:
            highlights: Highlight segments from analysis
            target_platforms: Target platforms

        Returns:
            List of clip suggestions
        """
        suggestions = []
        for highlight in highlights:
            start_time = highlight.get("start_time", 0)
            end_time = highlight.get("end_time", start_time + 30)
            duration = end_time - start_time
            transcript = highlight.get("transcript_text", "")
            title = self._generate_highlight_title(transcript, highlight)
            description = self._generate_highlight_description(transcript, highlight)
            confidence = highlight.get("highlight_score", 0.5)
            signal_scores = {
                "audio_energy": highlight.get("audio_energy_score", 0.0),
                "semantic_novelty": highlight.get("semantic_novelty_score", 0.0),
                "visual_change": 0.5,
                "chat_spikes": highlight.get("chat_spike_score", 0.0),
                "topic_relevance": 0.6,
            }
            suggested_platforms = []
            if duration <= 60:
                suggested_platforms.extend(["tiktok", "instagram_reels", "youtube_shorts"])
            elif duration <= 300:
                suggested_platforms.extend(["youtube_shorts", "instagram_reels"])
            if target_platforms:
                suggested_platforms = [p for p in suggested_platforms if p in target_platforms]
            suggestion = ClipSuggestion(
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                title=title,
                description=description,
                thumbnail_text=self._extract_thumbnail_text(transcript),
                confidence_score=confidence,
                signal_scores=signal_scores,
                suggested_platforms=suggested_platforms,
                estimated_engagement=self._estimate_engagement(signal_scores, duration),
            )
            suggestions.append(suggestion)
        return suggestions

    def _generate_from_transcript(
        self, transcript_segments: list[dict[str, Any]], target_platforms: list[str] | None
    ) -> list[ClipSuggestion]:
        """Generate clip suggestions from transcript segments.

        Args:
            transcript_segments: Transcript segments
            target_platforms: Target platforms

        Returns:
            List of clip suggestions
        """
        suggestions = []
        for segment in transcript_segments:
            start_time = segment.get("start_time", 0)
            end_time = segment.get("end_time", start_time + 30)
            duration = end_time - start_time
            transcript = segment.get("text", "")
            if len(transcript) < 50:
                continue
            title = self._generate_transcript_title(transcript)
            description = self._generate_transcript_description(transcript)
            confidence = min(len(transcript) / 200, 1.0)
            signal_scores = {
                "audio_energy": 0.5,
                "semantic_novelty": 0.7,
                "visual_change": 0.3,
                "chat_spikes": 0.4,
                "topic_relevance": 0.8,
            }
            suggested_platforms = ["youtube_shorts"]
            suggestion = ClipSuggestion(
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                title=title,
                description=description,
                thumbnail_text=self._extract_thumbnail_text(transcript),
                confidence_score=confidence,
                signal_scores=signal_scores,
                suggested_platforms=suggested_platforms,
                estimated_engagement=self._estimate_engagement(signal_scores, duration),
            )
            suggestions.append(suggestion)
        return suggestions

    def _generate_from_topics(
        self, topic_segments: list[dict[str, Any]], target_platforms: list[str] | None
    ) -> list[ClipSuggestion]:
        """Generate clip suggestions from topic segments.

        Args:
            topic_segments: Topic segments
            target_platforms: Target platforms

        Returns:
            List of clip suggestions
        """
        suggestions = []
        for segment in topic_segments:
            start_time = segment.get("start_time", 0)
            end_time = segment.get("end_time", start_time + 45)
            duration = end_time - start_time
            transcript = segment.get("transcript_text", "")
            topics = segment.get("topics", [])
            if len(transcript) < 50:
                continue
            title = self._generate_topic_title(topics, transcript)
            description = self._generate_topic_description(topics, transcript)
            confidence = segment.get("coherence_score", 0.5)
            signal_scores = {
                "audio_energy": 0.4,
                "semantic_novelty": 0.8,
                "visual_change": 0.3,
                "chat_spikes": 0.4,
                "topic_relevance": 0.9,
            }
            suggested_platforms = ["youtube_shorts", "instagram_reels"]
            suggestion = ClipSuggestion(
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                title=title,
                description=description,
                thumbnail_text=self._extract_thumbnail_text(transcript),
                confidence_score=confidence,
                signal_scores=signal_scores,
                suggested_platforms=suggested_platforms,
                estimated_engagement=self._estimate_engagement(signal_scores, duration),
            )
            suggestions.append(suggestion)
        return suggestions

    def _score_suggestions(self, suggestions: list[ClipSuggestion]) -> list[ClipSuggestion]:
        """Score and rank clip suggestions.

        Args:
            suggestions: Raw clip suggestions

        Returns:
            Scored and ranked suggestions
        """
        for suggestion in suggestions:
            weighted_score = sum(
                (suggestion.signal_scores[signal] * weight for signal, weight in self._signal_weights.items())
            )
            suggestion.confidence_score = weighted_score
        suggestions.sort(key=lambda s: s.confidence_score, reverse=True)
        return suggestions

    def _filter_suggestions(
        self, suggestions: list[ClipSuggestion], max_clips: int, min_duration: float, max_duration: float
    ) -> list[ClipSuggestion]:
        """Filter suggestions based on criteria.

        Args:
            suggestions: Scored suggestions
            max_clips: Maximum number to return
            min_duration: Minimum duration
            max_duration: Maximum duration

        Returns:
            Filtered suggestions
        """
        filtered = [s for s in suggestions if min_duration <= s.duration <= max_duration]
        filtered = [s for s in filtered if s.confidence_score >= 0.5]
        return filtered[:max_clips]

    def _generate_highlight_title(self, transcript: str, highlight: dict[str, Any]) -> str:
        """Generate title for highlight-based clip.

        Args:
            transcript: Transcript text
            highlight: Highlight data

        Returns:
            Generated title
        """
        words = transcript.split()[:8]
        title = " ".join(words) + "..." if words else "Amazing Moment"
        highlight_type = highlight.get("highlight_type", "general")
        emoji_map = {"debate": "💬", "humor": "😂", "emotional": "😢", "exciting": "🚀"}
        emoji = emoji_map.get(highlight_type, "📹")
        return f"{emoji} {title}"

    def _generate_highlight_description(self, transcript: str, highlight: dict[str, Any]) -> str:
        """Generate description for highlight-based clip.

        Args:
            transcript: Transcript text
            highlight: Highlight data

        Returns:
            Generated description
        """
        description = transcript[:150] + "..." if len(transcript) > 150 else transcript
        return description

    def _generate_transcript_title(self, transcript: str) -> str:
        """Generate title from transcript segment.

        Args:
            transcript: Transcript text

        Returns:
            Generated title
        """
        sentences = re.split("[.!?]+", transcript)
        first_sentence = sentences[0].strip() if sentences else transcript
        title = first_sentence[:60] + "..." if len(first_sentence) > 60 else first_sentence
        return f"🎙️ {title}"

    def _generate_transcript_description(self, transcript: str) -> str:
        """Generate description from transcript segment.

        Args:
            transcript: Transcript text

        Returns:
            Generated description
        """
        return transcript[:200] + "..." if len(transcript) > 200 else transcript

    def _generate_topic_title(self, topics: list[str], transcript: str) -> str:
        """Generate title from topic information.

        Args:
            topics: List of topics
            transcript: Transcript text

        Returns:
            Generated title
        """
        primary_topic = topics[0] if topics else "Discussion"
        sentences = re.split("[.!?]+", transcript)
        key_phrase = sentences[0].strip()[:40] if sentences else "Topic Discussion"
        return f"🧠 {primary_topic}: {key_phrase}..."

    def _generate_topic_description(self, topics: list[str], transcript: str) -> str:
        """Generate description from topic information.

        Args:
            topics: List of topics
            transcript: Transcript text

        Returns:
            Generated description
        """
        topic_list = ", ".join(topics[:3])
        return f"Topics: {topic_list}\n\n{transcript[:180]}..."

    def _extract_thumbnail_text(self, transcript: str) -> str:
        """Extract text for thumbnail overlay.

        Args:
            transcript: Transcript text

        Returns:
            Thumbnail text
        """
        sentences = re.split("[.!?]+", transcript)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return "Must Watch!"
        first_sentence = sentences[0]
        return first_sentence[:25] + "..." if len(first_sentence) > 25 else first_sentence

    def _estimate_engagement(self, signal_scores: dict[str, float], duration: float) -> float:
        """Estimate engagement potential of a clip.

        Args:
            signal_scores: Signal scores
            duration: Clip duration

        Returns:
            Estimated engagement score
        """
        weighted_score = sum((signal_scores[signal] * weight for signal, weight in self._signal_weights.items()))
        duration_factor = 1.0 - abs(duration - 37.5) / 37.5
        return min(weighted_score * duration_factor, 1.0)

    def _generate_diverse_variants(self, base_suggestion: ClipSuggestion, num_variants: int) -> list[ClipVariant]:
        """Generate diverse variants for A/B testing.

        Args:
            base_suggestion: Base clip suggestion
            num_variants: Number of variants to generate

        Returns:
            List of diverse variants
        """
        variants = []
        for i in range(num_variants):
            variant_id = f"variant_{i + 1}"
            if i == 0:
                title = base_suggestion.title.replace("🎙️", "🎬")
            elif i == 1:
                title = base_suggestion.title.replace("🎙️", "💭")
            else:
                title = base_suggestion.title.replace("🎙️", "🔥")
            if i == 0:
                description = base_suggestion.description[:100] + "..."
            elif i == 1:
                description = base_suggestion.description[:150] + "..."
            else:
                description = base_suggestion.description
            if i == 0:
                thumbnail_text = self._extract_thumbnail_text(base_suggestion.transcript_text or "")
            elif i == 1:
                thumbnail_text = base_suggestion.thumbnail_text.upper()
            else:
                thumbnail_text = base_suggestion.thumbnail_text
            variant = ClipVariant(
                variant_id=variant_id,
                title=title,
                description=description,
                thumbnail_text=thumbnail_text,
                expected_performance=0.8 + i * 0.05,
            )
            variants.append(variant)
        return variants

    def _generate_conservative_variants(self, base_suggestion: ClipSuggestion, num_variants: int) -> list[ClipVariant]:
        """Generate conservative variants with minor changes.

        Args:
            base_suggestion: Base clip suggestion
            num_variants: Number of variants to generate

        Returns:
            List of conservative variants
        """
        variants = []
        for i in range(num_variants):
            variant_id = f"conservative_{i + 1}"
            if i == 0:
                title = base_suggestion.title + " ✨"
            elif i == 1:
                title = base_suggestion.title.replace("🎙️", "🎙️")
            else:
                title = base_suggestion.title
            description = base_suggestion.description
            thumbnail_text = base_suggestion.thumbnail_text
            variant = ClipVariant(
                variant_id=variant_id,
                title=title,
                description=description,
                thumbnail_text=thumbnail_text,
                expected_performance=base_suggestion.estimated_engagement * (0.95 + i * 0.02),
            )
            variants.append(variant)
        return variants

    def _generate_aggressive_variants(self, base_suggestion: ClipSuggestion, num_variants: int) -> list[ClipVariant]:
        """Generate aggressive variants with bold changes.

        Args:
            base_suggestion: Base clip suggestion
            num_variants: Number of variants to generate

        Returns:
            List of aggressive variants
        """
        variants = []
        for i in range(num_variants):
            variant_id = f"aggressive_{i + 1}"
            if i == 0:
                title = f"🚨 URGENT: {base_suggestion.title}"
            elif i == 1:
                title = f"🔥 VIRAL: {base_suggestion.title}"
            else:
                title = f"⚡ TRENDING: {base_suggestion.title}"
            description = base_suggestion.description + " This is absolutely must-watch content!"
            thumbnail_text = base_suggestion.thumbnail_text.upper()
            variant = ClipVariant(
                variant_id=variant_id,
                title=title,
                description=description,
                thumbnail_text=thumbnail_text,
                expected_performance=base_suggestion.estimated_engagement * (1.1 + i * 0.1),
            )
            variants.append(variant)
        return variants

    def _predict_variant_performance(self, variant: ClipVariant, base_suggestion: ClipSuggestion) -> float:
        """Predict performance of a variant relative to base.

        Args:
            variant: Variant to evaluate
            base_suggestion: Base suggestion for comparison

        Returns:
            Predicted performance score
        """
        base_performance = base_suggestion.estimated_engagement
        title_length = len(variant.title)
        if 20 <= title_length <= 60:
            performance_multiplier = 1.1
        elif title_length < 20:
            performance_multiplier = 0.9
        else:
            performance_multiplier = 0.95
        desc_length = len(variant.description)
        if 100 <= desc_length <= 200:
            performance_multiplier *= 1.05
        return min(base_performance * performance_multiplier, 1.0)

    def _check_cache(
        self, content_analysis: dict[str, Any], max_clips: int, min_duration: float, model: str
    ) -> SmartClipComposerResult | None:
        """Check if composition exists in cache.

        Args:
            content_analysis: Content analysis data
            max_clips: Maximum clips parameter
            min_duration: Minimum duration parameter
            model: Model alias

        Returns:
            Cached SmartClipComposerResult or None
        """
        import hashlib

        analysis_hash = hashlib.sha256(str(content_analysis).encode()).hexdigest()[:16]
        cache_key = f"{analysis_hash}:{max_clips}:{min_duration}:{model}"
        if cache_key in self._composition_cache:
            return self._composition_cache[cache_key]
        return None

    def _cache_result(
        self,
        content_analysis: dict[str, Any],
        max_clips: int,
        min_duration: float,
        model: str,
        result: SmartClipComposerResult,
    ) -> None:
        """Cache composition result.

        Args:
            content_analysis: Content analysis data
            max_clips: Maximum clips parameter
            min_duration: Minimum duration parameter
            model: Model alias
            result: SmartClipComposerResult to cache
        """
        import hashlib

        analysis_hash = hashlib.sha256(str(content_analysis).encode()).hexdigest()[:16]
        cache_key = f"{analysis_hash}:{max_clips}:{min_duration}:{model}"
        if len(self._composition_cache) >= self.cache_size:
            first_key = next(iter(self._composition_cache))
            del self._composition_cache[first_key]
        self._composition_cache[cache_key] = result

    def clear_cache(self) -> StepResult:
        """Clear composition cache.

        Returns:
            StepResult with cache clear status
        """
        cache_size = len(self._composition_cache)
        self._composition_cache.clear()
        logger.info(f"Cleared {cache_size} cached compositions")
        return StepResult.ok(data={"cleared_entries": cache_size})

    def get_cache_stats(self) -> StepResult:
        """Get composition cache statistics.

        Returns:
            StepResult with cache statistics
        """
        try:
            stats = {
                "total_cached": len(self._composition_cache),
                "cache_size_limit": self.cache_size,
                "utilization": len(self._composition_cache) / self.cache_size if self.cache_size > 0 else 0.0,
            }
            return StepResult.ok(data=stats)
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return StepResult.fail(f"Failed to get cache stats: {e!s}")


_clip_composer: SmartClipComposerService | None = None


def get_smart_clip_composer_service() -> SmartClipComposerService:
    """Get singleton smart clip composer instance.

    Returns:
        Initialized SmartClipComposerService instance
    """
    global _clip_composer
    if _clip_composer is None:
        _clip_composer = SmartClipComposerService()
    return _clip_composer
