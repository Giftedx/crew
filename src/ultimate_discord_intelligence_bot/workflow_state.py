"""Workflow state management system.

This module provides comprehensive workflow state management capabilities for
tracking, persisting, and managing workflow execution states across the system.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from .step_result import StepResult


if TYPE_CHECKING:
    from .tenancy.context import TenantContext


logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class WorkflowState:
    """Represents the state of a workflow execution."""

    def __init__(
        self,
        workflow_id: str,
        workflow_type: str,
        tenant_context: TenantContext,
        initial_data: dict[str, Any] | None = None,
    ):
        """Initialize workflow state.

        Args:
            workflow_id: Unique workflow identifier
            workflow_type: Type of workflow
            tenant_context: Tenant context for isolation
            initial_data: Initial workflow data
        """
        self.workflow_id = workflow_id
        self.workflow_type = workflow_type
        self.tenant_context = tenant_context
        self.status = WorkflowStatus.PENDING
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None

        # Workflow data and context
        self.data = initial_data or {}
        self.context = {}
        self.metadata = {}

        # Execution tracking
        self.current_step = 0
        self.total_steps = 0
        self.steps_completed = []
        self.steps_failed = []
        self.steps_pending = []

        # Error handling
        self.errors = []
        self.retry_count = 0
        self.max_retries = 3

        # Dependencies and relationships
        self.dependencies = []
        self.dependents = []
        self.parent_workflow: str | None = None
        self.child_workflows: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        """Convert workflow state to dictionary.

        Returns:
            Dictionary representation of workflow state
        """
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "tenant": self.tenant_context.tenant,
            "workspace": self.tenant_context.workspace,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "data": self.data,
            "context": self.context,
            "metadata": self.metadata,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "steps_completed": self.steps_completed,
            "steps_failed": self.steps_failed,
            "steps_pending": self.steps_pending,
            "errors": self.errors,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "dependencies": self.dependencies,
            "dependents": self.dependents,
            "parent_workflow": self.parent_workflow,
            "child_workflows": self.child_workflows,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], tenant_context: TenantContext) -> WorkflowState:
        """Create workflow state from dictionary.

        Args:
            data: Dictionary data
            tenant_context: Tenant context

        Returns:
            Workflow state instance
        """
        workflow = cls(
            workflow_id=data["workflow_id"],
            workflow_type=data["workflow_type"],
            tenant_context=tenant_context,
            initial_data=data.get("data", {}),
        )

        workflow.status = WorkflowStatus(data["status"])
        workflow.created_at = datetime.fromisoformat(data["created_at"])
        workflow.updated_at = datetime.fromisoformat(data["updated_at"])

        if data.get("started_at"):
            workflow.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            workflow.completed_at = datetime.fromisoformat(data["completed_at"])

        workflow.context = data.get("context", {})
        workflow.metadata = data.get("metadata", {})
        workflow.current_step = data.get("current_step", 0)
        workflow.total_steps = data.get("total_steps", 0)
        workflow.steps_completed = data.get("steps_completed", [])
        workflow.steps_failed = data.get("steps_failed", [])
        workflow.steps_pending = data.get("steps_pending", [])
        workflow.errors = data.get("errors", [])
        workflow.retry_count = data.get("retry_count", 0)
        workflow.max_retries = data.get("max_retries", 3)
        workflow.dependencies = data.get("dependencies", [])
        workflow.dependents = data.get("dependents", [])
        workflow.parent_workflow = data.get("parent_workflow")
        workflow.child_workflows = data.get("child_workflows", [])

        return workflow

    def update_status(self, status: WorkflowStatus) -> None:
        """Update workflow status.

        Args:
            status: New status
        """
        self.status = status
        self.updated_at = datetime.now(timezone.utc)

        if status == WorkflowStatus.RUNNING and not self.started_at:
            self.started_at = datetime.now(timezone.utc)
        elif status in [
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        ]:
            self.completed_at = datetime.now(timezone.utc)

    def add_step(self, step_name: str, step_data: dict[str, Any] | None = None) -> None:
        """Add a step to the workflow.

        Args:
            step_name: Name of the step
            step_data: Step data
        """
        step_info = {
            "name": step_name,
            "data": step_data or {},
            "added_at": datetime.now(timezone.utc).isoformat(),
        }

        self.steps_pending.append(step_info)
        self.total_steps = len(self.steps_pending) + len(self.steps_completed) + len(self.steps_failed)

    def complete_step(self, step_name: str, result: dict[str, Any] | None = None) -> None:
        """Mark a step as completed.

        Args:
            step_name: Name of the step
            result: Step result
        """
        # Find and move step from pending to completed
        for i, step in enumerate(self.steps_pending):
            if step["name"] == step_name:
                step["completed_at"] = datetime.now(timezone.utc).isoformat()
                step["result"] = result or {}
                self.steps_completed.append(self.steps_pending.pop(i))
                self.current_step += 1
                break

    def fail_step(self, step_name: str, error: str) -> None:
        """Mark a step as failed.

        Args:
            step_name: Name of the step
            error: Error message
        """
        # Find and move step from pending to failed
        for i, step in enumerate(self.steps_pending):
            if step["name"] == step_name:
                step["failed_at"] = datetime.now(timezone.utc).isoformat()
                step["error"] = error
                self.steps_failed.append(self.steps_pending.pop(i))
                self.errors.append(
                    {
                        "step": step_name,
                        "error": error,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                break

    def add_dependency(self, workflow_id: str) -> None:
        """Add a workflow dependency.

        Args:
            workflow_id: ID of dependent workflow
        """
        if workflow_id not in self.dependencies:
            self.dependencies.append(workflow_id)

    def add_dependent(self, workflow_id: str) -> None:
        """Add a dependent workflow.

        Args:
            workflow_id: ID of dependent workflow
        """
        if workflow_id not in self.dependents:
            self.dependents.append(workflow_id)

    def set_parent(self, parent_workflow_id: str) -> None:
        """Set parent workflow.

        Args:
            parent_workflow_id: ID of parent workflow
        """
        self.parent_workflow = parent_workflow_id

    def add_child(self, child_workflow_id: str) -> None:
        """Add child workflow.

        Args:
            child_workflow_id: ID of child workflow
        """
        if child_workflow_id not in self.child_workflows:
            self.child_workflows.append(child_workflow_id)

    def can_retry(self) -> bool:
        """Check if workflow can be retried.

        Returns:
            True if workflow can be retried
        """
        return self.retry_count < self.max_retries and self.status == WorkflowStatus.FAILED

    def increment_retry(self) -> None:
        """Increment retry count."""
        self.retry_count += 1
        self.status = WorkflowStatus.PENDING
        self.updated_at = datetime.now(timezone.utc)


class WorkflowStateManager:
    """Manages workflow states across the system."""

    def __init__(self):
        """Initialize workflow state manager."""
        self.states: dict[str, WorkflowState] = {}
        self.tenant_states: dict[str, list[str]] = {}  # tenant:workspace -> workflow_ids

    def create_workflow(
        self,
        workflow_type: str,
        tenant_context: TenantContext,
        initial_data: dict[str, Any] | None = None,
    ) -> StepResult:
        """Create a new workflow.

        Args:
            workflow_type: Type of workflow
            tenant_context: Tenant context
            initial_data: Initial workflow data

        Returns:
            StepResult with created workflow state
        """
        try:
            workflow_id = str(uuid.uuid4())
            workflow_state = WorkflowState(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                tenant_context=tenant_context,
                initial_data=initial_data,
            )

            self.states[workflow_id] = workflow_state

            # Track by tenant
            tenant_key = f"{tenant_context.tenant}:{tenant_context.workspace}"
            if tenant_key not in self.tenant_states:
                self.tenant_states[tenant_key] = []
            self.tenant_states[tenant_key].append(workflow_id)

            return StepResult.ok(
                data={
                    "workflow_id": workflow_id,
                    "workflow_state": workflow_state.to_dict(),
                }
            )

        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            return StepResult.fail(f"Workflow creation failed: {e!s}")

    def get_workflow(self, workflow_id: str) -> StepResult:
        """Get workflow state by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            StepResult with workflow state
        """
        try:
            if workflow_id not in self.states:
                return StepResult.fail(f"Workflow {workflow_id} not found")

            workflow_state = self.states[workflow_id]
            return StepResult.ok(data=workflow_state.to_dict())

        except Exception as e:
            logger.error(f"Failed to get workflow {workflow_id}: {e}")
            return StepResult.fail(f"Workflow retrieval failed: {e!s}")

    def update_workflow(self, workflow_id: str, updates: dict[str, Any]) -> StepResult:
        """Update workflow state.

        Args:
            workflow_id: Workflow ID
            updates: Updates to apply

        Returns:
            StepResult with update result
        """
        try:
            if workflow_id not in self.states:
                return StepResult.fail(f"Workflow {workflow_id} not found")

            workflow_state = self.states[workflow_id]

            # Apply updates
            for key, value in updates.items():
                if hasattr(workflow_state, key):
                    setattr(workflow_state, key, value)
                elif key in ["data", "context", "metadata"]:
                    getattr(workflow_state, key).update(value)

            workflow_state.updated_at = datetime.now(timezone.utc)

            return StepResult.ok(data=workflow_state.to_dict())

        except Exception as e:
            logger.error(f"Failed to update workflow {workflow_id}: {e}")
            return StepResult.fail(f"Workflow update failed: {e!s}")

    def delete_workflow(self, workflow_id: str) -> StepResult:
        """Delete workflow state.

        Args:
            workflow_id: Workflow ID

        Returns:
            StepResult with deletion result
        """
        try:
            if workflow_id not in self.states:
                return StepResult.fail(f"Workflow {workflow_id} not found")

            workflow_state = self.states[workflow_id]

            # Remove from tenant tracking
            tenant_key = f"{workflow_state.tenant_context.tenant}:{workflow_state.tenant_context.workspace}"
            if tenant_key in self.tenant_states:
                self.tenant_states[tenant_key] = [wid for wid in self.tenant_states[tenant_key] if wid != workflow_id]

            # Remove from states
            del self.states[workflow_id]

            return StepResult.ok(data={"deleted_workflow_id": workflow_id})

        except Exception as e:
            logger.error(f"Failed to delete workflow {workflow_id}: {e}")
            return StepResult.fail(f"Workflow deletion failed: {e!s}")

    def list_workflows(
        self,
        tenant_context: TenantContext,
        status: WorkflowStatus | None = None,
        workflow_type: str | None = None,
    ) -> StepResult:
        """List workflows for tenant.

        Args:
            tenant_context: Tenant context
            status: Filter by status
            workflow_type: Filter by workflow type

        Returns:
            StepResult with workflow list
        """
        try:
            tenant_key = f"{tenant_context.tenant}:{tenant_context.workspace}"
            workflow_ids = self.tenant_states.get(tenant_key, [])

            workflows = []
            for workflow_id in workflow_ids:
                if workflow_id in self.states:
                    workflow_state = self.states[workflow_id]

                    # Apply filters
                    if status and workflow_state.status != status:
                        continue
                    if workflow_type and workflow_state.workflow_type != workflow_type:
                        continue

                    workflows.append(workflow_state.to_dict())

            return StepResult.ok(
                data={
                    "workflows": workflows,
                    "count": len(workflows),
                    "tenant": tenant_context.tenant,
                    "workspace": tenant_context.workspace,
                }
            )

        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            return StepResult.fail(f"Workflow listing failed: {e!s}")

    def cleanup_completed_workflows(self, tenant_context: TenantContext, older_than_hours: int = 24) -> StepResult:
        """Clean up completed workflows older than specified hours.

        Args:
            tenant_context: Tenant context
            older_than_hours: Age threshold in hours

        Returns:
            StepResult with cleanup results
        """
        try:
            cutoff_time = datetime.now(timezone.utc).timestamp() - (older_than_hours * 3600)
            tenant_key = f"{tenant_context.tenant}:{tenant_context.workspace}"
            workflow_ids = self.tenant_states.get(tenant_key, [])

            cleaned_count = 0
            for workflow_id in workflow_ids[:]:  # Copy list to avoid modification during iteration
                if workflow_id in self.states:
                    workflow_state = self.states[workflow_id]

                    # Check if workflow is completed and old enough
                    if (
                        workflow_state.status
                        in [
                            WorkflowStatus.COMPLETED,
                            WorkflowStatus.FAILED,
                            WorkflowStatus.CANCELLED,
                        ]
                        and workflow_state.completed_at
                        and workflow_state.completed_at.timestamp() < cutoff_time
                    ):
                        # Delete workflow
                        delete_result = self.delete_workflow(workflow_id)
                        if delete_result.success:
                            cleaned_count += 1

            return StepResult.ok(
                data={
                    "cleaned_workflows": cleaned_count,
                    "tenant": tenant_context.tenant,
                    "workspace": tenant_context.workspace,
                }
            )

        except Exception as e:
            logger.error(f"Failed to cleanup workflows: {e}")
            return StepResult.fail(f"Workflow cleanup failed: {e!s}")


# Global workflow state manager
_workflow_manager = WorkflowStateManager()


def create_workflow(
    workflow_type: str,
    tenant_context: TenantContext,
    initial_data: dict[str, Any] | None = None,
) -> StepResult:
    """Create a new workflow.

    Args:
        workflow_type: Type of workflow
        tenant_context: Tenant context
        initial_data: Initial workflow data

    Returns:
        StepResult with created workflow state
    """
    return _workflow_manager.create_workflow(workflow_type, tenant_context, initial_data)


def get_workflow(workflow_id: str) -> StepResult:
    """Get workflow state by ID.

    Args:
        workflow_id: Workflow ID

    Returns:
        StepResult with workflow state
    """
    return _workflow_manager.get_workflow(workflow_id)


def update_workflow(workflow_id: str, updates: dict[str, Any]) -> StepResult:
    """Update workflow state.

    Args:
        workflow_id: Workflow ID
        updates: Updates to apply

    Returns:
        StepResult with update result
    """
    return _workflow_manager.update_workflow(workflow_id, updates)


def delete_workflow(workflow_id: str) -> StepResult:
    """Delete workflow state.

    Args:
        workflow_id: Workflow ID

    Returns:
        StepResult with deletion result
    """
    return _workflow_manager.delete_workflow(workflow_id)


def list_workflows(
    tenant_context: TenantContext,
    status: WorkflowStatus | None = None,
    workflow_type: str | None = None,
) -> StepResult:
    """List workflows for tenant.

    Args:
        tenant_context: Tenant context
        status: Filter by status
        workflow_type: Filter by workflow type

    Returns:
        StepResult with workflow list
    """
    return _workflow_manager.list_workflows(tenant_context, status, workflow_type)


def cleanup_completed_workflows(tenant_context: TenantContext, older_than_hours: int = 24) -> StepResult:
    """Clean up completed workflows older than specified hours.

    Args:
        tenant_context: Tenant context
        older_than_hours: Age threshold in hours

    Returns:
        StepResult with cleanup results
    """
    return _workflow_manager.cleanup_completed_workflows(tenant_context, older_than_hours)
