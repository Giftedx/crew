"""Utility for transcribing audio using Whisper.

The original implementation eagerly loaded the Whisper model at import time which
adds significant overhead and makes tests harder to run on systems without the
dependency installed.  The tool now performs a lazy import and model
initialisation so that the model is only loaded when the tool is executed.  This
also allows unit tests to mock out the behaviour without importing Whisper.
"""

import importlib
import logging
import os
import time
from functools import cached_property
from typing import Any, Protocol, TypedDict, cast

from core.secure_config import get_config

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool

# Optional dependency loaded dynamically to avoid hard import errors during typing/linting
whisper: Any | None
try:  # pragma: no cover - optional dependency
    whisper = importlib.import_module("whisper")
except Exception:  # pragma: no cover - handled in runtime
    whisper = None


class _TranscribeResult(TypedDict, total=False):
    text: str
    segments: list[dict[str, object]]


class _WhisperModel(Protocol):
    def transcribe(self, path: str) -> dict[str, Any]: ...


class AudioTranscriptionTool(BaseTool):
    name: str = "Audio Transcription Tool"
    description: str = "Transcribe audio from a video file using Whisper."

    def __init__(self, model_name: str | None = None):
        super().__init__()
        config = get_config()
        self._model_name = model_name or config.whisper_model
        self._metrics = get_metrics()

    @cached_property
    def model(self) -> _WhisperModel:  # pragma: no cover - heavy initialisation
        if whisper is None:
            raise RuntimeError("whisper package is not installed")
        logging.info("Loading Whisper model %s", self._model_name)
        return cast(_WhisperModel, whisper.load_model(self._model_name))

    def _load_corrections(self) -> dict[str, str]:
        """Load optional transcript corrections from config file.

        File format (JSON): {"sobra": "sabra", ...}
        """
        try:
            from ultimate_discord_intelligence_bot.settings import CONFIG_DIR  # noqa: PLC0415

            path = os.path.join(str(CONFIG_DIR), "transcript_corrections.json")
            if os.path.exists(path):
                import json

                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    # normalize keys to lowercase
                    return {str(k).lower(): str(v) for k, v in data.items()}
        except Exception:
            pass
        return {}

    def _apply_corrections(self, text: str, corrections: dict[str, str]) -> str:
        if not corrections or not text:
            return text
        import re

        out = text
        for wrong, right in corrections.items():
            # Replace whole words only, ignore case, handle punctuation adjacency
            pattern = re.compile(rf"\b{re.escape(wrong)}\b", flags=re.IGNORECASE)
            out = pattern.sub(right, out)
        return out

    def _run(self, video_path: str) -> StepResult:
        """Transcribe audio from a video file.

        Returns a StepResult; errors are captured rather than raised so the
        pipeline can continue gracefully.
        """
        start = time.monotonic()
        try:
            if not os.path.exists(video_path):
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "audio_transcription", "outcome": "error"}
                ).inc()
                return StepResult.fail(error="Video file not found.")

            # Provide language hint and stable decoding settings to improve proper nouns
            # If model ignores language, it will auto-detect; otherwise it guides decoding.
            opts = {"language": "en", "fp16": False}
            result = self.model.transcribe(video_path, **opts)
            text = str(result.get("text", ""))
            # Extract segments when available (start/end/text) for timestamped navigation
            raw_segments = result.get("segments", []) if isinstance(result, dict) else []
            segments: list[dict[str, object]] = []
            if isinstance(raw_segments, list):
                for seg in raw_segments:
                    if not isinstance(seg, dict):
                        continue
                    try:
                        start = float(seg.get("start", 0.0))
                    except Exception:
                        start = 0.0
                    try:
                        end = float(seg.get("end", start))
                    except Exception:
                        end = start
                    txt = str(seg.get("text", "")).strip()
                    segments.append({"start": start, "end": end, "text": txt})
            # Optional post-correction pass
            text = self._apply_corrections(text, self._load_corrections())
            self._metrics.counter("tool_runs_total", labels={"tool": "audio_transcription", "outcome": "success"}).inc()
            return StepResult.ok(transcript=text, segments=segments)
        except Exception as e:  # pragma: no cover - exercised in integration
            logging.exception("Transcription failed")
            self._metrics.counter("tool_runs_total", labels={"tool": "audio_transcription", "outcome": "error"}).inc()
            return StepResult.fail(error=str(e))
        finally:  # record latency regardless of outcome
            try:  # defensive: histogram may no-op
                duration = time.monotonic() - start
                self._metrics.histogram("tool_run_seconds", duration, labels={"tool": "audio_transcription"})
            except Exception as exc:  # pragma: no cover - metrics backend failure should not break tool
                logging.debug("audio_transcription metrics emit failed: %s", exc)

    # Expose a public run method for pipeline compatibility
    def run(self, video_path: str) -> StepResult:  # pragma: no cover - thin wrapper
        return self._run(video_path)
