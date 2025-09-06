#!/usr/bin/env python3
"""
Streaming Structured LLM Service Examples

This script demonstrates how to use the streaming functionality of the StructuredLLMService
for handling large structured responses with progress tracking and async processing.
"""

import asyncio
import traceback
from unittest.mock import MagicMock

from pydantic import BaseModel

# Import the streaming components
from core.structured_llm_service import (
    ProgressCallback,
    ProgressEvent,
    StreamingStructuredRequest,
    StructuredLLMService,
)


def create_mock_openrouter_service():
    """Create a mock OpenRouter service for examples."""
    mock_service = MagicMock()
    mock_service.api_key = "mock-api-key"
    mock_service.route.return_value = {
        "status": "success",
        "response": '{"name": "Mock User", "age": 25, "email": "mock@example.com"}',
    }
    return mock_service


class UserProfile(BaseModel):
    """Example user profile model."""

    name: str
    age: int
    email: str
    bio: str | None = None
    is_active: bool = True


class ProductInfo(BaseModel):
    """Example product information model."""

    title: str
    price: float
    category: str
    in_stock: bool
    description: str | None = None


def create_progress_callback() -> ProgressCallback:
    """Create a progress callback that prints progress events."""

    def progress_callback(event: ProgressEvent) -> None:
        print(f"[{event.timestamp:.2f}] {event.event_type}: {event.message}")
        if event.progress_percent is not None:
            print(f"  Progress: {event.progress_percent:.1f}%")
        if event.data:
            print(f"  Data: {event.data}")

    return progress_callback


async def basic_streaming_example():
    """Basic streaming example with simple progress tracking."""
    print("\n=== Basic Streaming Example ===")

    # Initialize service (in real usage, this would be properly configured)
    service = StructuredLLMService(create_mock_openrouter_service())

    # Create streaming request
    request = StreamingStructuredRequest(
        prompt="Create a profile for a software engineer named Alex Johnson, age 32, who works at TechCorp",
        response_model=UserProfile,
        progress_callback=create_progress_callback(),
        model="openai/gpt-4o",
    )

    print("Starting streaming request...")
    responses = []

    # Process streaming responses
    async for response in service.route_structured_streaming(request):
        responses.append(response)

        if response.is_complete:
            print("\n✅ Streaming completed!")
            if response.partial_result:
                print(f"Final result: {response.partial_result}")
            elif response.error:
                print(f"❌ Error: {response.error}")
        else:
            print(f"Partial response: {response}")

    return responses


async def advanced_streaming_example():
    """Advanced streaming example with custom progress handling."""
    print("\n=== Advanced Streaming Example ===")

    # Track progress events for analysis
    progress_events = []

    def detailed_progress_callback(event: ProgressEvent) -> None:
        progress_events.append(event)
        print(f"📊 {event.event_type.upper()}: {event.message}")

        # Custom handling based on event type
        if event.event_type == "start":
            print("🚀 Starting structured generation...")
        elif event.event_type == "progress":
            print(f"⚡ Processing... ({event.progress_percent:.1f}%)")
        elif event.event_type == "complete":
            print("Generation completed successfully!")
        elif event.event_type == "error":
            print(f"Error occurred: {event.data}")

    service = StructuredLLMService(create_mock_openrouter_service())

    # Create request for product information
    request = StreamingStructuredRequest(
        prompt="Create a detailed product listing for a premium wireless gaming headset with RGB lighting, priced at $299.99",
        response_model=ProductInfo,
        progress_callback=detailed_progress_callback,
        model="openai/gpt-4o",
        max_retries=3,
    )

    print("Processing product information request...")
    final_response = None

    async for response in service.route_structured_streaming(request):
        if response.is_complete:
            final_response = response
            break

    # Analyze progress events
    print("\nProgress Analysis:")
    print(f"Total events: {len(progress_events)}")
    event_types = {}
    for event in progress_events:
        event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
    print(f"Event breakdown: {event_types}")

    if final_response and final_response.partial_result:
        # Check if it's a ProductInfo instance
        if isinstance(final_response.partial_result, ProductInfo):
            product = final_response.partial_result
            print(f"\nFinal Product: {product.title}")
            print(f"Price: ${product.price}")
            print(f"Category: {product.category}")
            print(f"In Stock: {product.in_stock}")
        else:
            print(f"\nFinal Result: {final_response.partial_result}")

    return final_response


async def error_handling_example():
    """Example demonstrating error handling in streaming."""
    print("\n=== Error Handling Example ===")

    def error_tracking_callback(event: ProgressEvent) -> None:
        if event.event_type == "error":
            print(f"Error detected: {event.message}")
            if event.data:
                print(f"Error details: {event.data}")
        else:
            print(f"Info: {event.event_type}: {event.message}")

    service = StructuredLLMService(create_mock_openrouter_service())

    # Create request that might fail
    request = StreamingStructuredRequest(
        prompt="Generate invalid structured data that will cause parsing errors",
        response_model=UserProfile,
        progress_callback=error_tracking_callback,
        max_retries=2,
    )

    print("Testing error handling...")
    error_count = 0

    async for response in service.route_structured_streaming(request):
        if response.error:
            error_count += 1
            print(f"Error #{error_count}: {response.error}")

        if response.is_complete:
            if response.partial_result:
                print("✅ Successfully recovered from errors!")
                print(f"Result: {response.partial_result}")
            else:
                print("❌ Failed to generate valid result")
            break

    return error_count


async def batch_processing_example():
    """Example of processing multiple streaming requests in batch."""
    print("\n=== Batch Processing Example ===")

    service = StructuredLLMService(create_mock_openrouter_service())

    # Define multiple requests
    requests = [
        StreamingStructuredRequest(
            prompt=f"Create a user profile for Person {i + 1}",
            response_model=UserProfile,
            progress_callback=lambda e, i=i: print(f"Request {i + 1}: {e.message}"),
        )
        for i in range(3)
    ]

    print("Processing 3 streaming requests concurrently...")

    # Process all requests concurrently
    tasks = []
    for i, request in enumerate(requests):
        task = asyncio.create_task(process_single_request(service, request, i + 1))
        tasks.append(task)

    # Wait for all to complete
    results = await asyncio.gather(*tasks)

    print("\nBatch Results:")
    for i, result in enumerate(results):
        if result and result.partial_result:
            print(f"Request {i + 1}: SUCCESS - {result.partial_result.name}")
        else:
            print(f"Request {i + 1}: FAILED")

    return results


async def process_single_request(service: StructuredLLMService, request: StreamingStructuredRequest, request_id: int):
    """Process a single streaming request and return the final response."""
    async for response in service.route_structured_streaming(request):
        if response.is_complete:
            return response
    return None


async def main():
    """Run all streaming examples."""
    print("🚀 Structured LLM Streaming Examples")
    print("=" * 50)

    try:
        # Run examples
        await basic_streaming_example()
        await advanced_streaming_example()
        await error_handling_example()
        await batch_processing_example()

        print("\n" + "=" * 50)
        print("✅ All streaming examples completed!")

    except Exception as e:
        print(f"Example failed with error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
