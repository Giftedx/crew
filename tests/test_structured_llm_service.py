"""
Comprehensive tests for StructuredLLMService.
Tests cover unit tests, integration tests, error handling, and performance scenarios.
"""

from unittest.mock import Mock, patch

import pytest
from core.structured_llm_service import (
    CacheEntry,
    CacheKeyGenerator,
    ProgressCallback,
    ProgressEvent,
    ProgressTracker,
    ResponseCache,
    StreamingResponse,
    StreamingStructuredRequest,
    StructuredLLMService,
    StructuredRequest,
    create_structured_llm_service,
)
from pydantic import BaseModel


class TestUserProfile(BaseModel):
    """Test Pydantic model for user profiles."""

    name: str
    age: int
    email: str
    is_active: bool = True


class TestProductInfo(BaseModel):
    """Test Pydantic model for product information."""

    title: str
    price: float
    category: str
    in_stock: bool


@pytest.fixture
def mock_openrouter_service():
    """Create a mock OpenRouter service for testing."""
    service = Mock()
    service.api_key = "test-key"
    service.route = Mock()
    return service


@pytest.fixture
def structured_service(mock_openrouter_service):
    """Create a StructuredLLMService instance for testing."""
    return StructuredLLMService(mock_openrouter_service)


class TestStructuredRequest:
    """Test cases for StructuredRequest dataclass."""

    def test_structured_request_creation(self):
        """Test creating a StructuredRequest with all parameters."""
        request = StructuredRequest(
            prompt="Generate a user profile",
            response_model=TestUserProfile,
            task_type="general",
            model="openai/gpt-4o",
            provider_opts={"temperature": 0.7},
            max_retries=5,
        )

        assert request.prompt == "Generate a user profile"
        assert request.response_model == TestUserProfile
        assert request.task_type == "general"
        assert request.model == "openai/gpt-4o"
        assert request.provider_opts == {"temperature": 0.7}
        assert request.max_retries == 5

    def test_structured_request_defaults(self):
        """Test StructuredRequest with default values."""
        request = StructuredRequest(prompt="Test prompt", response_model=TestUserProfile)

        assert request.task_type == "general"
        assert request.model is None
        assert request.provider_opts is None
        assert request.max_retries == 3


class TestStructuredLLMService:
    """Test cases for StructuredLLMService class."""

    @patch("core.structured_llm_service.INSTRUCTOR_AVAILABLE", False)
    def test_service_initialization(self, mock_openrouter_service):
        """Test service initialization with and without Instructor."""
        service = StructuredLLMService(mock_openrouter_service)
        assert service.openrouter == mock_openrouter_service
        assert service.instructor_client is None

    def test_model_compatibility_check(self, structured_service):
        """Test model compatibility detection for structured outputs."""
        # Compatible models
        assert structured_service._is_structured_model_compatible("openai/gpt-4o")
        assert structured_service._is_structured_model_compatible("anthropic/claude-3-5-sonnet")
        assert structured_service._is_structured_model_compatible("google/gemini-1.5-pro")

        # Incompatible models
        assert not structured_service._is_structured_model_compatible("openai/gpt-3.5-turbo")
        assert not structured_service._is_structured_model_compatible(None)
        assert not structured_service._is_structured_model_compatible("unknown/model")

    def test_prompt_enhancement_for_json(self, structured_service):
        """Test prompt enhancement for JSON output."""
        prompt = "Generate a user profile"
        enhanced = structured_service._enhance_prompt_for_json(prompt, TestUserProfile)

        assert "IMPORTANT: Respond with valid JSON" in enhanced
        assert "UserProfile" in enhanced
        assert prompt in enhanced
        assert "```json" not in enhanced  # Should not have markdown

    def test_example_generation(self, structured_service):
        """Test generation of example instances for prompt enhancement."""
        example = structured_service._generate_example_instance(TestUserProfile)

        assert isinstance(example, TestUserProfile)
        assert example.name == "example_string"
        assert example.age == 0
        assert example.email == "example_string"
        assert example.is_active is True

    def test_prompt_enhancement_with_example(self, structured_service):
        """Test prompt enhancement with concrete examples."""
        prompt = "Create a product listing"
        enhanced = structured_service._enhance_prompt_with_example(prompt, TestProductInfo)

        assert "Example of the expected JSON format:" in enhanced
        assert '"title": "example_string"' in enhanced
        assert '"price": 0.0' in enhanced
        assert prompt in enhanced

    def test_json_parsing_and_validation_success(self, structured_service):
        """Test successful JSON parsing and validation."""
        json_str = '{"name": "John Doe", "age": 30, "email": "john@example.com", "is_active": true}'
        result = structured_service._parse_and_validate_json(json_str, TestUserProfile)

        assert isinstance(result, TestUserProfile)
        assert result.name == "John Doe"
        assert result.age == 30
        assert result.email == "john@example.com"
        assert result.is_active is True

    def test_json_parsing_with_markdown(self, structured_service):
        """Test JSON parsing with markdown code blocks."""
        json_str = '```json\n{"name": "Jane Doe", "age": 25, "email": "jane@example.com"}\n```'
        result = structured_service._parse_and_validate_json(json_str, TestUserProfile)

        assert isinstance(result, TestUserProfile)
        assert result.name == "Jane Doe"
        assert result.age == 25

    def test_json_parsing_validation_error(self, structured_service):
        """Test JSON parsing with validation errors."""
        # Missing required field
        json_str = '{"name": "John Doe", "email": "john@example.com"}'
        result = structured_service._parse_and_validate_json(json_str, TestUserProfile)

        assert result is None

    def test_json_parsing_invalid_json(self, structured_service):
        """Test JSON parsing with invalid JSON."""
        invalid_json = '{"name": "John", "age": 30'  # Missing closing brace
        result = structured_service._parse_and_validate_json(invalid_json, TestUserProfile)

        assert result is None

    @patch("core.structured_llm_service.INSTRUCTOR_AVAILABLE", False)
    def test_route_structured_fallback_mode(self, mock_openrouter_service):
        """Test routing in fallback mode when Instructor is unavailable."""
        service = StructuredLLMService(mock_openrouter_service)

        # Mock successful OpenRouter response with valid JSON
        mock_response = {"status": "success", "response": '{"name": "Alice", "age": 28, "email": "alice@test.com"}'}
        mock_openrouter_service.route.return_value = mock_response

        request = StructuredRequest(prompt="Generate a user profile", response_model=TestUserProfile)

        result = service.route_structured(request)

        assert isinstance(result, TestUserProfile)
        assert result.name == "Alice"
        assert result.age == 28
        assert result.email == "alice@test.com"

    @patch("core.structured_llm_service.INSTRUCTOR_AVAILABLE", False)
    def test_route_structured_fallback_with_retries(self, mock_openrouter_service):
        """Test fallback routing with retry logic."""
        service = StructuredLLMService(mock_openrouter_service)

        # Mock responses: first two fail, third succeeds
        responses = [
            {"status": "success", "response": "invalid json"},
            {"status": "success", "response": '{"name": "Bob"}'},  # Missing required fields
            {"status": "success", "response": '{"name": "Charlie", "age": 35, "email": "charlie@test.com"}'},
        ]
        mock_openrouter_service.route.side_effect = responses

        request = StructuredRequest(prompt="Generate a user profile", response_model=TestUserProfile, max_retries=3)

        result = service.route_structured(request)

        assert isinstance(result, TestUserProfile)
        assert result.name == "Charlie"
        assert result.age == 35
        assert result.email == "charlie@test.com"

        # Should have called OpenRouter 3 times
        assert mock_openrouter_service.route.call_count == 3

    @patch("core.structured_llm_service.INSTRUCTOR_AVAILABLE", False)
    def test_route_structured_fallback_max_retries_exceeded(self, mock_openrouter_service):
        """Test fallback routing when max retries are exceeded."""
        service = StructuredLLMService(mock_openrouter_service)

        # Mock consistent failure
        mock_openrouter_service.route.return_value = {"status": "success", "response": "invalid json response"}

        request = StructuredRequest(prompt="Generate a user profile", response_model=TestUserProfile, max_retries=2)

        result = service.route_structured(request)

        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "Failed to generate structured output" in result["error"]
        assert result["attempts"] == 2

    @patch("core.structured_llm_service.INSTRUCTOR_AVAILABLE", False)
    def test_route_structured_openrouter_error(self, mock_openrouter_service):
        """Test handling of OpenRouter service errors."""
        service = StructuredLLMService(mock_openrouter_service)

        # Mock OpenRouter error
        mock_openrouter_service.route.return_value = {"status": "error", "error": "API rate limit exceeded"}

        request = StructuredRequest(prompt="Generate a user profile", response_model=TestUserProfile)

        result = service.route_structured(request)

        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "API rate limit exceeded" in result["error"]

    def test_value_generation_for_types(self, structured_service):
        """Test example value generation for different types."""
        # Test simple types
        assert structured_service._generate_example_value(str) == "example_string"
        assert structured_service._generate_example_value(int) == 0
        assert structured_service._generate_example_value(float) == 0.0
        assert structured_service._generate_example_value(bool) is False

        # Test complex types
        assert structured_service._generate_example_value(list) == ["example_string"]
        assert structured_service._generate_example_value(dict) == {"key": "value"}

        # Test unknown type
        assert structured_service._generate_example_value(object) == "example"


