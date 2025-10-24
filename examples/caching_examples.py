"""
Caching Examples for StructuredLLMService
==========================================

This module demonstrates how to use the intelligent caching features of the
StructuredLLMService to reduce API costs and improve response times.

The caching system provides:
- Automatic cache key generation based on request parameters
- TTL-based expiration with task-specific defaults
- Cache hit/miss metrics for monitoring
- Background maintenance for expired entries
- Support for both regular and streaming requests
"""

import asyncio

from pydantic import BaseModel

from core.structured_llm_service import (
    CacheKeyGenerator,
    ResponseCache,
    StreamingStructuredRequest,
    StructuredLLMService,
    StructuredRequest,
)


class UserProfile(BaseModel):
    """Example user profile model."""

    name: str
    age: int
    email: str
    interests: list[str]


class ProductRecommendation(BaseModel):
    """Example product recommendation model."""

    product_name: str
    category: str
    price_range: str
    reasoning: str


async def basic_caching_example():
    """
    Basic caching example showing cache hits and misses.

    This example demonstrates:
    - How cache hits avoid API calls
    - How different requests generate different cache keys
    - Cache metrics tracking
    """
    print("=== Basic Caching Example ===")

    # Mock OpenRouter service for demonstration
    class MockOpenRouterService:
        def __init__(self):
            self.call_count = 0

        def route(self, prompt, **kwargs):
            self.call_count += 1
            return {
                "status": "success",
                "response": '{"name": "Alice", "age": 28, "email": "alice@example.com", "interests": ["reading", "coding"]}',
                "model": "gpt-4o",
                "tokens": 150,
            }

    # Create service with mock
    mock_service = MockOpenRouterService()
    service = StructuredLLMService(mock_service)

    # Create identical requests
    request1 = StructuredRequest(
        prompt="Generate a profile for a software engineer",
        response_model=UserProfile,
        task_type="general",
    )

    request2 = StructuredRequest(
        prompt="Generate a profile for a software engineer",  # Same prompt
        response_model=UserProfile,
        task_type="general",
    )

    # First request - cache miss
    print("Making first request (should be cache miss)...")
    result1 = service.route_structured(request1)
    print(f"Result 1: {result1}")
    print(f"API calls so far: {mock_service.call_count}")

    # Second request - cache hit
    print("\nMaking second request (should be cache hit)...")
    result2 = service.route_structured(request2)
    print(f"Result 2: {result2}")
    print(f"API calls so far: {mock_service.call_count}")

    # Results should be identical
    assert result1.name == result2.name
    assert result1.age == result2.age

    # Only one API call should have been made
    assert mock_service.call_count == 1

    print("\n✅ Cache working correctly - second request used cached result!")


async def ttl_based_caching_example():
    """
    TTL-based caching example showing different TTLs for different task types.

    This example demonstrates:
    - Task-specific TTL values
    - How TTL affects cache expiration
    - Cache statistics
    """
    print("\n=== TTL-Based Caching Example ===")

    # Create a cache with short TTLs for demonstration
    cache = ResponseCache(default_ttl_seconds=2)  # 2 second TTL

    # Different task types get different TTLs
    tasks_and_ttls = [
        ("general", 3600),  # 1 hour
        ("analysis", 7200),  # 2 hours
        ("code", 1800),  # 30 minutes
        ("factual", 86400),  # 24 hours
    ]

    print("TTL values for different task types:")
    for task_type, expected_ttl in tasks_and_ttls:
        request = StructuredRequest(
            prompt="test", response_model=UserProfile, task_type=task_type
        )
        ttl = cache.get_ttl_for_request(request)
        print(f"  {task_type}: {ttl} seconds ({ttl / 3600:.1f} hours)")

    # Demonstrate cache expiration
    print("\nDemonstrating cache expiration:")
    cache.set("test_key", "test_value", ttl_seconds=1)

    # Immediately retrieve - should work
    result = cache.get("test_key")
    print(f"Immediate retrieval: {result}")

    # Wait for expiration
    print("Waiting for cache expiration...")
    await asyncio.sleep(1.1)

    # Try to retrieve again - should be expired
    result = cache.get("test_key")
    print(f"After expiration: {result}")

    print("\n✅ TTL-based caching working correctly!")


