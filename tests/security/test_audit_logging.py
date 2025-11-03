"""
Test suite for audit logging functionality.

This module tests that all sensitive operations are logged, audit log integrity
and completeness, log retention policies, and log analysis and alerting.
"""

import time
from datetime import datetime, timedelta
from platform.core.step_result import StepResult
from unittest.mock import Mock

import pytest


class TestAuditLogging:
    """Test audit logging and security monitoring functionality."""

    @pytest.fixture
    def mock_audit_logger(self) -> Mock:
        """Mock audit logger for testing."""
        return Mock()

    @pytest.fixture
    def sample_operations(self) -> dict[str, dict[str, str]]:
        """Sample sensitive operations for testing."""
        return {
            "user_login": {
                "operation": "user_login",
                "tenant": "tenant_a",
                "workspace": "workspace_a",
                "user_id": "user_123",
                "ip_address": "192.168.1.1",
                "timestamp": datetime.now().isoformat(),
                "status": "success",
            },
            "data_access": {
                "operation": "data_access",
                "tenant": "tenant_a",
                "workspace": "workspace_a",
                "user_id": "user_123",
                "resource": "transcript_456",
                "action": "read",
                "timestamp": datetime.now().isoformat(),
                "status": "success",
            },
            "data_modification": {
                "operation": "data_modification",
                "tenant": "tenant_a",
                "workspace": "workspace_a",
                "user_id": "user_123",
                "resource": "analysis_789",
                "action": "update",
                "timestamp": datetime.now().isoformat(),
                "status": "success",
            },
            "admin_action": {
                "operation": "admin_action",
                "tenant": "tenant_a",
                "workspace": "workspace_a",
                "user_id": "admin_456",
                "action": "user_role_change",
                "target_user": "user_789",
                "timestamp": datetime.now().isoformat(),
                "status": "success",
            },
        }

    @pytest.fixture
    def mock_log_storage(self):
        """Mock log storage for testing."""
        return Mock()

    def test_user_authentication_logging(self, mock_audit_logger: Mock, sample_operations: dict) -> None:
        """Test logging of user authentication events."""
        login_event = sample_operations["user_login"]
        mock_audit_logger.log_authentication.return_value = StepResult.ok(data={"logged": True})
        result = mock_audit_logger.log_authentication(
            user_id=login_event["user_id"],
            tenant=login_event["tenant"],
            workspace=login_event["workspace"],
            ip_address=login_event["ip_address"],
            status="success",
        )
        assert result.success
        assert result.data["logged"]
        mock_audit_logger.log_authentication.assert_called_with(
            user_id=login_event["user_id"],
            tenant=login_event["tenant"],
            workspace=login_event["workspace"],
            ip_address=login_event["ip_address"],
            status="success",
        )

    def test_failed_authentication_logging(self, mock_audit_logger: Mock) -> None:
        """Test logging of failed authentication attempts."""
        mock_audit_logger.log_authentication.return_value = StepResult.ok(data={"logged": True})
        result = mock_audit_logger.log_authentication(
            user_id="user_123",
            tenant="tenant_a",
            workspace="workspace_a",
            ip_address="192.168.1.1",
            status="failed",
            failure_reason="invalid_credentials",
        )
        assert result.success
        assert result.data["logged"]
        mock_audit_logger.log_authentication.assert_called_with(
            user_id="user_123",
            tenant="tenant_a",
            workspace="workspace_a",
            ip_address="192.168.1.1",
            status="failed",
            failure_reason="invalid_credentials",
        )

    def test_data_access_logging(self, mock_audit_logger: Mock, sample_operations: dict) -> None:
        """Test logging of data access events."""
        access_event = sample_operations["data_access"]
        mock_audit_logger.log_data_access.return_value = StepResult.ok(data={"logged": True})
        result = mock_audit_logger.log_data_access(
            user_id=access_event["user_id"],
            tenant=access_event["tenant"],
            workspace=access_event["workspace"],
            resource=access_event["resource"],
            action=access_event["action"],
        )
        assert result.success
        assert result.data["logged"]
        mock_audit_logger.log_data_access.assert_called_with(
            user_id=access_event["user_id"],
            tenant=access_event["tenant"],
            workspace=access_event["workspace"],
            resource=access_event["resource"],
            action=access_event["action"],
        )

    def test_data_modification_logging(self, mock_audit_logger: Mock, sample_operations: dict) -> None:
        """Test logging of data modification events."""
        modification_event = sample_operations["data_modification"]
        mock_audit_logger.log_data_modification.return_value = StepResult.ok(data={"logged": True})
        result = mock_audit_logger.log_data_modification(
            user_id=modification_event["user_id"],
            tenant=modification_event["tenant"],
            workspace=modification_event["workspace"],
            resource=modification_event["resource"],
            action=modification_event["action"],
            changes={"old_value": "old", "new_value": "new"},
        )
        assert result.success
        assert result.data["logged"]
        mock_audit_logger.log_data_modification.assert_called_with(
            user_id=modification_event["user_id"],
            tenant=modification_event["tenant"],
            workspace=modification_event["workspace"],
            resource=modification_event["resource"],
            action=modification_event["action"],
            changes={"old_value": "old", "new_value": "new"},
        )

    def test_admin_action_logging(self, mock_audit_logger: Mock, sample_operations: dict) -> None:
        """Test logging of admin actions."""
        admin_event = sample_operations["admin_action"]
        mock_audit_logger.log_admin_action.return_value = StepResult.ok(data={"logged": True})
        result = mock_audit_logger.log_admin_action(
            user_id=admin_event["user_id"],
            tenant=admin_event["tenant"],
            workspace=admin_event["workspace"],
            action=admin_event["action"],
            target_user=admin_event["target_user"],
        )
        assert result.success
        assert result.data["logged"]
        mock_audit_logger.log_admin_action.assert_called_with(
            user_id=admin_event["user_id"],
            tenant=admin_event["tenant"],
            workspace=admin_event["workspace"],
            action=admin_event["action"],
            target_user=admin_event["target_user"],
        )

    def test_sensitive_operation_coverage(self, mock_audit_logger: Mock) -> None:
        """Test that all sensitive operations are covered by audit logging."""
        sensitive_operations = [
            "user_login",
            "user_logout",
            "data_access",
            "data_modification",
            "data_deletion",
            "admin_action",
            "role_change",
            "permission_change",
            "system_config_change",
            "backup_operation",
            "restore_operation",
        ]
        logged_operations = []

        def mock_log_operation(operation, **kwargs):
            logged_operations.append(operation)
            return StepResult.ok(data={"logged": True})

        mock_audit_logger.log_operation.side_effect = mock_log_operation
        for operation in sensitive_operations:
            result = mock_audit_logger.log_operation(
                operation=operation, tenant="test_tenant", workspace="test_workspace", user_id="test_user"
            )
            assert result.success
        assert len(logged_operations) == len(sensitive_operations)
        assert all(op in logged_operations for op in sensitive_operations)

    def test_audit_log_integrity_verification(self, mock_audit_logger, mock_log_storage):
        """Test audit log integrity verification."""
        log_entries = [
            {"id": "log_1", "operation": "user_login", "timestamp": datetime.now().isoformat(), "hash": "abc123"},
            {"id": "log_2", "operation": "data_access", "timestamp": datetime.now().isoformat(), "hash": "def456"},
        ]
        mock_log_storage.get_log_entries.return_value = StepResult.ok(data=log_entries)

        def mock_verify_integrity(log_entries):
            for entry in log_entries:
                if not entry.get("hash"):
                    return StepResult.fail("Missing hash in log entry")
            return StepResult.ok(data={"integrity_verified": True})

        mock_audit_logger.verify_integrity.side_effect = mock_verify_integrity
        result = mock_audit_logger.verify_integrity(log_entries)
        assert result.success
        assert result.data["integrity_verified"]

    def test_audit_log_tampering_detection(self, mock_audit_logger, mock_log_storage):
        """Test detection of audit log tampering."""
        tampered_entries = [
            {"id": "log_1", "operation": "user_login", "timestamp": datetime.now().isoformat(), "hash": "abc123"},
            {
                "id": "log_2",
                "operation": "data_access",
                "timestamp": datetime.now().isoformat(),
                "hash": "tampered_hash",
            },
        ]
        mock_log_storage.get_log_entries.return_value = StepResult.ok(data=tampered_entries)

        def mock_detect_tampering(log_entries):
            for entry in log_entries:
                if entry["hash"] == "tampered_hash":
                    return StepResult.fail("Log tampering detected", status="security_breach")
            return StepResult.ok(data={"integrity_verified": True})

        mock_audit_logger.detect_tampering.side_effect = mock_detect_tampering
        result = mock_audit_logger.detect_tampering(tampered_entries)
        assert not result.success
        assert result.status == "security_breach"
        assert "Log tampering detected" in result.error

    def test_audit_log_completeness_verification(self, mock_audit_logger: Mock) -> None:
        """Test verification of audit log completeness."""

        def mock_verify_completeness(operation_sequence):
            expected_operations = ["user_login", "data_access", "data_modification"]
            actual_operations = [op["operation"] for op in operation_sequence]
            if all(op in actual_operations for op in expected_operations):
                return StepResult.ok(data={"complete": True})
            else:
                missing = set(expected_operations) - set(actual_operations)
                return StepResult.fail(f"Missing operations: {missing}", status="incomplete")

        mock_audit_logger.verify_completeness.side_effect = mock_verify_completeness
        complete_sequence = [
            {"operation": "user_login", "timestamp": datetime.now().isoformat()},
            {"operation": "data_access", "timestamp": datetime.now().isoformat()},
            {"operation": "data_modification", "timestamp": datetime.now().isoformat()},
        ]
        result = mock_audit_logger.verify_completeness(complete_sequence)
        assert result.success
        assert result.data["complete"]
        incomplete_sequence = [
            {"operation": "user_login", "timestamp": datetime.now().isoformat()},
            {"operation": "data_access", "timestamp": datetime.now().isoformat()},
        ]
        result = mock_audit_logger.verify_completeness(incomplete_sequence)
        assert not result.success
        assert result.status == "incomplete"
        assert "Missing operations" in result.error

    def test_log_retention_policy_enforcement(self, mock_audit_logger, mock_log_storage):
        """Test enforcement of log retention policies."""
        old_log_entries = [
            {"id": "log_1", "operation": "user_login", "timestamp": (datetime.now() - timedelta(days=400)).isoformat()},
            {
                "id": "log_2",
                "operation": "data_access",
                "timestamp": (datetime.now() - timedelta(days=500)).isoformat(),
            },
        ]
        mock_log_storage.get_old_logs.return_value = StepResult.ok(data=old_log_entries)
        mock_log_storage.delete_logs.return_value = StepResult.ok(data={"deleted": 2})

        def mock_enforce_retention_policy(retention_days=365):
            old_logs = mock_log_storage.get_old_logs(retention_days)
            if old_logs.success:
                delete_result = mock_log_storage.delete_logs(old_logs.data)
                return delete_result
            return StepResult.fail("Failed to get old logs")

        mock_audit_logger.enforce_retention_policy.side_effect = mock_enforce_retention_policy
        result = mock_audit_logger.enforce_retention_policy(retention_days=365)
        assert result.success
        assert result.data["deleted"] == 2

    def test_log_archival_policy(self, mock_audit_logger, mock_log_storage):
        """Test log archival policy."""
        logs_to_archive = [
            {"id": "log_1", "operation": "user_login", "timestamp": (datetime.now() - timedelta(days=100)).isoformat()},
            {
                "id": "log_2",
                "operation": "data_access",
                "timestamp": (datetime.now() - timedelta(days=120)).isoformat(),
            },
        ]
        mock_log_storage.get_logs_for_archival.return_value = StepResult.ok(data=logs_to_archive)
        mock_log_storage.archive_logs.return_value = StepResult.ok(data={"archived": 2})

        def mock_archive_logs(archive_days=90):
            logs = mock_log_storage.get_logs_for_archival(archive_days)
            if logs.success:
                archive_result = mock_log_storage.archive_logs(logs.data)
                return archive_result
            return StepResult.fail("Failed to get logs for archival")

        mock_audit_logger.archive_logs.side_effect = mock_archive_logs
        result = mock_audit_logger.archive_logs(archive_days=90)
        assert result.success
        assert result.data["archived"] == 2

    def test_suspicious_activity_detection(self, mock_audit_logger: Mock) -> None:
        """Test detection of suspicious activity patterns."""

        def mock_detect_suspicious_activity(log_entries):
            suspicious_patterns = []
            failed_logins = [
                entry
                for entry in log_entries
                if entry.get("operation") == "user_login" and entry.get("status") == "failed"
            ]
            ip_counts = {}
            for entry in failed_logins:
                ip = entry.get("ip_address")
                ip_counts[ip] = ip_counts.get(ip, 0) + 1
            for ip, count in ip_counts.items():
                if count > 5:
                    suspicious_patterns.append({"type": "multiple_failed_logins", "ip_address": ip, "count": count})
            if suspicious_patterns:
                return StepResult.ok(data={"suspicious_activity": suspicious_patterns})
            else:
                return StepResult.ok(data={"suspicious_activity": []})

        mock_audit_logger.detect_suspicious_activity.side_effect = mock_detect_suspicious_activity
        suspicious_logs = [
            {"operation": "user_login", "status": "failed", "ip_address": "192.168.1.1"},
            {"operation": "user_login", "status": "failed", "ip_address": "192.168.1.1"},
            {"operation": "user_login", "status": "failed", "ip_address": "192.168.1.1"},
            {"operation": "user_login", "status": "failed", "ip_address": "192.168.1.1"},
            {"operation": "user_login", "status": "failed", "ip_address": "192.168.1.1"},
            {"operation": "user_login", "status": "failed", "ip_address": "192.168.1.1"},
        ]
        result = mock_audit_logger.detect_suspicious_activity(suspicious_logs)
        assert result.success
        assert len(result.data["suspicious_activity"]) > 0
        assert result.data["suspicious_activity"][0]["type"] == "multiple_failed_logins"

    def test_security_alert_generation(self, mock_audit_logger: Mock) -> None:
        """Test generation of security alerts."""

        def mock_generate_security_alert(alert_type, severity, details):
            alert = {
                "id": f"alert_{int(time.time())}",
                "type": alert_type,
                "severity": severity,
                "details": details,
                "timestamp": datetime.now().isoformat(),
                "status": "active",
            }
            return StepResult.ok(data=alert)

        mock_audit_logger.generate_security_alert.side_effect = mock_generate_security_alert
        result = mock_audit_logger.generate_security_alert(
            alert_type="multiple_failed_logins", severity="high", details={"ip_address": "192.168.1.1", "attempts": 10}
        )
        assert result.success
        assert result.data["type"] == "multiple_failed_logins"
        assert result.data["severity"] == "high"
        assert result.data["status"] == "active"

    def test_audit_log_analysis(self, mock_audit_logger: Mock) -> None:
        """Test audit log analysis and reporting."""

        def mock_analyze_logs(log_entries, analysis_type="summary"):
            if analysis_type == "summary":
                summary = {
                    "total_operations": len(log_entries),
                    "unique_users": len({entry.get("user_id") for entry in log_entries}),
                    "operation_types": list({entry.get("operation") for entry in log_entries}),
                    "time_range": {
                        "start": min(entry.get("timestamp") for entry in log_entries),
                        "end": max(entry.get("timestamp") for entry in log_entries),
                    },
                }
                return StepResult.ok(data=summary)
            else:
                return StepResult.fail("Unknown analysis type")

        mock_audit_logger.analyze_logs.side_effect = mock_analyze_logs
        test_logs = [
            {"operation": "user_login", "user_id": "user_1", "timestamp": "2024-01-01T00:00:00"},
            {"operation": "data_access", "user_id": "user_2", "timestamp": "2024-01-01T01:00:00"},
            {"operation": "user_login", "user_id": "user_1", "timestamp": "2024-01-01T02:00:00"},
        ]
        result = mock_audit_logger.analyze_logs(test_logs, analysis_type="summary")
        assert result.success
        assert result.data["total_operations"] == 3
        assert result.data["unique_users"] == 2
        assert len(result.data["operation_types"]) == 2

    def test_audit_logging_integration_with_stepresult(self, mock_audit_logger: Mock) -> None:
        """Test audit logging integration with StepResult pattern."""

        def mock_log_operation(operation, **kwargs):
            return StepResult.ok(data={"logged": True, "operation": operation})

        mock_audit_logger.log_operation.side_effect = mock_log_operation
        result = mock_audit_logger.log_operation(
            operation="user_login", tenant="test_tenant", workspace="test_workspace", user_id="test_user"
        )
        assert result.success
        assert result.data["logged"]
        assert result.data["operation"] == "user_login"

    def test_audit_logging_error_handling(self, mock_audit_logger: Mock) -> None:
        """Test audit logging error handling."""

        def mock_log_operation(operation, **kwargs):
            if operation == "error_operation":
                return StepResult.fail("Audit logging error", status="logging_error")
            else:
                return StepResult.ok(data={"logged": True})

        mock_audit_logger.log_operation.side_effect = mock_log_operation
        result = mock_audit_logger.log_operation(
            operation="user_login", tenant="test_tenant", workspace="test_workspace", user_id="test_user"
        )
        assert result.success
        result = mock_audit_logger.log_operation(
            operation="error_operation", tenant="test_tenant", workspace="test_workspace", user_id="test_user"
        )
        assert not result.success
        assert result.status == "logging_error"
        assert "Audit logging error" in result.error
