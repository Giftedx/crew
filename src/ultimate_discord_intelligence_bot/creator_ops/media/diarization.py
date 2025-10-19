"""
Speaker diarization using pyannote.audio.

This module provides speaker diarization capabilities with overlap handling,
speaker count estimation, and integration with ASR timestamps.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import torch
from pyannote.audio import Pipeline
from pyannote.core import Annotation, Segment

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)


@dataclass
class DiarizationSegment:
    """Speaker diarization segment with timing and speaker information."""

    start_time: float
    end_time: float
    speaker: str
    confidence: float | None = None


@dataclass
class DiarizationResult:
    """Complete diarization result with metadata."""

    segments: list[DiarizationSegment]
    speakers: list[str]
    speaker_count: int
    duration: float
    model_name: str
    processing_time: float
    device: str
    created_at: datetime
    der_score: float | None = None  # Diarization Error Rate


class SpeakerDiarization:
    """
    Speaker diarization using pyannote.audio with comprehensive features.

    Features:
    - Overlap handling for multiple speakers
    - Speaker count estimation
    - Integration with ASR timestamps
    - DER evaluation (target <15%)
    - GPU acceleration with CPU fallback
    """

    def __init__(
        self,
        model_name: str = "pyannote/speaker-diarization-3.1",
        device: str | None = None,
        config: CreatorOpsConfig | None = None,
    ) -> None:
        """Initialize speaker diarization."""
        self.config = config or CreatorOpsConfig()
        self.model_name = model_name
        self.device = device or self._get_optimal_device()
        self.pipeline = None

        # Initialize pipeline
        self._initialize_pipeline()

    def _get_optimal_device(self) -> str:
        """Get optimal device for diarization processing."""
        if self.config.use_gpu and torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def _initialize_pipeline(self) -> None:
        """Initialize pyannote.audio pipeline."""
        try:
            # Load the diarization pipeline
            self.pipeline = Pipeline.from_pretrained(
                self.model_name,
                use_auth_token=self.config.huggingface_token,
            )

            # Move to device if available
            if self.device == "cuda" and torch.cuda.is_available():
                self.pipeline = self.pipeline.to(torch.device("cuda"))
                logger.info(f"Loaded diarization pipeline on {self.device}")
            else:
                logger.info("Loaded diarization pipeline on CPU")

        except Exception as e:
            logger.error(f"Failed to initialize diarization pipeline: {str(e)}")
            raise

    def diarize_audio(
        self,
        audio_path: str,
        num_speakers: int | None = None,
        min_speakers: int | None = None,
        max_speakers: int | None = None,
    ) -> StepResult:
        """
        Perform speaker diarization on audio file.

        Args:
            audio_path: Path to audio file
            num_speakers: Exact number of speakers (if known)
            min_speakers: Minimum number of speakers
            max_speakers: Maximum number of speakers

        Returns:
            StepResult with DiarizationResult
        """
        start_time = datetime.utcnow()

        try:
            # Validate audio file
            if not audio_path or not audio_path.strip():
                return StepResult.fail("Audio path cannot be empty")

            # Perform diarization
            if num_speakers:
                # Use exact speaker count
                diarization = self.pipeline(audio_path, num_speakers=num_speakers)
            else:
                # Use min/max speaker counts
                kwargs = {}
                if min_speakers:
                    kwargs["min_speakers"] = min_speakers
                if max_speakers:
                    kwargs["max_speakers"] = max_speakers

                diarization = self.pipeline(audio_path, **kwargs)

            # Parse results
            segments = []
            speakers = set()

            for segment, _, speaker in diarization.itertracks(yield_label=True):
                diarization_segment = DiarizationSegment(
                    start_time=segment.start,
                    end_time=segment.end,
                    speaker=speaker,
                    confidence=None,  # pyannote doesn't provide confidence scores
                )
                segments.append(diarization_segment)
                speakers.add(speaker)

            # Sort segments by start time
            segments.sort(key=lambda x: x.start_time)

            # Calculate duration
            duration = max(segment.end_time for segment in segments) if segments else 0.0

            # Create result
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result = DiarizationResult(
                segments=segments,
                speakers=sorted(list(speakers)),
                speaker_count=len(speakers),
                duration=duration,
                model_name=self.model_name,
                processing_time=processing_time,
                device=self.device,
                created_at=start_time,
            )

            return StepResult.ok(data=result)

        except Exception as e:
            logger.error(f"Speaker diarization failed: {str(e)}")
            return StepResult.fail(f"Speaker diarization failed: {str(e)}")

    def estimate_speaker_count(
        self,
        audio_path: str,
        min_speakers: int = 1,
        max_speakers: int = 10,
    ) -> StepResult:
        """
        Estimate the number of speakers in audio.

        Args:
            audio_path: Path to audio file
            min_speakers: Minimum number of speakers
            max_speakers: Maximum number of speakers

        Returns:
            StepResult with estimated speaker count
        """
        try:
            # Perform diarization with range
            diarization = self.pipeline(
                audio_path,
                min_speakers=min_speakers,
                max_speakers=max_speakers,
            )

            # Count unique speakers
            speakers = set()
            for _, _, speaker in diarization.itertracks(yield_label=True):
                speakers.add(speaker)

            estimated_count = len(speakers)

            return StepResult.ok(
                data={
                    "estimated_speaker_count": estimated_count,
                    "speakers": sorted(list(speakers)),
                    "confidence": "medium",  # pyannote doesn't provide confidence
                }
            )

        except Exception as e:
            logger.error(f"Speaker count estimation failed: {str(e)}")
            return StepResult.fail(f"Speaker count estimation failed: {str(e)}")

    def handle_overlaps(
        self,
        diarization_result: DiarizationResult,
        overlap_threshold: float = 0.1,
    ) -> StepResult:
        """
        Handle overlapping speaker segments.

        Args:
            diarization_result: Diarization result to process
            overlap_threshold: Minimum overlap duration to consider

        Returns:
            StepResult with overlap information
        """
        try:
            overlaps = []
            segments = diarization_result.segments

            # Find overlapping segments
            for i, seg1 in enumerate(segments):
                for j, seg2 in enumerate(segments[i + 1 :], i + 1):
                    # Check for overlap
                    overlap_start = max(seg1.start_time, seg2.start_time)
                    overlap_end = min(seg1.end_time, seg2.end_time)

                    if overlap_start < overlap_end:
                        overlap_duration = overlap_end - overlap_start

                        if overlap_duration >= overlap_threshold:
                            overlaps.append(
                                {
                                    "start_time": overlap_start,
                                    "end_time": overlap_end,
                                    "duration": overlap_duration,
                                    "speaker1": seg1.speaker,
                                    "speaker2": seg2.speaker,
                                    "segment1_index": i,
                                    "segment2_index": j,
                                }
                            )

            return StepResult.ok(
                data={
                    "overlaps": overlaps,
                    "total_overlaps": len(overlaps),
                    "total_overlap_duration": sum(overlap["duration"] for overlap in overlaps),
                    "overlap_percentage": (
                        sum(overlap["duration"] for overlap in overlaps) / diarization_result.duration * 100
                        if diarization_result.duration > 0
                        else 0
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Overlap handling failed: {str(e)}")
            return StepResult.fail(f"Overlap handling failed: {str(e)}")

    def evaluate_der(
        self,
        predicted: DiarizationResult,
        reference: DiarizationResult,
    ) -> StepResult:
        """
        Evaluate Diarization Error Rate (DER).

        Args:
            predicted: Predicted diarization result
            reference: Reference (ground truth) diarization result

        Returns:
            StepResult with DER score
        """
        try:
            from pyannote.metrics.diarization import DiarizationErrorRate

            # Convert to pyannote format
            predicted_annotation = self._to_pyannote_annotation(predicted)
            reference_annotation = self._to_pyannote_annotation(reference)

            # Calculate DER
            der = DiarizationErrorRate()
            der_score = der(reference_annotation, predicted_annotation)

            return StepResult.ok(
                data={
                    "der_score": der_score,
                    "target_met": der_score < 0.15,  # Target <15%
                    "evaluation": "DER < 15% target met"
                    if der_score < 0.15
                    else f"DER {der_score:.3f} exceeds 15% target",
                }
            )

        except Exception as e:
            logger.error(f"DER evaluation failed: {str(e)}")
            return StepResult.fail(f"DER evaluation failed: {str(e)}")

    def _to_pyannote_annotation(self, diarization_result: DiarizationResult) -> Annotation:
        """Convert DiarizationResult to pyannote Annotation."""
        annotation = Annotation()

        for segment in diarization_result.segments:
            annotation[Segment(segment.start_time, segment.end_time)] = segment.speaker

        return annotation

    def get_model_info(self) -> dict[str, Any]:
        """Get model information."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "has_gpu": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "pipeline_loaded": self.pipeline is not None,
        }

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.pipeline:
            del self.pipeline
            self.pipeline = None

        # Clear CUDA cache if using GPU
        if self.device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()
