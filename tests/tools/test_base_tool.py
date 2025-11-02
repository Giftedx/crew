"""Tests for BaseTool."""

from platform.core.step_result import StepResult
from unittest.mock import patch

import pytest

from ultimate_discord_intelligence_bot.tenancy.context import TenantContext
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class TestBaseTool:
    """Test cases for BaseTool."""

    @pytest.fixture
    def base_tool(self):
        """Create BaseTool instance."""
        return BaseTool()

    @pytest.fixture
    def test_tenant_context(self):
        """Create test tenant context."""
        return TenantContext(tenant="test_tenant", workspace="test_workspace")

    def test_base_tool_initialization(self, base_tool):
        """Test BaseTool initialization."""
        assert base_tool is not None
        assert hasattr(base_tool, "_run")
        assert hasattr(base_tool, "args_schema")

    def test_base_tool_args_schema(self, base_tool):
        """Test BaseTool args schema."""
        schema = base_tool.args_schema
        assert schema is not None

    def test_base_tool_run_method(self, base_tool, test_tenant_context):
        """Test BaseTool _run method."""
        result = base_tool._run(tenant_context=test_tenant_context)
        assert isinstance(result, StepResult)
        assert result.success

    def test_base_tool_tenant_isolation(self, base_tool):
        """Test BaseTool tenant isolation."""
        tenant1 = TenantContext(tenant="tenant1", workspace="workspace1")
        tenant2 = TenantContext(tenant="tenant2", workspace="workspace2")
        result1 = base_tool._run(tenant_context=tenant1)
        result2 = base_tool._run(tenant_context=tenant2)
        assert result1.success
        assert result2.success
        assert result1.data["tenant"] == tenant1.tenant
        assert result2.data["tenant"] == tenant2.tenant

    def test_base_tool_error_handling(self, base_tool, test_tenant_context):
        """Test BaseTool error handling."""
        with patch.object(base_tool, "_run_internal", side_effect=Exception("Test error")):
            result = base_tool._run(tenant_context=test_tenant_context)
            assert isinstance(result, StepResult)
            assert not result.success
            assert "error" in result.data

    def test_base_tool_validation(self, base_tool, test_tenant_context):
        """Test BaseTool input validation."""
        result = base_tool._run(tenant_context=test_tenant_context)
        assert result.success
        result = base_tool._run(tenant_context=None)
        assert not result.success
        assert "error" in result.data

    def test_base_tool_performance(self, base_tool, test_tenant_context, performance_benchmark):
        """Test BaseTool performance."""
        performance_benchmark.start()
        result = base_tool._run(tenant_context=test_tenant_context)
        elapsed_time = performance_benchmark.stop()
        assert result.success
        assert elapsed_time < 1.0

    def test_base_tool_logging(self, base_tool, test_tenant_context):
        """Test BaseTool logging."""
        with patch.object(base_tool, "logger") as mock_logger:
            result = base_tool._run(tenant_context=test_tenant_context)
            assert result.success
            mock_logger.info.assert_called()

    def test_base_tool_metadata(self, base_tool, test_tenant_context):
        """Test BaseTool metadata handling."""
        result = base_tool._run(tenant_context=test_tenant_context)
        assert result.success
        assert "metadata" in result.data
        assert "processing_time" in result.data["metadata"]
        assert "tool_name" in result.data["metadata"]

    def test_base_tool_caching(self, base_tool, test_tenant_context):
        """Test BaseTool caching."""
        result1 = base_tool._run(tenant_context=test_tenant_context)
        assert result1.success
        result2 = base_tool._run(tenant_context=test_tenant_context)
        assert result2.success
        assert result1.data == result2.data

    def test_base_tool_retry_mechanism(self, base_tool, test_tenant_context):
        """Test BaseTool retry mechanism."""
        with patch.object(base_tool, "_run_internal", side_effect=[Exception("Test error"), "success"]):
            result = base_tool._run(tenant_context=test_tenant_context)
            assert result.success
            assert result.data == "success"

    def test_base_tool_timeout(self, base_tool, test_tenant_context):
        """Test BaseTool timeout handling."""
        with patch.object(base_tool, "_run_internal", side_effect=TimeoutError("Operation timed out")):
            result = base_tool._run(tenant_context=test_tenant_context)
            assert not result.success
            assert "timeout" in result.data["error"].lower()

    def test_base_tool_rate_limiting(self, base_tool, test_tenant_context):
        """Test BaseTool rate limiting."""
        with patch.object(base_tool, "_run_internal", side_effect=Exception("Rate limit exceeded")):
            result = base_tool._run(tenant_context=test_tenant_context)
            assert not result.success
            assert "rate limit" in result.data["error"].lower()

    def test_base_tool_authentication(self, base_tool, test_tenant_context):
        """Test BaseTool authentication handling."""
        with patch.object(base_tool, "_run_internal", side_effect=Exception("Authentication failed")):
            result = base_tool._run(tenant_context=test_tenant_context)
            assert not result.success
            assert "authentication" in result.data["error"].lower()

    def test_base_tool_authorization(self, base_tool, test_tenant_context):
        """Test BaseTool authorization handling."""
        with patch.object(base_tool, "_run_internal", side_effect=Exception("Authorization failed")):
            result = base_tool._run(tenant_context=test_tenant_context)
            assert not result.success
            assert "authorization" in result.data["error"].lower()

    def test_base_tool_network_error(self, base_tool, test_tenant_context):
        """Test BaseTool network error handling."""
        with patch.object(base_tool, "_run_internal", side_effect=Exception("Network error")):
            result = base_tool._run(tenant_context=test_tenant_context)
            assert not result.success
            assert "network" in result.data["error"].lower()

    def test_base_tool_validation_error(self, base_tool, test_tenant_context):
        """Test BaseTool validation error handling."""
        with patch.object(base_tool, "_run_internal", side_effect=ValueError("Invalid input")):
            result = base_tool._run(tenant_context=test_tenant_context)
            assert not result.success
            assert "validation" in result.data["error"].lower()

    def test_base_tool_serialization_error(self, base_tool, test_tenant_context):
        """Test BaseTool serialization error handling."""
        with patch.object(base_tool, "_run_internal", side_effect=Exception("Serialization failed")):
            result = base_tool._run(tenant_context=test_tenant_context)
            assert not result.success
            assert "serialization" in result.data["error"].lower()

    def test_base_tool_deserialization_error(self, base_tool, test_tenant_context):
        """Test BaseTool deserialization error handling."""
        with patch.object(base_tool, "_run_internal", side_effect=Exception("Deserialization failed")):
            result = base_tool._run(tenant_context=test_tenant_context)
            assert not result.success
            assert "deserialization" in result.data["error"].lower()

    def test_base_tool_compression_error(self, base_tool, test_tenant_context):
        """Test BaseTool compression error handling."""
        with patch.object(base_tool, "_run_internal", side_effect=Exception("Compression failed")):
            result = base_tool._run(tenant_context=test_tenant_context)
            assert not result.success
            assert "compression" in result.data["error"].lower()

    def test_base_tool_decompression_error(self, base_tool, test_tenant_context):
        """Test BaseTool decompression error handling."""
        with patch.object(base_tool, "_run_internal", side_effect=Exception("Decompression failed")):
            result = base_tool._run(tenant_context=test_tenant_context)
            assert not result.success
            assert "decompression" in result.data["error"].lower()

    def test_base_tool_encryption_error(self, base_tool, test_tenant_context):
        """Test BaseTool encryption error handling."""
        with patch.object(base_tool, "_run_internal", side_effect=Exception("Encryption failed")):
            result = base_tool._run(tenant_context=test_tenant_context)
            assert not result.success
            assert "encryption" in result.data["error"].lower()

    def test_base_tool_decryption_error(self, base_tool, test_tenant_context):
        """Test BaseTool decryption error handling."""
        with patch.object(base_tool, "_run_internal", side_effect=Exception("Decryption failed")):
            result = base_tool._run(tenant_context=test_tenant_context)
            assert not result.success
            assert "decryption" in result.data["error"].lower()
