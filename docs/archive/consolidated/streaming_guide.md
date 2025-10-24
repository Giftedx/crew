# Structured LLM Streaming Support

This document provides comprehensive documentation for the streaming functionality added to the StructuredLLMService.

## Overview

The streaming functionality enables processing of large structured responses with progress tracking and async processing. It provides:

- **Progress Callbacks**: Real-time progress updates during processing
- **Async Generators**: Memory-efficient streaming of results
- **Error Recovery**: Robust error handling with circuit breaker patterns
- **Metrics Integration**: Comprehensive observability with Prometheus metrics
- **Backward Compatibility**: Existing API remains unchanged

## Key Components

### StreamingStructuredRequest

Enhanced request object for streaming operations:

```python
from core.structured_llm_service import StreamingStructuredRequest

request = StreamingStructuredRequest(
    prompt="Generate a user profile",
    response_model=UserProfile,
    progress_callback=my_callback,
    model="openai/gpt-4o",
    max_retries=3,
    enable_streaming=True,
    streaming_chunk_size=1024
)
```

### ProgressEvent

Data structure for progress tracking:

```python
@dataclass
class ProgressEvent:
    event_type: str  # "start", "progress", "complete", "error"
    message: str
    progress_percent: float = 0.0
    data: dict[str, Any] | None = None
    timestamp: float = 0.0
```

### ProgressCallback

Type for progress callback functions:

```python
ProgressCallback = Callable[[ProgressEvent], None]

def my_progress_callback(event: ProgressEvent) -> None:
    print(f"{event.event_type}: {event.message} ({event.progress_percent:.1f}%)")
```

### StreamingResponse

Container for streaming response data:

```python
@dataclass
class StreamingResponse:
    partial_result: BaseModel | None = None
    is_complete: bool = False
    progress_percent: float = 0.0
    raw_chunks: list[str] | None = None
    error: str | None = None
```

### ProgressTracker

Tracks progress for streaming operations:

```python
tracker = ProgressTracker(callback=my_callback)
tracker.start_operation("Processing request")
tracker.update_progress("Halfway done", 50.0)
tracker.complete_operation("Finished successfully")
```

## Usage Examples

### Basic Streaming

```python
import asyncio
from core.structured_llm_service import StructuredLLMService, StreamingStructuredRequest

async def basic_example():
    service = StructuredLLMService(openrouter_service)

    request = StreamingStructuredRequest(
        prompt="Create a profile for a software engineer",
        response_model=UserProfile
    )

    async for response in service.route_structured_streaming(request):
        if response.is_complete:
            if response.partial_result:
                print(f"Result: {response.partial_result}")
            elif response.error:
                print(f"Error: {response.error}")

asyncio.run(basic_example())
```

### With Progress Callbacks

```python
def progress_callback(event: ProgressEvent) -> None:
    print(f"[{event.timestamp:.2f}] {event.event_type}: {event.message}")
    if event.progress_percent > 0:
        print(f"Progress: {event.progress_percent:.1f}%")

request = StreamingStructuredRequest(
    prompt="Generate complex structured data",
    response_model=MyModel,
    progress_callback=progress_callback
)
```

### Error Handling

```python
request = StreamingStructuredRequest(
    prompt="Generate data that might fail",
    response_model=MyModel,
    max_retries=3
)

async for response in service.route_structured_streaming(request):
    if response.error:
        print(f"Error occurred: {response.error}")
    elif response.is_complete and response.partial_result:
        print(f"Success: {response.partial_result}")
```

## Metrics

The streaming functionality integrates with the existing metrics system:

- `STRUCTURED_LLM_STREAMING_REQUESTS`: Total streaming requests
- `STRUCTURED_LLM_STREAMING_CHUNKS`: Number of chunks processed
- `STRUCTURED_LLM_STREAMING_LATENCY`: Request latency
- `STRUCTURED_LLM_STREAMING_PROGRESS`: Progress tracking events
- `STRUCTURED_LLM_STREAMING_ERRORS`: Error counts by type

## Error Recovery

The streaming implementation includes robust error recovery:

- **Circuit Breaker**: Prevents cascading failures
- **Exponential Backoff**: Intelligent retry delays
- **Error Categorization**: Different handling for rate limits, timeouts, parsing errors
- **Fallback Modes**: Graceful degradation when instructor is unavailable

## Testing

Comprehensive test suite covers:

- Data structure validation
- Streaming service functionality
- Progress tracking
- Error handling scenarios
- Integration tests

Run tests with:

```bash
pytest tests/test_structured_llm_service.py::TestStreamingDataStructures
pytest tests/test_structured_llm_service.py::TestStreamingLLMService
pytest tests/test_structured_llm_service.py::TestStreamingIntegration
```

## Examples

See `scripts/streaming_examples.py` for comprehensive usage examples including:

- Basic streaming workflow
- Advanced progress tracking
- Error handling patterns
- Batch processing
- Custom callback implementations

## Migration Guide

### From Regular to Streaming

```python
# Before (regular)
result = service.route_structured(request)

# After (streaming)
async for response in service.route_structured_streaming(request):
    if response.is_complete:
        result = response.partial_result
        break
```

### Adding Progress Callbacks

```python
# Add progress tracking to existing requests
request = StreamingStructuredRequest(
    prompt=existing_prompt,
    response_model=existing_model,
    progress_callback=my_progress_callback
)
```

## Performance Considerations

- **Memory Efficiency**: Async generators prevent loading large responses into memory
- **Progress Feedback**: Users get real-time updates for long-running operations
- **Error Recovery**: Circuit breaker prevents resource waste on failing services
- **Metrics Overhead**: Minimal performance impact from metrics collection

## Troubleshooting

### Common Issues

1. **No Progress Events**: Ensure `progress_callback` is properly set
2. **Streaming Not Working**: Check if `enable_streaming=True` (default)
3. **Type Errors**: Verify `response_model` is a valid Pydantic model
4. **Circuit Breaker**: Check logs for "Service temporarily unavailable" messages

### Debug Mode

Enable debug logging to see detailed progress:

```python
import logging
logging.getLogger('core.structured_llm_service').setLevel(logging.DEBUG)
```

## Future Enhancements

- True streaming from LLM providers (currently simulated)
- Configurable chunk sizes
- Pause/resume functionality
- Parallel streaming requests
- Custom progress event filtering
