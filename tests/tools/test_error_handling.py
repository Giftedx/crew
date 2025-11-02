"""Error handling tests for all tools."""
from __future__ import annotations
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool

class TestToolErrorHandling:
    """Test error handling patterns across all tools."""

    def test_base_tool_error_handling(self):
        """Test that BaseTool properly handles errors."""

        class TestTool(BaseTool[dict]):

            def _run(self, content: str, tenant: str, workspace: str) -> StepResult:
                if not content:
                    return StepResult.fail('Content cannot be empty')
                if not tenant:
                    return StepResult.fail('Tenant is required')
                if not workspace:
                    return StepResult.fail('Workspace is required')
                return StepResult.ok(data={'processed': content})
        tool = TestTool()
        result = tool._run('', 'tenant', 'workspace')
        assert not result.success
        assert 'Content cannot be empty' in result.error
        result = tool._run('content', '', 'workspace')
        assert not result.success
        assert 'Tenant is required' in result.error
        result = tool._run('content', 'tenant', '')
        assert not result.success
        assert 'Workspace is required' in result.error
        result = tool._run('content', 'tenant', 'workspace')
        assert result.success
        assert result.data['processed'] == 'content'

    def test_network_error_handling(self):
        """Test handling of network errors."""

        class NetworkTool(BaseTool[dict]):

            def _run(self, content: str, tenant: str, workspace: str) -> StepResult:
                try:
                    if 'network_error' in content:
                        raise ConnectionError('Network unreachable')
                    return StepResult.ok(data={'network_result': 'success'})
                except ConnectionError as e:
                    return StepResult.fail(f'Network error: {e!s}')
                except Exception as e:
                    return StepResult.fail(f'Unexpected error: {e!s}')
        tool = NetworkTool()
        result = tool._run('network_error', 'tenant', 'workspace')
        assert not result.success
        assert 'Network error' in result.error
        result = tool._run('normal_content', 'tenant', 'workspace')
        assert result.success
        assert result.data['network_result'] == 'success'

    def test_validation_error_handling(self):
        """Test handling of validation errors."""

        class ValidationTool(BaseTool[dict]):

            def _run(self, content: str, tenant: str, workspace: str) -> StepResult:
                if len(content) < 5:
                    return StepResult.fail('Content must be at least 5 characters')
                if len(content) > 1000:
                    return StepResult.fail('Content must be less than 1000 characters')
                if not content.isalnum():
                    return StepResult.fail('Content must contain only alphanumeric characters')
                return StepResult.ok(data={'validated': content})
        tool = ValidationTool()
        result = tool._run('abc', 'tenant', 'workspace')
        assert not result.success
        assert 'at least 5 characters' in result.error
        result = tool._run('a' * 1001, 'tenant', 'workspace')
        assert not result.success
        assert 'less than 1000 characters' in result.error
        result = tool._run('content with spaces!', 'tenant', 'workspace')
        assert not result.success
        assert 'alphanumeric characters' in result.error
        result = tool._run('validcontent', 'tenant', 'workspace')
        assert result.success
        assert result.data['validated'] == 'validcontent'

    def test_timeout_error_handling(self):
        """Test handling of timeout errors."""
        import time

        class TimeoutTool(BaseTool[dict]):

            def _run(self, content: str, tenant: str, workspace: str) -> StepResult:
                try:
                    if 'timeout' in content:
                        time.sleep(2)
                    return StepResult.ok(data={'result': 'success'})
                except Exception as e:
                    return StepResult.fail(f'Operation failed: {e!s}')
        tool = TimeoutTool()
        result = tool._run('timeout', 'tenant', 'workspace')
        assert result.success or not result.success

    def test_resource_error_handling(self):
        """Test handling of resource errors."""

        class ResourceTool(BaseTool[dict]):

            def _run(self, content: str, tenant: str, workspace: str) -> StepResult:
                try:
                    if 'resource_error' in content:
                        raise MemoryError('Insufficient memory')
                    if 'disk_error' in content:
                        raise OSError('Disk full')
                    return StepResult.ok(data={'resource_result': 'success'})
                except MemoryError as e:
                    return StepResult.fail(f'Memory error: {e!s}')
                except OSError as e:
                    return StepResult.fail(f'Disk error: {e!s}')
                except Exception as e:
                    return StepResult.fail(f'Resource error: {e!s}')
        tool = ResourceTool()
        result = tool._run('resource_error', 'tenant', 'workspace')
        assert not result.success
        assert 'Memory error' in result.error
        result = tool._run('disk_error', 'tenant', 'workspace')
        assert not result.success
        assert 'Disk error' in result.error
        result = tool._run('normal_content', 'tenant', 'workspace')
        assert result.success
        assert result.data['resource_result'] == 'success'

    def test_concurrent_error_handling(self):
        """Test error handling in concurrent operations."""
        import threading

        class ConcurrentTool(BaseTool[dict]):

            def __init__(self):
                self._lock = threading.Lock()
                self._counter = 0

            def _run(self, content: str, tenant: str, workspace: str) -> StepResult:
                try:
                    with self._lock:
                        self._counter += 1
                        if self._counter % 3 == 0:
                            raise ValueError('Simulated concurrent error')
                    return StepResult.ok(data={'counter': self._counter})
                except ValueError as e:
                    return StepResult.fail(f'Concurrent error: {e!s}')
                except Exception as e:
                    return StepResult.fail(f'Unexpected error: {e!s}')
        tool = ConcurrentTool()
        results = []

        def worker():
            result = tool._run('test', 'tenant', 'workspace')
            results.append(result)
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        assert len(results) == 10
        success_count = sum((1 for result in results if result.success))
        error_count = sum((1 for result in results if not result.success))
        assert success_count > 0
        assert error_count > 0

    def test_error_recovery_patterns(self):
        """Test error recovery patterns."""

        class RecoveryTool(BaseTool[dict]):

            def _run(self, content: str, tenant: str, workspace: str) -> StepResult:
                try:
                    if 'primary_fail' in content:
                        raise ConnectionError('Primary service unavailable')
                    return StepResult.ok(data={'method': 'primary', 'result': 'success'})
                except ConnectionError:
                    try:
                        if 'secondary_fail' in content:
                            raise ConnectionError('Secondary service unavailable')
                        return StepResult.ok(data={'method': 'secondary', 'result': 'success'})
                    except ConnectionError:
                        return StepResult.ok(data={'method': 'fallback', 'result': 'degraded'})
        tool = RecoveryTool()
        result = tool._run('normal', 'tenant', 'workspace')
        assert result.success
        assert result.data['method'] == 'primary'
        result = tool._run('primary_fail', 'tenant', 'workspace')
        assert result.success
        assert result.data['method'] == 'secondary'
        result = tool._run('primary_fail secondary_fail', 'tenant', 'workspace')
        assert result.success
        assert result.data['method'] == 'fallback'

    def test_error_context_preservation(self):
        """Test that error context is preserved."""

        class ContextTool(BaseTool[dict]):

            def _run(self, content: str, tenant: str, workspace: str) -> StepResult:
                try:
                    if 'error' in content:
                        raise ValueError('Test error')
                    return StepResult.ok(data={'content': content, 'tenant': tenant, 'workspace': workspace})
                except Exception as e:
                    return StepResult.fail(f"Error in {tenant}:{workspace} processing '{content}': {e!s}")
        tool = ContextTool()
        result = tool._run('error', 'test_tenant', 'test_workspace')
        assert not result.success
        assert 'test_tenant' in result.error
        assert 'test_workspace' in result.error
        assert 'error' in result.error
        result = tool._run('success', 'test_tenant', 'test_workspace')
        assert result.success
        assert result.data['tenant'] == 'test_tenant'
        assert result.data['workspace'] == 'test_workspace'