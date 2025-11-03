"""Maintenance utilities (memory compaction, housekeeping)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..tenancy import current_tenant
from ..tools.memory.memory_compaction_tool import MemoryCompactionTool


if TYPE_CHECKING:
    from platform.core.step_result import StepResult


class MemoryMaintenance:
    """Coordinate memory maintenance actions such as compaction.

    This thin orchestrator wraps MemoryCompactionTool to allow batch compaction
    across multiple logical collections while respecting tenancy context.
    """

    def __init__(self) -> StepResult:
        self._default_collections = ["content", "transcripts", "analysis"]

    def compact(self, collections: list[str] | None = None, max_delete: int | None = None) -> StepResult:
        cols = collections or list(self._default_collections)
        summaries: dict[str, Any] = {}
        for name in cols:
            tool = MemoryCompactionTool(collection=name)
            res = tool.run(collection=name, max_delete=max_delete)
            summaries[name] = {
                "status": res["status"],
                "deleted": res.get("deleted", 0),
                "scanned": res.get("scanned", 0),
                "remaining": res.get("remaining", 0),
                "tenant": f"{getattr(current_tenant(), 'tenant_id', 'default')}:{getattr(current_tenant(), 'workspace_id', 'main')}",
            }
        return summaries


__all__ = ["MemoryMaintenance"]
