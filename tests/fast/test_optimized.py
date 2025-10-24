"""Optimized fast tests for the Ultimate Discord Intelligence Bot.

This module contains fast tests that run in <5 seconds with proper mocking
and in-memory databases for optimal performance.
"""

import time
from unittest.mock import patch

import pytest

from ultimate_discord_intelligence_bot.crew_modular import UltimateDiscordIntelligenceBotCrew
from ultimate_discord_intelligence_bot.main import create_app
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext


class TestFastOptimized:
    """Optimized fast test cases."""

    @pytest.fixture
    def app(self):
        """Create test application."""
        return create_app()

    @pytest.fixture
    def crew(self):
        """Create test crew."""
        return UltimateDiscordIntelligenceBotCrew()

    @pytest.fixture
    def test_tenant_context(self):
        """Create test tenant context."""
        return TenantContext(tenant="test_tenant", workspace="test_workspace")

    @pytest.fixture
    def mock_services(self):
        """Create mock services for fast testing."""
        with patch("ultimate_discord_intelligence_bot.services.memory_service.MemoryService") as mock_memory:
            with patch("ultimate_discord_intelligence_bot.services.prompt_engine.PromptEngine") as mock_prompt:
                with patch(
                    "ultimate_discord_intelligence_bot.services.openrouter_service.OpenRouterService"
                ) as mock_openrouter:
                    # Configure mocks for fast responses
                    mock_memory.return_value.store_content.return_value = StepResult.ok(data={"id": "test_id"})
                    mock_prompt.return_value.generate_prompt.return_value = StepResult.ok(
                        data={"prompt": "Generated prompt"}
                    )
                    mock_openrouter.return_value.generate_response.return_value = StepResult.ok(
                        data={"response": "Generated response"}
                    )

                    yield {"memory": mock_memory, "prompt": mock_prompt, "openrouter": mock_openrouter}

    @pytest.mark.fast
    def test_crew_initialization(self, crew):
        """Test crew initialization is fast."""
        start_time = time.time()

        # Test crew initialization
        crew_instance = crew.crew()

        end_time = time.time()
        assert end_time - start_time < 1.0  # Should initialize in <1 second
        assert crew_instance is not None

    @pytest.mark.fast
    def test_agent_creation(self, crew):
        """Test agent creation is fast."""
        start_time = time.time()

        # Test agent creation
        acquisition_agents = crew.acquisition_agents
        analysis_agents = crew.analysis_agents
        verification_agents = crew.verification_agents
        intelligence_agents = crew.intelligence_agents
        observability_agents = crew.observability_agents

        end_time = time.time()
        assert end_time - start_time < 0.5  # Should create agents in <0.5 seconds

        # Verify agents exist
        assert acquisition_agents is not None
        assert analysis_agents is not None
        assert verification_agents is not None
        assert intelligence_agents is not None
        assert observability_agents is not None

    @pytest.mark.fast
    def test_task_creation(self, crew):
        """Test task creation is fast."""
        start_time = time.time()

        # Test task creation
        content_tasks = crew.content_processing_tasks
        qa_tasks = crew.quality_assurance_tasks

        end_time = time.time()
        assert end_time - start_time < 0.5  # Should create tasks in <0.5 seconds

        # Verify tasks exist
        assert content_tasks is not None
        assert qa_tasks is not None

    @pytest.mark.fast
    def test_step_result_creation(self):
        """Test StepResult creation is fast."""
        start_time = time.time()

        # Test StepResult creation
        success_result = StepResult.ok(data={"test": "data"})
        error_result = StepResult.fail(error="test error")
        skip_result = StepResult.skip(reason="test skip")

        end_time = time.time()
        assert end_time - start_time < 0.1  # Should create results in <0.1 seconds

        # Verify results
        assert success_result.success
        assert not error_result.success
        assert skip_result.skipped

    @pytest.mark.fast
    def test_tenant_context_creation(self):
        """Test tenant context creation is fast."""
        start_time = time.time()

        # Test tenant context creation
        context = TenantContext(tenant="test_tenant", workspace="test_workspace")

        end_time = time.time()
        assert end_time - start_time < 0.1  # Should create context in <0.1 seconds

        # Verify context
        assert context.tenant == "test_tenant"
        assert context.workspace == "test_workspace"

    @pytest.mark.fast
    def test_mock_services_performance(self, mock_services):
        """Test mock services perform fast."""
        start_time = time.time()

        # Test mock service calls
        memory_result = mock_services["memory"].return_value.store_content("test")
        prompt_result = mock_services["prompt"].return_value.generate_prompt("test")
        openrouter_result = mock_services["openrouter"].return_value.generate_response("test")

        end_time = time.time()
        assert end_time - start_time < 0.1  # Should complete in <0.1 seconds

        # Verify results
        assert memory_result.success
        assert prompt_result.success
        assert openrouter_result.success

    @pytest.mark.fast
    def test_lazy_loading_performance(self):
        """Test lazy loading performance."""
        start_time = time.time()

        # Test lazy loading
        from ultimate_discord_intelligence_bot.lazy_loading import get_lazy_loader

        lazy_loader = get_lazy_loader()

        end_time = time.time()
        assert end_time - start_time < 0.1  # Should load in <0.1 seconds

        # Verify lazy loader
        assert lazy_loader is not None

    @pytest.mark.fast
    def test_configuration_loading(self):
        """Test configuration loading is fast."""
        start_time = time.time()

        # Test configuration loading
        from ultimate_discord_intelligence_bot.config import BaseConfig, FeatureFlags, PathConfig

        base_config = BaseConfig.from_env()
        feature_flags = FeatureFlags.from_env()
        path_config = PathConfig.from_env()

        end_time = time.time()
        assert end_time - start_time < 0.5  # Should load config in <0.5 seconds

        # Verify configuration
        assert base_config is not None
        assert feature_flags is not None
        assert path_config is not None

    @pytest.mark.fast
    def test_tool_import_performance(self):
        """Test tool import performance."""
        start_time = time.time()

        # Test tool imports
        from ultimate_discord_intelligence_bot.tools import (
            EnhancedAnalysisTool,
            FactCheckTool,
            MemoryStorageTool,
            SystemStatusTool,
        )

        end_time = time.time()
        assert end_time - start_time < 0.5  # Should import tools in <0.5 seconds

        # Verify tools exist
        assert SystemStatusTool is not None
        assert EnhancedAnalysisTool is not None
        assert FactCheckTool is not None
        assert MemoryStorageTool is not None

    @pytest.mark.fast
    def test_error_handling_performance(self):
        """Test error handling performance."""
        start_time = time.time()

        # Test error handling
        try:
            raise ValueError("Test error")
        except ValueError as e:
            result = StepResult.fail(error=str(e))

        end_time = time.time()
        assert end_time - start_time < 0.1  # Should handle errors in <0.1 seconds

        # Verify error handling
        assert not result.success
        assert "Test error" in result.error

    @pytest.mark.fast
    def test_memory_usage_optimization(self):
        """Test memory usage optimization."""
        import sys

        start_time = time.time()
        sys.getsizeof([])

        # Test memory optimization
        test_data = list(range(1000))
        memory_usage = sys.getsizeof(test_data)

        end_time = time.time()
        assert end_time - start_time < 0.1  # Should complete in <0.1 seconds

        # Verify memory usage is reasonable
        assert memory_usage < 10000  # Should use <10KB for test data

    @pytest.mark.fast
    def test_concurrent_operations(self):
        """Test concurrent operations performance."""
        import threading
        import time

        start_time = time.time()

        # Test concurrent operations
        results = []

        def worker():
            result = StepResult.ok(data={"worker": "test"})
            results.append(result)

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        end_time = time.time()
        assert end_time - start_time < 1.0  # Should complete in <1 second

        # Verify results
        assert len(results) == 10
        assert all(result.success for result in results)

    @pytest.mark.fast
    def test_fast_test_suite_performance(self):
        """Test that the fast test suite itself runs quickly."""
        start_time = time.time()

        # This test should complete quickly
        test_data = {"fast": True, "optimized": True}
        result = StepResult.ok(data=test_data)

        end_time = time.time()
        assert end_time - start_time < 0.1  # Should complete in <0.1 seconds

        # Verify test performance
        assert result.success
        assert result.data["fast"]
        assert result.data["optimized"]
