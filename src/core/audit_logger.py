"""Comprehensive audit logging system for security and compliance monitoring.

This module provides detailed audit trails for all system operations,
including user actions, data access, security events, and compliance tracking.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events for classification and alerting."""

    # Authentication events
    AUTH_LOGIN = "auth_login"
    AUTH_LOGOUT = "auth_logout"
    AUTH_FAILED = "auth_failed"
    AUTH_TOKEN_REFRESH = "auth_token_refresh"

    # Data access events
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"

    # User actions
    USER_ACTION = "user_action"
    COMMAND_EXECUTED = "command_executed"
    QUERY_EXECUTED = "query_executed"

    # System events
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    CONFIG_CHANGE = "config_change"
    BACKUP_CREATED = "backup_created"

    # Security events
    SECURITY_VIOLATION = "security_violation"
    PRIVACY_BREACH = "privacy_breach"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

    # Performance events
    PERFORMANCE_DEGRADATION = "performance_degradation"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SERVICE_UNAVAILABLE = "service_unavailable"

    # Compliance events
    GDPR_REQUEST = "gdpr_request"
    DATA_RETENTION_VIOLATION = "data_retention_violation"
    AUDIT_ACCESS = "audit_access"


@dataclass
class AuditEvent:
    """Represents a single audit event."""

    event_type: AuditEventType
    timestamp: float
    user_id: str | None = None
    tenant_id: str | None = None
    workspace_id: str | None = None
    operation_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    action: str
    details: dict[str, Any] = field(default_factory=dict)
    ip_address: str | None = None
    user_agent: str | None = None
    session_id: str | None = None
    severity: str = "info"  # "info", "warning", "error", "critical"
    success: bool = True
    error_message: str | None = None
    result_size: int | None = None
    execution_time_ms: float | None = None

    @property
    def event_id(self) -> str:
        """Generate unique event ID."""
        content = f"{self.event_type.value}:{self.timestamp}:{self.user_id}:{self.operation_id}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for storage."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "tenant_id": self.user_id,
            "workspace_id": self.workspace_id,
            "operation_id": self.operation_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "severity": self.severity,
            "success": self.success,
            "error_message": self.error_message,
            "result_size": self.result_size,
            "execution_time_ms": self.execution_time_ms,
        }


