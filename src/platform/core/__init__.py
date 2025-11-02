"""Platform core module.

Contains foundational protocols and utilities with zero domain dependencies.
"""

from .step_result import (
    ErrorCategory,
    StepResult,
)


__all__ = [
    "ErrorCategory",
    "StepResult",
]

