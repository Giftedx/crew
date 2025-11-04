"""Type stubs for pyannote.metrics package."""

from typing import Any

class DiarizationErrorRate:
    def __init__(self) -> None: ...
    def __call__(self, reference: Any, hypothesis: Any) -> float: ...
