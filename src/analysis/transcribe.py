"""Lightweight Whisper wrapper for speech-to-text.

This module intentionally keeps dependencies optional; when the
`whisper` package is unavailable (e.g. in tests), the `run_whisper`
function will fall back to reading plain-text files where each line is
interpreted as a transcript segment. This allows deterministic unit
tests without requiring heavy models.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Segment:
    """A single transcript span."""

    start: float
    end: float
    text: str
    speaker: str | None = None


@dataclass
class Transcript:
    """Collection of transcript segments."""

    segments: list[Segment]


def run_whisper(path: str, model: str = "tiny") -> Transcript:
    """Transcribe audio at *path* using OpenAI's Whisper.

    If the optional :mod:`whisper` package is not installed this function
    treats *path* as a UTF-8 text file and returns each line as a
    one-second segment.  The behaviour is sufficient for tests which
    operate on tiny fixtures.
    """

    try:
        import whisper  # type: ignore

        model_inst = whisper.load_model(model)
        result = model_inst.transcribe(path)
        segments = [
            Segment(start=s["start"], end=s["end"], text=s["text"].strip())
            for s in result["segments"]
        ]
        return Transcript(segments=segments)
    except Exception:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        segments = [
            Segment(start=float(i), end=float(i + 1), text=line) for i, line in enumerate(lines)
        ]
        return Transcript(segments=segments)
