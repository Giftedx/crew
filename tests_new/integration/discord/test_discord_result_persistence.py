"""Unit tests for discord result persistence module."""

import tempfile
from unittest.mock import Mock, patch

import pytest

from src.ultimate_discord_intelligence_bot.orchestrator import (
    discord_result_persistence,
)


class TestDiscordResultPersistence:
    """Test suite for discord result persistence."""

    def setup_method(self):
        """Set up test fixtures."""
        self.workflow_id = "test_workflow_123"
        self.results = {"analysis": "test_results", "deception_score": 0.5}
        self.url = "https://example.com/video"
        self.depth = "experimental"

    @pytest.mark.asyncio
    async def test_persist_workflow_results_success(self):
        """Test successful workflow result persistence."""
        # Arrange
        with (
            tempfile.TemporaryDirectory(),
            patch("src.ultimate_discord_intelligence_bot.orchestrator.discord_result_persistence.Path") as mock_path,
        ):
            # Mock the results directory
            mock_results_dir = Mock()
            mock_results_dir.mkdir = Mock()
            mock_path.return_value = mock_results_dir

            # Mock the result file
            mock_result_file = Mock()
            mock_result_file.__truediv__ = Mock(return_value=mock_result_file)
            mock_result_file.__str__ = Mock(return_value="data/orphaned_results/test_workflow_123.json")
            mock_results_dir.__truediv__ = Mock(return_value=mock_result_file)

            with (
                patch("builtins.open", mock_open()) as mock_file,
                patch(
                    "src.ultimate_discord_intelligence_bot.orchestrator.discord_result_persistence._get_metrics"
                ) as mock_metrics,
            ):
                # Act
                result_path = await discord_result_persistence.persist_workflow_results(
                    self.workflow_id, self.results, self.url, self.depth
                )

                # Assert
                assert result_path == "data/orphaned_results/test_workflow_123.json"
                mock_results_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
                mock_file.assert_called_once()
                mock_metrics.return_value.counter.assert_called_once()

    @pytest.mark.asyncio
    async def test_persist_workflow_results_file_write_error(self):
        """Test workflow result persistence with file write error."""
        # Arrange
        with patch("src.ultimate_discord_intelligence_bot.orchestrator.discord_result_persistence.Path") as mock_path:
            mock_results_dir = Mock()
            mock_results_dir.mkdir = Mock()
            mock_path.return_value = mock_results_dir

            mock_result_file = Mock()
            mock_result_file.__truediv__ = Mock(return_value=mock_result_file)
            mock_results_dir.__truediv__ = Mock(return_value=mock_result_file)

            with patch("builtins.open", side_effect=OSError("Write failed")):
                # Act
                result_path = await discord_result_persistence.persist_workflow_results(
                    self.workflow_id, self.results, self.url, self.depth
                )

                # Assert
                assert result_path == ""

    @pytest.mark.asyncio
    async def test_persist_workflow_results_json_serialization_error(self):
        """Test workflow result persistence with JSON serialization error."""
        # Arrange
        # Create results with non-serializable data
        non_serializable_results = {"analysis": "test", "callback": lambda x: x}

        with patch("src.ultimate_discord_intelligence_bot.orchestrator.discord_result_persistence.Path") as mock_path:
            mock_results_dir = Mock()
            mock_results_dir.mkdir = Mock()
            mock_path.return_value = mock_results_dir

            mock_result_file = Mock()
            mock_result_file.__truediv__ = Mock(return_value=mock_result_file)
            mock_results_dir.__truediv__ = Mock(return_value=mock_result_file)

            with (
                patch("builtins.open", mock_open()),
                patch("json.dump", side_effect=TypeError("Object not JSON serializable")),
            ):
                # Act
                result_path = await discord_result_persistence.persist_workflow_results(
                    self.workflow_id,
                    non_serializable_results,
                    self.url,
                    self.depth,
                )

                # Assert
                assert result_path == ""

    @pytest.mark.asyncio
    async def test_persist_workflow_results_directory_creation_error(self):
        """Test workflow result persistence with directory creation error."""
        # Arrange
        with patch("src.ultimate_discord_intelligence_bot.orchestrator.discord_result_persistence.Path") as mock_path:
            mock_results_dir = Mock()
            mock_results_dir.mkdir = Mock(side_effect=OSError("Permission denied"))
            mock_path.return_value = mock_results_dir

            # Act
            result_path = await discord_result_persistence.persist_workflow_results(
                self.workflow_id, self.results, self.url, self.depth
            )

            # Assert
            assert result_path == ""

    @pytest.mark.asyncio
    async def test_persist_workflow_results_metrics_import_error(self):
        """Test workflow result persistence with metrics import error."""
        # Arrange
        with patch("src.ultimate_discord_intelligence_bot.orchestrator.discord_result_persistence.Path") as mock_path:
            mock_results_dir = Mock()
            mock_results_dir.mkdir = Mock()
            mock_path.return_value = mock_results_dir

            mock_result_file = Mock()
            mock_result_file.__truediv__ = Mock(return_value=mock_result_file)
            mock_results_dir.__truediv__ = Mock(return_value=mock_result_file)

            with (
                patch("builtins.open", mock_open()),
                patch(
                    "src.ultimate_discord_intelligence_bot.orchestrator.discord_result_persistence._get_metrics",
                    side_effect=ImportError("Metrics not available"),
                ),
            ):
                # Act
                result_path = await discord_result_persistence.persist_workflow_results(
                    self.workflow_id, self.results, self.url, self.depth
                )

                # Assert
                assert result_path == "data/orphaned_results/test_workflow_123.json"

    @pytest.mark.asyncio
    async def test_persist_workflow_results_with_custom_logger(self):
        """Test workflow result persistence with custom logger."""
        # Arrange
        custom_logger = Mock()

        with patch("src.ultimate_discord_intelligence_bot.orchestrator.discord_result_persistence.Path") as mock_path:
            mock_results_dir = Mock()
            mock_results_dir.mkdir = Mock()
            mock_path.return_value = mock_results_dir

            mock_result_file = Mock()
            mock_result_file.__truediv__ = Mock(return_value=mock_result_file)
            mock_results_dir.__truediv__ = Mock(return_value=mock_result_file)

            with (
                patch("builtins.open", mock_open()),
                patch("src.ultimate_discord_intelligence_bot.orchestrator.discord_result_persistence._get_metrics"),
            ):
                # Act
                result_path = await discord_result_persistence.persist_workflow_results(
                    self.workflow_id,
                    self.results,
                    self.url,
                    self.depth,
                    log=custom_logger,
                )

                # Assert
                assert result_path == "data/orphaned_results/test_workflow_123.json"

    @pytest.mark.asyncio
    async def test_persist_workflow_results_data_structure(self):
        """Test that persisted data has correct structure."""
        # Arrange
        with patch("src.ultimate_discord_intelligence_bot.orchestrator.discord_result_persistence.Path") as mock_path:
            mock_results_dir = Mock()
            mock_results_dir.mkdir = Mock()
            mock_path.return_value = mock_results_dir

            mock_result_file = Mock()
            mock_result_file.__truediv__ = Mock(return_value=mock_result_file)
            mock_results_dir.__truediv__ = Mock(return_value=mock_result_file)

            captured_data = {}

            def capture_json_data(file, data, **kwargs):
                captured_data["json_data"] = data

            with patch("builtins.open", mock_open()), patch("json.dump", side_effect=capture_json_data):
                with patch(
                    "src.ultimate_discord_intelligence_bot.orchestrator.discord_result_persistence._get_metrics"
                ):
                    # Act
                    await discord_result_persistence.persist_workflow_results(
                        self.workflow_id, self.results, self.url, self.depth
                    )

                    # Assert
                    data = captured_data["json_data"]
                    assert data["workflow_id"] == self.workflow_id
                    assert data["url"] == self.url
                    assert data["depth"] == self.depth
                    assert data["results"] == self.results
                    assert "timestamp" in data
                    assert "retrieval_info" in data
                    assert data["retrieval_info"]["command"] == f"/retrieve_results workflow_id:{self.workflow_id}"


def mock_open():
    """Create a mock open function."""
    from unittest.mock import mock_open as unittest_mock_open

    return unittest_mock_open()