class TestStructuredLLMServiceIntegration:
    """Integration tests for StructuredLLMService with real dependencies."""

    @patch("core.structured_llm_service.INSTRUCTOR_AVAILABLE", False)
    def test_full_integration_workflow(self, mock_openrouter_service):
        """Test complete workflow from request to validated response."""
        service = StructuredLLMService(mock_openrouter_service)

        # Mock a realistic OpenRouter response
        mock_openrouter_service.route.return_value = {
            "status": "success",
            "response": """
            {
                "name": "Sarah Johnson",
                "age": 32,
                "email": "sarah.johnson@example.com",
                "is_active": true
            }
            """,
            "model": "openai/gpt-4o",
            "tokens": 150,
        }

        request = StructuredRequest(
            prompt="Create a profile for a software engineer named Sarah",
            response_model=TestUserProfile,
            task_type="general",
            model="openai/gpt-4o",
        )

        result = service.route_structured(request)

        # Verify the result
        assert isinstance(result, TestUserProfile)
        assert result.name == "Sarah Johnson"
        assert result.age == 32
        assert result.email == "sarah.johnson@example.com"
        assert result.is_active is True

        # Verify OpenRouter was called correctly
        mock_openrouter_service.route.assert_called_once()
        call_args = mock_openrouter_service.route.call_args

        # Check that the prompt was enhanced
        enhanced_prompt = call_args[1]["prompt"]
        assert "IMPORTANT: Respond with valid JSON" in enhanced_prompt
        assert "UserProfile" in enhanced_prompt
        assert request.prompt in enhanced_prompt


class TestStructuredLLMServiceFactory:
    """Test cases for the service factory function."""

    def test_create_structured_llm_service(self, mock_openrouter_service):
        """Test the factory function creates a properly configured service."""
        service = create_structured_llm_service(mock_openrouter_service)

        assert isinstance(service, StructuredLLMService)
        assert service.openrouter == mock_openrouter_service


