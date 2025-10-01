"""Structured LLM components package.

This package contains the split modules for the Structured LLM service:
- cache: Cache primitives and key generation
- streaming: Streaming types and progress tracking
- recovery: Circuit breaker and backoff logic
- service: Public StructuredLLMService API and factory

The top-level module core.structured_llm_service re-exports public symbols
for backward compatibility. Prefer importing from core.structured_llm.service
for new code.
"""

from . import service as _service
from . import streaming as _streaming

StructuredLLMService = _service.StructuredLLMService
StructuredRequest = _service.StructuredRequest
create_structured_llm_service = _service.create_structured_llm_service

ProgressCallback = _streaming.ProgressCallback
ProgressEvent = _streaming.ProgressEvent
ProgressTracker = _streaming.ProgressTracker
StreamingResponse = _streaming.StreamingResponse
StreamingStructuredRequest = _streaming.StreamingStructuredRequest

__all__ = [
    "StructuredLLMService",
    "create_structured_llm_service",
    "StructuredRequest",
    "StreamingStructuredRequest",
    "StreamingResponse",
    "ProgressEvent",
    "ProgressCallback",
    "ProgressTracker",
]
