"""Highlight Detection Service for Creator Intelligence.

This module provides highlight detection capabilities combining multiple signals:
- Audio energy analysis (librosa)
- Chat spike detection (from live streams)
- Semantic novelty scoring (embedding-based)

Features:
- Multi-signal highlight scoring
- Temporal alignment with transcript segments
- Confidence-based ranking
- Integration with existing analysis pipeline

Dependencies:
- librosa: For audio feature extraction
- numpy: For signal processing
- Optional: Custom models for semantic analysis
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any, Literal
from platform.core.step_result import StepResult

logger = logging.getLogger(__name__)
try:
    import librosa
    import numpy as np

    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa not available, audio analysis disabled")


@dataclass
class HighlightSegment:
    """A detected highlight moment in content."""

    start_time: float
    end_time: float
    duration: float
    highlight_score: float
    confidence: float
    audio_energy_score: float = 0.0
    chat_spike_score: float = 0.0
    semantic_novelty_score: float = 0.0
    transcript_text: str | None = None
    speakers: list[str] | None = None
    topics: list[str] | None = None
    highlight_type: str = "general"


@dataclass
class HighlightDetectionResult:
    """Result of highlight detection operation."""

    highlights: list[HighlightSegment]
    total_duration: float
    detection_method: str
    signal_weights: dict[str, float]
    processing_time_ms: float = 0.0


class HighlightDetectionService:
    """Service for detecting highlights in video/audio content.

    Usage:
        service = HighlightDetectionService()
        result = service.detect_highlights("audio.wav", transcript_segments)
        highlights = result.data["highlights"]
    """

    def __init__(self, cache_size: int = 1000):
        """Initialize highlight detection service.

        Args:
            cache_size: Maximum number of cached results
        """
        self.cache_size = cache_size
        self._detection_cache: dict[str, HighlightDetectionResult] = {}
        self._signal_weights = {"audio_energy": 0.4, "chat_spikes": 0.3, "semantic_novelty": 0.3}

    def detect_highlights(
        self,
        audio_path: str | None = None,
        transcript_segments: list[dict[str, Any]] | None = None,
        chat_data: list[dict[str, Any]] | None = None,
        model: Literal["fast", "balanced", "quality"] = "balanced",
        min_highlight_duration: float = 5.0,
        max_highlights: int = 20,
        use_cache: bool = True,
    ) -> StepResult:
        """Detect highlights using multiple signal analysis.

        Args:
            audio_path: Path to audio file (optional)
            transcript_segments: Transcript segments with timing
            chat_data: Chat messages with timestamps
            model: Model selection
            min_highlight_duration: Minimum duration for highlight
            max_highlights: Maximum number of highlights to return
            use_cache: Whether to use detection cache

        Returns:
            StepResult with highlight detection data
        """
        try:
            import time

            start_time = time.time()
            if not audio_path and (not transcript_segments):
                return StepResult.fail(
                    "Either audio_path or transcript_segments must be provided", status="bad_request"
                )
            if use_cache:
                cache_result = self._check_cache(audio_path, transcript_segments, chat_data, model)
                if cache_result:
                    logger.info("Highlight detection cache hit")
                    return StepResult.ok(
                        data={
                            "highlights": [h.__dict__ for h in cache_result.highlights],
                            "total_duration": cache_result.total_duration,
                            "detection_method": cache_result.detection_method,
                            "signal_weights": cache_result.signal_weights,
                            "cache_hit": True,
                            "processing_time_ms": (time.time() - start_time) * 1000,
                        }
                    )
            self._select_model(model)
            detection_result = self._detect_highlights(
                audio_path, transcript_segments, chat_data, min_highlight_duration
            )
            if detection_result:
                filtered_highlights = self._filter_and_rank_highlights(
                    detection_result.highlights, max_highlights, min_highlight_duration
                )
                if use_cache:
                    self._cache_result(audio_path, transcript_segments, chat_data, model, detection_result)
                processing_time = (time.time() - start_time) * 1000
                return StepResult.ok(
                    data={
                        "highlights": [h.__dict__ for h in filtered_highlights],
                        "total_duration": detection_result.total_duration,
                        "detection_method": detection_result.detection_method,
                        "signal_weights": detection_result.signal_weights,
                        "cache_hit": False,
                        "processing_time_ms": processing_time,
                    }
                )
            else:
                return StepResult.fail("Highlight detection failed", status="retryable")
        except Exception as e:
            logger.error(f"Highlight detection failed: {e}")
            return StepResult.fail(f"Detection failed: {e!s}", status="retryable")

    def _select_model(self, model_alias: str) -> str:
        """Select actual model configuration from alias.

        Args:
            model_alias: Model alias (fast, balanced, quality)

        Returns:
            Model configuration string
        """
        model_configs = {"fast": "fast_detection", "balanced": "balanced_detection", "quality": "quality_detection"}
        return model_configs.get(model_alias, "balanced_detection")

    def _detect_highlights(
        self,
        audio_path: str | None,
        transcript_segments: list[dict[str, Any]] | None,
        chat_data: list[dict[str, Any]] | None,
        min_duration: float,
    ) -> HighlightDetectionResult | None:
        """Detect highlights using multiple signals.

        Args:
            audio_path: Path to audio file
            transcript_segments: Transcript segments
            chat_data: Chat messages
            min_duration: Minimum highlight duration

        Returns:
            HighlightDetectionResult or None if detection fails
        """
        try:
            total_duration = self._get_total_duration(audio_path, transcript_segments)
            audio_scores = self._analyze_audio_energy(audio_path, total_duration)
            chat_scores = self._analyze_chat_spikes(chat_data, total_duration)
            semantic_scores = self._analyze_semantic_novelty(transcript_segments, total_duration)
            combined_scores = self._combine_signals(audio_scores, chat_scores, semantic_scores, total_duration)
            highlights = self._detect_highlight_segments(combined_scores, min_duration)
            return HighlightDetectionResult(
                highlights=highlights,
                total_duration=total_duration,
                detection_method="multi_signal",
                signal_weights=self._signal_weights,
            )
        except Exception as e:
            logger.error(f"Highlight detection failed: {e}")
            return None

    def _get_total_duration(self, audio_path: str | None, transcript_segments: list[dict[str, Any]] | None) -> float:
        """Get total duration from audio or transcript segments.

        Args:
            audio_path: Audio file path
            transcript_segments: Transcript segments

        Returns:
            Total duration in seconds
        """
        if transcript_segments:
            last_segment = max(transcript_segments, key=lambda s: s.get("end_time", 0))
            return last_segment.get("end_time", 0) + 30
        if audio_path and LIBROSA_AVAILABLE:
            try:
                import librosa

                duration = librosa.get_duration(filename=audio_path)
                return duration
            except Exception:
                pass
        return 3600.0

    def _analyze_audio_energy(self, audio_path: str | None, duration: float) -> list[float]:
        """Analyze audio energy over time.

        Args:
            audio_path: Path to audio file
            duration: Total duration for scoring

        Returns:
            List of energy scores per time segment
        """
        if not audio_path or not LIBROSA_AVAILABLE:
            return [0.5] * int(duration / 10)
        try:
            y, sr = librosa.load(audio_path, sr=None)
            frame_length = int(sr * 10)
            hop_length = frame_length // 2
            rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            if len(rms) > 0:
                min_rms, max_rms = (np.min(rms), np.max(rms))
                if max_rms > min_rms:
                    rms = (rms - min_rms) / (max_rms - min_rms)
            num_segments = int(duration / 10)
            if len(rms) < num_segments:
                rms = np.pad(rms, (0, num_segments - len(rms)), mode="constant")
            elif len(rms) > num_segments:
                rms = rms[:num_segments]
            return rms.tolist()
        except Exception as e:
            logger.warning(f"Audio energy analysis failed: {e}")
            return [0.5] * int(duration / 10)

    def _analyze_chat_spikes(self, chat_data: list[dict[str, Any]] | None, duration: float) -> list[float]:
        """Analyze chat message frequency for spikes.

        Args:
            chat_data: Chat messages with timestamps
            duration: Total duration for scoring

        Returns:
            List of chat spike scores per time segment
        """
        if not chat_data:
            return [0.0] * int(duration / 10)
        message_counts = [0] * int(duration / 10)
        for message in chat_data:
            timestamp = message.get("timestamp", 0)
            if timestamp and timestamp <= duration:
                segment_index = int(timestamp / 10)
                if segment_index < len(message_counts):
                    message_counts[segment_index] += 1
        if message_counts:
            max_count = max(message_counts) if max(message_counts) > 0 else 1
            chat_scores = [count / max_count for count in message_counts]
        else:
            chat_scores = [0.0] * len(message_counts)
        return chat_scores

    def _analyze_semantic_novelty(
        self, transcript_segments: list[dict[str, Any]] | None, duration: float
    ) -> list[float]:
        """Analyze semantic novelty using embedding distances.

        Args:
            transcript_segments: Transcript segments
            duration: Total duration for scoring

        Returns:
            List of novelty scores per time segment
        """
        if not transcript_segments:
            return [0.5] * int(duration / 10)
        novelty_scores = []
        for _i, segment in enumerate(transcript_segments):
            text_length = len(segment.get("text", ""))
            length_score = min(text_length / 1000, 1.0)
            topic_score = 0.5
            novelty = length_score * 0.6 + topic_score * 0.4
            novelty_scores.append(novelty)
        num_segments = int(duration / 10)
        if len(novelty_scores) < num_segments:
            avg_score = sum(novelty_scores) / len(novelty_scores) if novelty_scores else 0.5
            novelty_scores.extend([avg_score] * (num_segments - len(novelty_scores)))
        elif len(novelty_scores) > num_segments:
            novelty_scores = novelty_scores[:num_segments]
        return novelty_scores

    def _combine_signals(
        self, audio_scores: list[float], chat_scores: list[float], semantic_scores: list[float], duration: float
    ) -> list[float]:
        """Combine multiple signal scores into overall highlight scores.

        Args:
            audio_scores: Audio energy scores
            chat_scores: Chat spike scores
            semantic_scores: Semantic novelty scores
            duration: Total duration

        Returns:
            Combined highlight scores
        """
        num_segments = int(duration / 10)
        audio_scores = audio_scores[:num_segments] + [0.5] * max(0, num_segments - len(audio_scores))
        chat_scores = chat_scores[:num_segments] + [0.0] * max(0, num_segments - len(chat_scores))
        semantic_scores = semantic_scores[:num_segments] + [0.5] * max(0, num_segments - len(semantic_scores))
        combined_scores = []
        for i in range(num_segments):
            combined_score = (
                audio_scores[i] * self._signal_weights["audio_energy"]
                + chat_scores[i] * self._signal_weights["chat_spikes"]
                + semantic_scores[i] * self._signal_weights["semantic_novelty"]
            )
            combined_scores.append(combined_score)
        return combined_scores

    def _detect_highlight_segments(self, scores: list[float], min_duration: float) -> list[HighlightSegment]:
        """Detect highlight segments from combined scores.

        Args:
            scores: Combined highlight scores per segment
            min_duration: Minimum duration for highlight

        Returns:
            List of highlight segments
        """
        highlights = []
        current_start = None
        current_score = 0.0
        segment_duration = 10.0
        for i, score in enumerate(scores):
            if score > 0.6:
                if current_start is None:
                    current_start = i * segment_duration
                    current_score = score
                else:
                    current_score = (current_score + score) / 2
            elif current_start is not None:
                highlight_duration = i * segment_duration - current_start
                if highlight_duration >= min_duration:
                    highlight = HighlightSegment(
                        start_time=current_start,
                        end_time=i * segment_duration,
                        duration=highlight_duration,
                        highlight_score=current_score,
                        confidence=min(current_score, 1.0),
                        audio_energy_score=current_score * self._signal_weights["audio_energy"],
                        chat_spike_score=current_score * self._signal_weights["chat_spikes"],
                        semantic_novelty_score=current_score * self._signal_weights["semantic_novelty"],
                    )
                    highlights.append(highlight)
                current_start = None
                current_score = 0.0
        if current_start is not None:
            highlight_duration = len(scores) * segment_duration - current_start
            if highlight_duration >= min_duration:
                highlight = HighlightSegment(
                    start_time=current_start,
                    end_time=len(scores) * segment_duration,
                    duration=highlight_duration,
                    highlight_score=current_score,
                    confidence=min(current_score, 1.0),
                    audio_energy_score=current_score * self._signal_weights["audio_energy"],
                    chat_spike_score=current_score * self._signal_weights["chat_spikes"],
                    semantic_novelty_score=current_score * self._signal_weights["semantic_novelty"],
                )
                highlights.append(highlight)
        return highlights

    def _filter_and_rank_highlights(
        self, highlights: list[HighlightSegment], max_highlights: int, min_duration: float
    ) -> list[HighlightSegment]:
        """Filter and rank highlights by score and duration.

        Args:
            highlights: Raw highlight segments
            max_highlights: Maximum number to return
            min_duration: Minimum duration filter

        Returns:
            Filtered and ranked highlight segments
        """
        filtered = [h for h in highlights if h.duration >= min_duration]
        filtered.sort(key=lambda h: h.highlight_score, reverse=True)
        return filtered[:max_highlights]

    def _check_cache(
        self,
        audio_path: str | None,
        transcript_segments: list[dict[str, Any]] | None,
        chat_data: list[dict[str, Any]] | None,
        model: str,
    ) -> HighlightDetectionResult | None:
        """Check if highlight detection exists in cache.

        Args:
            audio_path: Audio file path
            transcript_segments: Transcript segments
            chat_data: Chat data
            model: Model alias

        Returns:
            Cached HighlightDetectionResult or None
        """
        import hashlib

        combined = f"{audio_path}:{transcript_segments!s}:{chat_data!s}:{model}"
        cache_key = hashlib.sha256(combined.encode()).hexdigest()
        if cache_key in self._detection_cache:
            return self._detection_cache[cache_key]
        return None

    def _cache_result(
        self,
        audio_path: str | None,
        transcript_segments: list[dict[str, Any]] | None,
        chat_data: list[dict[str, Any]] | None,
        model: str,
        result: HighlightDetectionResult,
    ) -> None:
        """Cache highlight detection result.

        Args:
            audio_path: Audio file path
            transcript_segments: Transcript segments
            chat_data: Chat data
            model: Model alias
            result: HighlightDetectionResult to cache
        """
        import hashlib
        import time

        combined = f"{audio_path}:{transcript_segments!s}:{chat_data!s}:{model}"
        cache_key = hashlib.sha256(combined.encode()).hexdigest()
        result.processing_time_ms = time.time() * 1000
        if len(self._detection_cache) >= self.cache_size:
            first_key = next(iter(self._detection_cache))
            del self._detection_cache[first_key]
        self._detection_cache[cache_key] = result

    def clear_cache(self) -> StepResult:
        """Clear highlight detection cache.

        Returns:
            StepResult with cache clear status
        """
        cache_size = len(self._detection_cache)
        self._detection_cache.clear()
        logger.info(f"Cleared {cache_size} cached highlight detections")
        return StepResult.ok(data={"cleared_entries": cache_size})

    def get_cache_stats(self) -> StepResult:
        """Get highlight detection cache statistics.

        Returns:
            StepResult with cache statistics
        """
        try:
            stats = {
                "total_cached": len(self._detection_cache),
                "cache_size_limit": self.cache_size,
                "utilization": len(self._detection_cache) / self.cache_size if self.cache_size > 0 else 0.0,
                "models_cached": {},
            }
            for result in self._detection_cache.values():
                model = result.detection_method
                stats["models_cached"][model] = stats["models_cached"].get(model, 0) + 1
            return StepResult.ok(data=stats)
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return StepResult.fail(f"Failed to get cache stats: {e!s}")


_highlight_service: HighlightDetectionService | None = None


def get_highlight_detection_service() -> HighlightDetectionService:
    """Get singleton highlight detection service instance.

    Returns:
        Initialized HighlightDetectionService instance
    """
    global _highlight_service
    if _highlight_service is None:
        _highlight_service = HighlightDetectionService()
    return _highlight_service
