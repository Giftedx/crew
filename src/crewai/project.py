"""Minimal stub of crewai.project providing decorator shims.

These decorators are used by our codebase to annotate agent, task, and crew
factory methods. In tests/minimal environments we simply return the original
function unchanged.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar


F = TypeVar("F", bound=Callable[..., object])


def agent(fn: F) -> F:  # pragma: no cover - trivial shim
    return fn


def task(fn: F) -> F:  # pragma: no cover - trivial shim
    return fn


def crew(fn: F) -> F:  # pragma: no cover - trivial shim
    return fn
