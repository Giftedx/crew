"""Compatibility shim for legacy ai.structured_outputs imports.

DEPRECATED: This module provides backward compatibility for code using the old
`ai.structured_outputs` import path. New code should import directly from
`platform.rl.structured_outputs` instead.

This shim will be removed in a future release after all imports are migrated.
"""

from platform.rl.structured_outputs import (
    INSTRUCTOR_AVAILABLE,
    InstructorClientFactory,
)


# Re-export dependencies for test mocking compatibility
try:
    import instructor
except ImportError:
    instructor = None  # type: ignore

from platform.config.configuration import get_config


__all__ = [
    "INSTRUCTOR_AVAILABLE",
    "InstructorClientFactory",
    "get_config",
    "instructor",
]
