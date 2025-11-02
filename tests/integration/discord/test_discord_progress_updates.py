"""Unit tests for discord progress updates module."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.ultimate_discord_intelligence_bot.orchestrator import discord_progress_updates


class TestDiscordProgressUpdates:
    """Test suite for discord progress updates."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_interaction = Mock()
        self.mock_interaction.followup = AsyncMock()

    @pytest.mark.asyncio
    async def test_send_progress_update_success(self):
        """Test successful progress update."""
        # Arrange
        message = "Processing content"
        current = 2
        total = 5

        with patch(
            "src.ultimate_discord_intelligence_bot.orchestrator.discord_progress_updates.is_session_valid",
            return_value=True,
        ):
            # Act
            await discord_progress_updates.send_progress_update(self.mock_interaction, message, current, total)

            # Assert
            self.mock_interaction.followup.send.assert_called_once()
            call_args = self.mock_interaction.followup.send.call_args
            assert "Processing content" in call_args[0][0]
            assert "🟢🟢⚪⚪⚪" in call_args[0][0]
            assert "2/5 (40%)" in call_args[0][0]
            assert call_args[1]["ephemeral"] is False

    @pytest.mark.asyncio
    async def test_send_progress_update_session_closed(self):
        """Test progress update when session is closed."""
        # Arrange
        message = "Processing content"
        current = 2
        total = 5

        with patch(
            "src.ultimate_discord_intelligence_bot.orchestrator.discord_progress_updates.is_session_valid",
            return_value=False,
        ):
            # Act
            await discord_progress_updates.send_progress_update(self.mock_interaction, message, current, total)

            # Assert
            self.mock_interaction.followup.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_progress_update_zero_total(self):
        """Test progress update with zero total (division by zero protection)."""
        # Arrange
        message = "Processing content"
        current = 1
        total = 0

        with patch(
            "src.ultimate_discord_intelligence_bot.orchestrator.discord_progress_updates.is_session_valid",
            return_value=True,
        ):
            # Act
            await discord_progress_updates.send_progress_update(self.mock_interaction, message, current, total)

            # Assert
            self.mock_interaction.followup.send.assert_called_once()
            call_args = self.mock_interaction.followup.send.call_args
            assert "1/1 (100%)" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_send_progress_update_negative_total(self):
        """Test progress update with negative total."""
        # Arrange
        message = "Processing content"
        current = 1
        total = -5

        with patch(
            "src.ultimate_discord_intelligence_bot.orchestrator.discord_progress_updates.is_session_valid",
            return_value=True,
        ):
            # Act
            await discord_progress_updates.send_progress_update(self.mock_interaction, message, current, total)

            # Assert
            self.mock_interaction.followup.send.assert_called_once()
            call_args = self.mock_interaction.followup.send.call_args
            assert "1/1 (100%)" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_send_progress_update_current_exceeds_total(self):
        """Test progress update when current exceeds total."""
        # Arrange
        message = "Processing content"
        current = 7
        total = 5

        with patch(
            "src.ultimate_discord_intelligence_bot.orchestrator.discord_progress_updates.is_session_valid",
            return_value=True,
        ):
            # Act
            await discord_progress_updates.send_progress_update(self.mock_interaction, message, current, total)

            # Assert
            self.mock_interaction.followup.send.assert_called_once()
            call_args = self.mock_interaction.followup.send.call_args
            assert "🟢🟢🟢🟢🟢" in call_args[0][0]
            assert "7/5 (140%)" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_send_progress_update_session_closed_during_send(self):
        """Test progress update when session closes during send."""
        # Arrange
        message = "Processing content"
        current = 2
        total = 5
        self.mock_interaction.followup.send.side_effect = RuntimeError("Session is closed")

        with patch(
            "src.ultimate_discord_intelligence_bot.orchestrator.discord_progress_updates.is_session_valid",
            return_value=True,
        ):
            # Act
            await discord_progress_updates.send_progress_update(self.mock_interaction, message, current, total)

            # Assert
            self.mock_interaction.followup.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_progress_update_runtime_error_not_session_closed(self):
        """Test progress update with runtime error that's not session closed."""
        # Arrange
        message = "Processing content"
        current = 2
        total = 5
        self.mock_interaction.followup.send.side_effect = RuntimeError("Other error")

        with patch(
            "src.ultimate_discord_intelligence_bot.orchestrator.discord_progress_updates.is_session_valid",
            return_value=True,
        ):
            # Act & Assert
            with pytest.raises(RuntimeError, match="Other error"):
                await discord_progress_updates.send_progress_update(self.mock_interaction, message, current, total)

    @pytest.mark.asyncio
    async def test_send_progress_update_general_exception(self):
        """Test progress update with general exception."""
        # Arrange
        message = "Processing content"
        current = 2
        total = 5
        self.mock_interaction.followup.send.side_effect = Exception("General error")

        with patch(
            "src.ultimate_discord_intelligence_bot.orchestrator.discord_progress_updates.is_session_valid",
            return_value=True,
        ):
            # Act
            await discord_progress_updates.send_progress_update(self.mock_interaction, message, current, total)

            # Assert - should not raise exception
            self.mock_interaction.followup.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_progress_update_with_custom_logger(self):
        """Test progress update with custom logger."""
        # Arrange
        message = "Processing content"
        current = 2
        total = 5
        custom_logger = Mock()

        with patch(
            "src.ultimate_discord_intelligence_bot.orchestrator.discord_progress_updates.is_session_valid",
            return_value=True,
        ):
            # Act
            await discord_progress_updates.send_progress_update(
                self.mock_interaction, message, current, total, log=custom_logger
            )

            # Assert
            self.mock_interaction.followup.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_progress_update_progress_bar_formatting(self):
        """Test progress bar formatting for various progress levels."""
        # Test cases: (current, total, expected_bar, expected_percentage)
        test_cases = [
            (0, 5, "⚪⚪⚪⚪⚪", "0/5 (0%)"),
            (1, 5, "🟢⚪⚪⚪⚪", "1/5 (20%)"),
            (3, 5, "🟢🟢🟢⚪⚪", "3/5 (60%)"),
            (5, 5, "🟢🟢🟢🟢🟢", "5/5 (100%)"),
        ]

        with patch(
            "src.ultimate_discord_intelligence_bot.orchestrator.discord_progress_updates.is_session_valid",
            return_value=True,
        ):
            for current, total, expected_bar, expected_count in test_cases:
                # Reset mock
                self.mock_interaction.followup.send.reset_mock()

                # Act
                await discord_progress_updates.send_progress_update(self.mock_interaction, "Test", current, total)

                # Assert
                call_args = self.mock_interaction.followup.send.call_args[0][0]
                assert expected_bar in call_args
                assert expected_count in call_args
