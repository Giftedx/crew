"""OpenTelemetry context stub."""

from typing import Any


def attach(context: Any) -> Any:
    """Stub attach function."""
    return None


def detach(token: Any) -> None:
    """Stub detach function."""


def get_current() -> dict:
    """Stub get_current function."""
    return {}


__all__ = ["attach", "detach", "get_current"]