class TestStreamingDataStructures:
    """Test cases for streaming data structures."""

    def test_progress_event_creation(self):
        """Test creating a ProgressEvent."""
        event = ProgressEvent(
            event_type="chunk_received",
            message="Received chunk 1",
            progress_percent=25.0,
            data={"chunk": "test data", "chunk_index": 1},
            timestamp=1234567890.0,
        )

        assert event.event_type == "chunk_received"
        assert event.message == "Received chunk 1"
        assert event.progress_percent == 25.0
        assert event.data is not None
        assert event.data["chunk"] == "test data"
        assert event.data["chunk_index"] == 1
        assert event.timestamp == 1234567890.0

    def test_progress_event_defaults(self):
        """Test ProgressEvent with default values."""
        event = ProgressEvent(event_type="started", message="Starting operation")

        assert event.event_type == "started"
        assert event.message == "Starting operation"
        assert event.progress_percent == 0.0
        assert event.data is None
        assert isinstance(event.timestamp, float)

    def test_progress_callback_creation(self):
        """Test creating a ProgressCallback."""

        def callback_func(event: ProgressEvent):
            pass

        # ProgressCallback is just a type alias for Callable[[ProgressEvent], None]
        callback: ProgressCallback = callback_func
        assert callback == callback_func

    def test_progress_callback_defaults(self):
        """Test ProgressCallback with default values."""

        def callback_func(event: ProgressEvent):
            pass

        callback: ProgressCallback = callback_func
        assert callback == callback_func

    def test_streaming_structured_request_creation(self):
        """Test creating a StreamingStructuredRequest."""

        def callback_func(event: ProgressEvent):
            pass

        request = StreamingStructuredRequest(
            prompt="Generate a user profile",
            response_model=TestUserProfile,
            progress_callback=callback_func,
            task_type="general",
            model="openai/gpt-4o",
            provider_opts={"temperature": 0.7},
            max_retries=5,
            enable_streaming=True,
            streaming_chunk_size=1024,
        )

        assert request.prompt == "Generate a user profile"
        assert request.response_model == TestUserProfile
        assert request.progress_callback == callback_func
        assert request.task_type == "general"
        assert request.model == "openai/gpt-4o"
        assert request.provider_opts == {"temperature": 0.7}
        assert request.max_retries == 5
        assert request.enable_streaming is True
        assert request.streaming_chunk_size == 1024

    def test_streaming_structured_request_defaults(self):
        """Test StreamingStructuredRequest with default values."""
        request = StreamingStructuredRequest(prompt="Test prompt", response_model=TestUserProfile)

        assert request.task_type == "general"
        assert request.model is None
        assert request.provider_opts is None
        assert request.max_retries == 3
        assert request.enable_streaming is True
        assert request.progress_callback is None
        assert request.streaming_chunk_size == 1024

    def test_streaming_response_creation(self):
        """Test creating a StreamingResponse."""
        response = StreamingResponse(
            partial_result=None, is_complete=False, progress_percent=50.0, raw_chunks=["chunk1", "chunk2"], error=None
        )

        assert response.partial_result is None
        assert response.is_complete is False
        assert response.progress_percent == 50.0
        assert response.raw_chunks == ["chunk1", "chunk2"]
        assert response.error is None

    def test_progress_tracker_creation(self):
        """Test creating a ProgressTracker."""
        tracker = ProgressTracker()

        assert tracker.callback is None
        assert isinstance(tracker.start_time, float)
        assert len(tracker.events) == 0

    def test_progress_tracker_events(self):
        """Test ProgressTracker event tracking."""
        tracker = ProgressTracker()

        # Add some events
        tracker.emit_event("started", "Starting processing", 0.0)
        tracker.emit_event("chunk_received", "Received chunk 1", 25.0, {"chunk_index": 1})
        tracker.emit_event("completed", "Processing completed", 100.0)

        assert len(tracker.events) == 3
        assert tracker.events[0].event_type == "started"
        assert tracker.events[0].message == "Starting processing"
        assert tracker.events[0].progress_percent == 0.0

        assert tracker.events[1].event_type == "chunk_received"
        assert tracker.events[1].message == "Received chunk 1"
        assert tracker.events[1].progress_percent == 25.0
        assert tracker.events[1].data is not None
        assert tracker.events[1].data["chunk_index"] == 1

        assert tracker.events[2].event_type == "completed"
        assert tracker.events[2].message == "Processing completed"
        assert tracker.events[2].progress_percent == 100.0

    def test_progress_tracker_operations(self):
        """Test ProgressTracker operation methods."""
        tracker = ProgressTracker()

        tracker.start_operation("test operation")
        assert len(tracker.events) == 1
        assert tracker.events[0].event_type == "start"
        assert "test operation" in tracker.events[0].message

        tracker.update_progress("Halfway done", 50.0, {"step": 2})
        assert len(tracker.events) == 2
        assert tracker.events[1].event_type == "progress"
        assert tracker.events[1].progress_percent == 50.0
        assert tracker.events[1].data is not None
        assert tracker.events[1].data["step"] == 2

        tracker.complete_operation("Operation finished", {"result": "success"})
        assert len(tracker.events) == 3
        assert tracker.events[2].event_type == "complete"
        assert tracker.events[2].progress_percent == 100.0
        assert tracker.events[2].data is not None
        assert tracker.events[2].data["result"] == "success"

    def test_progress_tracker_timing(self):
        """Test ProgressTracker timing functionality."""
        tracker = ProgressTracker()

        assert isinstance(tracker.start_time, float)
        duration = tracker.get_duration()
        assert duration >= 0.0
        assert isinstance(duration, float)


class TestStreamingLLMService:
    """Test cases for streaming functionality in StructuredLLMService."""

    @patch("core.structured_llm_service.INSTRUCTOR_AVAILABLE", True)
    def test_route_structured_streaming_instructor_mode(self, mock_openrouter_service):
        """Test streaming routing in instructor mode."""
        service = StructuredLLMService(mock_openrouter_service)

        # Mock successful OpenRouter response with valid JSON
        mock_openrouter_service.route.return_value = {
            "status": "success",
            "response": '{"name": "Alice", "age": 28, "email": "alice@test.com"}',
        }

        request = StreamingStructuredRequest(prompt="Generate a user profile", response_model=TestUserProfile)

        # Test async streaming
        import asyncio

        async def run_test():
            responses = [response async for response in service.route_structured_streaming(request)]

            # Should get at least one final response
            assert len(responses) >= 1
            final_response = responses[-1]
            assert final_response.is_complete is True
            assert isinstance(final_response.partial_result, TestUserProfile)
            assert final_response.partial_result.name == "Alice"
            assert final_response.partial_result.age == 28
            assert final_response.partial_result.email == "alice@test.com"

        asyncio.run(run_test())

    @patch("core.structured_llm_service.INSTRUCTOR_AVAILABLE", False)
    def test_route_structured_streaming_fallback_mode(self, mock_openrouter_service):
        """Test streaming routing in fallback mode."""
        service = StructuredLLMService(mock_openrouter_service)

        # Mock successful OpenRouter response with valid JSON
        mock_openrouter_service.route.return_value = {
            "status": "success",
            "response": '{"name": "Bob", "age": 35, "email": "bob@test.com"}',
        }

        request = StreamingStructuredRequest(prompt="Generate a user profile", response_model=TestUserProfile)

        # Test async streaming
        import asyncio

        async def run_test():
            responses = [response async for response in service.route_structured_streaming(request)]

            # Should get at least one final response
            assert len(responses) >= 1
            final_response = responses[-1]
            assert final_response.is_complete is True
            assert isinstance(final_response.partial_result, TestUserProfile)
            assert final_response.partial_result.name == "Bob"
            assert final_response.partial_result.age == 35
            assert final_response.partial_result.email == "bob@test.com"

        asyncio.run(run_test())

    def test_route_structured_streaming_with_progress_callback(self, mock_openrouter_service):
        """Test streaming with progress callback."""
        service = StructuredLLMService(mock_openrouter_service)

        # Mock successful OpenRouter response
        mock_openrouter_service.route.return_value = {
            "status": "success",
            "response": '{"name": "Charlie", "age": 25, "email": "charlie@test.com"}',
        }

        # Track callback calls
        callback_calls = []

        def progress_callback(event: ProgressEvent):
            callback_calls.append(event)

        request = StreamingStructuredRequest(
            prompt="Generate a user profile", response_model=TestUserProfile, progress_callback=progress_callback
        )

        # Test async streaming
        import asyncio

        async def run_test():
            responses = [response async for response in service.route_structured_streaming(request)]

            # Should get at least one final response
            assert len(responses) >= 1
            final_response = responses[-1]
            assert final_response.is_complete is True
            assert isinstance(final_response.partial_result, TestUserProfile)
            assert final_response.partial_result.name == "Charlie"

            # Verify progress callback was called
            assert len(callback_calls) >= 2  # At least started and completed events

        asyncio.run(run_test())

    @patch("core.structured_llm_service.INSTRUCTOR_AVAILABLE", False)
    def test_route_structured_streaming_error_handling(self, mock_openrouter_service):
        """Test streaming error handling."""
        service = StructuredLLMService(mock_openrouter_service)

        # Mock OpenRouter error response
        mock_openrouter_service.route.return_value = {"status": "error", "error": "Service unavailable"}

        request = StreamingStructuredRequest(prompt="Generate a user profile", response_model=TestUserProfile)

        # Test async streaming
        import asyncio

        async def run_test():
            responses = [response async for response in service.route_structured_streaming(request)]

            # Should get at least one final response
            assert len(responses) >= 1
            final_response = responses[-1]
            assert final_response.is_complete is True
            assert final_response.error is not None
            assert "Service unavailable" in final_response.error

        asyncio.run(run_test())

    @patch("core.structured_llm_service.INSTRUCTOR_AVAILABLE", False)
    def test_route_structured_streaming_max_retries_exceeded(self, mock_openrouter_service):
        """Test streaming when max retries are exceeded."""
        service = StructuredLLMService(mock_openrouter_service)

        # Mock OpenRouter error response
        mock_openrouter_service.route.return_value = {"status": "error", "error": "Service unavailable"}

        request = StreamingStructuredRequest(
            prompt="Generate a user profile", response_model=TestUserProfile, max_retries=2
        )

        # Test async streaming
        import asyncio

        async def run_test():
            responses = [response async for response in service.route_structured_streaming(request)]

            # Should get at least one final response
            assert len(responses) >= 1
            final_response = responses[-1]
            assert final_response.is_complete is True
            if final_response.error:
                assert "Service unavailable" in final_response.error

        asyncio.run(run_test())


