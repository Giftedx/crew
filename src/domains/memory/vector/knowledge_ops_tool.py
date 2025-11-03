from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from platform.core.step_result import StepResult
from typing import Any

from crewai_tools import BaseTool
from pydantic import BaseModel, Field

from kg.creator_kg_store import CreatorKGStore


logger = logging.getLogger(__name__)


class KnowledgeOpsInput(BaseModel):
    """Input schema for knowledge operations."""

    operation: str = Field(..., description="Operation type: search, tag, annotate, share, audit")
    query: str = Field(default="", description="Search query or content to tag/annotate")
    content_id: str = Field(default="", description="ID of content to operate on")
    tags: list[str] = Field(default=[], description="Tags to add or search for")
    annotations: dict[str, Any] = Field(default={}, description="Annotations to add")
    user_id: str = Field(..., description="User performing the operation")
    team_id: str = Field(default="", description="Team context for the operation")
    permissions: list[str] = Field(default=["read"], description="Required permissions")


@dataclass
class KnowledgeItem:
    """Represents a knowledge item with metadata."""

    item_id: str
    content_type: str
    title: str
    content: str
    tags: list[str]
    annotations: dict[str, Any]
    created_by: str
    created_at: datetime
    modified_by: str
    modified_at: datetime
    team_id: str
    permissions: list[str]
    url: str = ""
    metadata: dict[str, Any] = None


@dataclass
class SearchResult:
    """Search result with relevance scoring."""

    item: KnowledgeItem
    relevance_score: float
    matched_fields: list[str]
    highlights: dict[str, str]


@dataclass
class AuditLog:
    """Audit log entry for knowledge operations."""

    log_id: str
    timestamp: datetime
    user_id: str
    team_id: str
    operation: str
    resource_id: str
    resource_type: str
    details: dict[str, Any]
    ip_address: str = ""
    user_agent: str = ""


