"""Type stubs for faster-whisper package."""

from collections.abc import Iterator
from typing import Any

class WhisperModel:
    def __init__(
        self,
        model_size_or_path: str,
        device: str = "auto",
        device_index: int | list[int] = 0,
        compute_type: str = "default",
        cpu_threads: int = 0,
        num_workers: int = 1,
        download_root: str | None = None,
        local_files_only: bool = False,
    ) -> None: ...
    def transcribe(
        self,
        audio: str,
        language: str | None = None,
        task: str = ...,
        beam_size: int = 5,
        best_of: int = 5,
        patience: float = 1,
        length_penalty: float = 1,
        temperature: float | list[float] = ...,
        compression_ratio_threshold: float | None = ...,
        log_prob_threshold: float | None = ...,
        no_speech_threshold: float | None = ...,
        condition_on_previous_text: bool = True,
        initial_prompt: str | None = None,
        word_timestamps: bool = False,
        prepend_punctuations: str = ...,
        append_punctuations: str = ...,
        vad_filter: bool = False,
        vad_parameters: dict | None = None,
    ) -> tuple[Iterator[Any], Any]: ...