class TestStreamingIntegration:
    """Integration tests for streaming functionality."""

    @patch("core.structured_llm_service.INSTRUCTOR_AVAILABLE", True)
    def test_full_streaming_workflow_with_instructor(self, mock_openrouter_service):
        """Test complete streaming workflow with instructor."""
        service = StructuredLLMService(mock_openrouter_service)

        # Mock successful OpenRouter response with complete JSON
        mock_openrouter_service.route.return_value = {
            "status": "success",
            "response": '{\n  "name": "Diana Prince",\n  "age": 30,\n  "email": "diana@example.com",\n  "is_active": true\n}',
        }

        # Track progress events
        progress_events = []

        def track_progress(event: ProgressEvent):
            progress_events.append(event)

        request = StreamingStructuredRequest(
            prompt="Create a profile for Diana Prince",
            response_model=TestUserProfile,
            progress_callback=track_progress,
            model="openai/gpt-4o",
        )

        # Test async streaming
        import asyncio

        async def run_test():
            responses = [response async for response in service.route_structured_streaming(request)]

            # Should get at least one final response
            assert len(responses) >= 1
            final_response = responses[-1]
            assert final_response.is_complete is True
            assert isinstance(final_response.partial_result, TestUserProfile)
            assert final_response.partial_result.name == "Diana Prince"
            assert final_response.partial_result.age == 30
            assert final_response.partial_result.email == "diana@example.com"
            assert final_response.partial_result.is_active is True

            # Verify progress tracking
            assert len(progress_events) >= 3  # started, chunks, completed
            assert any(e.event_type == "start" for e in progress_events)
            assert any(e.event_type == "progress" for e in progress_events)
            assert any(e.event_type == "complete" for e in progress_events)

        asyncio.run(run_test())

    @patch("core.structured_llm_service.INSTRUCTOR_AVAILABLE", False)
    def test_full_streaming_workflow_with_fallback(self, mock_openrouter_service):
        """Test complete streaming workflow with fallback parsing."""
        service = StructuredLLMService(mock_openrouter_service)

        # Mock successful OpenRouter response with complete JSON
        mock_openrouter_service.route.return_value = {
            "status": "success",
            "response": '{\n  "title": "Wireless Headphones",\n  "price": 199.99,\n  "category": "Electronics",\n  "in_stock": true\n}',
        }

        request = StreamingStructuredRequest(
            prompt="Create a product listing for wireless headphones", response_model=TestProductInfo
        )

        # Test async streaming
        import asyncio

        async def run_test():
            responses = [response async for response in service.route_structured_streaming(request)]

            # Should get at least one final response
            assert len(responses) >= 1
            final_response = responses[-1]
            assert final_response.is_complete is True
            assert isinstance(final_response.partial_result, TestProductInfo)
            assert final_response.partial_result.title == "Wireless Headphones"
            assert final_response.partial_result.price == 199.99
            assert final_response.partial_result.category == "Electronics"
            assert final_response.partial_result.in_stock is True

        asyncio.run(run_test())


class TestCacheEntry:
    """Test cases for CacheEntry dataclass."""

    def test_cache_entry_creation(self):
        """Test creating a CacheEntry with all parameters."""
        import time

        current_time = time.time()

        entry = CacheEntry(
            key="test_key",
            value={"test": "data"},
            created_at=current_time,
            ttl_seconds=3600,
            access_count=5,
            last_accessed=current_time + 100,
        )

        assert entry.key == "test_key"
        assert entry.value == {"test": "data"}
        assert entry.created_at == current_time
        assert entry.ttl_seconds == 3600
        assert entry.access_count == 5
        assert entry.last_accessed == current_time + 100

    def test_cache_entry_defaults(self):
        """Test CacheEntry with default values."""
        import time

        current_time = time.time()

        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time,
            ttl_seconds=1800,
        )

        assert entry.access_count == 0
        assert entry.last_accessed == 0.0

    def test_cache_entry_is_expired(self):
        """Test CacheEntry expiration logic."""
        import time

        current_time = time.time()

        # Not expired
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time,
            ttl_seconds=3600,
        )
        assert not entry.is_expired()

        # Expired
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time - 7200,  # 2 hours ago
            ttl_seconds=3600,  # 1 hour TTL
        )
        assert entry.is_expired()

    def test_cache_entry_access(self):
        """Test CacheEntry access tracking."""
        import time

        current_time = time.time()

        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time,
            ttl_seconds=3600,
        )

        assert entry.access_count == 0
        assert entry.last_accessed == 0.0

        # Access the entry
        entry.access()

        assert entry.access_count == 1
        assert entry.last_accessed >= current_time


