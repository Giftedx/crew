from __future__ import annotations

"""Prompt guards for enforcing citation markers."""

import re


def has_min_citations(text: str, minimum: int) -> bool:
    """Return ``True`` if ``text`` contains at least ``minimum`` unique markers."""

    markers = set(re.findall(r"\[(\d+)\]", text))
    return len(markers) >= minimum


__all__ = ["has_min_citations"]
