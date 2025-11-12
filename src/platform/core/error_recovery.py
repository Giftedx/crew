"""Pipeline error recovery orchestration.

Provides intelligent error recovery for pipeline steps based on ErrorCategory,
configured via config/error_recovery.yaml.
"""

from __future__ import annotations

import logging
import time
from enum import Enum
from pathlib import Path
from platform.core.step_result import StepResult
from typing import TYPE_CHECKING, Any

import yaml


if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)


class RecoveryAction(Enum):
    """Actions to take when handling errors."""

    RETRY = "retry"
    SKIP = "skip"
    FALLBACK = "fallback"
    FAIL = "fail"


class ErrorRecoveryOrchestrator:
    """Orchestrates error recovery for pipeline steps."""

    def __init__(self, config_path: str | Path | None = None):
        """Initialize recovery orchestrator.

        Args:
            config_path: Path to error_recovery.yaml, defaults to config/error_recovery.yaml
        """
        if config_path is None:
            repo_root = Path(__file__).resolve().parents[3]
            config_path = repo_root / "config" / "error_recovery.yaml"

        self.config_path = Path(config_path)
        self.policies: dict[str, dict[str, Any]] = {}
        self._load_policies()

        # Track recovery attempts per step execution
        self._attempt_counts: dict[str, int] = {}

    def _load_policies(self) -> None:
        """Load recovery policies from YAML config."""
        if not self.config_path.exists():
            logger.warning(
                "Error recovery config not found at %s, using defaults",
                self.config_path,
            )
            self._set_default_policies()
            return

        try:
            with open(self.config_path, encoding="utf-8") as f:
                self.policies = yaml.safe_load(f) or {}
            logger.info(
                "Loaded %d error recovery policies from %s",
                len(self.policies),
                self.config_path,
            )
        except Exception as e:
            logger.error("Failed to load error recovery config: %s", e)
            self._set_default_policies()

    def _set_default_policies(self) -> None:
        """Set minimal default policies when config unavailable."""
        self.policies = {
            "NETWORK": {"max_retries": 3, "backoff_base_seconds": 1.0, "action": "RETRY"},
            "TIMEOUT": {"max_retries": 3, "backoff_base_seconds": 2.0, "action": "RETRY"},
            "VALIDATION": {"max_retries": 0, "action": "SKIP"},
            "DEFAULT": {"max_retries": 1, "backoff_base_seconds": 1.0, "action": "RETRY"},
        }

    def handle_error(
        self,
        result: StepResult,
        step_name: str,
        execution_id: str | None = None,
    ) -> tuple[RecoveryAction, dict[str, Any]]:
        """Determine recovery action for a failed step result.

        Args:
            result: Failed StepResult
            step_name: Name of the pipeline step
            execution_id: Optional unique ID for this execution

        Returns:
            Tuple of (RecoveryAction, metadata dict with backoff_seconds, reason, etc.)
        """
        if result.success:
            return RecoveryAction.RETRY, {"reason": "Success, no recovery needed"}

        # Get policy for this error category (uppercase to match YAML keys)
        category_str = result.error_category.value.upper() if result.error_category else "DEFAULT"
        policy = self.policies.get(category_str, self.policies.get("DEFAULT", {}))

        # Track attempt count
        attempt_key = f"{execution_id or 'unknown'}:{step_name}"
        current_attempt = self._attempt_counts.get(attempt_key, 0) + 1
        self._attempt_counts[attempt_key] = current_attempt

        # Determine action
        max_retries = policy.get("max_retries", 1)
        action_str = policy.get("action", "RETRY")

        if current_attempt > max_retries:
            # Exceeded retry limit
            action = RecoveryAction.FAIL
            metadata = {
                "reason": f"Exceeded max retries ({max_retries})",
                "attempts": current_attempt,
                "max_retries": max_retries,
                "backoff_seconds": 0,
            }
        else:
            try:
                action = RecoveryAction(action_str.lower())
            except ValueError:
                logger.warning("Invalid action %s, defaulting to RETRY", action_str)
                action = RecoveryAction.RETRY

            # Calculate backoff
            backoff_base = policy.get("backoff_base_seconds", 1.0)
            backoff_factor = policy.get("backoff_factor", 2.0)
            backoff_seconds = backoff_base * (backoff_factor ** (current_attempt - 1))

            metadata = {
                "reason": policy.get("reason", f"Error category: {category_str}"),
                "attempts": current_attempt,
                "max_retries": max_retries,
                "backoff_seconds": backoff_seconds,
                "fallback_step": policy.get("fallback_step"),
            }

        logger.info(
            "Error recovery for %s (attempt %d/%d): action=%s category=%s",
            step_name,
            current_attempt,
            max_retries,
            action.value,
            category_str,
        )

        return action, metadata

    def reset_attempts(self, execution_id: str, step_name: str | None = None) -> None:
        """Reset attempt counters for an execution.

        Args:
            execution_id: Execution ID to reset
            step_name: Optional specific step, or None to reset all for this execution
        """
        if step_name:
            key = f"{execution_id}:{step_name}"
            self._attempt_counts.pop(key, None)
        else:
            # Reset all steps for this execution
            prefix = f"{execution_id}:"
            keys_to_remove = [k for k in self._attempt_counts if k.startswith(prefix)]
            for key in keys_to_remove:
                self._attempt_counts.pop(key, None)

    def execute_with_recovery(
        self,
        step_fn: Callable[..., StepResult],
        step_name: str,
        execution_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> StepResult:
        """Execute a step function with automatic error recovery.

        Args:
            step_fn: Function to execute (should return StepResult)
            step_name: Name of the step
            execution_id: Unique execution ID
            *args, **kwargs: Arguments to pass to step_fn

        Returns:
            Final StepResult after recovery attempts
        """
        while True:
            result = step_fn(*args, **kwargs)

            if result.success:
                # Reset attempts on success
                self.reset_attempts(execution_id, step_name)
                return result

            # Handle error
            action, metadata = self.handle_error(result, step_name, execution_id)

            if action == RecoveryAction.RETRY:
                backoff = metadata.get("backoff_seconds", 1.0)
                logger.info(
                    "Retrying %s after %.1fs (attempt %d/%d)",
                    step_name,
                    backoff,
                    metadata["attempts"],
                    metadata["max_retries"],
                )
                time.sleep(backoff)
                continue

            if action == RecoveryAction.SKIP:
                logger.info("Skipping %s: %s", step_name, metadata.get("reason"))
                return StepResult.skip(
                    step=step_name,
                    reason=metadata.get("reason", "Error recovery: skip"),
                    original_error=result.error,
                    recovery_metadata=metadata,
                )

            if action == RecoveryAction.FALLBACK:
                fallback_step = metadata.get("fallback_step")
                if fallback_step:
                    logger.info("Using fallback %s for %s", fallback_step, step_name)
                    # Caller should implement fallback logic
                    return StepResult.uncertain(
                        step=step_name,
                        fallback_step=fallback_step,
                        reason="Fallback required",
                        original_error=result.error,
                        recovery_metadata=metadata,
                    )
                # No fallback configured, treat as fail
                action = RecoveryAction.FAIL

            if action == RecoveryAction.FAIL:
                logger.error("Recovery failed for %s: %s", step_name, metadata.get("reason"))
                return StepResult.fail(
                    error=metadata.get("reason", "Recovery exhausted"),
                    error_category=result.error_category,
                    retryable=False,
                    recovery_metadata=metadata,
                    original_error=result.error,
                )
                # Augment original result with recovery metadata
                result.metadata["recovery_action"] = "fail"
                result.metadata["recovery_metadata"] = metadata
                return result

        # Unreachable, but satisfies type checker
        return result


# Global singleton
_orchestrator: ErrorRecoveryOrchestrator | None = None


def get_error_recovery_orchestrator() -> ErrorRecoveryOrchestrator:
    """Get global error recovery orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ErrorRecoveryOrchestrator()
    return _orchestrator
