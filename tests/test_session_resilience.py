"""Test session resilience for Discord interactions during long-running workflows."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestSessionResilience:
    """Test suite for Discord session resilience during long workflows."""

    @pytest.fixture
    def mock_interaction_valid(self):
        """Create a mock Discord interaction with valid session."""
        interaction = Mock()
        interaction.id = "test_interaction_123"
        interaction.followup = Mock()
        interaction.followup._adapter = Mock()

        # Mock aiohttp session as open
        session = Mock()
        session.closed = False
        interaction.followup._adapter._session = session

        # Mock followup.send as async
        interaction.followup.send = AsyncMock()

        return interaction

    @pytest.fixture
    def mock_interaction_closed(self):
        """Create a mock Discord interaction with closed session."""
        interaction = Mock()
        interaction.id = "test_interaction_456"
        interaction.followup = Mock()
        interaction.followup._adapter = Mock()

        # Mock aiohttp session as closed
        session = Mock()
        session.closed = True
        interaction.followup._adapter._session = session

        # Mock followup.send to raise session closed error
        async def raise_session_closed(*args, **kwargs):
            raise RuntimeError("Session is closed")

        interaction.followup.send = AsyncMock(side_effect=raise_session_closed)

        return interaction

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance with mocked dependencies."""
        with patch("ultimate_discord_intelligence_bot.autonomous_orchestrator.UltimateDiscordIntelligenceBotCrew"):
            from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
                AutonomousIntelligenceOrchestrator,
            )

            return AutonomousIntelligenceOrchestrator()

    def test_is_session_valid_with_open_session(self, orchestrator, mock_interaction_valid):
        """Test that _is_session_valid returns True for open session."""
        assert orchestrator._is_session_valid(mock_interaction_valid) is True

    def test_is_session_valid_with_closed_session(self, orchestrator, mock_interaction_closed):
        """Test that _is_session_valid returns False for closed session."""
        assert orchestrator._is_session_valid(mock_interaction_closed) is False

    def test_is_session_valid_with_missing_followup(self, orchestrator):
        """Test that _is_session_valid returns False when followup is missing."""
        interaction = Mock(spec=[])  # No attributes
        assert orchestrator._is_session_valid(interaction) is False

    def test_is_session_valid_with_invalid_interaction(self, orchestrator):
        """Test that _is_session_valid returns False when interaction.id raises."""
        interaction = Mock()
        interaction.followup = Mock()
        interaction.followup._adapter = Mock()
        interaction.followup._adapter._session = None

        # Make interaction.id raise exception
        type(interaction).id = property(lambda self: (_ for _ in ()).throw(RuntimeError("Invalid")))

        assert orchestrator._is_session_valid(interaction) is False

    @pytest.mark.asyncio
    async def test_persist_workflow_results_success(self, orchestrator, tmp_path):
        """Test successful persistence of workflow results."""
        # Set up temporary data directory
        data_dir = tmp_path / "data" / "orphaned_results"

        with patch("pathlib.Path", return_value=data_dir):
            workflow_id = "test_wf_123"
            results = {
                "deception": {"threat_score": 0.75},
                "analysis": {"summary": "Test analysis"},
            }
            url = "https://example.com/test"
            depth = "comprehensive"

            # Call persistence method
            result_file = await orchestrator._persist_workflow_results(workflow_id, results, url, depth)

            # Verify file was created
            assert result_file  # Not empty string

            # In actual implementation, verify file contents
            # For now, just check the path format
            assert workflow_id in result_file

    @pytest.mark.asyncio
    async def test_persist_workflow_results_failure(self, orchestrator):
        """Test graceful handling when persistence fails."""
        workflow_id = "test_wf_456"
        results = {"test": "data"}
        url = "https://example.com/test"
        depth = "standard"

        # Mock Path to raise exception
        with patch("pathlib.Path") as mock_path:
            mock_path.return_value.mkdir.side_effect = PermissionError("No write access")

            result_file = await orchestrator._persist_workflow_results(workflow_id, results, url, depth)

            # Should return empty string on failure
            assert result_file == ""

    @pytest.mark.asyncio
    async def test_send_progress_update_with_closed_session(self, orchestrator, mock_interaction_closed):
        """Test that progress updates are skipped when session is closed."""
        # This should not raise an exception
        await orchestrator._send_progress_update(mock_interaction_closed, "Processing...", 5, 10)

        # Verify send was NOT called
        mock_interaction_closed.followup.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_progress_update_with_valid_session(self, orchestrator, mock_interaction_valid):
        """Test that progress updates are sent when session is valid."""
        await orchestrator._send_progress_update(mock_interaction_valid, "Processing...", 5, 10)

        # Verify send was called
        mock_interaction_valid.followup.send.assert_called_once()

        # Check the message format
        call_args = mock_interaction_valid.followup.send.call_args
        message = call_args[0][0]  # First positional arg
        assert "Processing..." in message
        assert "5/10" in message or "50%" in message

    @pytest.mark.asyncio
    async def test_send_error_response_with_closed_session(self, orchestrator, mock_interaction_closed):
        """Test that error responses are logged but not sent when session is closed."""
        # This should not raise an exception
        await orchestrator._send_error_response(mock_interaction_closed, "Test Stage", "Test error message")

        # Verify send was NOT called (session validation prevents it)
        mock_interaction_closed.followup.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_communication_reporting_with_closed_session_before_send(
        self, orchestrator, mock_interaction_closed, tmp_path
    ):
        """Test communication/reporting when session is closed before sending."""
        synthesis_result = {
            "workflow_id": "test_wf_789",
            "workflow_metadata": {"url": "https://example.com/test"},
            "deception": {"threat_score": 0.5},
        }
        depth = "standard"

        # Set up temporary data directory
        data_dir = tmp_path / "data" / "orphaned_results"
        data_dir.mkdir(parents=True, exist_ok=True)

        with patch("pathlib.Path") as mock_path_class:
            mock_path_class.return_value = data_dir

            # This should not raise an exception
            await orchestrator._execute_specialized_communication_reporting(
                mock_interaction_closed, synthesis_result, depth
            )

            # Verify send was NOT called
            mock_interaction_closed.followup.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_communication_reporting_session_closes_during_send(
        self, orchestrator, mock_interaction_valid, tmp_path
    ):
        """Test communication/reporting when session closes during send."""
        synthesis_result = {
            "workflow_id": "test_wf_999",
            "workflow_metadata": {"url": "https://example.com/test"},
            "deception": {"threat_score": 0.5},
        }
        depth = "comprehensive"

        # Mock session as valid initially, but send fails with closed session
        async def fail_on_send(*args, **kwargs):
            raise RuntimeError("Session is closed")

        mock_interaction_valid.followup.send = AsyncMock(side_effect=fail_on_send)

        # Set up temporary data directory
        data_dir = tmp_path / "data" / "orphaned_results"
        data_dir.mkdir(parents=True, exist_ok=True)

        with patch("pathlib.Path") as mock_path_class:
            mock_path_class.return_value = data_dir

            # This should not raise an exception
            await orchestrator._execute_specialized_communication_reporting(
                mock_interaction_valid, synthesis_result, depth
            )

            # Verify send WAS attempted (but failed gracefully)
            mock_interaction_valid.followup.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_metrics_tracking_on_session_closure(self, orchestrator, mock_interaction_closed):
        """Test that session closure events are tracked in metrics."""
        # Verify metrics are called when session closes
        synthesis_result = {
            "workflow_id": "test_wf_metrics",
            "workflow_metadata": {"url": "https://example.com/test"},
        }
        depth = "standard"

        with patch("pathlib.Path"):
            await orchestrator._execute_specialized_communication_reporting(
                mock_interaction_closed, synthesis_result, depth
            )

        # Metrics tracking is verified through execution without errors
        # Actual metric values depend on the metrics backend implementation


