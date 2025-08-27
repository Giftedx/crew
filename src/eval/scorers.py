from __future__ import annotations

"""Deterministic scorers for golden evaluation suites."""

from typing import Sequence, Dict
import json


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


def json_schema(output: str, schema: Dict) -> bool:
    try:
        data = json.loads(output)
    except Exception:
        return False
    for key, typ in schema.items():
        if key not in data or not isinstance(data[key], typ):
            return False
    return True

__all__ = [
    "must_include",
    "forbidden",
    "classification",
    "claimcheck",
    "json_schema",
]
