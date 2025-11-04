"""Type stubs for pyannote.audio package."""

from typing import Any

class Pipeline:
    def __call__(self, audio: Any, **kwargs: Any) -> Any: ...
    @classmethod
    def from_pretrained(cls, model_name: str, **kwargs: Any) -> Pipeline: ...
