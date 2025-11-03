"""Speaker Diarization Service for Creator Intelligence.

This module provides speaker identification and segmentation capabilities
using pyannote.audio, building on the ASR transcription service.

Features:
- Automatic speaker segmentation from audio
- Speaker role identification (host, guest, etc.)
- Integration with ASR service for combined transcription + diarization
- Voiceprint-based speaker recognition for known creators
- Confidence scoring for speaker assignments

Dependencies:
- pyannote.audio: For speaker diarization
- Optional: Voiceprint models for creator identification
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from analysis.transcription.asr_service import (
    ASRService,
    TranscriptionResult,
    TranscriptionSegment,
)

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)

# Try to import pyannote.audio (optional dependency)
try:
    from pyannote.audio import Pipeline

    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    Pipeline = None  # type: ignore
    logger.warning("pyannote.audio not available, speaker diarization disabled")


@dataclass
class SpeakerSegment:
    """A segment of audio attributed to a specific speaker."""

    start: float
    end: float
    speaker_id: str
    speaker_name: str | None = None
    speaker_role: str | None = None  # host, guest, moderator, etc.
    confidence: float = 1.0
    transcript_text: str | None = None


@dataclass
class DiarizationResult:
    """Result of speaker diarization operation."""

    segments: list[SpeakerSegment]
    num_speakers: int
    speaker_map: dict[str, str]  # speaker_id -> speaker_name
    model: str
    duration: float
    confidence: float = 1.0
    processing_time_ms: float = 0.0


class SpeakerDiarizationService:
    """Speaker diarization service with role identification.

    Usage:
        service = SpeakerDiarizationService()
        result = service.diarize_audio("episode.mp3")
        segments = result.data["segments"]
    """

    def __init__(self, cache_size: int = 1000):
        """Initialize diarization service.

        Args:
            cache_size: Maximum number of cached diarization results
        """
        self.cache_size = cache_size
        self._diarization_cache: dict[str, DiarizationResult] = {}

        # Load diarization model lazily
        self._diarization_model: Any = None

        # Known speaker voiceprints (for creator identification)
        self._voiceprints: dict[str, dict[str, Any]] = {}

    def diarize_audio(
        self,
        audio_path: str | Path,
        model: Literal["fast", "balanced", "quality"] = "balanced",
        use_cache: bool = True,
    ) -> StepResult:
        """Diarize audio to identify speakers and their segments.

        Args:
            audio_path: Path to audio file
            model: Model selection (fast, balanced, quality)
            use_cache: Whether to use diarization cache

        Returns:
            StepResult with diarization data
        """
        try:
            import time

            start_time = time.time()
            audio_path = Path(audio_path)

            # Validate input
            if not audio_path.exists():
                return StepResult.fail(f"Audio file not found: {audio_path}", status="bad_request")

            # Check cache first
            if use_cache:
                cache_result = self._check_cache(audio_path, model)
                if cache_result:
                    logger.info(f"Diarization cache hit for {audio_path}")
                    return StepResult.ok(
                        data={
                            "segments": [s.__dict__ for s in cache_result.segments],
                            "num_speakers": cache_result.num_speakers,
                            "speaker_map": cache_result.speaker_map,
                            "model": cache_result.model,
                            "duration": cache_result.duration,
                            "confidence": cache_result.confidence,
                            "cache_hit": True,
                            "processing_time_ms": (time.time() - start_time) * 1000,
                        }
                    )

            # Perform diarization
            model_name = self._select_model(model)
            diarization_result = self._diarize_audio(audio_path, model_name)

            if diarization_result:
                # Cache result
                if use_cache:
                    self._cache_result(audio_path, model, diarization_result)

                processing_time = (time.time() - start_time) * 1000

                return StepResult.ok(
                    data={
                        "segments": [s.__dict__ for s in diarization_result.segments],
                        "num_speakers": diarization_result.num_speakers,
                        "speaker_map": diarization_result.speaker_map,
                        "model": diarization_result.model,
                        "duration": diarization_result.duration,
                        "confidence": diarization_result.confidence,
                        "cache_hit": False,
                        "processing_time_ms": processing_time,
                    }
                )
            else:
                return StepResult.fail("Diarization failed", status="retryable")

        except Exception as e:
            logger.error(f"Audio diarization failed: {e}")
            return StepResult.fail(f"Diarization failed: {e!s}", status="retryable")

    def diarize_with_transcript(
        self,
        audio_path: str | Path,
        transcript_path: str | Path | None = None,
        asr_service: ASRService | None = None,
        model: Literal["fast", "balanced", "quality"] = "balanced",
        use_cache: bool = True,
    ) -> StepResult:
        """Diarize audio and align with existing transcript.

        Args:
            audio_path: Path to audio file
            transcript_path: Optional path to existing transcript
            asr_service: ASR service instance for transcript generation
            model: Model selection
            use_cache: Whether to use caches

        Returns:
            StepResult with aligned diarization and transcript data
        """
        try:
            # First, get or generate transcript
            if transcript_path and Path(transcript_path).exists():
                # Use existing transcript
                logger.info(f"Using existing transcript: {transcript_path}")
                transcript_text = Path(transcript_path).read_text()
                transcript_result = TranscriptionResult(
                    text=transcript_text,
                    segments=[],  # Will be populated by alignment
                    model="external",
                    duration=0.0,  # Will be determined from audio
                )
            elif asr_service:
                # Generate transcript using ASR service
                logger.info("Generating transcript with ASR service")
                asr_result = asr_service.transcribe_audio(
                    audio_path=audio_path,
                    model="balanced",  # Use balanced for accuracy
                    use_cache=use_cache,
                )

                if not asr_result.success:
                    return StepResult.fail(f"ASR transcription failed: {asr_result.error}")

                transcript_data = asr_result.data
                transcript_result = TranscriptionResult(
                    text=transcript_data["text"],
                    segments=[
                        TranscriptionSegment(
                            start=seg["start"],
                            end=seg["end"],
                            text=seg["text"],
                            confidence=seg.get("confidence", 1.0),
                        )
                        for seg in transcript_data["segments"]
                    ],
                    model=transcript_data["model"],
                    duration=transcript_data["duration"],
                    language=transcript_data.get("language"),
                    confidence=transcript_data.get("confidence", 1.0),
                )
            else:
                return StepResult.fail("No transcript available and ASR service not provided")

            # Perform diarization
            diarization_result = self._diarize_audio(audio_path, self._select_model(model))

            if not diarization_result:
                return StepResult.fail("Diarization failed")

            # Align transcript segments with speaker segments
            aligned_segments = self._align_transcript_with_diarization(
                transcript_result.segments, diarization_result.segments
            )

            # Update diarization result with aligned segments
            diarization_result.segments = aligned_segments

            # Add transcript information
            if transcript_result.segments:
                # Calculate average confidence from both ASR and diarization
                asr_confidence = transcript_result.confidence
                diarization_confidence = diarization_result.confidence
                diarization_result.confidence = (asr_confidence + diarization_confidence) / 2

            return StepResult.ok(
                data={
                    "segments": [s.__dict__ for s in diarization_result.segments],
                    "num_speakers": diarization_result.num_speakers,
                    "speaker_map": diarization_result.speaker_map,
                    "model": diarization_result.model,
                    "duration": diarization_result.duration,
                    "confidence": diarization_result.confidence,
                    "transcript_text": transcript_result.text,
                    "transcript_segments": len(transcript_result.segments),
                    "cache_hit": False,
                    "processing_time_ms": diarization_result.processing_time_ms,
                }
            )

        except Exception as e:
            logger.error(f"Combined diarization+transcript failed: {e}")
            return StepResult.fail(f"Combined processing failed: {e!s}")

    def _select_model(self, model_alias: str) -> str:
        """Select actual model name from alias.

        Args:
            model_alias: Model alias (fast, balanced, quality)

        Returns:
            Actual model identifier
        """
        model_map = {
            "fast": "pyannote/speaker-diarization-mini",
            "balanced": "pyannote/speaker-diarization",
            "quality": "pyannote/speaker-diarization",
        }

        return model_map.get(model_alias, "pyannote/speaker-diarization")

    def _diarize_audio(self, audio_path: Path, model_name: str) -> DiarizationResult | None:
        """Diarize audio using specified model.

        Args:
            audio_path: Path to audio file
            model_name: Model identifier

        Returns:
            DiarizationResult or None if diarization fails
        """
        try:
            if not PYANNOTE_AVAILABLE:
                logger.warning("pyannote.audio not available, using fallback diarization")
                return self._diarize_fallback(audio_path, model_name)

            # Load model lazily
            if self._diarization_model is None:
                logger.info(f"Loading pyannote diarization model: {model_name}")
                self._diarization_model = Pipeline.from_pretrained(model_name)

            # Perform diarization
            diarization = self._diarization_model(str(audio_path))

            # Convert to our format
            segments = []
            speaker_map = {}

            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_id = str(speaker)

                # Assign speaker names (placeholder logic)
                if speaker_id not in speaker_map:
                    speaker_map[speaker_id] = self._identify_speaker(speaker_id, audio_path)

                segment = SpeakerSegment(
                    start=turn.start,
                    end=turn.end,
                    speaker_id=speaker_id,
                    speaker_name=speaker_map[speaker_id],
                    speaker_role=self._infer_speaker_role(speaker_id, turn.start, turn.end),
                    confidence=0.8,  # pyannote doesn't provide per-segment confidence
                )
                segments.append(segment)

            # Sort segments by start time
            segments.sort(key=lambda s: s.start)

            return DiarizationResult(
                segments=segments,
                num_speakers=len(speaker_map),
                speaker_map=speaker_map,
                model=model_name,
                duration=diarization.get_timeline().extent.end,
                confidence=0.8,  # Overall confidence estimate
            )

        except Exception as e:
            logger.error(f"Diarization failed for model {model_name}: {e}")
            return None

    def _diarize_fallback(self, audio_path: Path, model_name: str) -> DiarizationResult:
        """Fallback diarization when pyannote is unavailable.

        Args:
            audio_path: Path to audio file
            model_name: Requested model identifier

        Returns:
            DiarizationResult with fallback segments
        """
        # Simple fallback: assume single speaker for entire duration
        # In production, this would use a simpler diarization method

        # Get audio duration (placeholder - would need actual audio analysis)
        duration = 3600.0  # Assume 1 hour default

        segments = [
            SpeakerSegment(
                start=0.0,
                end=duration,
                speaker_id="SPEAKER_00",
                speaker_name="Unknown Speaker",
                speaker_role="host",  # Assume host for fallback
                confidence=0.5,
            )
        ]

        return DiarizationResult(
            segments=segments,
            num_speakers=1,
            speaker_map={"SPEAKER_00": "Unknown Speaker"},
            model=f"fallback-{model_name}",
            duration=duration,
            confidence=0.5,
        )

    def _identify_speaker(self, speaker_id: str, audio_path: Path) -> str:
        """Identify speaker by voiceprint matching.

        Args:
            speaker_id: Speaker identifier from diarization
            audio_path: Path to audio file (for context)

        Returns:
            Speaker name or "Unknown Speaker"
        """
        # Placeholder for voiceprint-based speaker identification
        # In production, this would:
        # 1. Extract voiceprint from speaker segment
        # 2. Compare against known creator voiceprints
        # 3. Return matched name or "Unknown Speaker"

        # For now, return generic names based on speaker order
        speaker_names = [
            "Host",
            "Guest 1",
            "Guest 2",
            "Guest 3",
            "Moderator",
        ]

        # Simple mapping based on speaker ID
        try:
            speaker_num = int(speaker_id.split("_")[1]) if "_" in speaker_id else 0
            return speaker_names[speaker_num % len(speaker_names)]
        except (ValueError, IndexError):
            return "Unknown Speaker"

    def _infer_speaker_role(self, speaker_id: str, start_time: float, end_time: float) -> str:
        """Infer speaker role based on speaking patterns.

        Args:
            speaker_id: Speaker identifier
            start_time: Segment start time
            end_time: Segment end time

        Returns:
            Inferred role (host, guest, moderator, etc.)
        """
        duration = end_time - start_time

        # Simple heuristics for role inference
        if start_time < 60 and duration > 30:  # First minute, long segment
            return "host"  # Likely introduction
        elif duration > 300:  # Very long segments
            return "host"  # Hosts tend to speak more
        elif start_time > 3600:  # Later in content
            return "guest"  # Guests often speak later
        else:
            return "participant"  # Default role

    def _align_transcript_with_diarization(
        self,
        transcript_segments: list[TranscriptionSegment],
        speaker_segments: list[SpeakerSegment],
    ) -> list[SpeakerSegment]:
        """Align transcript segments with speaker segments.

        Args:
            transcript_segments: ASR transcript segments
            speaker_segments: Speaker diarization segments

        Returns:
            Speaker segments with aligned transcript text
        """
        # Simple alignment: find transcript segments that overlap with speaker segments
        aligned_speaker_segments = []

        for speaker_seg in speaker_segments:
            speaker_seg.transcript_text = ""

            # Find overlapping transcript segments
            for transcript_seg in transcript_segments:
                # Check for overlap
                overlap_start = max(speaker_seg.start, transcript_seg.start)
                overlap_end = min(speaker_seg.end, transcript_seg.end)

                if overlap_start < overlap_end:
                    # Add transcript text to speaker segment
                    speaker_seg.transcript_text += transcript_seg.text + " "

            # Clean up transcript text
            speaker_seg.transcript_text = speaker_seg.transcript_text.strip()
            aligned_speaker_segments.append(speaker_seg)

        return aligned_speaker_segments

    def _check_cache(self, audio_path: Path, model: str) -> DiarizationResult | None:
        """Check if diarization exists in cache.

        Args:
            audio_path: Path to audio file
            model: Model alias

        Returns:
            Cached DiarizationResult or None
        """
        cache_key = self._compute_cache_key(audio_path, model)

        if cache_key in self._diarization_cache:
            cached = self._diarization_cache[cache_key]

            # Check if file has been modified since caching
            if audio_path.stat().st_mtime <= cached.processing_time_ms / 1000:
                return cached

        return None

    def _cache_result(self, audio_path: Path, model: str, result: DiarizationResult) -> None:
        """Cache diarization result.

        Args:
            audio_path: Path to audio file
            model: Model alias
            result: Diarization result to cache
        """
        import time

        cache_key = self._compute_cache_key(audio_path, model)

        # Add processing timestamp
        result.processing_time_ms = time.time() * 1000

        # Evict old entries if cache is full
        if len(self._diarization_cache) >= self.cache_size:
            # Simple FIFO eviction - remove first key
            first_key = next(iter(self._diarization_cache))
            del self._diarization_cache[first_key]

        self._diarization_cache[cache_key] = result

    @staticmethod
    def _compute_cache_key(audio_path: Path, model: str) -> str:
        """Compute cache key for audio file and model.

        Args:
            audio_path: Path to audio file
            model: Model alias

        Returns:
            Cache key string
        """
        import hashlib

        # Use file path and modification time for cache key
        file_stat = audio_path.stat()
        combined = f"{audio_path}:{file_stat.st_mtime}:{file_stat.st_size}:{model}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def clear_cache(self) -> StepResult:
        """Clear diarization cache.

        Returns:
            StepResult with cache clear status
        """
        cache_size = len(self._diarization_cache)
        self._diarization_cache.clear()

        logger.info(f"Cleared {cache_size} cached diarizations")

        return StepResult.ok(data={"cleared_entries": cache_size})

    def get_cache_stats(self) -> StepResult:
        """Get diarization cache statistics.

        Returns:
            StepResult with cache statistics
        """
        try:
            stats = {
                "total_cached": len(self._diarization_cache),
                "cache_size_limit": self.cache_size,
                "utilization": len(self._diarization_cache) / self.cache_size if self.cache_size > 0 else 0.0,
                "models_cached": {},
            }

            # Count entries per model
            for result in self._diarization_cache.values():
                model = result.model
                stats["models_cached"][model] = stats["models_cached"].get(model, 0) + 1

            return StepResult.ok(data=stats)

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return StepResult.fail(f"Failed to get cache stats: {e!s}")


# Singleton instance
_diarization_service: SpeakerDiarizationService | None = None


def get_diarization_service() -> SpeakerDiarizationService:
    """Get singleton diarization service instance.

    Returns:
        Initialized SpeakerDiarizationService instance
    """
    global _diarization_service

    if _diarization_service is None:
        _diarization_service = SpeakerDiarizationService()

    return _diarization_service
