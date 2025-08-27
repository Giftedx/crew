from __future__ import annotations

"""Deterministic PII pattern detector."""

from dataclasses import dataclass
import re
from typing import List

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[ -]?)?(?:\d{3}[ -]?){2}\d{4}\b")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
IPV6_RE = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b")
CREDIT_RE = re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
ADDRESS_RE = re.compile(r"\b\d{1,5}\s+[A-Za-z0-9\.\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b", re.I)
GEO_RE = re.compile(r"\b-?\d{1,2}\.\d+,\s*-?\d{1,3}\.\d+\b")


@dataclass
class Span:
    type: str
    start: int
    end: int
    value: str


def detect(text: str, lang: str = "en") -> List[Span]:
    spans: List[Span] = []
    patterns = {
        "email": EMAIL_RE,
        "phone": PHONE_RE,
        "ip": IPV4_RE,
        "ipv6": IPV6_RE,
        "credit_like": CREDIT_RE,
        "gov_id_like": SSN_RE,
        "address_like": ADDRESS_RE,
        "geo_exact": GEO_RE,
    }
    for typ, regex in patterns.items():
        for m in regex.finditer(text):
            spans.append(Span(typ, m.start(), m.end(), m.group()))
    return spans


__all__ = ["Span", "detect"]
