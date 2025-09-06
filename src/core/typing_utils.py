"""Typing helpers for narrowing external decorator effects.

The crewai framework decorators (e.g. ``@agent``, ``@task``) return wrapper
objects that mypy treats as ``Any`` or overly generic, eroding type precision
for the underlying function signature.  We provide a no-op ``@typed``
decorator that re-exposes the original callable's ParamSpec / return type so
subsequent static analysis preserves the intended contract.

Usage:

    from core.typing_utils import typed

    @typed  # outermost so it wraps the *result* of framework decorators
    @agent
    def my_agent(arg: str) -> Agent: ...

Because ``@typed`` is applied last (source order), it receives the already
decorated callable and simply returns it while retaining the original
signature via ParamSpec/TypeVar inference.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def typed(func: Callable[P, R]) -> Callable[P, R]:  # pragma: no cover - pure typing aid
    """Identity decorator that preserves the input function's type.

    Acts as an *outer* wrapper around third-party decorators whose return
    type would otherwise degrade to ``Any``. At runtime this is a zero-cost
    no-op; at type-check time it rebinds the precise generic signature.
    """
    return func


__all__ = ["typed"]
