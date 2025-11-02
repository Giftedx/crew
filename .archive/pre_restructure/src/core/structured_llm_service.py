"""Compatibility shim for structured LLM service (split refactor).

This module used to contain the full implementation. It now re-exports the
public API from the split modules under core.structured_llm.
"""

from .structured_llm.cache import CacheEntry, CacheKeyGenerator, ResponseCache
from .structured_llm.recovery import EnhancedErrorRecovery
from .structured_llm.service import (
    StructuredLLMService,
    StructuredRequest,
    create_structured_llm_service,
)
from .structured_llm.streaming import (
    ProgressCallback,
    ProgressEvent,
    ProgressTracker,
    StreamingResponse,
    StreamingStructuredRequest,
)


__all__ = [
    "INSTRUCTOR_AVAILABLE",  # Expose INSTRUCTOR_AVAILABLE for testing
    "CacheEntry",
    "CacheKeyGenerator",
    "EnhancedErrorRecovery",
    "ProgressCallback",
    "ProgressEvent",
    "ProgressTracker",
    "ResponseCache",
    "StreamingResponse",
    "StreamingStructuredRequest",
    "StructuredLLMService",
    "StructuredRequest",
    "create_structured_llm_service",
]

# Back-compat test knob: tests patch this symbol. Keep default False to favor fallback.
INSTRUCTOR_AVAILABLE = False
