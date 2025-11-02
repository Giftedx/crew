"""Tests for CheckpointManagementTool."""

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools.checkpoint_management_tool import CheckpointManagementTool


class TestCheckpointManagementTool:
    """Test suite for CheckpointManagementTool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = CheckpointManagementTool()

    def test_tool_initialization(self):
        """Test tool initializes correctly."""
        assert self.tool.name == "checkpoint_management_tool"
        assert "checkpoint" in self.tool.description

    def test_create_checkpoint(self):
        """Test checkpoint creation."""
        result = self.tool._run("create", "test_checkpoint", "test_data")
        assert isinstance(result, StepResult)

    def test_restore_checkpoint(self):
        """Test checkpoint restoration."""
        result = self.tool._run("restore", "test_checkpoint")
        assert isinstance(result, StepResult)

    def test_list_checkpoints(self):
        """Test checkpoint listing."""
        result = self.tool._run("list")
        assert isinstance(result, StepResult)

    def test_delete_checkpoint(self):
        """Test checkpoint deletion."""
        result = self.tool._run("delete", "test_checkpoint")
        assert isinstance(result, StepResult)

    def test_invalid_operation(self):
        """Test invalid operation."""
        result = self.tool._run("invalid", "test_checkpoint")
        assert not result.success
        assert "Unknown operation" in result.error

    def test_missing_checkpoint_name(self):
        """Test missing checkpoint name."""
        result = self.tool._run("create", "", "test_data")
        assert not result.success
        assert "checkpoint_name is required" in result.error
