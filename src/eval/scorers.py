"""Deterministic scorers for golden evaluation suites."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Sequence


def must_include(output: str, substrings: Sequence[str]) -> bool:
    low = output.lower()
    return all(s.lower() in low for s in substrings)


def forbidden(output: str, substrings: Sequence[str]) -> bool:
    low = output.lower()
    return all(s.lower() not in low for s in substrings)


def classification(pred: str, expected: str) -> bool:
    return pred.strip().lower() == expected.strip().lower()


def claimcheck(pred: str, expected: str) -> bool:
    return classification(pred, expected)


def json_schema(output: str, schema: dict[str, type[Any]]) -> bool:
    try:
        data = json.loads(output)
    except Exception:
        return False
    return all(key in data and isinstance(data[key], typ) for key, typ in schema.items())


__all__ = [
    "claimcheck",
    "classification",
    "forbidden",
    "json_schema",
    "must_include",
]
