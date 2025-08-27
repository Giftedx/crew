from __future__ import annotations

"""Apply masking to detected PII spans."""

from typing import Dict, List

from .pii_detector import Span


def apply(text: str, spans: List[Span], masks: Dict[str, str]) -> str:
    if not spans:
        return text
    out = text
    for span in sorted(spans, key=lambda s: s.start, reverse=True):
        mask = masks.get(span.type, "[redacted]")
        rep = f"{mask} (redacted:{span.type})"
        out = out[: span.start] + rep + out[span.end :]
    return out


__all__ = ["apply"]
