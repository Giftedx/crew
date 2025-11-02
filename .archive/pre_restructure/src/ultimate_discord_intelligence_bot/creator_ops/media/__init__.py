"""Media processing pipeline for Creator Operations.

This module provides comprehensive media processing capabilities including:
- Automatic Speech Recognition (ASR) with Whisper
- Speaker diarization with pyannote.audio
- Natural Language Processing (NLP) pipeline
- Embeddings generation and storage
- Transcript alignment and cleanup
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .alignment import TranscriptAlignment


if TYPE_CHECKING:
    from .asr import WhisperASR
    from .diarization import SpeakerDiarization
    from .embeddings import EmbeddingsGenerator
    from .nlp import NLPPipeline, NLPResult

# Optional imports for ML-dependent features
# Catch all exceptions (not just ImportError) because ML dependencies may have broken dependency chains
try:
    from .asr import WhisperASR
except Exception:
    WhisperASR = None  # type: ignore[assignment,misc]

try:
    from .diarization import SpeakerDiarization
except Exception:
    SpeakerDiarization = None  # type: ignore[assignment,misc]

try:
    from .embeddings import EmbeddingsGenerator
except Exception:
    EmbeddingsGenerator = None  # type: ignore[assignment,misc]

try:
    from .nlp import NLPPipeline, NLPResult
except Exception:
    NLPPipeline = None  # type: ignore[assignment,misc]
    NLPResult = None  # type: ignore[assignment,misc]


__all__ = [
    "EmbeddingsGenerator",
    "NLPPipeline",
    "NLPResult",
    "SpeakerDiarization",
    "TranscriptAlignment",
    "WhisperASR",
]
