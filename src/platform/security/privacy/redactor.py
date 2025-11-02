"""Apply masking to detected PII spans.

Docstring placed before future import to satisfy Ruff E402.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .pii_detector import Span


def apply(text: str, spans: list[Span], masks: dict[str, str]) -> str:
    if not spans:
        return text
    out = text
    for span in sorted(spans, key=lambda s: s.start, reverse=True):
        mask = masks.get(span.type, "[redacted]")
        rep = f"{mask} (redacted:{span.type})"
        out = out[: span.start] + rep + out[span.end :]
    return out


__all__ = ["apply"]
