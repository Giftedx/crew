from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from . import Response


if TYPE_CHECKING:
    from collections.abc import Iterable


class JSONResponse(Response):  # pragma: no cover - minimal wrapper
    def __init__(self, content: Any, status_code: int = 200) -> None:
        super().__init__(json.dumps(content), status_code=status_code, media_type="application/json")


class FileResponse(Response):  # pragma: no cover - minimal wrapper
    def __init__(self, path: str, status_code: int = 200, media_type: str = "application/octet-stream") -> None:
        try:
            with open(path, "rb") as f:
                data = f.read()
        except Exception:
            data = b""
        super().__init__(data, status_code=status_code, media_type=media_type)


class StreamingResponse(Response):  # pragma: no cover - lightweight stream wrapper
    def __init__(
        self,
        content: Iterable[bytes] | Iterable[str],
        status_code: int = 200,
        media_type: str | None = None,
    ) -> None:
        # Buffer into a single payload for simplicity in tests
        try:
            body_bytes = b"".join(c if isinstance(c, (bytes, bytearray)) else str(c).encode("utf-8") for c in content)
        except TypeError:
            # If content is a generator, consume it
            body_bytes = b"".join(
                c if isinstance(c, (bytes, bytearray)) else str(c).encode("utf-8") for c in list(content)
            )
        super().__init__(body_bytes, status_code=status_code, media_type=media_type or "application/octet-stream")
