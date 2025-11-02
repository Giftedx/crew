from __future__ import annotations

from typing import Any


# Common resource semantic conventions
SERVICE_NAME = "service.name"
SERVICE_VERSION = "service.version"
SERVICE_INSTANCE_ID = "service.instance.id"


class Resource:
    @staticmethod
    def create(attrs: dict[str, Any]) -> dict[str, Any]:
        return dict(attrs)


__all__ = ["SERVICE_INSTANCE_ID", "SERVICE_NAME", "SERVICE_VERSION", "Resource"]
