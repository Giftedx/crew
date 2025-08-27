from __future__ import annotations

"""Deterministic text embedding helper.

This module provides a tiny embedding function suitable for tests and
local development without external model dependencies.  Each text is
hashed with SHA-256 and the resulting bytes are converted into a fixed
-length list of floats in the range [0, 1).
"""

import hashlib
from typing import Iterable, List


def embed(texts: Iterable[str], model_hint: str | None = None) -> List[List[float]]:
    vectors: List[List[float]] = []
    for text in texts:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = [int.from_bytes(h[i : i + 4], "big") / 2 ** 32 for i in range(0, 32, 4)]
        vectors.append(vec)
    return vectors
