"""
Test utilities and helper functions.

This module provides async helpers, mock builders, and other utility functions
for testing the Ultimate Discord Intelligence Bot.
"""
import asyncio
import json
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, Mock
from platform.core.step_result import StepResult

class AsyncTestHelper:
    """Helper class for async testing operations."""

    @staticmethod
    async def run_async_test(test_func: Callable, timeout: float=5.0) -> Any:
        """Run an async test function with timeout."""
        try:
            return await asyncio.wait_for(test_func(), timeout=timeout)
        except TimeoutError:
            raise AssertionError(f'Async test timed out after {timeout} seconds')

    @staticmethod
    async def wait_for_condition(condition_func: Callable[[], bool], timeout: float=5.0, check_interval: float=0.1) -> bool:
        """Wait for a condition to become true."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            await asyncio.sleep(check_interval)
        return False

    @staticmethod
    async def run_concurrent_tasks(tasks: list[Callable], max_concurrent: int | None=None) -> list[Any]:
        """Run multiple async tasks concurrently."""
        if max_concurrent:
            semaphore = asyncio.Semaphore(max_concurrent)

            async def limited_task(task: Callable[..., Any]) -> Any:
                async with semaphore:
                    return await task()
            tasks = [limited_task(task) for task in tasks]
        return await asyncio.gather(*tasks)

    @staticmethod
    async def simulate_network_delay(delay: float=0.1) -> None:
        """Simulate network delay for testing."""
        await asyncio.sleep(delay)

    @staticmethod
    async def simulate_api_rate_limit(request_count: int, rate_limit: int, reset_time: float=60.0) -> list[StepResult]:
        """Simulate API rate limiting behavior."""
        results = []
        for i in range(request_count):
            if i < rate_limit:
                results.append(StepResult.ok(data={'request_id': i}))
            else:
                results.append(StepResult.fail('Rate limit exceeded', status='rate_limited'))
            await asyncio.sleep(0.01)
        return results

class MockBuilder:
    """Builder class for creating complex mock objects."""

    @staticmethod
    def create_http_client_mock(responses: dict[str, Any] | None=None, raise_exceptions: list[str] | None=None) -> Mock:
        """Create a mock HTTP client with configurable responses."""
        mock_client = Mock()
        if responses is None:
            responses = {'GET': {'status_code': 200, 'json': {'success': True}}, 'POST': {'status_code': 201, 'json': {'created': True}}, 'PUT': {'status_code': 200, 'json': {'updated': True}}, 'DELETE': {'status_code': 204, 'json': {'deleted': True}}}
        if raise_exceptions is None:
            raise_exceptions = []

        async def mock_request(method: str, url: str, **kwargs: dict) -> Mock:
            if method in raise_exceptions:
                raise Exception(f'Simulated {method} error')
            response_data = responses.get(method, {'status_code': 200, 'json': {'success': True}})
            mock_response = Mock()
            mock_response.status_code = response_data['status_code']
            mock_response.json.return_value = response_data['json']
            mock_response.text = json.dumps(response_data['json'])
            mock_response.raise_for_status.return_value = None
            return mock_response
        mock_client.request = AsyncMock(side_effect=mock_request)
        return mock_client

    @staticmethod
    def create_database_mock(query_results: dict[str, list[dict]] | None=None, raise_exceptions: list[str] | None=None) -> Mock:
        """Create a mock database with configurable query results."""
        mock_db = Mock()
        if query_results is None:
            query_results = {'SELECT': [{'id': 1, 'name': 'test'}], 'INSERT': [{'id': 1, 'inserted': True}], 'UPDATE': [{'id': 1, 'updated': True}], 'DELETE': [{'id': 1, 'deleted': True}]}
        if raise_exceptions is None:
            raise_exceptions = []

        def mock_execute(query: str, params: dict | None=None):
            if any((exc in query.upper() for exc in raise_exceptions)):
                raise Exception(f'Simulated database error for query: {query}')
            query_type = query.strip().split()[0].upper()
            return query_results.get(query_type, [])
        mock_db.execute = Mock(side_effect=mock_execute)
        mock_db.fetchall = Mock(return_value=query_results.get('SELECT', []))
        mock_db.fetchone = Mock(return_value=query_results.get('SELECT', [{}])[0] if query_results.get('SELECT') else None)
        return mock_db

    @staticmethod
    def create_redis_mock(cache_data: dict[str, Any] | None=None, raise_exceptions: list[str] | None=None) -> Mock:
        """Create a mock Redis client with configurable cache data."""
        mock_redis = Mock()
        if cache_data is None:
            cache_data = {'key1': 'value1', 'key2': 'value2', 'key3': json.dumps({'data': 'value3'})}
        if raise_exceptions is None:
            raise_exceptions = []

        def mock_get(key: str):
            if key in raise_exceptions:
                raise Exception(f'Simulated Redis error for key: {key}')
            return cache_data.get(key)

        def mock_set(key: str, value: Any, ex: int | None=None):
            if key in raise_exceptions:
                raise Exception(f'Simulated Redis error for key: {key}')
            cache_data[key] = value
            return True

        def mock_delete(key: str):
            if key in raise_exceptions:
                raise Exception(f'Simulated Redis error for key: {key}')
            if key in cache_data:
                del cache_data[key]
                return 1
            return 0
        mock_redis.get = Mock(side_effect=mock_get)
        mock_redis.set = Mock(side_effect=mock_set)
        mock_redis.delete = Mock(side_effect=mock_delete)
        mock_redis.exists = Mock(side_effect=lambda key: key in cache_data)
        return mock_redis

    @staticmethod
    def create_file_system_mock(files: dict[str, str] | None=None, raise_exceptions: list[str] | None=None) -> Mock:
        """Create a mock file system with configurable files."""
        mock_fs = Mock()
        if files is None:
            files = {'/path/to/file1.txt': 'Content of file 1', '/path/to/file2.json': '{"key": "value"}', '/path/to/file3.py': "print('Hello, World!')"}
        if raise_exceptions is None:
            raise_exceptions = []

        def mock_read_file(filepath: str):
            if filepath in raise_exceptions:
                raise FileNotFoundError(f'Simulated file not found: {filepath}')
            return files.get(filepath, '')

        def mock_write_file(filepath: str, content: str):
            if filepath in raise_exceptions:
                raise PermissionError(f'Simulated permission error: {filepath}')
            files[filepath] = content
            return True

        def mock_file_exists(filepath: str):
            return filepath in files
        mock_fs.read_file = Mock(side_effect=mock_read_file)
        mock_fs.write_file = Mock(side_effect=mock_write_file)
        mock_fs.file_exists = Mock(side_effect=mock_file_exists)
        return mock_fs

class TestDataGenerator:
    """Generator class for creating test data."""

    @staticmethod
    def generate_transcript_data(length: int=100, language: str='en', include_timestamps: bool=True) -> dict[str, Any]:
        """Generate realistic transcript data for testing."""
        words = ['the', 'quick', 'brown', 'fox', 'jumps', 'over', 'lazy', 'dog', 'artificial', 'intelligence', 'machine', 'learning', 'deep', 'neural', 'network', 'algorithm', 'data', 'science', 'programming', 'python']
        text_parts = []
        segments = []
        for i in range(length):
            word = words[i % len(words)]
            text_parts.append(word)
            if include_timestamps:
                start_time = i * 0.5
                end_time = start_time + 0.5
                segments.append({'start': start_time, 'end': end_time, 'text': word, 'confidence': 0.9 + i % 10 * 0.01})
        return {'text': ' '.join(text_parts), 'language': language, 'confidence': 0.95, 'duration': length * 0.5, 'segments': segments, 'metadata': {'source': 'test_generator', 'generated_at': datetime.now(UTC).isoformat(), 'word_count': length}}

    @staticmethod
    def generate_analysis_data(sentiment: str='neutral', topic_count: int=5, entity_count: int=10) -> dict[str, Any]:
        """Generate realistic analysis data for testing."""
        topics = ['technology', 'artificial intelligence', 'machine learning', 'programming', 'data science', 'software development', 'algorithms', 'neural networks', 'deep learning', 'automation']
        entities = [{'text': 'Python', 'type': 'TECHNOLOGY', 'confidence': 0.95}, {'text': 'TensorFlow', 'type': 'TECHNOLOGY', 'confidence': 0.9}, {'text': 'Google', 'type': 'ORGANIZATION', 'confidence': 0.88}, {'text': 'AI researcher', 'type': 'PERSON', 'confidence': 0.85}, {'text': 'machine learning', 'type': 'CONCEPT', 'confidence': 0.92}]
        return {'sentiment': sentiment, 'score': 0.5 + hash(sentiment) % 50 / 100, 'topics': topics[:topic_count], 'entities': entities[:entity_count], 'summary': f'This is a generated analysis with {sentiment} sentiment.', 'metadata': {'analysis_type': 'generated', 'model_version': 'test_v1.0', 'processing_time': 1.5, 'confidence': 0.85}}

    @staticmethod
    def generate_user_data(user_count: int=10, include_roles: bool=True) -> list[dict[str, Any]]:
        """Generate realistic user data for testing."""
        users = []
        roles = ['admin', 'user', 'moderator', 'viewer']
        for i in range(user_count):
            user = {'id': f'user_{i:03d}', 'username': f'testuser{i}', 'email': f'user{i}@example.com', 'created_at': (datetime.now(UTC) - timedelta(days=i)).isoformat(), 'last_login': (datetime.now(UTC) - timedelta(hours=i)).isoformat(), 'active': i % 3 != 0}
            if include_roles:
                user['role'] = roles[i % len(roles)]
            users.append(user)
        return users

    @staticmethod
    def generate_tenant_data(tenant_count: int=5, workspace_per_tenant: int=3) -> list[dict[str, Any]]:
        """Generate realistic tenant data for testing."""
        tenants = []
        for i in range(tenant_count):
            tenant = {'id': f'tenant_{i:03d}', 'name': f'Test Tenant {i}', 'created_at': (datetime.now(UTC) - timedelta(days=i * 10)).isoformat(), 'workspaces': []}
            for j in range(workspace_per_tenant):
                workspace = {'id': f'workspace_{i:03d}_{j:03d}', 'name': f'Workspace {j}', 'created_at': (datetime.now(UTC) - timedelta(days=i * 10 + j)).isoformat(), 'active': j % 2 == 0}
                tenant['workspaces'].append(workspace)
            tenants.append(tenant)
        return tenants

class PerformanceTestHelper:
    """Helper class for performance testing."""

    @staticmethod
    def measure_execution_time(func: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, float]:
        """Measure the execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return (result, execution_time)

    @staticmethod
    async def measure_async_execution_time(func: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, float]:
        """Measure the execution time of an async function."""
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return (result, execution_time)

    @staticmethod
    def benchmark_function(func: Callable[..., Any], iterations: int=100, *args: Any, **kwargs: Any) -> dict[str, float]:
        """Benchmark a function over multiple iterations."""
        times = []
        for _ in range(iterations):
            _, execution_time = PerformanceTestHelper.measure_execution_time(func, *args, **kwargs)
            times.append(execution_time)
        return {'min': min(times), 'max': max(times), 'mean': sum(times) / len(times), 'median': sorted(times)[len(times) // 2], 'iterations': iterations}

    @staticmethod
    async def benchmark_async_function(func: Callable[..., Any], iterations: int=100, *args: Any, **kwargs: Any) -> dict[str, float]:
        """Benchmark an async function over multiple iterations."""
        times = []
        for _ in range(iterations):
            _, execution_time = await PerformanceTestHelper.measure_async_execution_time(func, *args, **kwargs)
            times.append(execution_time)
        return {'min': min(times), 'max': max(times), 'mean': sum(times) / len(times), 'median': sorted(times)[len(times) // 2], 'iterations': iterations}

class TestAssertionHelper:
    """Helper class for custom test assertions."""

    @staticmethod
    def assert_stepresult_success(result: StepResult, expected_data: Any=None) -> None:
        """Assert that a StepResult is successful."""
        assert result.success, f'Expected success but got failure: {result.error}'
        if expected_data is not None:
            assert result.data == expected_data, f'Expected data {expected_data} but got {result.data}'

    @staticmethod
    def assert_stepresult_failure(result: StepResult, expected_status: str | None=None) -> None:
        """Assert that a StepResult is a failure."""
        assert not result.success, f'Expected failure but got success: {result.data}'
        if expected_status:
            assert result.status == expected_status, f'Expected status {expected_status} but got {result.status}'

    @staticmethod
    def assert_tenant_isolation(result_a: StepResult, result_b: StepResult, tenant_a: str, tenant_b: str) -> None:
        """Assert that tenant data is properly isolated."""
        if result_a.success and result_b.success:
            assert result_a.data != result_b.data, f'Tenant {tenant_a} and {tenant_b} data should be different'

    @staticmethod
    def assert_performance_within_limits(execution_time: float, max_time: float, operation: str='operation') -> None:
        """Assert that an operation completes within time limits."""
        assert execution_time <= max_time, f'{operation} took {execution_time:.2f}s, expected <= {max_time:.2f}s'

    @staticmethod
    def assert_rate_limit_respected(results: list[StepResult], rate_limit: int) -> None:
        """Assert that rate limits are respected."""
        successful_requests = sum((1 for result in results if result.success))
        assert successful_requests <= rate_limit, f'Expected <= {rate_limit} successful requests, got {successful_requests}'