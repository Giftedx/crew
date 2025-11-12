"""
Tests for Creator Operations configuration and secrets management.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from ultimate_discord_intelligence_bot.creator_ops.auth.vault import (
    PlatformSecrets,
    SecretsVault,
    generate_encryption_key,
    validate_secrets_configuration,
)
from ultimate_discord_intelligence_bot.creator_ops.config import (
    CreatorOpsConfig,
    PlatformConfig,
    get_config,
    reload_config,
    validate_environment,
)


class TestPlatformConfig:
    """Test PlatformConfig class."""

    def test_create_platform_config(self):
        """Test creating a platform configuration."""
        config = PlatformConfig(
            name="youtube",
            api_base_url="https://api.youtube.com/v3",
            rate_limit_requests_per_minute=100,
            rate_limit_requests_per_hour=1000,
            rate_limit_requests_per_day=10000,
        )

        assert config.name == "youtube"
        assert config.api_base_url == "https://api.youtube.com/v3"
        assert config.rate_limit_requests_per_minute == 100
        assert config.enabled is True  # Default value

    def test_platform_config_with_quota_units(self):
        """Test platform config with quota units."""
        config = PlatformConfig(
            name="youtube",
            api_base_url="https://api.youtube.com/v3",
            rate_limit_requests_per_minute=100,
            rate_limit_requests_per_hour=1000,
            rate_limit_requests_per_day=10000,
            quota_units_per_request={"search": 100, "videos": 1},
        )

        assert config.quota_units_per_request["search"] == 100
        assert config.quota_units_per_request["videos"] == 1


class TestCreatorOpsConfig:
    """Test CreatorOpsConfig class."""

    def test_config_initialization(self):
        """Test configuration initialization."""
        config = CreatorOpsConfig()

        # Check default values
        assert config.enabled is False  # Default from environment
        assert config.fixture_mode is True  # Default when real_apis is False
        assert config.max_workers == 4
        assert config.batch_size == 10
        assert config.whisper_model == "large-v3"
        assert config.use_gpu is True

    @patch.dict(
        os.environ,
        {
            "ENABLE_CREATOR_OPS": "true",
            "ENABLE_REAL_APIS": "true",
            "MAX_WORKERS": "8",
            "WHISPER_MODEL": "small",
        },
    )
    def test_config_from_environment(self):
        """Test configuration loading from environment variables."""
        config = CreatorOpsConfig()

        assert config.enabled is True
        assert config.real_apis is True
        assert config.fixture_mode is False
        assert config.max_workers == 8
        assert config.whisper_model == "small"

    def test_platform_configs_initialized(self):
        """Test that platform configurations are initialized."""
        config = CreatorOpsConfig()

        assert "youtube" in config.platforms
        assert "twitch" in config.platforms
        assert "tiktok" in config.platforms
        assert "instagram" in config.platforms
        assert "x" in config.platforms

    def test_get_platform_config(self):
        """Test getting platform configuration."""
        config = CreatorOpsConfig()

        youtube_config = config.get_platform_config("youtube")
        assert youtube_config is not None
        assert youtube_config.name == "youtube"
        assert youtube_config.api_base_url == "https://www.googleapis.com/youtube/v3"

        # Test non-existent platform
        unknown_config = config.get_platform_config("unknown")
        assert unknown_config is None

    def test_get_rate_limit_config(self):
        """Test getting rate limit configuration."""
        config = CreatorOpsConfig()

        rate_limit = config.get_rate_limit_config("youtube")
        assert "requests_per_minute" in rate_limit
        assert "requests_per_hour" in rate_limit
        assert "requests_per_day" in rate_limit
        assert rate_limit["requests_per_minute"] == 100

    def test_is_platform_enabled(self):
        """Test checking if platform is enabled."""
        config = CreatorOpsConfig()

        # Should be enabled by default
        assert config.is_platform_enabled("youtube") is True

        # Test disabled platform
        config.platforms["youtube"].enabled = False
        assert config.is_platform_enabled("youtube") is False

    def test_get_enabled_platforms(self):
        """Test getting list of enabled platforms."""
        config = CreatorOpsConfig()

        enabled = config.get_enabled_platforms()
        assert "youtube" in enabled
        assert "twitch" in enabled

        # Disable a platform
        config.platforms["youtube"].enabled = False
        enabled = config.get_enabled_platforms()
        assert "youtube" not in enabled

    @patch.dict(
        os.environ,
        {
            "ENABLE_CREATOR_OPS": "true",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "MINIO_ENDPOINT": "http://localhost:9000",
            "QDRANT_URL": "http://localhost:6333",
            "CREATOR_OPS_ENCRYPTION_KEY": "test_key",
        },
    )
    def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        config = CreatorOpsConfig()
        result = config.validate_configuration()

        assert result.success
        assert "enabled_platforms" in result.data
        assert "fixture_mode" in result.data

    def test_validate_configuration_disabled(self):
        """Test configuration validation when disabled."""
        config = CreatorOpsConfig()
        config.enabled = False
        result = config.validate_configuration()

        assert result.success
        assert result.data["status"] == "disabled"

    @patch.dict(
        os.environ,
        {
            "ENABLE_CREATOR_OPS": "true",
            # Missing required settings
        },
    )
    def test_validate_configuration_failure(self):
        """Test configuration validation failure."""
        config = CreatorOpsConfig()
        result = config.validate_configuration()

        assert not result.success
        assert "DATABASE_URL not configured" in result.error

    def test_to_dict(self):
        """Test converting configuration to dictionary."""
        config = CreatorOpsConfig()
        config_dict = config.to_dict()

        assert "enabled" in config_dict
        assert "platforms" in config_dict
        assert "processing" in config_dict
        assert "ml" in config_dict
        assert "security" in config_dict


class TestSecretsVault:
    """Test SecretsVault class."""

    def test_generate_encryption_key(self):
        """Test encryption key generation."""
        key = generate_encryption_key()
        assert isinstance(key, str)
        assert len(key) > 0

    def test_secrets_vault_initialization(self):
        """Test secrets vault initialization."""
        key = generate_encryption_key()
        vault = SecretsVault(key)
        assert vault is not None

    def test_secrets_vault_invalid_key(self):
        """Test secrets vault with invalid key."""
        with pytest.raises(ValueError, match="Invalid encryption key"):
            SecretsVault("invalid_key")

    def test_encrypt_decrypt_secret(self):
        """Test encrypting and decrypting secrets."""
        key = generate_encryption_key()
        vault = SecretsVault(key)

        secret = "test_secret_value"
        encrypted = vault.encrypt_secret(secret)
        decrypted = vault.decrypt_secret(encrypted)

        assert encrypted != secret
        assert decrypted == secret

    def test_store_retrieve_secret(self):
        """Test storing and retrieving secrets."""
        key = generate_encryption_key()
        vault = SecretsVault(key)

        # Store secret
        result = vault.store_secret("test_key", "test_value", {"source": "test"})
        assert result.success

        # Retrieve secret
        result = vault.retrieve_secret("test_key")
        assert result.success
        assert result.data["value"] == "test_value"

        # Clean up
        vault.delete_secret("test_key")

    def test_retrieve_nonexistent_secret(self):
        """Test retrieving non-existent secret."""
        key = generate_encryption_key()
        vault = SecretsVault(key)

        result = vault.retrieve_secret("nonexistent")
        assert not result.success
        assert "Secret not found" in result.error

    def test_delete_secret(self):
        """Test deleting secrets."""
        key = generate_encryption_key()
        vault = SecretsVault(key)

        # Store and delete secret
        vault.store_secret("test_key", "test_value")
        result = vault.delete_secret("test_key")
        assert result.success

        # Verify deletion
        result = vault.retrieve_secret("test_key")
        assert not result.success

    def test_list_secrets(self):
        """Test listing secrets."""
        key = generate_encryption_key()
        vault = SecretsVault(key)

        # Store some secrets
        vault.store_secret("key1", "value1")
        vault.store_secret("key2", "value2")

        result = vault.list_secrets()
        assert result.success
        assert "key1" in result.data["secrets"]
        assert "key2" in result.data["secrets"]

        # Clean up
        vault.delete_secret("key1")
        vault.delete_secret("key2")


class TestPlatformSecrets:
    """Test PlatformSecrets class."""

    def test_platform_secrets_initialization(self):
        """Test platform secrets initialization."""
        key = generate_encryption_key()
        vault = SecretsVault(key)
        platform_secrets = PlatformSecrets(vault)

        assert platform_secrets is not None
        assert "youtube" in platform_secrets.platform_secrets

    def test_get_platform_secret(self):
        """Test getting platform secrets."""
        key = generate_encryption_key()
        vault = SecretsVault(key)
        platform_secrets = PlatformSecrets(vault)

        # Store a secret
        vault.store_secret("youtube_api_key", "test_api_key")

        result = platform_secrets.get_platform_secret("youtube", "api_key")
        assert result.success
        assert result.data["value"] == "test_api_key"

    def test_get_platform_secret_invalid_platform(self):
        """Test getting secret for invalid platform."""
        key = generate_encryption_key()
        vault = SecretsVault(key)
        platform_secrets = PlatformSecrets(vault)

        result = platform_secrets.get_platform_secret("invalid", "api_key")
        assert not result.success
        assert "Unknown platform" in result.error

    def test_set_platform_secret(self):
        """Test setting platform secrets."""
        key = generate_encryption_key()
        vault = SecretsVault(key)
        platform_secrets = PlatformSecrets(vault)

        result = platform_secrets.set_platform_secret("youtube", "api_key", "test_key")
        assert result.success

        # Verify it was stored
        result = platform_secrets.get_platform_secret("youtube", "api_key")
        assert result.success
        assert result.data["value"] == "test_key"

    def test_validate_platform_secrets(self):
        """Test validating platform secrets."""
        key = generate_encryption_key()
        vault = SecretsVault(key)
        platform_secrets = PlatformSecrets(vault)

        # No secrets stored yet
        result = platform_secrets.validate_platform_secrets("youtube")
        assert result.success
        assert not result.data["complete"]
        assert "api_key" in result.data["missing"]

    def test_validate_all_platforms(self):
        """Test validating all platforms."""
        key = generate_encryption_key()
        vault = SecretsVault(key)
        platform_secrets = PlatformSecrets(vault)

        result = platform_secrets.validate_all_platforms()
        assert result.success
        assert "platforms" in result.data
        assert not result.data["all_complete"]  # No secrets configured


class TestConfigurationIntegration:
    """Test configuration integration functions."""

    @patch.dict(
        os.environ,
        {
            "ENABLE_CREATOR_OPS": "true",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "MINIO_ENDPOINT": "http://localhost:9000",
            "QDRANT_URL": "http://localhost:6333",
            "CREATOR_OPS_ENCRYPTION_KEY": "test_key",
        },
    )
    def test_get_config(self):
        """Test getting global configuration."""
        config = get_config()
        assert isinstance(config, CreatorOpsConfig)
        assert config.enabled is True

    def test_reload_config(self):
        """Test reloading configuration."""
        with patch.dict(os.environ, {"ENABLE_CREATOR_OPS": "false"}):
            config = reload_config()
            assert config.enabled is False

    @patch.dict(
        os.environ,
        {
            "ENABLE_CREATOR_OPS": "true",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "MINIO_ENDPOINT": "http://localhost:9000",
            "QDRANT_URL": "http://localhost:6333",
            "CREATOR_OPS_ENCRYPTION_KEY": "test_key",
        },
    )
    def test_validate_environment(self):
        """Test environment validation."""
        result = validate_environment()
        assert result.success

    def test_validate_secrets_configuration(self):
        """Test secrets configuration validation."""
        # Test without encryption key
        with patch.dict(os.environ, {}, clear=True):
            result = validate_secrets_configuration()
            assert not result.success
            assert "CREATOR_OPS_ENCRYPTION_KEY not set" in result.error

        # Test with valid encryption key
        key = generate_encryption_key()
        with patch.dict(os.environ, {"CREATOR_OPS_ENCRYPTION_KEY": key}):
            result = validate_secrets_configuration()
            assert result.success
            assert result.data["status"] == "valid"
