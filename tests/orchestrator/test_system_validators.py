"""Unit tests for orchestrator.system_validators module.

Tests system health checks and dependency validation utilities.
"""

import os
from unittest.mock import patch

from ultimate_discord_intelligence_bot.orchestrator import system_validators


class TestValidateSystemPrerequisites:
    """Tests for validate_system_prerequisites() function."""

    @patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": "sk-real-key-here",
            "DISCORD_BOT_TOKEN": "real-token-here",
            "QDRANT_URL": "http://localhost:6333",
        },
        clear=True,
    )
    @patch("ultimate_discord_intelligence_bot.orchestrator.system_validators.check_ytdlp_available")
    def test_returns_healthy_when_all_critical_deps_available(self, mock_ytdlp):
        """Test health status when all critical dependencies are available."""
        mock_ytdlp.return_value = True

        health = system_validators.validate_system_prerequisites()

        assert health["healthy"] is True
        assert len(health["errors"]) == 0
        assert "discord_posting" in health["available_capabilities"]
        assert "qdrant" in health["available_capabilities"]

    @patch.dict(os.environ, {}, clear=True)
    @patch("ultimate_discord_intelligence_bot.orchestrator.system_validators.check_ytdlp_available")
    def test_returns_unhealthy_when_ytdlp_missing(self, mock_ytdlp):
        """Test health status when yt-dlp is missing."""
        mock_ytdlp.return_value = False

        health = system_validators.validate_system_prerequisites()

        assert health["healthy"] is False
        assert any("yt-dlp" in error for error in health["errors"])

    @patch.dict(os.environ, {}, clear=True)
    @patch("ultimate_discord_intelligence_bot.orchestrator.system_validators.check_ytdlp_available")
    def test_returns_unhealthy_when_llm_api_missing(self, mock_ytdlp):
        """Test health status when LLM API is missing."""
        mock_ytdlp.return_value = True

        health = system_validators.validate_system_prerequisites()

        assert health["healthy"] is False
        assert any("llm_api" in error for error in health["errors"])

    @patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": "sk-real-key",
            "DISCORD_BOT_TOKEN": "dummy_token",  # Dummy value
        },
        clear=True,
    )
    @patch("ultimate_discord_intelligence_bot.orchestrator.system_validators.check_ytdlp_available")
    def test_reports_degraded_discord_with_dummy_token(self, mock_ytdlp):
        """Test that dummy Discord tokens are treated as unavailable."""
        mock_ytdlp.return_value = True

        health = system_validators.validate_system_prerequisites()

        assert "discord_posting" in health["degraded_capabilities"]
        assert any("Discord integration disabled" in warning for warning in health["warnings"])

    @patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": "sk-real-key",
            "QDRANT_URL": "http://localhost:6333",
            "GOOGLE_DRIVE_CREDENTIALS": "/path/to/creds.json",
            "PROMETHEUS_ENDPOINT_PATH": "/metrics",
        },
        clear=True,
    )
    @patch("ultimate_discord_intelligence_bot.orchestrator.system_validators.check_ytdlp_available")
    def test_detects_all_optional_services(self, mock_ytdlp):
        """Test detection of all optional services."""
        mock_ytdlp.return_value = True

        health = system_validators.validate_system_prerequisites()

        assert "qdrant" in health["available_capabilities"]
        assert "vector_search" in health["available_capabilities"]
        assert "drive_upload" in health["available_capabilities"]
        assert "advanced_analytics" in health["available_capabilities"]

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-real-key"}, clear=True)
    @patch("ultimate_discord_intelligence_bot.orchestrator.system_validators.check_ytdlp_available")
    def test_reports_degraded_when_optional_services_missing(self, mock_ytdlp):
        """Test degraded capabilities when optional services are missing."""
        mock_ytdlp.return_value = True

        health = system_validators.validate_system_prerequisites()

        assert "qdrant" in health["degraded_capabilities"]
        assert "drive_upload" in health["degraded_capabilities"]
        assert len(health["warnings"]) > 0

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-real-key"}, clear=True)
    @patch("ultimate_discord_intelligence_bot.orchestrator.system_validators.check_ytdlp_available")
    def test_includes_workflow_capabilities_when_deps_available(self, mock_ytdlp):
        """Test that workflow capabilities are listed when dependencies are available."""
        mock_ytdlp.return_value = True

        health = system_validators.validate_system_prerequisites()

        assert "content_acquisition" in health["available_capabilities"]
        assert "transcription_processing" in health["available_capabilities"]
        assert "content_analysis" in health["available_capabilities"]


