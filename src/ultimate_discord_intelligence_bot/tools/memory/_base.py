"""Base classes for memory tools.

This module provides specialized base classes for memory and storage tools
that handle data persistence, retrieval, and management.
"""

from __future__ import annotations

from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class MemoryBaseTool(BaseTool):
    """Base class for memory and storage tools.

    Provides common functionality for tools that handle data persistence,
    retrieval, and management operations.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def validate_tenant_context(self, tenant: str, workspace: str) -> StepResult:
        """Validate tenant and workspace context.

        Args:
            tenant: The tenant identifier
            workspace: The workspace identifier

        Returns:
            StepResult indicating validation success or failure
        """
        if not tenant or not isinstance(tenant, str):
            return StepResult.fail("Invalid tenant: must be a non-empty string")

        if not workspace or not isinstance(workspace, str):
            return StepResult.fail("Invalid workspace: must be a non-empty string")

        if len(tenant.strip()) < 1:
            return StepResult.fail("Tenant cannot be empty")

        if len(workspace.strip()) < 1:
            return StepResult.fail("Workspace cannot be empty")

        return StepResult.ok(data={"tenant": tenant, "workspace": workspace, "valid": True})

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime

        return datetime.utcnow().isoformat()


__all__ = ["MemoryBaseTool"]
