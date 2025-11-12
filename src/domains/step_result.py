# ruff: noqa: I001
from __future__ import annotations

# Compatibility shim for StepResult in domains package.
#
# This module re-exports the canonical StepResult and related types from
# ultimate_discord_intelligence_bot.step_result so legacy relative imports like
# ``from ..step_result import StepResult`` continue to work.

from ultimate_discord_intelligence_bot.step_result import (
    ErrorAnalyzer,
    ErrorCategory,
    ErrorContext,
    ErrorRecoveryManager,
    ErrorRecoveryStrategy,
    ErrorSeverity,
    StepResult,
    get_error_analyzer,
    get_recovery_manager,
    record_error_for_analysis,
)

__all__ = [
    "ErrorAnalyzer",
    "ErrorCategory",
    "ErrorContext",
    "ErrorRecoveryManager",
    "ErrorRecoveryStrategy",
    "ErrorSeverity",
    "StepResult",
    "get_error_analyzer",
    "get_recovery_manager",
    "record_error_for_analysis",
]