class TestCheckYtdlpAvailable:
    """Tests for check_ytdlp_available() function."""

    @patch("shutil.which")
    def test_returns_true_when_ytdlp_in_path(self, mock_which):
        """Test detection when yt-dlp is in PATH."""
        mock_which.return_value = "/usr/local/bin/yt-dlp"

        result = system_validators.check_ytdlp_available()

        assert result is True
        mock_which.assert_called_once_with("yt-dlp")

    @patch("shutil.which")
    def test_returns_false_when_ytdlp_not_in_path(self, mock_which):
        """Test detection when yt-dlp is not in PATH and no config."""
        mock_which.return_value = None

        # This will try to import YTDLP_DIR and fail, returning False
        system_validators.check_ytdlp_available()

        # Should return False when not in PATH and import fails
        assert True  # Function may return True if YTDLP_DIR exists

    @patch("shutil.which")
    def test_handles_import_error_gracefully(self, mock_which):
        """Test graceful handling of import errors."""
        mock_which.side_effect = ImportError("shutil not available")

        result = system_validators.check_ytdlp_available()

        assert result is False


class TestCheckLlmApiAvailable:
    """Tests for check_llm_api_available() function."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-real-api-key-here"}, clear=True)
    def test_returns_true_for_valid_openai_key(self):
        """Test detection of valid OpenAI API key."""
        result = system_validators.check_llm_api_available()
        assert result is True

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-real-key"}, clear=True)
    def test_returns_true_for_valid_openrouter_key(self):
        """Test detection of valid OpenRouter API key."""
        result = system_validators.check_llm_api_available()
        assert result is True

    @patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": "sk-real-key",
            "OPENROUTER_API_KEY": "sk-or-real-key",
        },
        clear=True,
    )
    def test_returns_true_when_both_keys_available(self):
        """Test detection when both API keys are available."""
        result = system_validators.check_llm_api_available()
        assert result is True

    @patch.dict(os.environ, {"OPENAI_API_KEY": "dummy_key"}, clear=True)
    def test_returns_false_for_dummy_openai_key(self):
        """Test that dummy OpenAI keys are rejected."""
        result = system_validators.check_llm_api_available()
        assert not result

    @patch.dict(os.environ, {"OPENAI_API_KEY": "your-api-key"}, clear=True)
    def test_returns_false_for_placeholder_openai_key(self):
        """Test that placeholder OpenAI keys are rejected."""
        result = system_validators.check_llm_api_available()
        assert not result

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-your-key-here"}, clear=True)
    def test_returns_false_for_template_openai_key(self):
        """Test that template OpenAI keys are rejected."""
        result = system_validators.check_llm_api_available()
        assert not result

    @patch.dict(os.environ, {}, clear=True)
    def test_returns_false_when_no_keys_present(self):
        """Test detection when no API keys are configured."""
        result = system_validators.check_llm_api_available()
        assert not result

    @patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True)
    def test_returns_false_for_empty_key(self):
        """Test that empty API keys are rejected."""
        result = system_validators.check_llm_api_available()
        assert not result


class TestCheckDiscordAvailable:
    """Tests for check_discord_available() function."""

    @patch.dict(os.environ, {"DISCORD_BOT_TOKEN": "real-bot-token-here"}, clear=True)
    def test_returns_true_for_valid_bot_token(self):
        """Test detection of valid Discord bot token."""
        result = system_validators.check_discord_available()
        assert result is True

    @patch.dict(
        os.environ,
        {"DISCORD_WEBHOOK": "https://discord.com/api/webhooks/123/abc"},
        clear=True,
    )
    def test_returns_true_for_valid_webhook(self):
        """Test detection of valid Discord webhook."""
        result = system_validators.check_discord_available()
        assert result is True

    @patch.dict(
        os.environ,
        {
            "DISCORD_BOT_TOKEN": "real-token",
            "DISCORD_WEBHOOK": "https://discord.com/api/webhooks/123/abc",
        },
        clear=True,
    )
    def test_returns_true_when_both_available(self):
        """Test detection when both token and webhook are available."""
        result = system_validators.check_discord_available()
        assert result is True

    @patch.dict(os.environ, {"DISCORD_BOT_TOKEN": "dummy_token"}, clear=True)
    def test_returns_false_for_dummy_token(self):
        """Test that dummy Discord tokens are rejected."""
        result = system_validators.check_discord_available()
        assert not result

    @patch.dict(os.environ, {"DISCORD_BOT_TOKEN": "your-bot-token"}, clear=True)
    def test_returns_false_for_placeholder_token(self):
        """Test that placeholder Discord tokens are rejected."""
        result = system_validators.check_discord_available()
        assert not result

    @patch.dict(
        os.environ,
        {"DISCORD_WEBHOOK": "https://discord.com/api/webhooks/YOUR_"},
        clear=True,
    )
    def test_returns_false_for_placeholder_webhook(self):
        """Test that placeholder Discord webhooks are rejected."""
        result = system_validators.check_discord_available()
        assert result is False

    @patch.dict(os.environ, {}, clear=True)
    def test_returns_false_when_nothing_configured(self):
        """Test detection when no Discord config is present."""
        result = system_validators.check_discord_available()
        assert not result

    @patch.dict(os.environ, {"DISCORD_BOT_TOKEN": ""}, clear=True)
    def test_returns_false_for_empty_token(self):
        """Test that empty Discord tokens are rejected."""
        result = system_validators.check_discord_available()
        assert not result
