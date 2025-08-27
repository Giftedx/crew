from __future__ import annotations

"""Regex-based PII detector.

The detector searches text for simple patterns such as email addresses and
phone numbers. It returns spans with the type, start/end offsets, and value.
The implementation is intentionally conservative and deterministic to keep
false positives low.
"""

from dataclasses import dataclass
import re
from typing import List

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[ -]?)?(?:\d{3}[ -]?){2}\d{4}\b")


@dataclass
class Span:
    type: str
    start: int
    end: int
    value: str


def detect(text: str, lang: str = "en") -> List[Span]:
    """Return a list of PII spans found in ``text``."""
    spans: List[Span] = []
    for match in EMAIL_RE.finditer(text):
        spans.append(Span("email", match.start(), match.end(), match.group()))
    for match in PHONE_RE.finditer(text):
        spans.append(Span("phone", match.start(), match.end(), match.group()))
    return spans