class KnowledgeOpsTool(BaseTool):
    """
    Cross-Team Knowledge Operations Tool.

    Provides collaborative knowledge management with search, tagging, annotation,
    role-based access control, and audit logging for creator teams.
    """

    name: str = "knowledge_ops_tool"
    description: str = "\n    Cross-team knowledge operations including search, tagging, annotation,\n    sharing, and audit logging. Supports role-based access control and\n    collaborative workflows for creator teams.\n    "
    args_schema: type[BaseModel] = KnowledgeOpsInput

    def __init__(self, kg_store: CreatorKGStore | None = None):
        """Initialize the knowledge ops tool."""
        super().__init__()
        self.kg_store = kg_store or CreatorKGStore(":memory:")
        self.audit_logs: list[AuditLog] = []
        self.user_permissions: dict[str, dict[str, list[str]]] = {}

    def _run(
        self,
        operation: str,
        user_id: str,
        query: str = "",
        content_id: str = "",
        tags: list[str] | None = None,
        annotations: dict[str, Any] | None = None,
        team_id: str = "",
        permissions: list[str] | None = None,
        tenant: str = "",
        workspace: str = "",
    ) -> StepResult:
        """
        Execute knowledge operations.

        Supported operations:
        - search: Search knowledge base
        - tag: Add/remove tags from content
        - annotate: Add annotations to content
        - share: Share content with team members
        - audit: View audit logs
        """
        try:
            if tags is None:
                tags = []
            if annotations is None:
                annotations = {}
            if permissions is None:
                permissions = ["read"]
            logger.info(f"Knowledge operation: {operation} by user {user_id}")
            required_permissions = self._get_required_permissions(operation)
            if not self._check_permissions(user_id, team_id, required_permissions):
                return StepResult.fail(f"Insufficient permissions for user {user_id}")
            if operation == "search":
                result = self._search_knowledge(query, team_id, user_id)
            elif operation == "tag":
                result = self._tag_content(content_id, tags, user_id, team_id)
            elif operation == "annotate":
                result = self._annotate_content(content_id, annotations, user_id, team_id)
            elif operation == "share":
                result = self._share_content(content_id, team_id, user_id)
            elif operation == "audit":
                result = self._get_audit_logs(team_id, user_id)
            else:
                return StepResult.fail(f"Unknown operation: {operation}")
            self._log_operation(user_id, team_id, operation, content_id or query, result)
            return result
        except Exception as e:
            logger.error(f"Knowledge operation failed: {e!s}")
            return StepResult.fail(f"Knowledge operation failed: {e!s}")

    def _get_required_permissions(self, operation: str) -> list[str]:
        """Get required permissions for an operation."""
        permission_map = {
            "search": ["read"],
            "audit": ["read"],
            "tag": ["write"],
            "annotate": ["write"],
            "share": ["write"],
        }
        return permission_map.get(operation, ["read"])

    def _check_permissions(self, user_id: str, team_id: str, required_permissions: list[str]) -> bool:
        """Check if user has required permissions for the team."""
        user_team_permissions = self.user_permissions.get(user_id, {}).get(team_id, [])
        if "admin" in user_team_permissions:
            return True
        return all(perm in user_team_permissions for perm in required_permissions)

    def _search_knowledge(self, query: str, team_id: str, user_id: str) -> StepResult:
        """Search the knowledge base."""
        try:
            mock_results = self._get_mock_search_results(query, team_id)
            search_results = []
            for item_data in mock_results:
                item = KnowledgeItem(
                    item_id=item_data["item_id"],
                    content_type=item_data["content_type"],
                    title=item_data["title"],
                    content=item_data["content"],
                    tags=item_data["tags"],
                    annotations=item_data["annotations"],
                    created_by=item_data["created_by"],
                    created_at=datetime.fromisoformat(item_data["created_at"]),
                    modified_by=item_data["modified_by"],
                    modified_at=datetime.fromisoformat(item_data["modified_at"]),
                    team_id=item_data["team_id"],
                    permissions=item_data["permissions"],
                    url=item_data.get("url", ""),
                    metadata=item_data.get("metadata", {}),
                )
                result = SearchResult(
                    item=item,
                    relevance_score=item_data["relevance_score"],
                    matched_fields=item_data["matched_fields"],
                    highlights=item_data["highlights"],
                )
                search_results.append(result)
            return StepResult.ok(
                data={
                    "operation": "search",
                    "query": query,
                    "results": [self._serialize_search_result(r) for r in search_results],
                    "total_results": len(search_results),
                    "search_time_ms": 50,
                }
            )
        except Exception as e:
            logger.error(f"Search failed: {e!s}")
            return StepResult.fail(f"Search failed: {e!s}")

    def _tag_content(self, content_id: str, tags: list[str], user_id: str, team_id: str) -> StepResult:
        """Add or remove tags from content."""
        try:
            existing_tags = ["existing_tag1", "existing_tag2"]
            updated_tags = list(set(existing_tags + tags))
            return StepResult.ok(
                data={
                    "operation": "tag",
                    "content_id": content_id,
                    "tags_added": tags,
                    "updated_tags": updated_tags,
                    "user_id": user_id,
                    "team_id": team_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Tagging failed: {e!s}")
            return StepResult.fail(f"Tagging failed: {e!s}")

    def _annotate_content(self, content_id: str, annotations: dict[str, Any], user_id: str, team_id: str) -> StepResult:
        """Add annotations to content."""
        try:
            existing_annotations = {"existing_key": "existing_value"}
            updated_annotations = {**existing_annotations, **annotations}
            return StepResult.ok(
                data={
                    "operation": "annotate",
                    "content_id": content_id,
                    "annotations_added": annotations,
                    "updated_annotations": updated_annotations,
                    "user_id": user_id,
                    "team_id": team_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Annotation failed: {e!s}")
            return StepResult.fail(f"Annotation failed: {e!s}")

    def _share_content(self, content_id: str, team_id: str, user_id: str) -> StepResult:
        """Share content with team members."""
        try:
            shared_with = ["user1", "user2", "user3"]
            return StepResult.ok(
                data={
                    "operation": "share",
                    "content_id": content_id,
                    "team_id": team_id,
                    "shared_with": shared_with,
                    "shared_by": user_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Sharing failed: {e!s}")
            return StepResult.fail(f"Sharing failed: {e!s}")

    def _get_audit_logs(self, team_id: str, user_id: str) -> StepResult:
        """Get audit logs for the team."""
        try:
            team_logs = [log for log in self.audit_logs if log.team_id == team_id]
            return StepResult.ok(
                data={
                    "operation": "audit",
                    "team_id": team_id,
                    "logs": [self._serialize_audit_log(log) for log in team_logs],
                    "total_logs": len(team_logs),
                    "requested_by": user_id,
                }
            )
        except Exception as e:
            logger.error(f"Audit log retrieval failed: {e!s}")
            return StepResult.fail(f"Audit log retrieval failed: {e!s}")

    def _get_mock_search_results(self, query: str, team_id: str) -> list[dict[str, Any]]:
        """Get mock search results for testing."""
        mock_results = [
            {
                "item_id": "item_001",
                "content_type": "episode",
                "title": "H3 Podcast #123 - Triller Lawsuit Discussion",
                "content": "Ethan and Hila discuss the ongoing Triller lawsuit and their confidence in winning the case...",
                "tags": ["legal", "lawsuit", "triller", "podcast"],
                "annotations": {"sentiment": "positive", "confidence": 0.85},
                "created_by": "h3_team",
                "created_at": "2024-02-15T10:30:00Z",
                "modified_by": "h3_team",
                "modified_at": "2024-02-15T10:30:00Z",
                "team_id": team_id,
                "permissions": ["read", "write"],
                "url": "https://youtube.com/watch?v=xyz123",
                "metadata": {"duration": 3600, "views": 500000},
                "relevance_score": 0.92,
                "matched_fields": ["title", "content"],
                "highlights": {
                    "title": "H3 Podcast #123 - <mark>Triller Lawsuit</mark> Discussion",
                    "content": "Ethan and Hila discuss the ongoing <mark>Triller lawsuit</mark> and their confidence...",
                },
            },
            {
                "item_id": "item_002",
                "content_type": "claim",
                "title": "Triller Lawsuit Evidence",
                "content": "Key evidence supporting the Triller lawsuit case including court filings and expert opinions...",
                "tags": ["legal", "evidence", "triller", "court"],
                "annotations": {"verified": True, "source_quality": "high"},
                "created_by": "legal_team",
                "created_at": "2024-02-14T15:45:00Z",
                "modified_by": "legal_team",
                "modified_at": "2024-02-14T15:45:00Z",
                "team_id": team_id,
                "permissions": ["read"],
                "url": "https://legal-docs.com/triller-evidence",
                "metadata": {"document_type": "legal_brief", "pages": 25},
                "relevance_score": 0.88,
                "matched_fields": ["title", "content", "tags"],
                "highlights": {
                    "title": "<mark>Triller Lawsuit</mark> Evidence",
                    "content": "Key evidence supporting the <mark>Triller lawsuit</mark> case including...",
                },
            },
        ]
        filtered_results = [r for r in mock_results if r["team_id"] == team_id]
        return filtered_results

    def _log_operation(self, user_id: str, team_id: str, operation: str, resource_id: str, result: StepResult) -> None:
        """Log an operation for audit purposes."""
        log_entry = AuditLog(
            log_id=f"log_{int(time.time() * 1000)}",
            timestamp=datetime.now(),
            user_id=user_id,
            team_id=team_id,
            operation=operation,
            resource_id=resource_id,
            resource_type="knowledge_item",
            details={
                "success": result.success,
                "operation_data": result.data if result.success else {"error": result.error},
            },
            ip_address="127.0.0.1",
            user_agent="KnowledgeOpsTool/1.0",
        )
        self.audit_logs.append(log_entry)

    def _serialize_search_result(self, result: SearchResult) -> dict[str, Any]:
        """Serialize a search result to a dictionary."""
        return {
            "item": {
                "item_id": result.item.item_id,
                "content_type": result.item.content_type,
                "title": result.item.title,
                "content": result.item.content,
                "tags": result.item.tags,
                "annotations": result.item.annotations,
                "created_by": result.item.created_by,
                "created_at": result.item.created_at.isoformat(),
                "modified_by": result.item.modified_by,
                "modified_at": result.item.modified_at.isoformat(),
                "team_id": result.item.team_id,
                "permissions": result.item.permissions,
                "url": result.item.url,
                "metadata": result.item.metadata or {},
            },
            "relevance_score": result.relevance_score,
            "matched_fields": result.matched_fields,
            "highlights": result.highlights,
        }

    def _serialize_audit_log(self, log: AuditLog) -> dict[str, Any]:
        """Serialize an audit log to a dictionary."""
        return {
            "log_id": log.log_id,
            "timestamp": log.timestamp.isoformat(),
            "user_id": log.user_id,
            "team_id": log.team_id,
            "operation": log.operation,
            "resource_id": log.resource_id,
            "resource_type": log.resource_type,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
        }

    def set_user_permissions(self, user_id: str, team_id: str, permissions: list[str]) -> None:
        """Set permissions for a user in a team (for testing)."""
        if user_id not in self.user_permissions:
            self.user_permissions[user_id] = {}
        self.user_permissions[user_id][team_id] = permissions
