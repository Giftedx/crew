# ruff: noqa: I001
from __future__ import annotations

# Compatibility shim for StepResult in domains package.
#
# This module re-exports the canonical StepResult and related types from
# platform.core.step_result so legacy relative imports like
# ``from ..step_result import StepResult`` continue to work.

from platform.core import step_result as _sr

ErrorAnalyzer = _sr.ErrorAnalyzer
ErrorCategory = _sr.ErrorCategory
ErrorContext = _sr.ErrorContext
ErrorRecoveryManager = _sr.ErrorRecoveryManager
ErrorRecoveryStrategy = _sr.ErrorRecoveryStrategy
ErrorSeverity = _sr.ErrorSeverity
StepResult = _sr.StepResult
get_error_analyzer = _sr.get_error_analyzer
get_recovery_manager = _sr.get_recovery_manager
record_error_for_analysis = _sr.record_error_for_analysis

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
