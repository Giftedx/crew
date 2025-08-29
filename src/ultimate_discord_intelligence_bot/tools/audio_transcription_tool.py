"""Utility for transcribing audio using Whisper.

The original implementation eagerly loaded the Whisper model at import time which
adds significant overhead and makes tests harder to run on systems without the
dependency installed.  The tool now performs a lazy import and model
initialisation so that the model is only loaded when the tool is executed.  This
also allows unit tests to mock out the behaviour without importing Whisper.
"""

import logging
import os
from functools import cached_property

from crewai.tools import BaseTool

try:  # pragma: no cover - optional dependency
    import whisper  # type: ignore
except Exception:  # pragma: no cover - handled in runtime
    whisper = None


class AudioTranscriptionTool(BaseTool):
    name: str = "Audio Transcription Tool"
    description: str = "Transcribe audio from a video file using Whisper."

    def __init__(self, model_name: str | None = None):
        super().__init__()
        self._model_name = model_name or os.getenv("WHISPER_MODEL", "base")

    @cached_property
    def model(self):  # pragma: no cover - heavy initialisation
        if whisper is None:
            raise RuntimeError("whisper package is not installed")
        logging.info("Loading Whisper model %s", self._model_name)
        return whisper.load_model(self._model_name)

    def _run(self, video_path: str) -> dict:
        """Transcribe audio from a video file."""
        try:
            if not os.path.exists(video_path):
                return {"status": "error", "error": "Video file not found."}

            result = self.model.transcribe(video_path)

            return {
                "status": "success",
                "transcript": result["text"],
            }

        except Exception as e:  # pragma: no cover - exercised in integration
            logging.exception("Transcription failed")
            return {"status": "error", "error": str(e)}

    # Expose a public run method for pipeline compatibility
    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
