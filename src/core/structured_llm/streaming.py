from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from pydantic import BaseModel


logger = logging.getLogger(__name__)


ProgressCallback = Callable[["ProgressEvent"], None]


@dataclass
class ProgressEvent:
    """Progress event for streaming operations."""

    event_type: str  # "start", "progress", "complete", "error"
    message: str
    progress_percent: float = 0.0
    data: dict[str, Any] | None = None
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class StreamingStructuredRequest:
    """Streaming version of structured LLM request parameters."""

    prompt: str
    response_model: Any
    task_type: str = "general"
    model: str | None = None
    provider_opts: dict[str, Any] | None = None
    max_retries: int = 3
    enable_streaming: bool = True
    progress_callback: ProgressCallback | None = None
    streaming_chunk_size: int = 1024


@dataclass
class StreamingResponse:
    """Container for streaming response data."""

    partial_result: BaseModel | None = None
    is_complete: bool = False
    progress_percent: float = 0.0
    raw_chunks: list[str] | None = None
    error: str | None = None

    def __post_init__(self):
        if self.raw_chunks is None:
            self.raw_chunks = []


class ProgressTracker:
    """Tracks progress for streaming operations with callbacks."""

    def __init__(self, callback: ProgressCallback | None = None):
        self.callback = callback
        self.start_time = time.time()
        self.events: list[ProgressEvent] = []

    def emit_event(
        self,
        event_type: str,
        message: str,
        progress_percent: float = 0.0,
        data: dict[str, Any] | None = None,
    ):
        event = ProgressEvent(
            event_type=event_type,
            message=message,
            progress_percent=progress_percent,
            data=data,
        )
        self.events.append(event)
        if self.callback:
            try:
                self.callback(event)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
        logger.debug(f"Progress event: {event_type} - {message} ({progress_percent:.1f}%)")

    def start_operation(self, operation: str):
        self.emit_event("start", f"Starting {operation}", 0.0)

    def update_progress(self, message: str, percent: float, data: dict[str, Any] | None = None):
        self.emit_event("progress", message, percent, data)

    def complete_operation(self, message: str = "Operation completed", data: dict[str, Any] | None = None):
        duration = time.time() - self.start_time
        self.emit_event("complete", f"{message} (took {duration:.2f}s)", 100.0, data)

    def error_operation(self, error_message: str, data: dict[str, Any] | None = None):
        self.emit_event("error", f"Operation failed: {error_message}", 0.0, data)

    def get_duration(self) -> float:
        return time.time() - self.start_time
