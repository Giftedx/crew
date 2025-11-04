"""Type stubs for sentence-transformers package."""

from typing import Any

class SentenceTransformer:
    def __init__(
        self,
        model_name_or_path: str,
        device: str | None = None,
        cache_folder: str | None = None,
        **kwargs: Any,
    ) -> None: ...
    def encode(
        self,
        sentences: str | list[str],
        batch_size: int = 32,
        show_progress_bar: bool = False,
        convert_to_numpy: bool = True,
        **kwargs: Any,
    ) -> Any: ...
