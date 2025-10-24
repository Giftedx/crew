"""
Utility for transcribing audio using the faster Distil-Whisper model.

This implementation uses the Hugging Face transformers library to run the
distil-whisper/distil-large-v3 model, which offers a 6x speed improvement over
traditional Whisper with minimal degradation in transcription quality.

The tool lazy-loads the model on first use to reduce initial application startup
time and memory overhead. It's designed to be a drop-in replacement for the
previous Whisper tool.
"""

from __future__ import annotations

import importlib
import logging
import os
import time
from functools import cached_property
from typing import Any

import torch

from ultimate_discord_intelligence_bot.cache import EnhancedTranscriptionCache
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import TranscriptionTool


# Lazy load transformers to avoid import errors if not installed and to speed up startup
transformers: Any | None
try:  # pragma: no cover
    transformers = importlib.import_module("transformers")
except ImportError:  # pragma: no cover
    transformers = None


class AudioTranscriptionTool(TranscriptionTool):
    name: str = "Enhanced Whisper Audio Transcription"
    description: str = "Transcribes audio from a file using the high-performance Distil-Whisper model."

    def __init__(
        self,
        model_id: str | None = None,
        device: str | None = None,
        chunk_length_s: int = 30,
        torch_dtype: torch.dtype | None = None,
        enable_caching: bool = True,
    ):
        super().__init__()
        # Use environment variable directly since DISTIL_WHISPER_MODEL_ID is not in SecureConfig fields
        self._model_id = model_id or os.getenv("DISTIL_WHISPER_MODEL_ID", "distil-whisper/distil-large-v3")

        # Determine device, defaulting to CUDA if available
        if device:
            self._device = device
        else:
            self._device = "cuda:0" if torch.cuda.is_available() else "cpu"

        self._chunk_length_s = chunk_length_s
        self._torch_dtype = torch_dtype or torch.float16
        self._metrics = get_metrics()

        # Initialize cache if enabled
        self._cache = EnhancedTranscriptionCache(enabled=enable_caching) if enable_caching else None

    @cached_property
    def transcriber(self) -> Any:
        """
        Lazy-loads and initializes the transcription pipeline from the transformers library.
        This property is cached, so the model is only loaded once per tool instance.
        """
        if transformers is None:
            raise RuntimeError(
                "The 'transformers' package is not installed. Please install it with `pip install '.[distil_whisper]'`."
            )

        logging.info(f"Loading Distil-Whisper model '{self._model_id}' on device '{self._device}'")

        # Initialize the ASR pipeline
        return transformers.pipeline(
            "automatic-speech-recognition",
            model=self._model_id,
            torch_dtype=self._torch_dtype,
            device=self._device,
        )

    def _run(self, audio_path: str, video_id: str | None = None, **metadata: Any) -> StepResult:
        """
        Performs transcription on the given audio file with caching support.

        Args:
            audio_path: The absolute path to the audio file to be transcribed.
            video_id: Optional video identifier for cache key generation
            **metadata: Additional metadata for cache key generation

        Returns:
            A StepResult containing the transcription text and segment data, or an error.
        """
        start_time = time.monotonic()
        try:
            if not os.path.exists(audio_path):
                self._metrics.counter("tool_runs_total", labels={"tool": self.name, "outcome": "error"}).inc()
                return StepResult.fail(error=f"Audio file not found at path: {audio_path}")

            # Generate cache key if video_id is provided
            if self._cache and video_id:
                # Check cache first
                cached_result = self._cache.get_transcription(
                    video_id=video_id,
                    model_name=self._model_id or "distil-whisper/distil-large-v3",
                    file_path=audio_path,
                    **metadata,
                )
                if cached_result:
                    self._metrics.counter(
                        "tool_runs_total",
                        labels={"tool": self.name, "outcome": "cache_hit"},
                    ).inc()
                    return StepResult.ok(
                        transcript=cached_result["transcript"],
                        segments=cached_result.get("segments", []),
                        cached=True,
                    )

            # Perform transcription
            result = self.transcriber(
                audio_path,
                chunk_length_s=self._chunk_length_s,
                batch_size=8,  # Small batch size for CPU, can be increased for GPU
                return_timestamps=True,
            )

            text = result.get("text", "").strip()

            # Process segments for structured output
            segments = [
                {
                    "start": chunk["timestamp"][0],
                    "end": chunk["timestamp"][1],
                    "text": chunk["text"].strip(),
                }
                for chunk in result.get("chunks", [])
                if chunk.get("timestamp") and chunk.get("text")
            ]

            # Store in cache if available and video_id provided
            if self._cache and video_id:
                quality_score = self._calculate_transcript_quality(text, segments)
                self._cache.store_transcription(
                    video_id=video_id,
                    model_name=self._model_id or "distil-whisper/distil-large-v3",
                    transcript=text,
                    segments=segments,
                    quality_score=quality_score,
                    file_path=audio_path,
                    **metadata,
                )

            self._metrics.counter("tool_runs_total", labels={"tool": self.name, "outcome": "success"}).inc()
            return StepResult.ok(transcript=text, segments=segments)

        except Exception as e:
            logging.exception(f"Enhanced Whisper transcription failed for {audio_path}")
            self._metrics.counter("tool_runs_total", labels={"tool": self.name, "outcome": "error"}).inc()
            return StepResult.fail(error=str(e))
        finally:
            duration = time.monotonic() - start_time
            self._metrics.histogram("tool_run_seconds", duration, labels={"tool": self.name})

    def _calculate_transcript_quality(self, text: str, segments: list[dict[str, Any]]) -> float:
        """Calculate a simple quality score for the transcript.

        Args:
            text: The transcript text
            segments: List of transcript segments with timestamps

        Returns:
            Quality score between 0.0 and 1.0
        """
        if not text:
            return 0.0

        quality_score = 0.5  # Base score

        # Length factor (longer transcripts are generally better)
        if len(text) > 1000:
            quality_score += 0.2
        elif len(text) > 500:
            quality_score += 0.1

        # Segment count factor (more segments indicate better segmentation)
        if segments:
            quality_score += min(0.2, len(segments) / 100)

        # Basic text quality indicators
        word_count = len(text.split())
        if word_count > 100:
            quality_score += 0.1

        # Cap at 1.0
        return min(1.0, quality_score)

    def run(self, audio_path: str, video_id: str | None = None, **metadata: Any) -> StepResult:
        """Public run method for pipeline compatibility."""
        return self._run(audio_path, video_id, **metadata)
