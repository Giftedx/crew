"""Lightweight Whisper wrapper for speech-to-text.

This module intentionally keeps dependencies optional; when the
`whisper` package is unavailable (e.g. in tests), the `run_whisper`
function will fall back to reading plain-text files where each line is
interpreted as a transcript segment. This allows deterministic unit
tests without requiring heavy models.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.degradation_reporter import record_degradation

try:
    from core.secure_config import get_config
except Exception:  # pragma: no cover - fallback when secure_config deps unavailable

    class _FallbackConfig:
        """Fallback configuration when secure_config is unavailable."""

        enable_faster_whisper: bool = False
        whisper_model: str | None = None

    def _get_fallback_config() -> _FallbackConfig:
        return _FallbackConfig()

    # Alias for compatibility
    get_config = _get_fallback_config


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

    cfg = get_config()
    # Prefer Faster-Whisper when enabled and available
    if getattr(cfg, "enable_faster_whisper", False):
        try:  # pragma: no cover - heavy dependency path
            from faster_whisper import WhisperModel

            model_name = getattr(cfg, "whisper_model", model) or model
            wm = WhisperModel(model_name)
            segments_it, _info = wm.transcribe(path)
            segs = list(segments_it)
            return Transcript(
                segments=[Segment(start=float(s.start), end=float(s.end), text=str(s.text).strip()) for s in segs]
            )
        except Exception:
            # Record degradation (faster-whisper failed -> fallback path)
            record_degradation(
                component="transcribe",
                event_type="faster_whisper_fallback",
                severity="warn",
                detail="faster-whisper path failed; falling back to whisper/text",
            )
            # fall back to standard whisper or text path
    try:
        import whisper  # type: ignore  # noqa: PLC0415 - optional heavy dependency imported lazily

        model_inst = whisper.load_model(getattr(cfg, "whisper_model", model) or model)
        result = model_inst.transcribe(path)
        segments = [Segment(start=s["start"], end=s["end"], text=s["text"].strip()) for s in result["segments"]]
        return Transcript(segments=segments)
    except Exception:
        # If whisper also fails we fallback to plain-text mode (record degradation once)
        record_degradation(
            component="transcribe",
            event_type="whisper_fallback_text",
            severity="warn",
            detail="whisper unavailable; treating path as plaintext transcript",
        )
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        segments = [Segment(start=float(i), end=float(i + 1), text=line) for i, line in enumerate(lines)]
        return Transcript(segments=segments)
