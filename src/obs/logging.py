"""Structured JSON logging with basic redaction."""

from __future__ import annotations

import json
import logging
from typing import Any

from core.privacy import privacy_filter
from ultimate_discord_intelligence_bot.tenancy import current_tenant


class JsonLogger(logging.Logger):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.addHandler(handler)
        self.setLevel(logging.INFO)

    def _serialize(self, message: str, **fields: Any) -> str:
        clean, report = privacy_filter.filter_text(message, {})
        payload: dict[str, Any] = {"msg": clean, **fields, "redactions": report.found}
        ctx = current_tenant()
        if ctx:
            payload.setdefault("tenant", ctx.tenant_id)
            payload.setdefault("workspace", ctx.workspace_id)
        return json.dumps(payload, ensure_ascii=False)

    def info(self, message: str, **fields: Any) -> None:  # type: ignore[override]
        super().info(self._serialize(message, **fields))


logger = JsonLogger("obs")

__all__ = ["JsonLogger", "logger"]
