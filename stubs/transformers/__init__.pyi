"""Type stubs for transformers (Hugging Face) package."""

from typing import Any

class PreTrainedModel: ...
class PreTrainedTokenizer: ...

class Pipeline:
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

def pipeline(
    task: str,
    model: str | None = None,
    tokenizer: str | None = None,
    device: int | str | None = None,
    torch_dtype: Any = None,
    **kwargs: Any,
) -> Pipeline: ...

class AutoModel:
    @classmethod
    def from_pretrained(cls, model_name: str, **kwargs: Any) -> PreTrainedModel: ...

class AutoTokenizer:
    @classmethod
    def from_pretrained(cls, model_name: str, **kwargs: Any) -> PreTrainedTokenizer: ...
