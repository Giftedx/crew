"""Unit tests for discord session validators module."""

from unittest.mock import Mock

from src.ultimate_discord_intelligence_bot.orchestrator import (
    discord_session_validators,
)


class TestDiscordSessionValidators:
    """Test suite for discord session validators."""

    def setup_method(self):
        """Set up test fixtures."""
        self.valid_interaction = Mock()
        self.valid_interaction.id = "12345"
        self.valid_interaction.followup = Mock()
        self.valid_interaction.followup._adapter = Mock()
        self.valid_interaction.followup._adapter._session = Mock()
        self.valid_interaction.followup._adapter._session.closed = False

        self.closed_interaction = Mock()
        self.closed_interaction.id = "67890"
        self.closed_interaction.followup = Mock()
        self.closed_interaction.followup._adapter = Mock()
        self.closed_interaction.followup._adapter._session = Mock()
        self.closed_interaction.followup._adapter._session.closed = True

        self.invalid_interaction = Mock()
        # Missing followup attribute

    def test_is_session_valid_valid_session(self):
        """Test session validation with valid session."""
        # Act
        result = discord_session_validators.is_session_valid(self.valid_interaction)

        # Assert
        assert result is True

    def test_is_session_valid_closed_session(self):
        """Test session validation with closed session."""
        # Act
        result = discord_session_validators.is_session_valid(self.closed_interaction)

        # Assert
        assert result is False

    def test_is_session_valid_missing_followup(self):
        """Test session validation with missing followup attribute."""
        # Act
        result = discord_session_validators.is_session_valid(self.invalid_interaction)

        # Assert
        assert result is False

    def test_is_session_valid_no_adapter(self):
        """Test session validation with no adapter."""
        # Arrange
        interaction = Mock()
        interaction.followup = Mock()
        interaction.followup._adapter = None
        interaction.id = "12345"

        # Act
        result = discord_session_validators.is_session_valid(interaction)

        # Assert
        assert result is True  # Falls back to ID check

    def test_is_session_valid_no_session(self):
        """Test session validation with no session."""
        # Arrange
        interaction = Mock()
        interaction.followup = Mock()
        interaction.followup._adapter = Mock()
        interaction.followup._adapter._session = None
        interaction.id = "12345"

        # Act
        result = discord_session_validators.is_session_valid(interaction)

        # Assert
        assert result is True  # Falls back to ID check

    def test_is_session_valid_no_closed_attribute(self):
        """Test session validation with session missing closed attribute."""
        # Arrange
        interaction = Mock()
        interaction.followup = Mock()
        interaction.followup._adapter = Mock()
        interaction.followup._adapter._session = Mock()
        # Remove closed attribute from session
        del interaction.followup._adapter._session.closed
        interaction.id = "12345"

        # Act
        result = discord_session_validators.is_session_valid(interaction)

        # Assert
        assert result is True  # Falls back to ID check

    def test_is_session_valid_id_access_fails(self):
        """Test session validation when ID access fails."""
        # Arrange
        interaction = Mock()
        interaction.followup = Mock()
        interaction.followup._adapter = Mock()
        interaction.followup._adapter._session = Mock()
        # No closed attribute
        interaction.id = Mock(side_effect=Exception("ID access failed"))

        # Act
        result = discord_session_validators.is_session_valid(interaction)

        # Assert
        assert result is False

    def test_is_session_valid_exception_handling(self):
        """Test session validation with general exception."""
        # Arrange
        interaction = Mock()
        interaction.followup = Mock(side_effect=Exception("Unexpected error"))

        # Act
        result = discord_session_validators.is_session_valid(interaction)

        # Assert
        assert result is False

    def test_is_session_valid_with_custom_logger(self):
        """Test session validation with custom logger."""
        # Arrange
        custom_logger = Mock()

        # Act
        result = discord_session_validators.is_session_valid(self.valid_interaction, log=custom_logger)

        # Assert
        assert result is True
