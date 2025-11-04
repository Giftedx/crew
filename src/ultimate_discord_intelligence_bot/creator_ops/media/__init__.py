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


class _MLFeatureStub:
    """Stub for ML features when dependencies are unavailable."""

    def __init__(self, feature_name: str, required_packages: list[str]) -> None:
        self._feature_name = feature_name
        self._required_packages = required_packages

    def __call__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        """Raise helpful error when stub is instantiated."""
        packages = ", ".join(self._required_packages)
        raise RuntimeError(
            f"{self._feature_name} requires ML dependencies: {packages}\n"
            "Install with: pip install -e '.[ml]'\n"
            "See: docs/OPTIONAL_DEPENDENCIES.md for more information"
        )


# Optional imports for ML-dependent features
# Catch all exceptions (not just ImportError) because ML dependencies may have broken dependency chains
try:
    from .asr import WhisperASR
except Exception:
    WhisperASR = _MLFeatureStub("WhisperASR", ["torch", "whisper", "faster-whisper"])  # type: ignore[assignment,misc]

try:
    from .diarization import SpeakerDiarization
except Exception:
    SpeakerDiarization = _MLFeatureStub("SpeakerDiarization", ["torch", "pyannote.audio"])  # type: ignore[assignment,misc]

try:
    from .embeddings import EmbeddingsGenerator
except Exception:
    EmbeddingsGenerator = _MLFeatureStub("EmbeddingsGenerator", ["torch", "sentence-transformers", "qdrant-client"])  # type: ignore[assignment,misc]

try:
    from .nlp import NLPPipeline, NLPResult
except Exception:
    NLPPipeline = _MLFeatureStub("NLPPipeline", ["torch", "transformers"])  # type: ignore[assignment,misc]
    NLPResult = None  # type: ignore[assignment,misc]


__all__ = [
    "EmbeddingsGenerator",
    "NLPPipeline",
    "NLPResult",
    "SpeakerDiarization",
    "TranscriptAlignment",
    "WhisperASR",
]
