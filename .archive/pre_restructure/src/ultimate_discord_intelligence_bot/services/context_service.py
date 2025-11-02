"""
Context Service for managing request context and tenant information.

This module provides centralized context management for the multi-agent
orchestration system, including tenant isolation and request tracking.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from ..step_result import StepResult
from ..tenancy.helpers import require_tenant


logger = logging.getLogger(__name__)


@dataclass
class RequestContext:
    """Context for a request through the system."""

    request_id: str
    tenant: str
    workspace: str
    timestamp: float
    user_id: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] | None = None


class ContextService:
    """Service for managing request context and tenant information."""

    def __init__(self):
        """Initialize context service."""
        self.active_contexts: dict[str, RequestContext] = {}
        self.context_history: list[RequestContext] = []

        logger.info("Initialized ContextService")

    @require_tenant(strict_flag_enabled=False)
    def create_context(
        self,
        tenant: str = "",
        workspace: str = "",
        user_id: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StepResult:
        """Create a new request context.

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            user_id: User identifier
            session_id: Session identifier
            metadata: Additional context metadata

        Returns:
            StepResult with created context
        """
        try:
            request_id = f"req_{int(time.time() * 1000)}"
            context = RequestContext(
                request_id=request_id,
                tenant=tenant,
                workspace=workspace,
                timestamp=time.time(),
                user_id=user_id,
                session_id=session_id,
                metadata=metadata or {},
            )

            self.active_contexts[request_id] = context
            self.context_history.append(context)

            logger.debug("Created context %s for tenant %s", request_id, tenant)

            return StepResult.ok(data={"context": context, "request_id": request_id})

        except Exception as e:
            logger.error("Failed to create context: %s", str(e))
            return StepResult.fail(f"Failed to create context: {e!s}")

    def get_context(self, request_id: str) -> StepResult:
        """Get context by request ID.

        Args:
            request_id: Request identifier

        Returns:
            StepResult with context data
        """
        try:
            if request_id not in self.active_contexts:
                return StepResult.fail(f"Context not found: {request_id}")

            context = self.active_contexts[request_id]
            return StepResult.ok(data={"context": context})

        except Exception as e:
            logger.error("Failed to get context: %s", str(e))
            return StepResult.fail(f"Failed to get context: {e!s}")

    def update_context(
        self,
        request_id: str,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> StepResult:
        """Update context metadata.

        Args:
            request_id: Request identifier
            metadata: Updated metadata
            **kwargs: Additional context updates

        Returns:
            StepResult indicating success/failure
        """
        try:
            if request_id not in self.active_contexts:
                return StepResult.fail(f"Context not found: {request_id}")

            context = self.active_contexts[request_id]

            # Update metadata
            if metadata:
                context.metadata.update(metadata)

            # Update other fields
            for key, value in kwargs.items():
                if hasattr(context, key):
                    setattr(context, key, value)

            logger.debug("Updated context %s", request_id)
            return StepResult.ok(data={"updated": True})

        except Exception as e:
            logger.error("Failed to update context: %s", str(e))
            return StepResult.fail(f"Failed to update context: {e!s}")

    def close_context(self, request_id: str) -> StepResult:
        """Close and archive a context.

        Args:
            request_id: Request identifier

        Returns:
            StepResult indicating success/failure
        """
        try:
            if request_id not in self.active_contexts:
                return StepResult.fail(f"Context not found: {request_id}")

            context = self.active_contexts.pop(request_id)
            context.metadata["closed_at"] = time.time()
            context.metadata["duration"] = time.time() - context.timestamp

            logger.debug("Closed context %s", request_id)
            return StepResult.ok(data={"closed": True, "duration": context.metadata["duration"]})

        except Exception as e:
            logger.error("Failed to close context: %s", str(e))
            return StepResult.fail(f"Failed to close context: {e!s}")

    def get_active_contexts(self) -> StepResult:
        """Get all active contexts.

        Returns:
            StepResult with active contexts
        """
        try:
            return StepResult.ok(data={"active_contexts": list(self.active_contexts.keys())})

        except Exception as e:
            logger.error("Failed to get active contexts: %s", str(e))
            return StepResult.fail(f"Failed to get active contexts: {e!s}")

    def get_context_stats(self) -> StepResult:
        """Get context service statistics.

        Returns:
            StepResult with context statistics
        """
        try:
            stats = {
                "active_contexts": len(self.active_contexts),
                "total_contexts": len(self.context_history),
                "contexts_by_tenant": {},
                "contexts_by_workspace": {},
            }

            # Analyze contexts by tenant and workspace
            for context in self.context_history:
                tenant = context.tenant
                workspace = context.workspace

                if tenant not in stats["contexts_by_tenant"]:
                    stats["contexts_by_tenant"][tenant] = 0
                stats["contexts_by_tenant"][tenant] += 1

                if workspace not in stats["contexts_by_workspace"]:
                    stats["contexts_by_workspace"][workspace] = 0
                stats["contexts_by_workspace"][workspace] += 1

            return StepResult.ok(data=stats)

        except Exception as e:
            logger.error("Failed to get context stats: %s", str(e))
            return StepResult.fail(f"Failed to get context stats: {e!s}")

    async def health_check(self) -> StepResult:
        """Perform health check.

        Returns:
            StepResult with health status
        """
        try:
            return StepResult.ok(data={"status": "healthy", "service": "context"})

        except Exception as e:
            logger.error("Health check failed: %s", str(e))
            return StepResult.fail(f"Health check failed: {e!s}")

    def cleanup_old_contexts(self, max_age_seconds: float = 3600) -> StepResult:
        """Clean up old contexts.

        Args:
            max_age_seconds: Maximum age for contexts in seconds

        Returns:
            StepResult with cleanup results
        """
        try:
            current_time = time.time()
            cleaned_count = 0

            # Clean up active contexts
            to_remove = []
            for request_id, context in self.active_contexts.items():
                if current_time - context.timestamp > max_age_seconds:
                    to_remove.append(request_id)

            for request_id in to_remove:
                self.active_contexts.pop(request_id, None)
                cleaned_count += 1

            # Clean up context history
            self.context_history = [
                ctx for ctx in self.context_history if current_time - ctx.timestamp <= max_age_seconds
            ]

            logger.info("Cleaned up %d old contexts", cleaned_count)
            return StepResult.ok(data={"cleaned_count": cleaned_count})

        except Exception as e:
            logger.error("Failed to cleanup old contexts: %s", str(e))
            return StepResult.fail(f"Failed to cleanup old contexts: {e!s}")
