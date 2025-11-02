"""
Audit logging for OAuth and authentication events.

This module provides comprehensive audit logging for authentication events,
scope changes, token operations, and security-related activities.
"""

from __future__ import annotations
import json
import logging
from datetime import UTC, datetime
from typing import Any
from platform.core.step_result import StepResult

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit logger for OAuth and authentication events."""

    def __init__(self, audit_logger: logging.Logger | None = None) -> None:
        """Initialize audit logger.

        Args:
            audit_logger: Custom logger instance. If None, uses default audit logger.
        """
        self.audit_logger = audit_logger or self._create_audit_logger()

    def _create_audit_logger(self) -> logging.Logger:
        """Create audit logger with structured formatting."""
        audit_logger = logging.getLogger("creator_ops.audit")
        audit_logger.setLevel(logging.INFO)
        if not audit_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            audit_logger.addHandler(handler)
            audit_logger.propagate = False
        return audit_logger

    def log_oauth_authorization_request(
        self,
        platform: str,
        tenant: str,
        workspace: str,
        scopes: list[str],
        purpose: str,
        user_id: str | None = None,
        client_ip: str | None = None,
    ) -> None:
        """Log OAuth authorization request.

        Args:
            platform: Platform name
            tenant: Tenant identifier
            workspace: Workspace identifier
            scopes: Requested OAuth scopes
            purpose: Purpose of the authorization
            user_id: Platform user ID
            client_ip: Client IP address
        """
        audit_data = {
            "event_type": "oauth_authorization_request",
            "timestamp": datetime.now(UTC).isoformat(),
            "platform": platform,
            "tenant": tenant,
            "workspace": workspace,
            "user_id": user_id,
            "scopes": scopes,
            "purpose": purpose,
            "client_ip": client_ip,
            "status": "requested",
        }
        self.audit_logger.info(json.dumps(audit_data))

    def log_oauth_authorization_success(
        self,
        platform: str,
        tenant: str,
        workspace: str,
        user_id: str,
        scopes: list[str],
        token_expires_at: datetime | None = None,
    ) -> None:
        """Log successful OAuth authorization.

        Args:
            platform: Platform name
            tenant: Tenant identifier
            workspace: Workspace identifier
            user_id: Platform user ID
            scopes: Granted OAuth scopes
            token_expires_at: Token expiration time
        """
        audit_data = {
            "event_type": "oauth_authorization_success",
            "timestamp": datetime.now(UTC).isoformat(),
            "platform": platform,
            "tenant": tenant,
            "workspace": workspace,
            "user_id": user_id,
            "scopes": scopes,
            "token_expires_at": token_expires_at.isoformat() if token_expires_at else None,
            "status": "success",
        }
        self.audit_logger.info(json.dumps(audit_data))

    def log_oauth_authorization_failure(
        self,
        platform: str,
        tenant: str,
        workspace: str,
        error: str,
        user_id: str | None = None,
        scopes: list[str] | None = None,
    ) -> None:
        """Log failed OAuth authorization.

        Args:
            platform: Platform name
            tenant: Tenant identifier
            workspace: Workspace identifier
            error: Error message
            user_id: Platform user ID
            scopes: Requested scopes
        """
        audit_data = {
            "event_type": "oauth_authorization_failure",
            "timestamp": datetime.now(UTC).isoformat(),
            "platform": platform,
            "tenant": tenant,
            "workspace": workspace,
            "user_id": user_id,
            "scopes": scopes,
            "error": error,
            "status": "failure",
        }
        self.audit_logger.warning(json.dumps(audit_data))

    def log_token_refresh(
        self,
        platform: str,
        tenant: str,
        workspace: str,
        user_id: str,
        success: bool,
        new_expires_at: datetime | None = None,
        error: str | None = None,
    ) -> None:
        """Log token refresh attempt.

        Args:
            platform: Platform name
            tenant: Tenant identifier
            workspace: Workspace identifier
            user_id: Platform user ID
            success: Whether refresh was successful
            new_expires_at: New token expiration time
            error: Error message if failed
        """
        audit_data = {
            "event_type": "token_refresh",
            "timestamp": datetime.now(UTC).isoformat(),
            "platform": platform,
            "tenant": tenant,
            "workspace": workspace,
            "user_id": user_id,
            "success": success,
            "new_expires_at": new_expires_at.isoformat() if new_expires_at else None,
            "error": error,
            "status": "success" if success else "failure",
        }
        if success:
            self.audit_logger.info(json.dumps(audit_data))
        else:
            self.audit_logger.warning(json.dumps(audit_data))

    def log_token_validation(
        self, platform: str, tenant: str, workspace: str, user_id: str, valid: bool, expires_in: int | None = None
    ) -> None:
        """Log token validation.

        Args:
            platform: Platform name
            tenant: Tenant identifier
            workspace: Workspace identifier
            user_id: Platform user ID
            valid: Whether token is valid
            expires_in: Token expiration in seconds
        """
        audit_data = {
            "event_type": "token_validation",
            "timestamp": datetime.now(UTC).isoformat(),
            "platform": platform,
            "tenant": tenant,
            "workspace": workspace,
            "user_id": user_id,
            "valid": valid,
            "expires_in": expires_in,
            "status": "valid" if valid else "invalid",
        }
        self.audit_logger.info(json.dumps(audit_data))

    def log_scope_change(
        self,
        platform: str,
        tenant: str,
        workspace: str,
        user_id: str,
        old_scopes: list[str],
        new_scopes: list[str],
        change_type: str,
        approved_by: str | None = None,
    ) -> None:
        """Log scope change.

        Args:
            platform: Platform name
            tenant: Tenant identifier
            workspace: Workspace identifier
            user_id: Platform user ID
            old_scopes: Previous scopes
            new_scopes: New scopes
            change_type: Type of change (expansion, reduction, modification)
            approved_by: User who approved the change
        """
        audit_data = {
            "event_type": "scope_change",
            "timestamp": datetime.now(UTC).isoformat(),
            "platform": platform,
            "tenant": tenant,
            "workspace": workspace,
            "user_id": user_id,
            "old_scopes": old_scopes,
            "new_scopes": new_scopes,
            "change_type": change_type,
            "approved_by": approved_by,
            "status": "completed",
        }
        self.audit_logger.info(json.dumps(audit_data))

    def log_account_deactivation(
        self, platform: str, tenant: str, workspace: str, user_id: str, reason: str, deactivated_by: str | None = None
    ) -> None:
        """Log account deactivation.

        Args:
            platform: Platform name
            tenant: Tenant identifier
            workspace: Workspace identifier
            user_id: Platform user ID
            reason: Reason for deactivation
            deactivated_by: User who deactivated the account
        """
        audit_data = {
            "event_type": "account_deactivation",
            "timestamp": datetime.now(UTC).isoformat(),
            "platform": platform,
            "tenant": tenant,
            "workspace": workspace,
            "user_id": user_id,
            "reason": reason,
            "deactivated_by": deactivated_by,
            "status": "deactivated",
        }
        self.audit_logger.warning(json.dumps(audit_data))

    def log_security_event(
        self,
        event_type: str,
        platform: str,
        tenant: str,
        workspace: str,
        user_id: str | None,
        details: dict[str, Any],
        severity: str = "medium",
    ) -> None:
        """Log security-related event.

        Args:
            event_type: Type of security event
            platform: Platform name
            tenant: Tenant identifier
            workspace: Workspace identifier
            user_id: Platform user ID
            details: Event details
            severity: Event severity (low, medium, high, critical)
        """
        audit_data = {
            "event_type": "security_event",
            "security_event_type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "platform": platform,
            "tenant": tenant,
            "workspace": workspace,
            "user_id": user_id,
            "severity": severity,
            "details": details,
            "status": "detected",
        }
        if severity in ["high", "critical"]:
            self.audit_logger.error(json.dumps(audit_data))
        else:
            self.audit_logger.warning(json.dumps(audit_data))

    def log_api_access(
        self,
        platform: str,
        tenant: str,
        workspace: str,
        endpoint: str,
        method: str,
        status_code: int,
        user_id: str | None = None,
        response_time_ms: int | None = None,
    ) -> None:
        """Log API access.

        Args:
            platform: Platform name
            tenant: Tenant identifier
            workspace: Workspace identifier
            endpoint: API endpoint
            method: HTTP method
            status_code: HTTP status code
            user_id: Platform user ID
            response_time_ms: Response time in milliseconds
        """
        audit_data = {
            "event_type": "api_access",
            "timestamp": datetime.now(UTC).isoformat(),
            "platform": platform,
            "tenant": tenant,
            "workspace": workspace,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "user_id": user_id,
            "response_time_ms": response_time_ms,
            "status": "success" if 200 <= status_code < 300 else "failure",
        }
        self.audit_logger.info(json.dumps(audit_data))

    def log_rate_limit_exceeded(
        self,
        platform: str,
        tenant: str,
        workspace: str,
        endpoint: str,
        limit_type: str,
        current_usage: int,
        limit: int,
        reset_time: datetime,
    ) -> None:
        """Log rate limit exceeded.

        Args:
            platform: Platform name
            tenant: Tenant identifier
            workspace: Workspace identifier
            endpoint: API endpoint
            limit_type: Type of rate limit (per_minute, per_hour, per_day)
            current_usage: Current usage count
            limit: Rate limit
            reset_time: When the limit resets
        """
        audit_data = {
            "event_type": "rate_limit_exceeded",
            "timestamp": datetime.now(UTC).isoformat(),
            "platform": platform,
            "tenant": tenant,
            "workspace": workspace,
            "endpoint": endpoint,
            "limit_type": limit_type,
            "current_usage": current_usage,
            "limit": limit,
            "reset_time": reset_time.isoformat(),
            "status": "rate_limited",
        }
        self.audit_logger.warning(json.dumps(audit_data))

    def get_audit_events(
        self,
        tenant: str,
        workspace: str,
        platform: str | None = None,
        event_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> StepResult:
        """Get audit events (mock implementation - would query audit store in production).

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            platform: Filter by platform
            event_type: Filter by event type
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of events to return

        Returns:
            StepResult with audit events
        """
        try:
            mock_events = [
                {
                    "event_type": "oauth_authorization_success",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "platform": platform or "youtube",
                    "tenant": tenant,
                    "workspace": workspace,
                    "user_id": "mock_user",
                    "status": "success",
                }
            ]
            return StepResult.ok(
                data={
                    "events": mock_events,
                    "total_count": len(mock_events),
                    "filters_applied": {
                        "tenant": tenant,
                        "workspace": workspace,
                        "platform": platform,
                        "event_type": event_type,
                        "start_time": start_time.isoformat() if start_time else None,
                        "end_time": end_time.isoformat() if end_time else None,
                    },
                }
            )
        except Exception as e:
            logger.error(f"Failed to get audit events: {e!s}")
            return StepResult.fail(f"Audit event retrieval failed: {e!s}")

    def export_audit_log(
        self,
        tenant: str,
        workspace: str,
        fmt: str = "json",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> StepResult:
        """Export audit log (mock implementation).

        Args:
            tenant: Tenant identifier
            workspace: Workspace identifier
            fmt: Export format (json, csv)
            start_time: Start time filter
            end_time: End time filter

        Returns:
            StepResult with export data
        """
        try:
            events_result = self.get_audit_events(
                tenant=tenant, workspace=workspace, start_time=start_time, end_time=end_time, limit=10000
            )
            if not events_result.success:
                return events_result
            events = events_result.data["events"]
            if fmt == "json":
                export_data = json.dumps(events, indent=2)
            elif fmt == "csv":
                if events:
                    headers = list(events[0].keys())
                    csv_lines = [",".join(headers)]
                    for event in events:
                        values = [str(event.get(header, "")) for header in headers]
                        csv_lines.append(",".join(values))
                    export_data = "\n".join(csv_lines)
                else:
                    export_data = ""
            else:
                return StepResult.fail(f"Unsupported export format: {fmt}")
            return StepResult.ok(
                data={
                    "export_data": export_data,
                    "format": format,
                    "event_count": len(events),
                    "export_timestamp": datetime.now(UTC).isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Failed to export audit log: {e!s}")
            return StepResult.fail(f"Audit log export failed: {e!s}")