class AuditLogger:
    """Comprehensive audit logging system."""

    def __init__(
        self,
        log_file: str | None = None,
        max_file_size_mb: int = 100,
        backup_count: int = 5,
        enable_console: bool = True,
        enable_file: bool = True,
        enable_database: bool = False,
    ):
        self.log_file = log_file
        self.max_file_size_mb = max_file_size_mb
        self.backup_count = backup_count
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_database = enable_database

        # Event storage
        self.events_buffer: list[AuditEvent] = []
        self.buffer_size = 1000
        self.flush_interval = 30.0  # seconds
        self.last_flush = time.time()

        # Statistics
        self.event_counts: dict[str, int] = defaultdict(int)
        self.error_counts: dict[str, int] = defaultdict(int)

        # Security event tracking
        self.security_events: list[AuditEvent] = []
        self.failed_login_attempts: dict[str, list[float]] = defaultdict(list)

        # Setup logging
        self._setup_logging()

        # Start background flusher
        self._start_background_flushing()

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                fmt="%(asctime)s - AUDIT - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # File handler
        if self.enable_file and self.log_file:
            # Create log directory if needed
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # File handler with rotation
            from logging.handlers import RotatingFileHandler

            file_handler = RotatingFileHandler(
                self.log_file, maxBytes=self.max_file_size_mb * 1024 * 1024, backupCount=self.backup_count
            )
            file_formatter = logging.Formatter(
                fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def log_event(self, event: AuditEvent) -> None:
        """Log an audit event."""
        # Update statistics
        self.event_counts[event.event_type.value] += 1
        if not event.success:
            self.error_counts[event.event_type.value] += 1

        # Store in buffer
        self.events_buffer.append(event)

        # Special handling for security events
        if event.event_type in [
            AuditEventType.AUTH_FAILED,
            AuditEventType.SECURITY_VIOLATION,
            AuditEventType.UNAUTHORIZED_ACCESS,
            AuditEventType.PRIVACY_BREACH,
        ]:
            self.security_events.append(event)

        # Immediate flush for critical events
        if event.severity in ["error", "critical"]:
            self.flush()

        # Log to structured logger
        log_level = {
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }.get(event.severity, logging.INFO)

        self.logger.log(
            log_level,
            f"{event.event_type.value}: {event.action}",
            extra={
                "event_id": event.event_id,
                "user_id": event.user_id,
                "tenant_id": event.tenant_id,
                "operation_id": event.operation_id,
                "success": event.success,
                "details": json.dumps(event.details),
            },
        )

    def log_auth_event(
        self,
        action: str,
        user_id: str | None = None,
        success: bool = True,
        error_message: str | None = None,
        ip_address: str | None = None,
        session_id: str | None = None,
        **details,
    ) -> None:
        """Log authentication-related events."""
        event_type = AuditEventType.AUTH_LOGIN if action == "login" else AuditEventType.AUTH_FAILED
        severity = "error" if not success else "info"

        event = AuditEvent(
            event_type=event_type,
            timestamp=time.time(),
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address,
            session_id=session_id,
            severity=severity,
            success=success,
            error_message=error_message,
        )

        self.log_event(event)

        # Track failed login attempts for security monitoring
        if not success and user_id:
            self.failed_login_attempts[user_id].append(time.time())

            # Clean old attempts (keep last 24 hours)
            cutoff = time.time() - (24 * 3600)
            self.failed_login_attempts[user_id] = [
                attempt_time for attempt_time in self.failed_login_attempts[user_id] if attempt_time > cutoff
            ]

    def log_data_access(
        self,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        user_id: str | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
        success: bool = True,
        result_size: int | None = None,
        execution_time_ms: float | None = None,
        **details,
    ) -> None:
        """Log data access events."""
        event_type = {
            "read": AuditEventType.DATA_ACCESS,
            "write": AuditEventType.DATA_MODIFY,
            "delete": AuditEventType.DATA_DELETE,
            "export": AuditEventType.DATA_EXPORT,
        }.get(action, AuditEventType.DATA_ACCESS)

        event = AuditEvent(
            event_type=event_type,
            timestamp=time.time(),
            user_id=user_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details,
            severity="info" if success else "warning",
            success=success,
            result_size=result_size,
            execution_time_ms=execution_time_ms,
        )

        self.log_event(event)

    def log_system_event(
        self, action: str, component: str, success: bool = True, error_message: str | None = None, **details
    ) -> None:
        """Log system-level events."""
        event_type = {
            "start": AuditEventType.SYSTEM_START,
            "stop": AuditEventType.SYSTEM_STOP,
            "config_change": AuditEventType.CONFIG_CHANGE,
            "backup": AuditEventType.BACKUP_CREATED,
        }.get(action, AuditEventType.SYSTEM_START)

        event = AuditEvent(
            event_type=event_type,
            timestamp=time.time(),
            action=action,
            details={"component": component, **details},
            severity="info" if success else "error",
            success=success,
            error_message=error_message,
        )

        self.log_event(event)

    def log_security_event(
        self,
        action: str,
        violation_type: str,
        user_id: str | None = None,
        tenant_id: str | None = None,
        ip_address: str | None = None,
        severity: str = "warning",
        **details,
    ) -> None:
        """Log security-related events."""
        event = AuditEvent(
            event_type=AuditEventType.SECURITY_VIOLATION,
            timestamp=time.time(),
            user_id=user_id,
            tenant_id=tenant_id,
            action=action,
            details={"violation_type": violation_type, **details},
            ip_address=ip_address,
            severity=severity,
            success=False,
        )

        self.log_event(event)

    def log_privacy_event(
        self,
        action: str,
        data_type: str,
        user_id: str | None = None,
        tenant_id: str | None = None,
        severity: str = "warning",
        **details,
    ) -> None:
        """Log privacy-related events."""
        event = AuditEvent(
            event_type=AuditEventType.PRIVACY_BREACH,
            timestamp=time.time(),
            user_id=user_id,
            tenant_id=tenant_id,
            action=action,
            details={"data_type": data_type, **details},
            severity=severity,
            success=False,
        )

        self.log_event(event)

    def flush(self) -> None:
        """Flush buffered events to storage."""
        if not self.events_buffer:
            return

        events_to_flush = self.events_buffer.copy()
        self.events_buffer.clear()

        # Write to file if enabled
        if self.enable_file and self.log_file:
            self._write_events_to_file(events_to_flush)

        # Write to database if enabled
        if self.enable_database:
            self._write_events_to_database(events_to_flush)

        self.last_flush = time.time()

    def _write_events_to_file(self, events: list[AuditEvent]) -> None:
        """Write events to log file."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                for event in events:
                    json_line = json.dumps(event.to_dict(), default=str)
                    f.write(json_line + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit events to file: {e}")

    def _write_events_to_database(self, events: list[AuditEvent]) -> None:
        """Write events to database."""
        # This would implement database storage
        # For now, just log
        logger.debug(f"Would write {len(events)} events to database")

    def _start_background_flushing(self) -> None:
        """Start background task to flush events periodically."""

        def flush_task():
            while True:
                time.sleep(self.flush_interval)
                self.flush()

        import threading

        flush_thread = threading.Thread(target=flush_task, daemon=True)
        flush_thread.start()

    def get_security_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get security event summary for monitoring."""
        cutoff_time = time.time() - (hours * 3600)

        recent_security_events = [event for event in self.security_events if event.timestamp > cutoff_time]

        failed_logins = defaultdict(list)
        for event in recent_security_events:
            if event.event_type == AuditEventType.AUTH_FAILED and event.user_id:
                failed_logins[event.user_id].append(event.timestamp)

        # Count events by type
        events_by_type = defaultdict(int)
        for event in recent_security_events:
            events_by_type[event.event_type.value] += 1

        return {
            "time_window_hours": hours,
            "total_security_events": len(recent_security_events),
            "events_by_type": dict(events_by_type),
            "failed_login_attempts": {user_id: len(attempts) for user_id, attempts in failed_logins.items()},
            "high_severity_events": len(
                [event for event in recent_security_events if event.severity in ["error", "critical"]]
            ),
        }

    def get_audit_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get audit summary for compliance reporting."""
        cutoff_time = time.time() - (hours * 3600)

        recent_events = [event for event in self.events_buffer if event.timestamp > cutoff_time]

        # Group by event type
        events_by_type = defaultdict(int)
        for event in recent_events:
            events_by_type[event.event_type.value] += 1

        # Calculate success rates
        success_rates = {}
        for event_type in self.event_counts:
            total = self.event_counts[event_type]
            errors = self.error_counts.get(event_type, 0)
            success_rates[event_type] = (total - errors) / total if total > 0 else 1.0

        return {
            "time_window_hours": hours,
            "total_events": len(recent_events),
            "events_by_type": dict(events_by_type),
            "success_rates": success_rates,
            "error_counts": dict(self.error_counts),
            "buffer_size": len(self.events_buffer),
            "last_flush": self.last_flush,
        }

    def query_audit_events(
        self,
        event_type: AuditEventType | None = None,
        user_id: str | None = None,
        tenant_id: str | None = None,
        start_time: float | None = None,
        end_time: float | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Query audit events with filtering."""
        events = self.events_buffer.copy()

        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if user_id:
            events = [e for e in events if e.user_id == user_id]

        if tenant_id:
            events = [e for e in events if e.tenant_id == tenant_id]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        # Sort by timestamp (most recent first)
        events.sort(key=lambda e: e.timestamp, reverse=True)

        return events[:limit]

    def export_audit_log(
        self, start_time: float | None = None, end_time: float | None = None, format: str = "json"
    ) -> str:
        """Export audit events in various formats."""
        events = self.query_audit_events(
            start_time=start_time,
            end_time=end_time,
            limit=10000,  # Reasonable limit for export
        )

        if format == "json":
            return json.dumps(
                {
                    "audit_events": [event.to_dict() for event in events],
                    "export_metadata": {
                        "exported_at": time.time(),
                        "total_events": len(events),
                        "filters_applied": {
                            "start_time": start_time,
                            "end_time": end_time,
                        },
                    },
                },
                indent=2,
                default=str,
            )

        elif format == "csv":
            # CSV format for analysis tools
            if not events:
                return "No events to export"

            # Header
            csv_lines = ["event_id,event_type,timestamp,user_id,tenant_id,action,success,severity"]

            for event in events:
                csv_lines.append(
                    f"{event.event_id},{event.event_type.value},{event.timestamp},"
                    f"{event.user_id or ''},{event.tenant_id or ''},"
                    f"{event.action},{event.success},{event.severity}"
                )

            return "\n".join(csv_lines)

        else:
            return f"Unsupported export format: {format}"


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger."""
    global _audit_logger

    if _audit_logger is None:
        # Configure with reasonable defaults
        log_file = "logs/audit.log"
        _audit_logger = AuditLogger(
            log_file=log_file,
            max_file_size_mb=50,
            backup_count=10,
            enable_console=True,
            enable_file=True,
            enable_database=False,  # Could be enabled for production
        )
    return _audit_logger


# Convenience functions for common audit events
def log_user_action(
    action: str,
    user_id: str | None = None,
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    operation_id: str | None = None,
    success: bool = True,
    **details,
) -> None:
    """Log a user action event."""
    logger = get_audit_logger()
    event = AuditEvent(
        event_type=AuditEventType.USER_ACTION,
        timestamp=time.time(),
        user_id=user_id,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        operation_id=operation_id,
        action=action,
        details=details,
        success=success,
    )
    logger.log_event(event)


def log_command_execution(
    command: str,
    user_id: str | None = None,
    tenant_id: str | None = None,
    success: bool = True,
    execution_time_ms: float | None = None,
    **details,
) -> None:
    """Log a command execution event."""
    logger = get_audit_logger()
    event = AuditEvent(
        event_type=AuditEventType.COMMAND_EXECUTED,
        timestamp=time.time(),
        user_id=user_id,
        tenant_id=tenant_id,
        action=command,
        details=details,
        success=success,
        execution_time_ms=execution_time_ms,
    )
    logger.log_event(event)


def log_data_operation(
    operation: str,
    resource_type: str,
    resource_id: str | None = None,
    user_id: str | None = None,
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    success: bool = True,
    result_size: int | None = None,
    **details,
) -> None:
    """Log a data operation event."""
    logger = get_audit_logger()
    logger.log_data_access(
        action=operation,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        success=success,
        result_size=result_size,
        **details,
    )


def log_security_violation(
    violation_type: str,
    user_id: str | None = None,
    tenant_id: str | None = None,
    ip_address: str | None = None,
    **details,
) -> None:
    """Log a security violation event."""
    logger = get_audit_logger()
    logger.log_security_event(
        action=f"security_violation_{violation_type}",
        violation_type=violation_type,
        user_id=user_id,
        tenant_id=tenant_id,
        ip_address=ip_address,
        severity="warning",
        **details,
    )


def log_privacy_breach(
    breach_type: str, data_type: str, user_id: str | None = None, tenant_id: str | None = None, **details
) -> None:
    """Log a privacy breach event."""
    logger = get_audit_logger()
    logger.log_privacy_event(
        action=f"privacy_breach_{breach_type}",
        data_type=data_type,
        user_id=user_id,
        tenant_id=tenant_id,
        severity="warning",
        **details,
    )


def get_audit_summary(hours: int = 24) -> dict[str, Any]:
    """Get audit summary for monitoring."""
    logger = get_audit_logger()
    return logger.get_audit_summary(hours)


def get_security_summary(hours: int = 24) -> dict[str, Any]:
    """Get security summary for monitoring."""
    logger = get_audit_logger()
    return logger.get_security_summary(hours)


def export_audit_log(start_time: float | None = None, end_time: float | None = None, format: str = "json") -> str:
    """Export audit events."""
    logger = get_audit_logger()
    return logger.export_audit_log(start_time, end_time, format)


def initialize_audit_logging() -> None:
    """Initialize audit logging system."""
    logger = get_audit_logger()
    logger.log_system_event(
        action="audit_system_start",
        component="audit_logger",
        success=True,
    )
    logger.info("Audit logging system initialized")


__all__ = [
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "get_audit_logger",
    "log_user_action",
    "log_command_execution",
    "log_data_operation",
    "log_security_violation",
    "log_privacy_breach",
    "get_audit_summary",
    "get_security_summary",
    "export_audit_log",
    "initialize_audit_logging",
]
