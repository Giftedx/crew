"""Typed shim around crewai.tools.BaseTool.

crewai exposes an untyped ``BaseTool`` which propagates ``Any`` making subclass
checks noisy under mypy. We define a lightweight Protocol-compatible base
class that mirrors the minimal surface we rely upon to regain type safety for
our internal tools without modifying the third-party dependency.
"""

from __future__ import annotations

from typing import (  # noqa: I001 - single block intentionally grouped for clarity in shim
    Any,
    Generic,
    Protocol,
    TypeVar,
    runtime_checkable,
)


@runtime_checkable
class _BaseToolProto(Protocol):
    """Minimal protocol describing what we rely on from CrewAI tools.

    We intentionally keep the surface area small while still mirroring the
    commonly present ``name`` and ``description`` attributes from the vendor
    BaseTool so future upstream introspection (e.g. auto‑documentation or
    selection UIs) does not break when interacting with our shimmed tools.
    """

    name: str | None  # optional in our internal tools
    description: str | None

    def run(self, *args: Any, **kwargs: Any) -> Any:  # minimal execution surface
        ...  # pragma: no cover


R_co = TypeVar("R_co", covariant=True)


class BaseTool(Generic[R_co]):
    """Generic typed wrapper.

    Subclasses should type their internal ``_run``/``run`` returning structured
    dict payloads or domain objects.  The generic parameter ``R`` captures that
    return type for callers.
    """

    # Common metadata attributes used by our tools
    name: str | None = None
    description: str | None = None

    # We don't add new behaviour—purely for typing.
    def run(self, *args: Any, **kwargs: Any) -> R_co:  # runtime provided by subclass
        """Concrete subclasses must implement.

        Body raises to make misuse explicit at runtime.
        """
        raise NotImplementedError("Subclasses must implement run()")


__all__ = ["BaseTool"]