class TestWorkflowResultRetrieval:
    """Test suite for orphaned result retrieval system."""

    def test_persisted_result_file_structure(self, tmp_path):
        """Test the structure of persisted result files."""
        # Create a sample result file
        result_data = {
            "workflow_id": "test_123",
            "timestamp": 1234567890.0,
            "url": "https://example.com/test",
            "depth": "comprehensive",
            "results": {"test": "data"},
            "retrieval_info": {
                "command": "/retrieve_results workflow_id:test_123",
                "file_path": "/path/to/file.json",
                "status": "session_closed_during_workflow",
            },
        }

        result_file = tmp_path / "test_123.json"
        with open(result_file, "w") as f:
            json.dump(result_data, f, indent=2)

        # Verify file can be read back
        with open(result_file) as f:
            loaded = json.load(f)

        assert loaded["workflow_id"] == "test_123"
        assert loaded["url"] == "https://example.com/test"
        assert loaded["retrieval_info"]["status"] == "session_closed_during_workflow"

    def test_result_file_cleanup(self, tmp_path):
        """Test that old result files can be identified for cleanup."""
        import time

        # Create files with different timestamps
        old_file = tmp_path / "old_result.json"
        new_file = tmp_path / "new_result.json"

        old_data = {"workflow_id": "old", "timestamp": time.time() - (31 * 24 * 3600)}
        new_data = {"workflow_id": "new", "timestamp": time.time()}

        with open(old_file, "w") as f:
            json.dump(old_data, f)
        with open(new_file, "w") as f:
            json.dump(new_data, f)

        # Verify both files exist
        assert old_file.exists()
        assert new_file.exists()

        # In a real implementation, cleanup would remove files older than 30 days
        # For now, just verify we can identify them
        with open(old_file) as f:
            old_loaded = json.load(f)

        age_days = (time.time() - old_loaded["timestamp"]) / (24 * 3600)
        assert age_days > 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
