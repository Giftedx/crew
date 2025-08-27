from __future__ import annotations

"""Placeholder consistency checks for grounded answers."""

from typing import List

from .schema import AnswerContract


def check(contract: AnswerContract) -> List[str]:
    """Return a list of contradiction messages (empty for now)."""

    return []


__all__ = ["check"]