class TestCacheKeyGenerator:
    """Test cases for CacheKeyGenerator."""

    def test_generate_key_basic(self):
        """Test basic cache key generation."""
        request = StructuredRequest(
            prompt="Generate a user profile",
            response_model=TestUserProfile,
            task_type="general",
        )

        key = CacheKeyGenerator.generate_key(request)

        assert isinstance(key, str)
        assert key.startswith("structured_llm:")
        assert len(key) > len("structured_llm:")

    def test_generate_key_with_model(self):
        """Test cache key generation with model specified."""
        request1 = StructuredRequest(
            prompt="Generate a user profile",
            response_model=TestUserProfile,
            task_type="general",
        )

        request2 = StructuredRequest(
            prompt="Generate a user profile",
            response_model=TestUserProfile,
            task_type="general",
            model="openai/gpt-4o",
        )

        key1 = CacheKeyGenerator.generate_key(request1)
        key2 = CacheKeyGenerator.generate_key(request2)

        assert isinstance(key1, str)
        assert isinstance(key2, str)
        assert key1 != key2  # Different models should generate different keys

    def test_generate_key_with_provider_opts(self):
        """Test cache key generation with provider options."""
        request1 = StructuredRequest(
            prompt="Generate a user profile",
            response_model=TestUserProfile,
            task_type="general",
        )

        request2 = StructuredRequest(
            prompt="Generate a user profile",
            response_model=TestUserProfile,
            task_type="general",
            provider_opts={"temperature": 0.7, "max_tokens": 100},
        )

        key1 = CacheKeyGenerator.generate_key(request1)
        key2 = CacheKeyGenerator.generate_key(request2)

        assert isinstance(key1, str)
        assert isinstance(key2, str)
        assert key1 != key2  # Different provider opts should generate different keys

    def test_generate_key_deterministic(self):
        """Test that cache key generation is deterministic."""
        request1 = StructuredRequest(
            prompt="Generate a user profile",
            response_model=TestUserProfile,
            task_type="general",
            model="openai/gpt-4o",
        )

        request2 = StructuredRequest(
            prompt="Generate a user profile",
            response_model=TestUserProfile,
            task_type="general",
            model="openai/gpt-4o",
        )

        key1 = CacheKeyGenerator.generate_key(request1)
        key2 = CacheKeyGenerator.generate_key(request2)

        assert key1 == key2

    def test_generate_key_different_prompts(self):
        """Test that different prompts generate different keys."""
        request1 = StructuredRequest(
            prompt="Generate a user profile",
            response_model=TestUserProfile,
            task_type="general",
        )

        request2 = StructuredRequest(
            prompt="Generate a product listing",
            response_model=TestUserProfile,
            task_type="general",
        )

        key1 = CacheKeyGenerator.generate_key(request1)
        key2 = CacheKeyGenerator.generate_key(request2)

        assert key1 != key2

    def test_generate_key_different_models(self):
        """Test that different models generate different keys."""
        request1 = StructuredRequest(
            prompt="Generate a user profile",
            response_model=TestUserProfile,
            task_type="general",
            model="openai/gpt-4o",
        )

        request2 = StructuredRequest(
            prompt="Generate a user profile",
            response_model=TestUserProfile,
            task_type="general",
            model="anthropic/claude-3",
        )

        key1 = CacheKeyGenerator.generate_key(request1)
        key2 = CacheKeyGenerator.generate_key(request2)

        assert key1 != key2

    def test_generate_key_streaming_request(self):
        """Test cache key generation for streaming requests."""
        request = StreamingStructuredRequest(
            prompt="Generate a user profile",
            response_model=TestUserProfile,
            task_type="general",
            model="openai/gpt-4o",
        )

        key = CacheKeyGenerator.generate_key(request)

        assert isinstance(key, str)
        assert key.startswith("structured_llm:")

    def test_generate_model_schema_key(self):
        """Test model schema key generation."""
        schema_key = CacheKeyGenerator.generate_model_schema_key(TestUserProfile)

        assert isinstance(schema_key, str)
        assert len(schema_key) == 16  # Should be 16 characters (first 16 of hash)

    def test_generate_model_schema_key_deterministic(self):
        """Test that model schema key generation is deterministic."""
        key1 = CacheKeyGenerator.generate_model_schema_key(TestUserProfile)
        key2 = CacheKeyGenerator.generate_model_schema_key(TestUserProfile)

        assert key1 == key2


