"""Tests for secure configuration security validation."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from core.secure_config import reload_config
from security.net_guard import SecurityError
from security.webhook_guard import verify_incoming


class TestSecureConfigSecurity:
    """Test security validation in the secure configuration system."""

    def test_webhook_secret_prevents_default_values(self):
        """Test that webhook secrets cannot use default values."""
        # Test various default values that should be rejected
        default_values = ["CHANGE_ME", "changeme", "default", ""]

        for default_value in default_values:
            with patch.dict(os.environ, {"WEBHOOK_SECRET_DEFAULT": default_value}):
                from core.secure_config import reload_config

                config = reload_config()
                with pytest.raises(ValueError, match="must be changed from default value"):
                    config.get_webhook_secret("default")

    def test_webhook_secret_requires_configuration(self):
        """Test that webhook secrets must be configured."""
        with patch.dict(os.environ, {}, clear=True):
            from core.secure_config import reload_config

            config = reload_config()
            with pytest.raises(ValueError, match="is not configured"):
                config.get_webhook_secret("missing")

    def test_api_key_validation(self):
        """Test that API keys are properly validated."""
        # Test missing API key
        with patch.dict(os.environ, {}, clear=True):
            from core.secure_config import reload_config

            config = reload_config()
            with pytest.raises(ValueError, match="API key for service 'missing' is not configured"):
                config.get_api_key("missing")

        # Test valid API key
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-valid-key"}):
            from core.secure_config import reload_config

            config = reload_config()
            key = config.get_api_key("openai")
            assert key == "sk-valid-key"

    def test_webhook_verification_blocks_default_secrets(self):
        """Test that webhook verification blocks default secret values."""
        with patch.dict(os.environ, {"WEBHOOK_SECRET_DEFAULT": "CHANGE_ME"}):
            with pytest.raises(SecurityError, match="default/empty value"):
                verify_incoming(
                    body=b"test",
                    headers={"X-Signature": "test", "X-Timestamp": "123456789", "X-Nonce": "test"},
                    secret_id="default",
                )

    def test_http_retry_flag_handling(self):
        """Test HTTP retry flag configuration."""
        # Test flag enabled
        with patch.dict(os.environ, {"ENABLE_HTTP_RETRY": "true"}):
            from core.secure_config import reload_config

            config = reload_config()
            assert config.enable_http_retry is True

        # Test flag disabled
        with patch.dict(os.environ, {"ENABLE_HTTP_RETRY": "false"}):
            from core.secure_config import reload_config

            config = reload_config()
            assert config.enable_http_retry is False

    def test_audit_logging_for_sensitive_access(self):
        """Test that sensitive operations are audit logged."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key", "ENABLE_AUDIT_LOGGING": "true"}):
            from core.secure_config import reload_config

            config = reload_config()

            with patch("core.secure_config.logger") as mock_logger:
                config.get_api_key("openai")

                # Verify audit log was created
                mock_logger.info.assert_called_once()
                call_args = mock_logger.info.call_args
                assert "API key accessed for service: openai" in call_args[0][0]
                assert call_args[1]["extra"]["audit"] is True

    def test_config_reload_functionality(self):
        """Test that config can be reloaded for testing."""
        with patch.dict(os.environ, {"SERVICE_NAME": "test1"}):
            config1 = reload_config()  # Use reload to pick up env changes
            assert config1.service_name == "test1"

        with patch.dict(os.environ, {"SERVICE_NAME": "test2"}):
            config2 = reload_config()
            assert config2.service_name == "test2"
            assert config2 is not config1  # New instance created


class TestSecureConfigIntegration:
    """Test integration between secure config and existing systems."""

    def test_backward_compatibility_helpers(self):
        """Test that backward compatibility functions work."""
        from core.secure_config import get_api_key, get_webhook_url, is_feature_enabled, reload_config

        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "sk-test",
                "DISCORD_WEBHOOK": "https://discord.com/webhook",
                "ENABLE_HTTP_RETRY": "true",
            },
        ):
            reload_config()  # Reload to pick up env changes
            assert get_api_key("openai") == "sk-test"
            assert get_webhook_url("discord") == "https://discord.com/webhook"
            assert is_feature_enabled("http_retry") is True

    def test_security_secrets_integration(self):
        """Test integration with security.secrets module."""
        with patch.dict(os.environ, {"WEBHOOK_SECRET_TEST": "secure-secret-123"}):
            from core.secure_config import reload_config

            config = reload_config()
            secret = config.get_webhook_secret("test")
            assert secret == "secure-secret-123"

    def test_pydantic_validation_errors(self):
        """Test that invalid configuration values are caught."""
        with patch.dict(os.environ, {"QDRANT_GRPC_PORT": "not-a-number"}):
            from core.secure_config import reload_config

            with pytest.raises(ValueError):
                reload_config()
