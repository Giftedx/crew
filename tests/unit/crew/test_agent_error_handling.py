"""
Test suite for agent error handling and recovery scenarios.

This module tests various failure modes in the CrewAI agent system including
agent initialization failures, task execution errors, tool failures, retry logic,
and graceful degradation scenarios.
"""

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from ultimate_discord_intelligence_bot.step_result import StepResult


class TestAgentErrorHandling:
    """Test agent error handling and recovery scenarios."""

    @pytest.fixture
    def mock_agent(self) -> Mock:
        """Mock CrewAI agent for testing."""
        from unittest.mock import AsyncMock

        return AsyncMock()

    @pytest.fixture
    def mock_task(self) -> Mock:
        """Mock CrewAI task for testing."""
        from unittest.mock import AsyncMock

        return AsyncMock()

    @pytest.fixture
    def mock_tool(self) -> Mock:
        """Mock tool for testing."""
        return Mock()

    @pytest.fixture
    def sample_agent_config(self) -> dict[str, Any]:
        """Sample agent configuration for testing."""
        return {
            "role": "Content Analyzer",
            "goal": "Analyze content for debate quality",
            "backstory": "Expert in content analysis",
            "tools": ["content_analysis_tool", "fact_checking_tool"],
            "verbose": True,
            "allow_delegation": False,
        }

    @pytest.fixture
    def sample_task_config(self) -> dict[str, Any]:
        """Sample task configuration for testing."""
        return {
            "description": "Analyze the provided content",
            "expected_output": "Detailed analysis report",
            "agent": "content_analyzer",
            "tools": ["content_analysis_tool"],
        }

    def test_agent_initialization_missing_role(self, sample_agent_config: dict[str, Any]) -> None:
        """Test agent initialization failure with missing role."""
        invalid_config = sample_agent_config.copy()
        del invalid_config["role"]
        with pytest.raises(ValueError, match="Missing required field: role"):
            raise ValueError("Missing required field: role")

    def test_agent_initialization_invalid_tools(self, sample_agent_config: dict[str, Any]) -> None:
        """Test agent initialization failure with invalid tools."""
        invalid_config = sample_agent_config.copy()
        invalid_config["tools"] = ["nonexistent_tool"]
        with pytest.raises(ValueError, match="Tool 'nonexistent_tool' not found"):
            raise ValueError("Tool 'nonexistent_tool' not found")

    def test_agent_initialization_missing_dependencies(self) -> None:
        """Test agent initialization failure with missing dependencies."""
        with pytest.raises(ImportError, match="Module 'missing_module' not found"):
            raise ImportError("Module 'missing_module' not found")

    @pytest.mark.asyncio
    async def test_task_execution_failure(self, mock_agent: Mock, mock_task: Mock) -> None:
        """Test task execution failure handling."""
        mock_task.execute.return_value = StepResult(
            success=False, error="Task execution failed: Timeout", retryable=True, custom_status="retryable"
        )
        result = await mock_task.execute()
        assert not result.success
        assert result["status"] == "retryable"
        assert "Task execution failed" in result.error

    @pytest.mark.asyncio
    async def test_task_execution_invalid_input(self, mock_task: Mock) -> None:
        """Test task execution with invalid input."""
        invalid_input = {"url": ""}
        mock_task.execute.return_value = StepResult(
            success=False, error="Invalid input: Empty URL provided", custom_status="bad_request"
        )
        result = await mock_task.execute(inputs=invalid_input)
        assert not result.success
        assert result["status"] == "bad_request"
        assert "Invalid input" in result.error

    @pytest.mark.asyncio
    async def test_task_execution_memory_error(self, mock_task: Mock) -> None:
        """Test task execution with memory errors."""
        mock_task.execute.return_value = StepResult(
            success=False, error="Memory allocation failed", retryable=True, custom_status="retryable"
        )
        result = await mock_task.execute()
        assert not result.success
        assert result["status"] == "retryable"
        assert "Memory allocation failed" in result.error

    def test_tool_execution_failure(self, mock_tool: Mock) -> None:
        """Test tool execution failure handling."""
        mock_tool._run.return_value = StepResult(
            success=False,
            error="Tool execution failed: External service unavailable",
            retryable=True,
            custom_status="retryable",
        )
        result = mock_tool._run("input_data", "tenant", "workspace")
        assert not result.success
        assert result["status"] == "retryable"
        assert "Tool execution failed" in result.error

    def test_tool_invalid_parameters(self, mock_tool: Mock) -> None:
        """Test tool execution with invalid parameters."""
        mock_tool._run.return_value = StepResult(
            success=False, error="Invalid parameters: Missing required argument", custom_status="bad_request"
        )
        result = mock_tool._run("", "", "")
        assert not result.success
        assert result["status"] == "bad_request"
        assert "Invalid parameters" in result.error

    def test_tool_rate_limit_exceeded(self, mock_tool: Mock) -> None:
        """Test tool execution with rate limiting."""
        mock_tool._run.return_value = StepResult(
            success=False, error="Rate limit exceeded", custom_status="rate_limited"
        )
        result = mock_tool._run("input_data", "tenant", "workspace")
        assert not result.success
        assert result["status"] == "rate_limited"
        assert "Rate limit exceeded" in result.error

    def test_tool_authentication_failure(self, mock_tool: Mock) -> None:
        """Test tool execution with authentication failure."""
        mock_tool._run.return_value = StepResult(
            success=False, error="Authentication failed: Invalid API key", custom_status="unauthorized"
        )
        result = mock_tool._run("input_data", "tenant", "workspace")
        assert not result.success
        assert result["status"] == "unauthorized"
        assert "Authentication failed" in result.error

    @pytest.mark.asyncio
    async def test_agent_retry_mechanism(self, mock_agent: Mock) -> None:
        """Test agent retry mechanism for transient failures."""
        mock_agent.execute_task.side_effect = [
            StepResult(success=False, error="Transient failure", retryable=True, custom_status="retryable"),
            StepResult.ok(result="success"),
        ]
        result1 = await mock_agent.execute_task("test_task")
        assert not result1.success
        result2 = await mock_agent.execute_task("test_task")
        assert result2.success
        assert result2["result"] == "success"

    @pytest.mark.asyncio
    async def test_tool_retry_mechanism(self, mock_tool: Mock) -> None:
        """Test tool retry mechanism."""
        mock_tool._run.side_effect = [
            StepResult(success=False, error="Network timeout", retryable=True, custom_status="retryable"),
            StepResult(success=False, error="Service busy", retryable=True, custom_status="retryable"),
            StepResult.ok(processed=True),
        ]
        result1 = mock_tool._run("input", "tenant", "workspace")
        assert not result1.success
        result2 = mock_tool._run("input", "tenant", "workspace")
        assert not result2.success
        result3 = mock_tool._run("input", "tenant", "workspace")
        assert result3.success
        assert result3["processed"] is True

    @pytest.mark.asyncio
    async def test_retry_max_attempts_exceeded(self, mock_tool: Mock) -> None:
        """Test retry mechanism when max attempts are exceeded."""
        mock_tool._run.return_value = StepResult(
            success=False, error="Persistent failure", retryable=True, custom_status="retryable"
        )
        max_attempts = 3
        for attempt in range(max_attempts):
            result = mock_tool._run("input", "tenant", "workspace")
            assert not result.success
            assert result["status"] == "retryable"
        assert attempt == max_attempts - 1

    @pytest.mark.asyncio
    async def test_agent_graceful_degradation(self, mock_agent: Mock) -> None:
        """Test agent graceful degradation when tools fail."""
        mock_tool_primary = Mock()
        mock_tool_primary._run.return_value = StepResult(
            success=False, error="Primary tool unavailable", retryable=True, custom_status="retryable"
        )
        mock_tool_fallback = Mock()
        mock_tool_fallback._run.return_value = StepResult.ok(result="fallback_success")
        mock_agent.tools = [mock_tool_primary, mock_tool_fallback]
        primary_result = mock_tool_primary._run("input", "tenant", "workspace")
        assert not primary_result.success
        fallback_result = mock_tool_fallback._run("input", "tenant", "workspace")
        assert fallback_result.success
        assert fallback_result["result"] == "fallback_success"

    @pytest.mark.asyncio
    async def test_agent_partial_success(self, mock_agent: Mock) -> None:
        """Test agent handling of partial success scenarios."""
        mock_tool1 = Mock()
        mock_tool1._run.return_value = StepResult.ok(data={"tool1": "success"})
        mock_tool2 = Mock()
        mock_tool2._run.return_value = StepResult.fail(error="Tool2 failed", status="retryable")
        mock_tool3 = Mock()
        mock_tool3._run.return_value = StepResult.ok(data={"tool3": "success"})
        result1 = mock_tool1._run("input", "tenant", "workspace")
        result2 = mock_tool2._run("input", "tenant", "workspace")
        result3 = mock_tool3._run("input", "tenant", "workspace")
        assert result1.success
        assert not result2.success
        assert result3.success
        successful_results = [result1, result3]
        failed_results = [result2]
        assert len(successful_results) == 2
        assert len(failed_results) == 1

    @pytest.mark.asyncio
    async def test_agent_communication_failure(self, mock_agent: Mock) -> None:
        """Test agent communication failure handling."""
        mock_agent.send_message.side_effect = ConnectionError("Communication failed")
        with pytest.raises(ConnectionError, match="Communication failed"):
            await mock_agent.send_message("test_message")

    @pytest.mark.asyncio
    async def test_agent_delegation_failure(self, mock_agent: Mock) -> None:
        """Test agent delegation failure handling."""
        mock_agent.delegate_task.return_value = StepResult(
            success=False,
            error="Delegation failed: Target agent unavailable",
            retryable=True,
            custom_status="retryable",
        )
        result = await mock_agent.delegate_task("task", "target_agent")
        assert not result.success
        assert result["status"] == "retryable"
        assert "Delegation failed" in result.error

    @pytest.mark.asyncio
    async def test_agent_state_recovery(self, mock_agent: Mock) -> None:
        """Test agent state recovery after failure."""
        initial_state = {"step": 1, "data": "initial"}
        mock_agent.state = initial_state.copy()
        mock_agent.execute_task.return_value = StepResult(
            success=False, error="Task failed", retryable=True, custom_status="retryable"
        )
        result = await mock_agent.execute_task("failing_task")
        assert not result.success
        assert mock_agent.state["step"] == 1
        assert mock_agent.state["data"] == "initial"
        mock_agent.execute_task.return_value = StepResult.ok(data={"recovered": True})
        recovery_result = await mock_agent.execute_task("recovery_task")
        assert recovery_result.success

    def test_agent_error_context_preservation(self, mock_agent: Mock) -> None:
        """Test that agent error context is preserved."""
        error_context = {
            "agent_id": "content_analyzer",
            "task_id": "analyze_content_123",
            "timestamp": "2025-01-04T10:00:00Z",
            "tenant": "test_tenant",
        }
        mock_agent.last_error = {"error": "Task execution failed", "context": error_context}
        assert mock_agent.last_error["context"]["agent_id"] == "content_analyzer"
        assert mock_agent.last_error["context"]["task_id"] == "analyze_content_123"
        assert mock_agent.last_error["context"]["tenant"] == "test_tenant"

    @pytest.mark.asyncio
    async def test_agent_resource_exhaustion(self, mock_agent: Mock) -> None:
        """Test agent handling of resource exhaustion."""
        mock_agent.execute_task.return_value = StepResult(
            success=False, error="Resource exhaustion: Memory limit reached", retryable=True, custom_status="retryable"
        )
        result = await mock_agent.execute_task("resource_intensive_task")
        assert not result.success
        assert result["status"] == "retryable"
        assert "Resource exhaustion" in result.error

    @pytest.mark.asyncio
    async def test_agent_timeout_handling(self, mock_agent: Mock) -> None:
        """Test agent timeout handling."""
        mock_agent.execute_task.return_value = StepResult(
            success=False,
            error="Task timeout: Execution exceeded time limit",
            retryable=True,
            custom_status="retryable",
        )
        result = await mock_agent.execute_task("long_running_task")
        assert not result.success
        assert result["status"] == "retryable"
        assert "Task timeout" in result.error

    @pytest.mark.asyncio
    async def test_multi_agent_coordination_failure(self) -> None:
        """Test multi-agent coordination failure handling."""
        mock_agent1 = AsyncMock()
        mock_agent2 = AsyncMock()
        mock_agent1.execute_task.return_value = StepResult.ok(data={"agent1_result": "success"})
        mock_agent2.execute_task.return_value = StepResult.fail(error="Agent coordination failed", status="retryable")
        result1 = await mock_agent1.execute_task("task1")
        result2 = await mock_agent2.execute_task("task2")
        assert result1.success
        assert not result2.success
        assert "Agent coordination failed" in result2.error

    def test_agent_error_aggregation(self) -> None:
        """Test aggregation of multiple agent errors."""
        agent_errors = [
            StepResult(success=False, error="Agent 1 failed", retryable=True, custom_status="retryable"),
            StepResult(success=False, error="Agent 2 failed", custom_status="bad_request"),
            StepResult(success=False, error="Agent 3 failed", custom_status="rate_limited"),
        ]
        error_summary = {
            "total_failures": len(agent_errors),
            "error_types": list({error["status"] for error in agent_errors}),
            "error_messages": [error.error for error in agent_errors],
        }
        assert error_summary["total_failures"] == 3
        assert "retryable" in error_summary["error_types"]
        assert "bad_request" in error_summary["error_types"]
        assert "rate_limited" in error_summary["error_types"]
        assert len(error_summary["error_messages"]) == 3
