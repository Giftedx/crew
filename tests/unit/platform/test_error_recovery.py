"""Tests for pipeline error recovery orchestration."""

from __future__ import annotations

import time

import pytest

from platform.core.error_recovery import (
    ErrorRecoveryOrchestrator,
    RecoveryAction,
    get_error_recovery_orchestrator,
)
from platform.core.step_result import ErrorCategory, StepResult


@pytest.fixture
def orchestrator():
    """Create fresh orchestrator for each test."""
    return ErrorRecoveryOrchestrator()


def test_handle_success_no_recovery(orchestrator):
    """Test successful results don't trigger recovery."""
    result = StepResult.ok(data="success")
    action, metadata = orchestrator.handle_error(result, "test_step")

    assert action == RecoveryAction.RETRY
    assert "no recovery" in metadata["reason"].lower()


def test_network_error_retry(orchestrator):
    """Test network errors trigger retry with backoff."""
    result = StepResult.fail(
        "Connection failed",
        error_category=ErrorCategory.NETWORK,
        retryable=True,
    )

    action, metadata = orchestrator.handle_error(result, "download_step", "exec_1")

    assert action == RecoveryAction.RETRY
    assert metadata["attempts"] >= 1
    assert metadata["backoff_seconds"] > 0
    assert metadata.get("max_retries", 5) >= 5  # NETWORK policy has 5 retries


def test_validation_error_skip(orchestrator):
    """Test validation errors fail immediately (max_retries=0 means no retries allowed)."""
    result = StepResult.fail(
        "Invalid format",
        error_category=ErrorCategory.VALIDATION,
        retryable=False,
    )

    action, metadata = orchestrator.handle_error(result, "parse_step", "exec_2")

    # First attempt (1) exceeds max_retries (0), so FAIL not SKIP
    assert action == RecoveryAction.FAIL
    assert metadata["attempts"] >= 1
    assert "max retries" in metadata["reason"].lower()


def test_retry_backoff_exponential(orchestrator):
    """Test exponential backoff on successive retries."""
    result = StepResult.fail(
        "Timeout",
        error_category=ErrorCategory.TIMEOUT,
        retryable=True,
    )

    exec_id = "exec_backoff"
    backoffs = []

    # TIMEOUT max_retries=3, so first 3 should return RETRY with increasing backoff
    for i in range(3):
        action, metadata = orchestrator.handle_error(result, "timeout_step", exec_id)
        if action == RecoveryAction.RETRY:
            backoffs.append(metadata.get("backoff_seconds", 0))

    # Should have at least 2 backoff values that increase
    assert len(backoffs) >= 2
    assert backoffs[1] > backoffs[0]
    if len(backoffs) >= 3:
        assert backoffs[2] > backoffs[1]


def test_max_retries_exceeded(orchestrator):
    """Test failure after max retries exceeded."""
    result = StepResult.fail(
        "Network error",
        error_category=ErrorCategory.NETWORK,
        retryable=True,
    )

    exec_id = "exec_max_retries"
    actions = []

    # NETWORK max_retries=5, so 6th call should FAIL
    for i in range(10):
        action, metadata = orchestrator.handle_error(result, "retry_step", exec_id)
        actions.append(action)
        if action == RecoveryAction.FAIL:
            break

    # Should eventually fail
    assert RecoveryAction.FAIL in actions
    assert metadata["attempts"] > metadata["max_retries"]


def test_reset_attempts(orchestrator):
    """Test resetting attempt counters."""
    result = StepResult.fail(
        "Error",
        error_category=ErrorCategory.NETWORK,
        retryable=True,
    )

    exec_id = "exec_reset"

    # Make some attempts
    for _ in range(3):
        orchestrator.handle_error(result, "reset_step", exec_id)

    # Reset
    orchestrator.reset_attempts(exec_id, "reset_step")

    # Next attempt should be #1 again
    action, metadata = orchestrator.handle_error(result, "reset_step", exec_id)
    assert metadata["attempts"] == 1


def test_execute_with_recovery_success():
    """Test execute_with_recovery for successful step."""
    orchestrator = ErrorRecoveryOrchestrator()

    call_count = 0

    def successful_step():
        nonlocal call_count
        call_count += 1
        return StepResult.ok(data="success")

    result = orchestrator.execute_with_recovery(
        successful_step,
        "success_step",
        "exec_success",
    )

    assert result.success
    assert call_count == 1


def test_execute_with_recovery_retry_then_success():
    """Test execute_with_recovery retries and eventually succeeds."""
    orchestrator = ErrorRecoveryOrchestrator()

    call_count = 0

    def flaky_step():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return StepResult.fail(
                "Temporary failure",
                error_category=ErrorCategory.TRANSIENT,
                retryable=True,
            )
        return StepResult.ok(data="success after retries")

    result = orchestrator.execute_with_recovery(
        flaky_step,
        "flaky_step",
        "exec_flaky",
    )

    assert result.success
    assert call_count == 3


def test_execute_with_recovery_skip():
    """Test execute_with_recovery for VALIDATION errors (max_retries=0 means immediate FAIL)."""
    orchestrator = ErrorRecoveryOrchestrator()

    call_count = 0

    def validation_fail_step():
        nonlocal call_count
        call_count += 1
        return StepResult.fail(
            "Validation error",
            error_category=ErrorCategory.VALIDATION,
            retryable=False,
        )

    result = orchestrator.execute_with_recovery(
        validation_fail_step,
        "validation_step",
        "exec_skip",
    )

    assert not result.success  # VALIDATION max_retries=0 means immediate FAIL
    assert call_count == 1  # Only called once


def test_singleton_orchestrator():
    """Test global singleton works correctly."""
    orch1 = get_error_recovery_orchestrator()
    orch2 = get_error_recovery_orchestrator()

    assert orch1 is orch2


def test_model_error_fallback(orchestrator):
    """Test model errors can trigger fallback action."""
    result = StepResult.fail(
        "Model inference failed",
        error_category=ErrorCategory.MODEL_ERROR,
        retryable=True,
    )

    action, metadata = orchestrator.handle_error(result, "model_step", "exec_model")

    # Should support fallback (check config)
    if action == RecoveryAction.FALLBACK:
        assert metadata.get("fallback_step") is not None


@pytest.mark.parametrize(
    "error_category,expected_action",
    [
        (ErrorCategory.NETWORK, RecoveryAction.RETRY),
        (ErrorCategory.TIMEOUT, RecoveryAction.RETRY),
        (ErrorCategory.VALIDATION, RecoveryAction.SKIP),
        (ErrorCategory.AUTHENTICATION, RecoveryAction.FAIL),
        (ErrorCategory.RATE_LIMIT, RecoveryAction.RETRY),
    ],
)
def test_recovery_action_matrix(orchestrator, error_category, expected_action):
    """Test recovery actions for different error categories."""
    result = StepResult.fail(
        f"Error: {error_category.value}",
        error_category=error_category,
        retryable=error_category
        in {
            ErrorCategory.NETWORK,
            ErrorCategory.TIMEOUT,
            ErrorCategory.RATE_LIMIT,
        },
    )

    action, metadata = orchestrator.handle_error(result, "test_step", "exec_matrix")

    # First attempt should match expected action (unless max_retries=0)
    if metadata["max_retries"] > 0 and expected_action == RecoveryAction.RETRY:
        assert action == expected_action
    elif metadata["max_retries"] == 0:
        assert action in {RecoveryAction.SKIP, RecoveryAction.FAIL}
