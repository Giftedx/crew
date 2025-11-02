"""Platform core module.

Contains foundational protocols and utilities with zero domain dependencies.
"""

from platform.core.step_result import (  # noqa: PLC0415
    ErrorCategory,
    StepResult,
)

__all__ = [
    "ErrorCategory",
    "StepResult",
]

