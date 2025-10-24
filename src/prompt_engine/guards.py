from __future__ import annotations

import re


"""Prompt guards for enforcing citation markers."""


def has_min_citations(text: str, minimum: int) -> bool:
    """Return ``True`` if ``text`` contains at least ``minimum`` unique markers."""

    markers = set(re.findall(r"\[(\d+)\]", text))
    return len(markers) >= minimum


__all__ = ["has_min_citations"]
