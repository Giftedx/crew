"""Tests for PromptEngine."""

from platform.core.step_result import StepResult
from platform.prompts.engine import PromptEngine
from unittest.mock import patch

import pytest

from ultimate_discord_intelligence_bot.tenancy.context import TenantContext


class TestPromptEngine:
    """Test cases for PromptEngine."""

    @pytest.fixture
    def prompt_engine(self, mock_openai_client):
        """Create PromptEngine instance."""
        return PromptEngine(openai_client=mock_openai_client)

    @pytest.fixture
    def test_tenant_context(self):
        """Create test tenant context."""
        return TenantContext(tenant="test_tenant", workspace="test_workspace")

    def test_prompt_engine_initialization(self, prompt_engine):
        """Test prompt engine initialization."""
        assert prompt_engine is not None
        assert hasattr(prompt_engine, "generate_prompt")
        assert hasattr(prompt_engine, "process_response")

    def test_generate_prompt(self, prompt_engine, test_tenant_context):
        """Test prompt generation."""
        template = "Analyze this content: {content}"
        variables = {"content": "Test content"}
        result = prompt_engine.generate_prompt(
            template=template, variables=variables, tenant_context=test_tenant_context
        )
        assert isinstance(result, StepResult)
        assert result.success
        assert "prompt" in result.data

    def test_process_response(self, prompt_engine, test_tenant_context):
        """Test response processing."""
        response = "This is a test response"
        result = prompt_engine.process_response(response=response, tenant_context=test_tenant_context)
        assert isinstance(result, StepResult)
        assert result.success
        assert "processed_response" in result.data

    def test_tenant_isolation(self, prompt_engine):
        """Test tenant isolation."""
        tenant1 = TenantContext(tenant="tenant1", workspace="workspace1")
        tenant2 = TenantContext(tenant="tenant2", workspace="workspace2")
        template = "Analyze this content: {content}"
        variables = {"content": "Test content"}
        result1 = prompt_engine.generate_prompt(template=template, variables=variables, tenant_context=tenant1)
        result2 = prompt_engine.generate_prompt(template=template, variables=variables, tenant_context=tenant2)
        assert result1.success
        assert result2.success
        assert result1.data["prompt"] != result2.data["prompt"]

    def test_error_handling(self, prompt_engine, test_tenant_context):
        """Test error handling."""
        with patch.object(prompt_engine, "_generate_prompt_internal", side_effect=Exception("Test error")):
            result = prompt_engine.generate_prompt(
                template="Test template", variables={}, tenant_context=test_tenant_context
            )
            assert isinstance(result, StepResult)
            assert not result.success
            assert "error" in result.data

    def test_performance(self, prompt_engine, test_tenant_context, performance_benchmark):
        """Test performance."""
        template = "Analyze this content: {content}"
        variables = {"content": "Test content"}
        performance_benchmark.start()
        result = prompt_engine.generate_prompt(
            template=template, variables=variables, tenant_context=test_tenant_context
        )
        elapsed_time = performance_benchmark.stop()
        assert result.success
        assert elapsed_time < 1.0
