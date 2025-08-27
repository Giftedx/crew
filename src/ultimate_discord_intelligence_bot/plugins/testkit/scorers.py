"""Basic scorer helpers for plugin capability tests.

These predicates are intentionally lightweight so plugin tests remain
fast and deterministic. Scorers return ``True`` when expectations are
met and ``False`` otherwise.
"""
from __future__ import annotations

from typing import Iterable, Callable


def must_include(strs: Iterable[str]) -> Callable[[str], bool]:
    """Return a predicate asserting that all substrings appear.

    Parameters
    ----------
    strs:
        Substrings that must be present in the text under test.
    """

    targets = list(strs)

    def _check(text: str) -> bool:
        return all(s in text for s in targets)

    return _check


def forbidden(strs: Iterable[str]) -> Callable[[str], bool]:
    """Return a predicate asserting that no substrings appear.

    Parameters
    ----------
    strs:
        Substrings that must **not** be present in the text under test.
    """

    targets = list(strs)

    def _check(text: str) -> bool:
        return all(s not in text for s in targets)

    return _check


def must_link(urls: Iterable[str]) -> Callable[[str], bool]:
    """Predicate requiring that all URLs appear in the text.

    This is a thin wrapper around :func:`must_include` kept for clarity in
    plugin manifests.
    """

    return must_include(urls)


def status_ok() -> Callable[[object], bool]:
    """Predicate that passes when the value is truthy."""

    def _check(value: object) -> bool:
        return bool(value)

    return _check


__all__ = [
    "must_include",
    "forbidden",
    "must_link",
    "status_ok",
]
