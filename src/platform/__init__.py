"""Platform layer - infrastructure with zero domain dependencies.

This package provides reusable infrastructure components including:
- Core protocols (StepResult, ErrorCategory)
- HTTP utilities and retry logic
- Caching (Redis, in-memory, semantic)
- Observability (Logfire, Prometheus, Langfuse)
- LLM providers (OpenAI, Anthropic, OpenRouter)
- Reinforcement learning policies
- Security primitives
- Database connections
- Web automation

Architecture: Platform is the foundation layer with no knowledge of business logic.
"""

from platform.core.step_result import ErrorCategory, StepResult
from platform.http.http_utils import resilient_get, resilient_post
from platform.observability.metrics import record_metric


__all__ = [
    # Core protocols
    "StepResult",
    "ErrorCategory",
    # HTTP utilities
    "resilient_get",
    "resilient_post",
    # Observability
    "record_metric",
]

