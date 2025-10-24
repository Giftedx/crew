"""Unit tests for orchestrator validators module."""

import os
from unittest.mock import patch

import pytest

from src.ultimate_discord_intelligence_bot.orchestrator import validators


class TestValidators:
    """Test suite for validation functions."""

    def test_validate_stage_data_success(self):
        """Test successful stage data validation."""
        # Should not raise when all required keys present
        validators.validate_stage_data(
            "test_stage",
            ["key1", "key2"],
            {"key1": "value1", "key2": "value2", "extra": "ok"},
        )

    def test_validate_stage_data_missing_keys(self):
        """Test validation fails with missing keys."""
        with pytest.raises(ValueError, match="missing required keys: \\['key2'\\]"):
            validators.validate_stage_data("test_stage", ["key1", "key2"], {"key1": "value1"})

    @patch("subprocess.run")
    def test_check_ytdlp_available_success(self, mock_run):
        """Test yt-dlp availability check when present."""
        mock_run.return_value.returncode = 0
        assert validators.check_ytdlp_available() is True
        mock_run.assert_called_once_with(["yt-dlp", "--version"], capture_output=True, text=True, timeout=5)

    @patch("subprocess.run")
    def test_check_ytdlp_available_failure(self, mock_run):
        """Test yt-dlp availability check when missing."""
        mock_run.side_effect = FileNotFoundError()
        assert validators.check_ytdlp_available() is False

    def test_check_llm_api_available_with_keys(self):
        """Test LLM API availability with environment keys."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            assert validators.check_llm_api_available() is True

    def test_check_llm_api_available_no_keys(self):
        """Test LLM API availability without keys."""
        with patch.dict(os.environ, {}, clear=True):
            assert validators.check_llm_api_available() is False

    def test_check_discord_available_with_webhook(self):
        """Test Discord availability with webhook."""
        with patch.dict(os.environ, {"DISCORD_WEBHOOK": "https://discord.com/api/webhooks/123/abc"}):
            assert validators.check_discord_available() is True

    def test_check_discord_available_with_dummy_webhook(self):
        """Test Discord availability with dummy webhook."""
        with patch.dict(
            os.environ,
            {"DISCORD_WEBHOOK": "https://discord.com/api/webhooks/YOUR_WEBHOOK"},
        ):
            assert validators.check_discord_available() is False

    def test_detect_placeholder_responses_found(self, caplog):
        """Test placeholder detection when placeholder found."""
        validators.detect_placeholder_responses("test_task", {"result": "This is a placeholder response"})
        assert "may have returned placeholder content" in caplog.text

    def test_detect_placeholder_responses_not_found(self, caplog):
        """Test placeholder detection when no placeholder."""
        validators.detect_placeholder_responses("test_task", {"result": "This is a real response"})
        assert "placeholder" not in caplog.text

    def test_validate_depth_parameter_valid(self):
        """Test depth parameter validation with valid values."""
        assert validators.validate_depth_parameter("standard") == "standard"
        assert validators.validate_depth_parameter("DEEP") == "deep"
        assert validators.validate_depth_parameter(" Comprehensive ") == "comprehensive"

    def test_validate_depth_parameter_invalid(self):
        """Test depth parameter validation with invalid value."""
        with pytest.raises(ValueError, match="Invalid depth 'invalid'"):
            validators.validate_depth_parameter("invalid")

    @patch("subprocess.run")
    def test_validate_system_prerequisites_all_good(self, mock_run):
        """Test system prerequisites validation when all systems go."""
        mock_run.return_value.returncode = 0
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "DISCORD_WEBHOOK": "https://discord.com/api/webhooks/123/abc",
            },
        ):
            result = validators.validate_system_prerequisites()
            assert result["all_valid"] is True
            assert result["yt_dlp"] is True
            assert result["llm_api"] is True
            assert result["discord"] is True

    @patch("subprocess.run")
    def test_validate_system_prerequisites_missing_ytdlp(self, mock_run):
        """Test system prerequisites validation with missing yt-dlp."""
        mock_run.side_effect = FileNotFoundError()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            result = validators.validate_system_prerequisites()
            assert result["all_valid"] is False
            assert result["yt_dlp"] is False
            assert result["llm_api"] is True
