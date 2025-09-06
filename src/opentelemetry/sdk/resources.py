from __future__ import annotations

from typing import Any


class Resource:
    @staticmethod
    def create(attrs: dict[str, Any]) -> dict[str, Any]:
        return dict(attrs)

__all__ = ["Resource"]