async def streaming_caching_example():
    """
    Streaming caching example showing cache integration with streaming requests.

    This example demonstrates:
    - Cache hits for streaming requests
    - Progress tracking with cached results
    - Identical results from cache vs API
    """
    print("\n=== Streaming Caching Example ===")

    class MockOpenRouterService:
        def __init__(self):
            self.call_count = 0

        def route(self, prompt, **kwargs):
            self.call_count += 1
            return {
                "status": "success",
                "response": '{"product_name": "Wireless Headphones", "category": "Electronics", "price_range": "$100-200", "reasoning": "Great for music lovers"}',
                "model": "gpt-4o",
                "tokens": 120,
            }

    mock_service = MockOpenRouterService()
    service = StructuredLLMService(mock_service)

    # Create streaming request
    request = StreamingStructuredRequest(
        prompt="Recommend a product for music enthusiasts",
        response_model=ProductRecommendation,
        task_type="general",
    )

    # Track progress events
    progress_events = []

    def track_progress(event):
        progress_events.append(event)
        print(f"Progress: {event.event_type} - {event.message}")

    request.progress_callback = track_progress

    print("Making first streaming request...")
    responses1 = []
    async for response in service.route_structured_streaming(request):
        responses1.append(response)

    print(f"First request - API calls: {mock_service.call_count}")
    print(f"Progress events: {len(progress_events)}")

    # Reset progress events
    progress_events.clear()

    print("\nMaking second streaming request (should use cache)...")
    responses2 = []
    async for response in service.route_structured_streaming(request):
        responses2.append(response)

    print(f"Second request - API calls: {mock_service.call_count}")
    print(f"Progress events: {len(progress_events)}")

    # Compare results
    final_result1 = responses1[-1].partial_result
    final_result2 = responses2[-1].partial_result

    assert final_result1.product_name == final_result2.product_name
    assert final_result1.category == final_result2.category

    # Only one API call should have been made
    assert mock_service.call_count == 1

    print("\n✅ Streaming caching working correctly!")


async def cache_key_generation_example():
    """
    Cache key generation example showing how keys are created.

    This example demonstrates:
    - Deterministic key generation
    - How different parameters affect keys
    - Key uniqueness
    """
    print("\n=== Cache Key Generation Example ===")

    # Create various requests
    requests = [
        StructuredRequest(
            prompt="Generate a user profile",
            response_model=UserProfile,
            task_type="general",
        ),
        StructuredRequest(
            prompt="Generate a user profile",  # Same prompt
            response_model=UserProfile,
            task_type="general",
        ),
        StructuredRequest(
            prompt="Generate a different profile",  # Different prompt
            response_model=UserProfile,
            task_type="general",
        ),
        StructuredRequest(
            prompt="Generate a user profile",
            response_model=UserProfile,
            task_type="analysis",  # Different task type
        ),
        StructuredRequest(
            prompt="Generate a user profile",
            response_model=UserProfile,
            task_type="general",
            model="gpt-4o",  # Different model
        ),
    ]

    print("Generated cache keys:")
    keys = []
    for i, request in enumerate(requests, 1):
        key = CacheKeyGenerator.generate_key(request)
        keys.append(key)
        print(f"  Request {i}: {key}")

    # First two should be identical (same parameters)
    assert keys[0] == keys[1], "Identical requests should have same key"

    # Others should be different
    for i in range(2, len(keys)):
        assert keys[i] != keys[0], f"Request {i + 1} should have different key"

    print("\n✅ Cache key generation working correctly!")


async def cache_maintenance_example():
    """
    Cache maintenance example showing automatic cleanup.

    This example demonstrates:
    - Periodic cleanup of expired entries
    - Cache statistics
    - Memory management
    """
    print("\n=== Cache Maintenance Example ===")

    cache = ResponseCache(default_ttl_seconds=1)  # Very short TTL for demo

    # Add some entries
    print("Adding cache entries...")
    cache.set("key1", "value1", ttl_seconds=10)  # Won't expire soon
    cache.set("key2", "value2", ttl_seconds=1)  # Will expire
    cache.set("key3", "value3", ttl_seconds=1)  # Will expire

    print(f"Initial cache size: {len(cache.cache)} entries")

    # Wait for some entries to expire
    print("Waiting for entries to expire...")
    await asyncio.sleep(1.1)

    # Manually trigger cleanup
    print("Running cache cleanup...")
    expired_count = cache.clear_expired()

    print(f"Expired entries removed: {expired_count}")
    print(f"Remaining cache size: {len(cache.cache)} entries")

    # Get cache statistics
    stats = cache.get_stats()
    print("\nCache statistics:")
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Hit rate: {stats['hit_rate']:.2%}")
    print(f"  Evictions: {stats['evictions']}")

    print("\n✅ Cache maintenance working correctly!")


async def main():
    """Run all caching examples."""
    print("🚀 StructuredLLMService Caching Examples")
    print("=" * 50)

    await basic_caching_example()
    await ttl_based_caching_example()
    await streaming_caching_example()
    await cache_key_generation_example()
    await cache_maintenance_example()

    print("\n" + "=" * 50)
    print("✅ All caching examples completed successfully!")
    print("\nKey benefits of the caching system:")
    print("• Reduces API costs by avoiding duplicate requests")
    print("• Improves response times for cached queries")
    print("• Provides task-specific TTL values")
    print("• Includes comprehensive metrics and monitoring")
    print("• Supports both regular and streaming requests")
    print("• Automatic maintenance and cleanup")


if __name__ == "__main__":
    asyncio.run(main())
