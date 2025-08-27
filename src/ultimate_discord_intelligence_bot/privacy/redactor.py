from __future__ import annotations

"""Apply masking to PII spans according to redaction rules."""

from typing import Dict, List

from .pii_detector import Span


def apply(text: str, spans: List[Span], rules: Dict[str, str]) -> str:
    """Return ``text`` with ``spans`` replaced using ``rules`` masks."""
    if not spans:
        return text
    # Sort spans from end to start so replacements don't affect indices
    spans_sorted = sorted(spans, key=lambda s: s.start, reverse=True)
    out = text
    for span in spans_sorted:
        mask = rules.get(span.type, "[redacted]")
        out = out[: span.start] + mask + out[span.end :]
    return out

