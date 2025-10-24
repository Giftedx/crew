"""Tests for agent collaboration framework."""

import asyncio
from unittest.mock import patch

import pytest

from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags
from ultimate_discord_intelligence_bot.features.agent_collaboration import (
    AgentCollaboration,
    AgentTask,
    CollaborationPattern,
    CollaborationResult,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestAgentCollaboration:
    """Test suite for AgentCollaboration framework."""

    def setup_method(self):
        """Set up test fixtures."""
        self.feature_flags = FeatureFlags()
        self.feature_flags.ENABLE_AGENT_COLLABORATION = True
        self.collaboration = AgentCollaboration(self.feature_flags)

    def test_initialization(self):
        """Test collaboration framework initialization."""
        assert self.collaboration.feature_flags == self.feature_flags
        assert self.collaboration.is_enabled() is True
        assert len(self.collaboration.active_collaborations) == 0

    def test_disabled_collaboration(self):
        """Test behavior when collaboration is disabled."""
        self.feature_flags.ENABLE_AGENT_COLLABORATION = False
        collaboration = AgentCollaboration(self.feature_flags)

        assert collaboration.is_enabled() is False

    @pytest.mark.asyncio
    async def test_sequential_execution(self):
        """Test sequential task execution."""
        tasks = [
            AgentTask("agent1", "task1", {"input": "data1"}),
            AgentTask("agent2", "task2", {"input": "data2"}),
            AgentTask("agent3", "task3", {"input": "data3"}),
        ]

        result = await self.collaboration.execute_sequential(tasks, "test-collab")

        assert isinstance(result, CollaborationResult)
        assert result.pattern == CollaborationPattern.SEQUENTIAL
        assert result.success_count + result.failure_count == len(tasks)
        assert result.execution_time > 0
        assert "test-collab" in self.collaboration.active_collaborations

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test parallel task execution."""
        tasks = [
            AgentTask("agent1", "task1", {"input": "data1"}),
            AgentTask("agent2", "task2", {"input": "data2"}),
            AgentTask("agent3", "task3", {"input": "data3"}),
        ]

        result = await self.collaboration.execute_parallel(tasks, "test-parallel")

        assert isinstance(result, CollaborationResult)
        assert result.pattern == CollaborationPattern.PARALLEL
        assert result.success_count + result.failure_count == len(tasks)
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_hierarchical_execution(self):
        """Test hierarchical task execution."""
        coordinator = AgentTask("coordinator", "coordinate", {"plan": "strategy"})
        subordinates = [
            AgentTask("sub1", "subtask1", {"input": "data1"}),
            AgentTask("sub2", "subtask2", {"input": "data2"}),
        ]

        result = await self.collaboration.execute_hierarchical(coordinator, subordinates, "test-hierarchical")

        assert isinstance(result, CollaborationResult)
        assert result.pattern == CollaborationPattern.HIERARCHICAL
        assert result.success_count + result.failure_count == len(subordinates) + 1

    @pytest.mark.asyncio
    async def test_pipeline_execution(self):
        """Test pipeline task execution."""
        pipeline_stages = [
            [AgentTask("stage1_agent1", "stage1_task1", {"input": "data1"})],
            [AgentTask("stage2_agent1", "stage2_task1", {"input": "data2"})],
            [AgentTask("stage3_agent1", "stage3_task1", {"input": "data3"})],
        ]

        result = await self.collaboration.execute_pipeline(pipeline_stages, "test-pipeline")

        assert isinstance(result, CollaborationResult)
        assert result.pattern == CollaborationPattern.PIPELINE
        assert result.success_count + result.failure_count == sum(len(stage) for stage in pipeline_stages)

    @pytest.mark.asyncio
    async def test_disabled_execution(self):
        """Test execution when collaboration is disabled."""
        self.feature_flags.ENABLE_AGENT_COLLABORATION = False
        collaboration = AgentCollaboration(self.feature_flags)

        tasks = [AgentTask("agent1", "task1", {"input": "data1"})]
        result = await collaboration.execute_sequential(tasks)

        assert result.success_count == 0
        assert result.failure_count == len(tasks)
        assert "Agent collaboration disabled" in result.metadata["error"]

    def test_collaboration_status(self):
        """Test collaboration status tracking."""
        # Add a mock collaboration
        mock_result = CollaborationResult(
            pattern=CollaborationPattern.SEQUENTIAL, results={}, execution_time=1.0, success_count=1, failure_count=0
        )
        self.collaboration.active_collaborations["test-id"] = mock_result

        status = self.collaboration.get_collaboration_status("test-id")
        assert status == mock_result

        status = self.collaboration.get_collaboration_status("nonexistent")
        assert status is None

    def test_get_all_collaborations(self):
        """Test getting all active collaborations."""
        # Add mock collaborations
        mock_result1 = CollaborationResult(
            pattern=CollaborationPattern.SEQUENTIAL, results={}, execution_time=1.0, success_count=1, failure_count=0
        )
        mock_result2 = CollaborationResult(
            pattern=CollaborationPattern.PARALLEL, results={}, execution_time=2.0, success_count=2, failure_count=0
        )

        self.collaboration.active_collaborations["test1"] = mock_result1
        self.collaboration.active_collaborations["test2"] = mock_result2

        all_collaborations = self.collaboration.get_all_collaborations()
        assert len(all_collaborations) == 2
        assert "test1" in all_collaborations
        assert "test2" in all_collaborations

    def test_clear_collaboration(self):
        """Test clearing collaborations."""
        # Add a mock collaboration
        mock_result = CollaborationResult(
            pattern=CollaborationPattern.SEQUENTIAL, results={}, execution_time=1.0, success_count=1, failure_count=0
        )
        self.collaboration.active_collaborations["test-id"] = mock_result

        # Clear existing collaboration
        result = self.collaboration.clear_collaboration("test-id")
        assert result is True
        assert "test-id" not in self.collaboration.active_collaborations

        # Try to clear non-existent collaboration
        result = self.collaboration.clear_collaboration("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_task_timeout(self):
        """Test task execution with timeout."""
        task = AgentTask("agent1", "slow_task", {"input": "data"}, timeout=0.1)

        # Mock a slow execution
        with patch.object(self.collaboration, "_simulate_agent_execution") as mock_exec:
            mock_exec.side_effect = asyncio.sleep(1.0)  # Simulate slow execution

            result = await self.collaboration._execute_agent_task(task)
            assert not result.success
            assert "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_task_retry_logic(self):
        """Test task retry logic."""
        task = AgentTask("agent1", "failing_task", {"input": "data"}, max_retries=2)

        # Mock failing execution
        with patch.object(self.collaboration, "_simulate_agent_execution") as mock_exec:
            mock_exec.return_value = StepResult.fail("Simulated failure")

            result = await self.collaboration._execute_agent_task(task)
            assert not result.success

    def test_agent_task_creation(self):
        """Test AgentTask creation and properties."""
        task = AgentTask(
            agent_id="test_agent",
            task_name="test_task",
            inputs={"key": "value"},
            dependencies=["dep1", "dep2"],
            timeout=30.0,
            retry_count=1,
            max_retries=3,
        )

        assert task.agent_id == "test_agent"
        assert task.task_name == "test_task"
        assert task.inputs == {"key": "value"}
        assert task.dependencies == ["dep1", "dep2"]
        assert task.timeout == 30.0
        assert task.retry_count == 1
        assert task.max_retries == 3

    @pytest.mark.asyncio
    async def test_context_passing_sequential(self):
        """Test that context is passed between sequential tasks."""
        tasks = [AgentTask("agent1", "task1", {"input": "data1"}), AgentTask("agent2", "task2", {"input": "data2"})]

        # Mock successful execution with data
        with patch.object(self.collaboration, "_simulate_agent_execution") as mock_exec:
            mock_exec.return_value = StepResult.ok(data={"result": "processed", "context": "shared"})

            result = await self.collaboration.execute_sequential(tasks)

            # Verify both tasks were called
            assert mock_exec.call_count == 2

            # Check that context was passed to second task
            second_call = mock_exec.call_args_list[1]
            second_task = second_call[0][0]
            assert "context" in second_task.inputs

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in collaboration execution."""
        tasks = [AgentTask("agent1", "failing_task", {"input": "data"})]

        # Mock execution that raises an exception
        with patch.object(self.collaboration, "_simulate_agent_execution") as mock_exec:
            mock_exec.side_effect = Exception("Simulated error")

            result = await self.collaboration.execute_sequential(tasks)

            assert result.failure_count == 1
            assert result.success_count == 0
            assert "agent1" in result.results
            assert not result.results["agent1"].success
