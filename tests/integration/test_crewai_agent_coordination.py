"""Integration tests for CrewAI agent coordination workflows."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from ultimate_discord_intelligence_bot.enhanced_crew_integration import EnhancedCrewExecutor
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext


class TestCrewAIAgentCoordination:
    """Integration tests for CrewAI agent coordination."""

    @pytest.fixture
    def mock_crew(self):
        """Create a mock crew instance."""
        crew = MagicMock()
        crew.agents = [
            MagicMock(role="mission_orchestrator"),
            MagicMock(role="acquisition_specialist"),
            MagicMock(role="transcription_engineer"),
            MagicMock(role="analysis_cartographer"),
            MagicMock(role="verification_director"),
        ]
        crew.tasks = [
            MagicMock(description="Plan autonomy mission"),
            MagicMock(description="Capture source media"),
            MagicMock(description="Transcribe and index media"),
            MagicMock(description="Analyze content"),
            MagicMock(description="Verify information"),
        ]
        return crew

    @pytest.fixture
    def enhanced_executor(self, mock_crew):
        """Create an EnhancedCrewExecutor instance."""
        executor = EnhancedCrewExecutor()
        executor.crew_instance = mock_crew
        return executor

    @pytest.mark.asyncio
    async def test_agent_coordination_workflow(self, enhanced_executor):
        """Test the complete agent coordination workflow."""
        inputs = {"url": "https://youtube.com/watch?v=test123", "depth": "comprehensive"}

        # Mock the crew execution
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {
            "mission_plan": "Comprehensive analysis plan",
            "acquisition_result": "Media captured successfully",
            "transcription_result": "Transcript generated",
            "analysis_result": "Content analyzed",
            "verification_result": "Information verified",
        }

        with patch.object(
            enhanced_executor.crew_instance, "kickoff_with_performance_tracking", return_value=mock_result
        ):
            result = await enhanced_executor.execute_enhanced_workflow(
                inputs=inputs, tenant_id="test_tenant", execution_id="test_exec_123"
            )

        assert result["success"] is True
        assert "execution_summary" in result
        assert "quality_score" in result
        assert "execution_time" in result

    @pytest.mark.asyncio
    async def test_agent_coordination_with_failure(self, enhanced_executor):
        """Test agent coordination when an agent fails."""
        inputs = {"url": "https://youtube.com/watch?v=test123", "depth": "comprehensive"}

        # Mock crew execution to fail
        with patch.object(
            enhanced_executor.crew_instance,
            "kickoff_with_performance_tracking",
            side_effect=Exception("Agent coordination failed"),
        ):
            result = await enhanced_executor.execute_enhanced_workflow(
                inputs=inputs, tenant_id="test_tenant", execution_id="test_exec_123"
            )

        assert result["success"] is False
        assert "error" in result
        assert "execution_summary" in result

    @pytest.mark.asyncio
    async def test_hierarchical_task_execution(self, enhanced_executor):
        """Test hierarchical task execution with dependencies."""
        # Mock orchestration tasks with dependencies
        mock_tasks = [
            MagicMock(task_id="task1", dependencies=[]),
            MagicMock(task_id="task2", dependencies=["task1"]),
            MagicMock(task_id="task3", dependencies=["task1", "task2"]),
        ]

        inputs = {"url": "https://youtube.com/watch?v=test123"}

        with patch.object(enhanced_executor, "_execute_hierarchical_tasks") as mock_execute:
            mock_execute.return_value = MagicMock()

            await enhanced_executor._execute_hierarchical_tasks(mock_tasks, inputs)

            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_performance_tracking(self, enhanced_executor):
        """Test agent performance tracking and metrics."""
        inputs = {"url": "https://youtube.com/watch?v=test123", "depth": "comprehensive"}

        # Mock performance tracking
        with patch.object(enhanced_executor, "_record_comprehensive_performance") as mock_record:
            with patch.object(
                enhanced_executor.crew_instance, "kickoff_with_performance_tracking", return_value=MagicMock()
            ):
                await enhanced_executor.execute_enhanced_workflow(
                    inputs=inputs, tenant_id="test_tenant", execution_id="test_exec_123"
                )

            # Verify performance tracking was called
            mock_record.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_quality_assessment(self, enhanced_executor):
        """Test agent quality assessment during execution."""
        inputs = {"url": "https://youtube.com/watch?v=test123", "depth": "comprehensive"}

        # Mock quality assessment
        with patch.object(enhanced_executor, "_assess_comprehensive_execution_quality") as mock_assess:
            mock_assess.return_value = 0.85

            with patch.object(
                enhanced_executor.crew_instance, "kickoff_with_performance_tracking", return_value=MagicMock()
            ):
                result = await enhanced_executor.execute_enhanced_workflow(
                    inputs=inputs, tenant_id="test_tenant", execution_id="test_exec_123"
                )

            # Verify quality assessment was called
            mock_assess.assert_called_once()
            assert result["quality_score"] == 0.85

    @pytest.mark.asyncio
    async def test_agent_coordination_with_tenant_isolation(self, enhanced_executor):
        """Test agent coordination with tenant isolation."""
        inputs = {"url": "https://youtube.com/watch?v=test123", "depth": "comprehensive"}

        # Mock tenant context
        with patch("ultimate_discord_intelligence_bot.tenancy.current_tenant") as mock_tenant:
            mock_tenant.return_value = TenantContext(tenant="test_tenant", workspace="test_workspace")

            with patch.object(
                enhanced_executor.crew_instance, "kickoff_with_performance_tracking", return_value=MagicMock()
            ):
                result = await enhanced_executor.execute_enhanced_workflow(
                    inputs=inputs, tenant_id="test_tenant", execution_id="test_exec_123"
                )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_agent_coordination_with_websocket_updates(self, enhanced_executor):
        """Test agent coordination with WebSocket real-time updates."""
        inputs = {"url": "https://youtube.com/watch?v=test123", "depth": "comprehensive"}

        # Mock WebSocket updates
        with patch.object(enhanced_executor, "_send_websocket_update") as mock_websocket:
            with patch.object(
                enhanced_executor.crew_instance, "kickoff_with_performance_tracking", return_value=MagicMock()
            ):
                await enhanced_executor.execute_enhanced_workflow(
                    inputs=inputs, tenant_id="test_tenant", execution_id="test_exec_123"
                )

            # Verify WebSocket updates were sent
            assert mock_websocket.call_count > 0

    @pytest.mark.asyncio
    async def test_agent_coordination_with_real_time_monitoring(self, enhanced_executor):
        """Test agent coordination with real-time monitoring."""
        inputs = {"url": "https://youtube.com/watch?v=test123", "depth": "comprehensive"}

        # Mock real-time monitoring
        with patch.object(enhanced_executor, "_real_time_monitoring_loop") as mock_monitoring:
            with patch.object(
                enhanced_executor.crew_instance, "kickoff_with_performance_tracking", return_value=MagicMock()
            ):
                await enhanced_executor.execute_enhanced_workflow(
                    inputs=inputs, tenant_id="test_tenant", execution_id="test_exec_123", enable_real_time_alerts=True
                )

            # Verify monitoring was started
            mock_monitoring.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_coordination_with_hierarchical_orchestration(self, enhanced_executor):
        """Test agent coordination with hierarchical orchestration."""
        inputs = {"url": "https://youtube.com/watch?v=test123", "depth": "comprehensive"}

        # Mock hierarchical orchestration
        with patch.object(enhanced_executor, "_execute_with_hierarchical_orchestration") as mock_hierarchical:
            mock_hierarchical.return_value = MagicMock()

            await enhanced_executor.execute_enhanced_workflow(
                inputs=inputs, tenant_id="test_tenant", execution_id="test_exec_123"
            )

            # Verify hierarchical orchestration was called
            mock_hierarchical.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_coordination_concurrent_execution(self, enhanced_executor):
        """Test concurrent agent coordination execution."""
        inputs_list = [
            {"url": "https://youtube.com/watch?v=test1", "depth": "comprehensive"},
            {"url": "https://youtube.com/watch?v=test2", "depth": "comprehensive"},
            {"url": "https://youtube.com/watch?v=test3", "depth": "comprehensive"},
        ]

        # Mock crew execution
        with patch.object(
            enhanced_executor.crew_instance, "kickoff_with_performance_tracking", return_value=MagicMock()
        ):
            # Execute multiple workflows concurrently
            tasks = [
                enhanced_executor.execute_enhanced_workflow(
                    inputs=inputs, tenant_id="test_tenant", execution_id=f"test_exec_{i}"
                )
                for i, inputs in enumerate(inputs_list)
            ]

            results = await asyncio.gather(*tasks)

        # All should succeed
        for result in results:
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_agent_coordination_error_recovery(self, enhanced_executor):
        """Test agent coordination error recovery mechanisms."""
        inputs = {"url": "https://youtube.com/watch?v=test123", "depth": "comprehensive"}

        # Mock crew execution to fail first time, succeed second time
        call_count = 0

        async def mock_crew_execution(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Agent coordination failed")
            else:
                return MagicMock()

        with patch.object(
            enhanced_executor.crew_instance, "kickoff_with_performance_tracking", side_effect=mock_crew_execution
        ):
            result = await enhanced_executor.execute_enhanced_workflow(
                inputs=inputs, tenant_id="test_tenant", execution_id="test_exec_123"
            )

        # Should handle the failure gracefully
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_agent_coordination_with_different_depths(self, enhanced_executor):
        """Test agent coordination with different analysis depths."""
        url = "https://youtube.com/watch?v=test123"

        for depth in ["basic", "comprehensive", "experimental"]:
            inputs = {"url": url, "depth": depth}

            with patch.object(
                enhanced_executor.crew_instance, "kickoff_with_performance_tracking", return_value=MagicMock()
            ):
                result = await enhanced_executor.execute_enhanced_workflow(
                    inputs=inputs, tenant_id="test_tenant", execution_id=f"test_exec_{depth}"
                )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_agent_coordination_performance_metrics(self, enhanced_executor):
        """Test agent coordination performance metrics collection."""
        inputs = {"url": "https://youtube.com/watch?v=test123", "depth": "comprehensive"}

        # Mock performance metrics
        with patch.object(enhanced_executor, "_record_comprehensive_performance") as mock_record:
            with patch.object(
                enhanced_executor.crew_instance, "kickoff_with_performance_tracking", return_value=MagicMock()
            ):
                await enhanced_executor.execute_enhanced_workflow(
                    inputs=inputs, tenant_id="test_tenant", execution_id="test_exec_123"
                )

            # Verify performance metrics were recorded
            mock_record.assert_called_once()
            call_args = mock_record.call_args[0]
            assert "test_exec_123" in call_args  # execution_id
            assert call_args[2] is not None  # execution_quality
            assert call_args[3] > 0  # execution_time