class TestResponseCache:
    """Test cases for ResponseCache."""

    def test_cache_creation(self):
        """Test ResponseCache initialization."""
        cache = ResponseCache(default_ttl_seconds=1800)

        assert len(cache.cache) == 0
        assert cache.default_ttl == 1800
        assert cache.hits == 0
        assert cache.misses == 0
        assert cache.evictions == 0

    def test_cache_get_miss(self):
        """Test cache get with cache miss."""
        cache = ResponseCache()

        result = cache.get("nonexistent_key")

        assert result is None
        assert cache.misses == 1
        assert cache.hits == 0

    def test_cache_set_and_get(self):
        """Test cache set and get operations."""
        cache = ResponseCache()

        # Set a value
        cache.set("test_key", "test_value", ttl_seconds=3600)

        assert len(cache.cache) == 1
        assert "test_key" in cache.cache

        # Get the value
        result = cache.get("test_key")

        assert result == "test_value"
        assert cache.hits == 1
        assert cache.misses == 0

    def test_cache_get_expired(self):
        """Test cache get with expired entry."""
        import time

        cache = ResponseCache()

        # Set a value with very short TTL
        cache.set("test_key", "test_value", ttl_seconds=1)  # Expire in 1 second

        # Wait for expiration (add margin to avoid timing flakiness on CI)
        time.sleep(1.3)

        # Try to get the expired value
        result = cache.get("test_key")

        assert result is None
        assert cache.misses == 1
        assert cache.evictions == 1
        assert len(cache.cache) == 0  # Entry should be removed

    def test_cache_invalidate(self):
        """Test cache invalidation."""
        cache = ResponseCache()

        # Set a value
        cache.set("test_key", "test_value")

        # Verify it's cached
        assert cache.get("test_key") == "test_value"

        # Invalidate it
        result = cache.invalidate("test_key")

        assert result is True
        assert cache.get("test_key") is None
        assert cache.evictions == 1

    def test_cache_invalidate_nonexistent(self):
        """Test cache invalidation of nonexistent key."""
        cache = ResponseCache()

        result = cache.invalidate("nonexistent_key")

        assert result is False
        assert cache.evictions == 0

    def test_cache_clear_expired(self):
        """Test clearing expired entries."""
        cache = ResponseCache()

        # Set some values
        cache.set("key1", "value1", ttl_seconds=3600)  # Won't expire
        cache.set("key2", "value2", ttl_seconds=1)  # Will expire
        cache.set("key3", "value3", ttl_seconds=1)  # Will expire

        # Force expiration deterministically by adjusting created_at
        import time as _time

        cache.cache["key2"].created_at = _time.time() - 2.0
        cache.cache["key3"].created_at = _time.time() - 2.0

        # Clear expired entries
        removed_count = cache.clear_expired()

        assert removed_count == 2
        assert len(cache.cache) == 1
        assert "key1" in cache.cache
        assert "key2" not in cache.cache
        assert "key3" not in cache.cache
        assert cache.evictions == 2

    def test_cache_cleanup_stale_entries(self):
        """Test cleaning up stale entries."""
        import time

        cache = ResponseCache()

        current_time = time.time()

        # Create entries with different access times
        entry1 = CacheEntry("key1", "value1", current_time, 3600, 0, current_time)  # Recently accessed
        entry2 = CacheEntry("key2", "value2", current_time, 3600, 0, current_time - 7200)  # Accessed 2 hours ago
        entry3 = CacheEntry("key3", "value3", current_time, 3600, 0, current_time - 10800)  # Accessed 3 hours ago

        cache.cache = {"key1": entry1, "key2": entry2, "key3": entry3}

        # Clean up entries older than 1 hour
        removed_count = cache.cleanup_stale_entries(max_age_seconds=3600)

        assert removed_count == 2
        assert len(cache.cache) == 1
        assert "key1" in cache.cache
        assert "key2" not in cache.cache
        assert "key3" not in cache.cache
        assert cache.evictions == 2

    def test_cache_get_stats(self):
        """Test cache statistics."""
        cache = ResponseCache()

        # Initial stats
        stats = cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["hit_rate"] == 0.0
        assert stats["total_requests"] == 0

        # Add some data
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Generate some hits and misses
        cache.get("key1")  # Hit
        cache.get("key2")  # Hit
        cache.get("key3")  # Miss
        cache.get("key4")  # Miss

        stats = cache.get_stats()
        assert stats["total_entries"] == 2
        assert stats["hits"] == 2
        assert stats["misses"] == 2
        assert stats["evictions"] == 0
        assert stats["hit_rate"] == 0.5
        assert stats["total_requests"] == 4

    def test_cache_get_ttl_for_request(self):
        """Test TTL determination based on request type."""
        cache = ResponseCache()

        # Test different task types
        request_general = StructuredRequest(prompt="test", response_model=TestUserProfile, task_type="general")
        request_analysis = StructuredRequest(prompt="test", response_model=TestUserProfile, task_type="analysis")
        request_code = StructuredRequest(prompt="test", response_model=TestUserProfile, task_type="code")
        request_factual = StructuredRequest(prompt="test", response_model=TestUserProfile, task_type="factual")

        assert cache.get_ttl_for_request(request_general) == 3600  # 1 hour
        assert cache.get_ttl_for_request(request_analysis) == 7200  # 2 hours
        assert cache.get_ttl_for_request(request_code) == 1800  # 30 minutes
        assert cache.get_ttl_for_request(request_factual) == 86400  # 24 hours

    def test_cache_get_ttl_for_streaming_request(self):
        """Test TTL determination for streaming requests."""
        cache = ResponseCache()

        # Regular streaming request
        streaming_request = StreamingStructuredRequest(
            prompt="test", response_model=TestUserProfile, task_type="general"
        )

        ttl = cache.get_ttl_for_request(streaming_request)
        assert ttl <= 1800  # Should be <= 30 minutes for streaming

    def test_cache_get_size_info(self):
        """Test cache size information."""
        cache = ResponseCache()

        # Empty cache
        size_info = cache.get_size_info()
        assert size_info["total_entries"] == 0
        assert size_info["approximate_size_bytes"] == 0
        assert size_info["entries_by_ttl"] == {}
        assert isinstance(size_info["oldest_entry_age"], int | float)
        assert isinstance(size_info["newest_entry_age"], int | float)

        # Add some entries
        cache.set("key1", "short_value", ttl_seconds=1800)
        cache.set("key2", "longer_value_here", ttl_seconds=3600)
        cache.set("key3", "another_value", ttl_seconds=1800)

        size_info = cache.get_size_info()
        assert size_info["total_entries"] == 3
        assert size_info["approximate_size_bytes"] > 0
        assert size_info["entries_by_ttl"]["1800s"] == 2
        assert size_info["entries_by_ttl"]["3600s"] == 1

    def test_cache_size_limits_max_entries(self):
        """Test cache size limits with max_entries."""
        cache = ResponseCache(max_entries=3)

        # Add entries up to the limit
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        assert len(cache.cache) == 3

        # Add one more entry - should trigger eviction
        cache.set("key4", "value4")

        assert len(cache.cache) == 3  # Should still be 3
        assert "key1" not in cache.cache  # Oldest should be evicted (LRU)
        assert "key2" in cache.cache
        assert "key3" in cache.cache
        assert "key4" in cache.cache
        assert cache.size_limit_evictions == 1

    def test_cache_size_limits_max_memory(self):
        """Test cache size limits with max_memory_mb."""
        # Set very low memory limit (1KB)
        cache = ResponseCache(max_memory_mb=0.001)  # 1KB

        # Add a small entry
        cache.set("key1", "small_value")

        # Add a large entry that should trigger eviction
        large_value = "x" * 2000  # ~2KB string
        cache.set("key2", large_value)

        # Should have evicted the first entry to make room
        assert len(cache.cache) == 1
        assert "key1" not in cache.cache
        assert "key2" in cache.cache
        assert cache.size_limit_evictions >= 1

    def test_cache_memory_tracking(self):
        """Test accurate memory size tracking."""
        cache = ResponseCache()

        # Start with empty cache
        assert cache.current_memory_bytes == 0

        # Add first entry
        cache.set("key1", "test_value")
        initial_memory = cache.current_memory_bytes
        assert initial_memory > 0

        # Add second entry
        cache.set("key2", "another_value")
        second_memory = cache.current_memory_bytes
        assert second_memory > initial_memory

        # Remove first entry
        cache.invalidate("key1")
        after_removal_memory = cache.current_memory_bytes
        assert after_removal_memory < second_memory

        # Verify memory tracking accuracy
        size_info = cache.get_size_info()
        assert abs(size_info["approximate_size_bytes"] - after_removal_memory) < 100  # Allow small discrepancy

    def test_cache_compression_enabled(self):
        """Test cache compression when enabled."""
        cache = ResponseCache(enable_compression=True, compression_min_size_bytes=100)

        # Add a small value (shouldn't be compressed)
        small_value = TestUserProfile(name="Alice", age=25, email="alice@test.com")
        cache.set("small_key", small_value)

        entry = cache.cache["small_key"]
        assert not entry.compressed
        assert entry.original_size == 0

        # Add a large value (should be compressed)
        # Manually create a large string representation
        large_data = {"name": "Bob", "age": 30, "email": "bob@test.com", "data": "x" * 200}
        cache.set("large_key", large_data)

        entry = cache.cache["large_key"]
        if entry.compressed:
            assert entry.original_size > 0
            assert isinstance(entry.value, bytes)

            # Test decompression
            retrieved = cache.get("large_key")
            assert retrieved == large_data

    def test_cache_compression_disabled(self):
        """Test cache compression when disabled."""
        cache = ResponseCache(enable_compression=False)

        # Add a large value (shouldn't be compressed)
        large_value = "x" * 1000
        cache.set("large_key", large_value)

        entry = cache.cache["large_key"]
        assert not entry.compressed
        assert entry.original_size == 0
        assert isinstance(entry.value, str)

    def test_cache_lru_eviction_order(self):
        """Test LRU eviction maintains correct order."""
        cache = ResponseCache(max_entries=3)

        # Add entries in order
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 (make it most recently used)
        cache.get("key1")

        # Add new entry - should evict key2 (least recently used)
        cache.set("key4", "value4")

        assert "key1" in cache.cache  # Most recently used
        assert "key2" not in cache.cache  # Least recently used, should be evicted
        assert "key3" in cache.cache
        assert "key4" in cache.cache

    def test_cache_health_status_healthy(self):
        """Test cache health status when healthy."""
        cache = ResponseCache(max_entries=100, max_memory_mb=10.0)

        # Add some entries
        for i in range(10):
            cache.set(f"key{i}", f"value{i}")

        # Generate some cache hits
        for i in range(5):
            cache.get(f"key{i}")

        health = cache.get_health_status()

        assert health["status"] == "healthy"
        assert len(health["health_issues"]) == 0
        assert health["memory_usage_percent"] < cache.HIGH_MEMORY_USAGE_THRESHOLD
        assert health["entries_usage_percent"] < cache.HIGH_ENTRIES_USAGE_THRESHOLD
        assert health["hit_rate"] > cache.LOW_HIT_RATE_THRESHOLD

    def test_cache_health_status_warning(self):
        """Test cache health status with warnings."""
        cache = ResponseCache(max_entries=10, max_memory_mb=1.0)

        # Fill cache to high usage
        for i in range(8):  # 80% usage
            cache.set(f"key{i}", f"value{i}")

        health = cache.get_health_status()

        assert health["status"] in ["healthy", "warning"]
        assert health["entries_usage_percent"] >= 80

    def test_cache_health_status_critical(self):
        """Test cache health status when critical."""
        cache = ResponseCache(max_entries=5, max_memory_mb=0.1)

        # Fill cache completely
        for i in range(5):
            cache.set(f"key{i}", f"value{i}")

        # Set very low hit rate by having many misses
        for i in range(20):  # 20 misses
            cache.get(f"nonexistent{i}")

        health = cache.get_health_status()

        # Should be warning or critical due to multiple issues
        assert health["status"] in ["warning", "critical"]
        assert len(health["health_issues"]) > 0

    def test_cache_performance_metrics(self):
        """Test cache performance metrics collection."""
        cache = ResponseCache()

        # Add some test data
        for i in range(5):
            cache.set(f"key{i}", f"value{i}")

        # Generate hits and misses
        cache.get("key1")  # Hit
        cache.get("key2")  # Hit
        cache.get("nonexistent1")  # Miss
        cache.get("nonexistent2")  # Miss

        # Access entries multiple times
        cache.get("key1")  # Second access
        cache.get("key1")  # Third access

        metrics = cache.get_performance_metrics()

        assert metrics["cache_hits"] == 4  # 3 hits on key1 + 1 hit on key2
        assert metrics["cache_misses"] == 2
        assert metrics["total_requests"] == 6
        assert metrics["hit_rate"] == 4 / 6
        assert metrics["entries_count"] == 5
        assert metrics["avg_access_frequency"] > 0
        assert metrics["fresh_entries"] >= 0
        assert metrics["stale_entries"] >= 0

    def test_cache_size_info_with_limits(self):
        """Test cache size info includes limit information."""
        cache = ResponseCache(
            max_entries=50, max_memory_mb=5.0, enable_compression=True, compression_min_size_bytes=512
        )

        # Add some entries
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        size_info = cache.get_size_info()

        assert size_info["max_entries_limit"] == 50
        assert size_info["max_memory_mb_limit"] == 5.0
        assert size_info["compression_enabled"] is True
        assert size_info["compression_min_size"] == 512
        assert size_info["size_limit_evictions"] == 0

    def test_cache_eviction_updates_memory_tracking(self):
        """Test that evictions properly update memory tracking."""
        cache = ResponseCache(max_entries=2)

        # Add entries with different sizes
        cache.set("key1", "short")
        cache.set("key2", "medium_length")

        initial_memory = cache.current_memory_bytes

        # Add third entry with different size - should evict one
        cache.set("key3", "this_is_a_much_longer_value")

        # Memory should be updated
        assert cache.current_memory_bytes != initial_memory
        assert len(cache.cache) == 2
        assert cache.size_limit_evictions == 1

    def test_cache_compression_memory_savings(self):
        """Test that compression actually saves memory."""
        cache_compressed = ResponseCache(enable_compression=True, compression_min_size_bytes=50)
        cache_uncompressed = ResponseCache(enable_compression=False)

        # Create a large compressible value
        large_value = {"data": "x" * 1000, "metadata": "y" * 500}

        cache_compressed.set("key1", large_value)
        cache_uncompressed.set("key2", large_value)

        compressed_memory = cache_compressed.current_memory_bytes
        uncompressed_memory = cache_uncompressed.current_memory_bytes

        # Compressed version should use less memory (with some overhead for compression)
        # Allow for compression overhead, but should still be smaller for highly compressible data
        assert compressed_memory <= uncompressed_memory * 1.1  # Allow 10% overhead


