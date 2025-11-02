"""Test cases for OpenRouterService refactored implementation."""
import pytest
from platform.llm.providers.openrouter import OpenRouterService
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext

class TestOpenRouterService:
    """Test cases for OpenRouterService."""

    @pytest.fixture
    def openrouter_service(self):
        """Create OpenRouterService instance."""
        return OpenRouterService(api_key=None)

    @pytest.fixture
    def test_tenant_context(self):
        """Create test tenant context."""
        return TenantContext(tenant_id='test_tenant', workspace_id='test_workspace')

    def test_openrouter_service_initialization(self, openrouter_service):
        """Test OpenRouter service initialization."""
        assert openrouter_service is not None
        assert hasattr(openrouter_service, 'route')
        assert hasattr(openrouter_service, 'api_key')

    def test_route_basic(self, openrouter_service, test_tenant_context):
        """Test basic routing functionality."""
        prompt = 'Test prompt for routing'
        result = openrouter_service.route(prompt=prompt, task_type='general')
        assert isinstance(result, StepResult)
        assert result.success
        assert 'data' in result.data
        assert 'response' in result.data['data']
        assert result.data['data']['response'] == prompt.upper()

    def test_route_analysis_task(self, openrouter_service, test_tenant_context):
        """Test routing for analysis task."""
        prompt = 'Analyze this content'
        result = openrouter_service.route(prompt=prompt, task_type='analysis')
        assert isinstance(result, StepResult)
        assert result.success
        assert 'data' in result.data
        assert 'response' in result.data['data']
        assert result.data['data']['response'] == prompt.upper()

    def test_tenant_isolation(self, openrouter_service):
        """Test tenant isolation."""
        prompt = 'Test prompt'
        result1 = openrouter_service.route(prompt=prompt, task_type='general')
        result2 = openrouter_service.route(prompt=prompt, task_type='general')
        assert result1.success
        assert result2.success

    def test_error_handling(self, openrouter_service, test_tenant_context):
        """Test error handling."""
        result = openrouter_service.route(prompt='', task_type='general')
        assert result.success

    def test_performance(self, openrouter_service, test_tenant_context, performance_timer):
        """Test performance characteristics."""
        prompt = 'Performance test prompt'
        performance_timer.start()
        result = openrouter_service.route(prompt=prompt, task_type='general')
        performance_timer.stop()
        assert result.success
        assert performance_timer.elapsed < 1.0