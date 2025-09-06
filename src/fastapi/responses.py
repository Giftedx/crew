from __future__ import annotations

import json
from typing import Any


class JSONResponse:
    def __init__(self, content: Any, status_code: int = 200) -> None:
        self.status_code = status_code
        self.content = json.dumps(content).encode("utf-8")

__all__ = ["JSONResponse"]

