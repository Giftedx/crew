"""
Automatic Speech Recognition (ASR) using Whisper.

This module provides comprehensive ASR capabilities with GPU support,
language detection, and batch processing for creator content.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import torch
import whisper
from faster_whisper import WhisperModel

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)


@dataclass
class ASRSegment:
    """ASR segment with timing and confidence information."""

    start_time: float
    end_time: float
    text: str
    confidence: float
    language: str | None = None
    language_probability: float | None = None
    no_speech_prob: float | None = None


@dataclass
class ASRResult:
    """Complete ASR result with metadata."""

    text: str
    language: str
    language_probability: float
    segments: list[ASRSegment]
    duration: float
    model_name: str
    processing_time: float
    device: str
    created_at: datetime


class WhisperASR:
    """
    Whisper-based ASR with GPU support and fallback options.

    Features:
    - GPU acceleration with CUDA
    - CPU fallback with faster-whisper
    - Language detection
    - Batch processing
    - Word-level timestamps
    - Confidence scoring
    """

    def __init__(
        self,
        model_name: str = "large-v3",
        device: str | None = None,
        config: CreatorOpsConfig | None = None,
    ) -> None:
        """Initialize Whisper ASR."""
        self.config = config or CreatorOpsConfig()
        self.model_name = model_name
        self.device = device or self._get_optimal_device()
        self.model = None
        self.faster_model = None

        # Initialize models
        self._initialize_models()

    def _get_optimal_device(self) -> str:
        """Get optimal device for ASR processing."""
        if self.config.use_gpu and torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def _initialize_models(self) -> None:
        """Initialize Whisper models."""
        try:
            if self.device == "cuda":
                # Use standard Whisper for GPU
                self.model = whisper.load_model(self.model_name, device=self.device)
                logger.info(f"Loaded Whisper model {self.model_name} on {self.device}")
            else:
                # Use faster-whisper for CPU
                self.faster_model = WhisperModel(
                    self.model_name,
                    device="cpu",
                    compute_type="int8",  # Optimized for CPU
                )
                logger.info(f"Loaded faster-whisper model {self.model_name} on CPU")
        except Exception as e:
            logger.error(f"Failed to initialize Whisper model: {str(e)}")
            raise

    def transcribe_audio(
        self,
        audio_path: str | Path,
        language: str | None = None,
        word_timestamps: bool = True,
        temperature: float = 0.0,
        beam_size: int = 5,
    ) -> StepResult:
        """
        Transcribe audio file to text with timestamps.

        Args:
            audio_path: Path to audio file
            language: Language code (auto-detect if None)
            word_timestamps: Include word-level timestamps
            temperature: Sampling temperature (0.0 = deterministic)
            beam_size: Beam search size

        Returns:
            StepResult with ASRResult
        """
        start_time = datetime.utcnow()

        try:
            # Validate audio file
            if not os.path.exists(audio_path):
                return StepResult.fail(f"Audio file not found: {audio_path}")

            # Transcribe based on device
            if self.device == "cuda" and self.model:
                result = self._transcribe_with_whisper(audio_path, language, word_timestamps, temperature, beam_size)
            else:
                result = self._transcribe_with_faster_whisper(
                    audio_path, language, word_timestamps, temperature, beam_size
                )

            if not result.success:
                return result

            # Add metadata
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            asr_result = result.data
            asr_result.processing_time = processing_time
            asr_result.device = self.device
            asr_result.created_at = start_time

            return StepResult.ok(data=asr_result)

        except Exception as e:
            logger.error(f"ASR transcription failed: {str(e)}")
            return StepResult.fail(f"ASR transcription failed: {str(e)}")

    def _transcribe_with_whisper(
        self,
        audio_path: str | Path,
        language: str | None,
        word_timestamps: bool,
        temperature: float,
        beam_size: int,
    ) -> StepResult:
        """Transcribe using standard Whisper (GPU)."""
        try:
            # Prepare options
            options = {
                "language": language,
                "temperature": temperature,
                "beam_size": beam_size,
                "word_timestamps": word_timestamps,
            }

            # Remove None values
            options = {k: v for k, v in options.items() if v is not None}

            # Transcribe
            result = self.model.transcribe(str(audio_path), **options)

            # Parse result
            segments = []
            for segment in result["segments"]:
                asr_segment = ASRSegment(
                    start_time=segment["start"],
                    end_time=segment["end"],
                    text=segment["text"].strip(),
                    confidence=segment.get("avg_logprob", 0.0),
                    language=result.get("language"),
                    language_probability=result.get("language_probability"),
                    no_speech_prob=segment.get("no_speech_prob"),
                )
                segments.append(asr_segment)

            # Create ASR result
            asr_result = ASRResult(
                text=result["text"].strip(),
                language=result["language"],
                language_probability=result.get("language_probability", 0.0),
                segments=segments,
                duration=result.get("duration", 0.0),
                model_name=self.model_name,
                processing_time=0.0,  # Will be set by caller
                device=self.device,
                created_at=datetime.utcnow(),
            )

            return StepResult.ok(data=asr_result)

        except Exception as e:
            return StepResult.fail(f"Whisper transcription failed: {str(e)}")

    def _transcribe_with_faster_whisper(
        self,
        audio_path: str | Path,
        language: str | None,
        word_timestamps: bool,
        temperature: float,
        beam_size: int,
    ) -> StepResult:
        """Transcribe using faster-whisper (CPU)."""
        try:
            # Prepare options
            options = {
                "language": language,
                "temperature": temperature,
                "beam_size": beam_size,
                "word_timestamps": word_timestamps,
            }

            # Remove None values
            options = {k: v for k, v in options.items() if v is not None}

            # Transcribe
            segments, info = self.faster_model.transcribe(str(audio_path), **options)

            # Convert to list and parse
            segment_list = list(segments)
            asr_segments = []

            for segment in segment_list:
                asr_segment = ASRSegment(
                    start_time=segment.start,
                    end_time=segment.end,
                    text=segment.text.strip(),
                    confidence=segment.avg_logprob,
                    language=info.language,
                    language_probability=info.language_probability,
                    no_speech_prob=segment.no_speech_prob,
                )
                asr_segments.append(asr_segment)

            # Combine all text
            full_text = " ".join(segment.text for segment in segment_list)

            # Create ASR result
            asr_result = ASRResult(
                text=full_text.strip(),
                language=info.language,
                language_probability=info.language_probability,
                segments=asr_segments,
                duration=info.duration,
                model_name=self.model_name,
                processing_time=0.0,  # Will be set by caller
                device=self.device,
                created_at=datetime.utcnow(),
            )

            return StepResult.ok(data=asr_result)

        except Exception as e:
            return StepResult.fail(f"Faster-whisper transcription failed: {str(e)}")

    def batch_transcribe(
        self,
        audio_paths: list[str | Path],
        language: str | None = None,
        max_workers: int = 4,
    ) -> StepResult:
        """
        Transcribe multiple audio files in batch.

        Args:
            audio_paths: List of audio file paths
            language: Language code (auto-detect if None)
            max_workers: Maximum number of parallel workers

        Returns:
            StepResult with list of ASRResult
        """
        try:
            results = []

            # Process files sequentially for now (can be parallelized later)
            for audio_path in audio_paths:
                result = self.transcribe_audio(audio_path, language)
                if result.success:
                    results.append(result.data)
                else:
                    logger.error(f"Failed to transcribe {audio_path}: {result.error}")
                    # Continue with other files

            return StepResult.ok(data=results)

        except Exception as e:
            return StepResult.fail(f"Batch transcription failed: {str(e)}")

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages."""
        return whisper.tokenizer.LANGUAGES.keys()

    def get_model_info(self) -> dict[str, Any]:
        """Get model information."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "has_gpu": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "supported_languages": len(self.get_supported_languages()),
        }

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.model:
            del self.model
            self.model = None
        if self.faster_model:
            del self.faster_model
            self.faster_model = None

        # Clear CUDA cache if using GPU
        if self.device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()
