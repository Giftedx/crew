"""Type stubs for openai-whisper package."""

from typing import Any

def load_model(name: str, device: str = ..., download_root: str | None = None, in_memory: bool = False) -> Any: ...

class Whisper:
    def transcribe(
        self,
        audio: str,
        *,
        verbose: bool | None = None,
        temperature: float | list[float] = ...,
        compression_ratio_threshold: float | None = ...,
        logprob_threshold: float | None = ...,
        no_speech_threshold: float | None = ...,
        condition_on_previous_text: bool = True,
        initial_prompt: str | None = None,
        word_timestamps: bool = False,
        prepend_punctuations: str = ...,
        append_punctuations: str = ...,
        language: str | None = None,
    ) -> dict[str, Any]: ...
