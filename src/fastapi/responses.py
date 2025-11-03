from __future__ import annotations

import json

from . import Response


class JSONResponse(Response):  # pragma: no cover - minimal wrapper
    def __init__(self, content, status_code: int = 200) -> None:
        super().__init__(json.dumps(content), status_code=status_code, media_type="application/json")

__all__ = ["JSONResponse", "Response"]