class TestCachingIntegration:
    """Integration tests for caching functionality."""

    @patch("core.structured_llm_service.INSTRUCTOR_AVAILABLE", False)
    def test_cache_hit_integration(self, mock_openrouter_service):
        """Test cache hit integration with service."""
        service = StructuredLLMService(mock_openrouter_service)

        # Mock OpenRouter response
        mock_openrouter_service.route.return_value = {
            "status": "success",
            "response": '{"name": "Alice", "age": 28, "email": "alice@test.com"}',
        }

        request = StructuredRequest(prompt="Generate a user profile", response_model=TestUserProfile)

        # First call should miss cache and call OpenRouter
        result1 = service.route_structured(request)
        assert isinstance(result1, TestUserProfile)
        assert mock_openrouter_service.route.call_count == 1

        # Second call should hit cache and not call OpenRouter
        result2 = service.route_structured(request)
        assert isinstance(result2, TestUserProfile)
        assert mock_openrouter_service.route.call_count == 1  # Still 1 call

        # Results should be identical
        assert result1.name == result2.name
        assert result1.age == result2.age
        assert result1.email == result2.email

    @patch("core.structured_llm_service.INSTRUCTOR_AVAILABLE", False)
    def test_cache_miss_integration(self, mock_openrouter_service):
        """Test cache miss integration with service."""
        service = StructuredLLMService(mock_openrouter_service)

        # Mock OpenRouter to return different responses for different prompts
        def mock_route_response(*args, **kwargs):
            prompt = kwargs.get("prompt", "")
            if "profile 1" in prompt:
                return {"status": "success", "response": '{"name": "Alice", "age": 28, "email": "alice@test.com"}'}
            elif "profile 2" in prompt:
                return {"status": "success", "response": '{"name": "Bob", "age": 35, "email": "bob@test.com"}'}
            else:
                return {"status": "success", "response": '{"name": "Charlie", "age": 25, "email": "charlie@test.com"}'}

        mock_openrouter_service.route.side_effect = mock_route_response

        request1 = StructuredRequest(prompt="Generate profile 1", response_model=TestUserProfile)
        request2 = StructuredRequest(prompt="Generate profile 2", response_model=TestUserProfile)

        # Both calls should miss cache and call OpenRouter
        result1 = service.route_structured(request1)
        result2 = service.route_structured(request2)

        assert isinstance(result1, TestUserProfile)
        assert isinstance(result2, TestUserProfile)
        assert mock_openrouter_service.route.call_count == 2

        # Results should be different
        assert result1.name != result2.name
        assert result1.name == "Alice"
        assert result2.name == "Bob"

    @patch("core.structured_llm_service.INSTRUCTOR_AVAILABLE", False)
    def test_streaming_cache_hit_integration(self, mock_openrouter_service):
        """Test streaming cache hit integration."""
        service = StructuredLLMService(mock_openrouter_service)

        # Mock OpenRouter response
        mock_openrouter_service.route.return_value = {
            "status": "success",
            "response": '{"name": "Charlie", "age": 25, "email": "charlie@test.com"}',
        }

        request = StreamingStructuredRequest(prompt="Generate a user profile", response_model=TestUserProfile)

        # Test async streaming
        import asyncio

        async def run_test():
            # First streaming call
            responses1 = [response async for response in service.route_structured_streaming(request)]
            assert len(responses1) >= 1
            final_response1 = responses1[-1]
            assert isinstance(final_response1.partial_result, TestUserProfile)

            # Second streaming call should hit cache
            responses2 = [response async for response in service.route_structured_streaming(request)]
            assert len(responses2) >= 1
            final_response2 = responses2[-1]
            assert isinstance(final_response2.partial_result, TestUserProfile)

            # Results should be identical
            assert final_response1.partial_result.name == final_response2.partial_result.name
            assert final_response1.partial_result.age == final_response2.partial_result.age

            # OpenRouter should only be called once
            assert mock_openrouter_service.route.call_count == 1

        asyncio.run(run_test())

    @patch("core.structured_llm_service.INSTRUCTOR_AVAILABLE", False)
    def test_cache_maintenance_integration(self, mock_openrouter_service):
        """Test cache maintenance integration."""
        service = StructuredLLMService(mock_openrouter_service)

        # Mock OpenRouter response
        mock_openrouter_service.route.return_value = {
            "status": "success",
            "response": '{"name": "David", "age": 40, "email": "david@test.com"}',
        }

        request = StructuredRequest(prompt="Generate a user profile", response_model=TestUserProfile)

        # Make a request to populate cache
        result = service.route_structured(request)
        assert isinstance(result, TestUserProfile)

        # Verify cache has entry
        assert len(service.cache.cache) == 1

        # Manually set last cleanup to old time to trigger maintenance
        import time

        service._last_cleanup = time.time() - 400  # Older than cleanup interval

        # Make another request (should trigger maintenance)
        result2 = service.route_structured(request)
        assert isinstance(result2, TestUserProfile)

        # Cache should still have the entry (not expired)
        assert len(service.cache.cache) == 1

    def test_cache_ttl_different_task_types(self):
        """Test that different task types get different TTLs."""
        cache = ResponseCache()

        # Test various task types
        tasks_and_ttls = [
            ("general", 3600),  # 1 hour
            ("analysis", 7200),  # 2 hours
            ("code", 1800),  # 30 minutes
            ("creative", 1800),  # 30 minutes
            ("factual", 86400),  # 24 hours
            ("unknown", 3600),  # Default to 1 hour
        ]

        for task_type, expected_ttl in tasks_and_ttls:
            request = StructuredRequest(prompt="test", response_model=TestUserProfile, task_type=task_type)
            ttl = cache.get_ttl_for_request(request)
            assert ttl == expected_ttl, f"Task type {task_type} should have TTL {expected_ttl}, got {ttl}"

    def test_cache_key_uniqueness(self):
        """Test that cache keys are unique for different requests."""
        keys = set()

        # Generate keys for various request combinations
        requests = [
            StructuredRequest(prompt="test1", response_model=TestUserProfile, task_type="general"),
            StructuredRequest(prompt="test2", response_model=TestUserProfile, task_type="general"),
            StructuredRequest(prompt="test1", response_model=TestProductInfo, task_type="general"),
            StructuredRequest(prompt="test1", response_model=TestUserProfile, task_type="analysis"),
            StructuredRequest(prompt="test1", response_model=TestUserProfile, task_type="general", model="gpt-4"),
            StructuredRequest(prompt="test1", response_model=TestUserProfile, task_type="general", model="claude-3"),
        ]

        for request in requests:
            key = CacheKeyGenerator.generate_key(request)
            assert key not in keys, f"Duplicate key generated: {key}"
            keys.add(key)

        assert len(keys) == len(requests)


if __name__ == "__main__":
    pytest.main([__file__])
