"""
Secrets management for Creator Operations.

This module provides secure storage and retrieval of API keys, OAuth tokens,
and other sensitive configuration data with encryption and audit logging.
"""

from __future__ import annotations

import logging
import os
from platform.core.step_result import StepResult
from typing import Any

from cryptography.fernet import Fernet


logger = logging.getLogger(__name__)


class SecretsVault:
    """Secure vault for storing and retrieving secrets."""

    def __init__(self, encryption_key: str | None = None) -> None:
        """Initialize the secrets vault.

        Args:
            encryption_key: Base64-encoded encryption key. If None, uses environment variable.
        """
        self.encryption_key = encryption_key or os.getenv("CREATOR_OPS_ENCRYPTION_KEY")
        if not self.encryption_key:
            raise ValueError("Encryption key required. Set CREATOR_OPS_ENCRYPTION_KEY environment variable.")
        try:
            self.fernet = Fernet(self.encryption_key.encode())
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {e!s}") from e

    def encrypt_secret(self, secret: str) -> str:
        """Encrypt a secret string.

        Args:
            secret: Plain text secret to encrypt

        Returns:
            Base64-encoded encrypted secret
        """
        try:
            encrypted_bytes = self.fernet.encrypt(secret.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt secret: {e!s}")
            raise

    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt a secret string.

        Args:
            encrypted_secret: Base64-encoded encrypted secret

        Returns:
            Decrypted plain text secret
        """
        try:
            decrypted_bytes = self.fernet.decrypt(encrypted_secret.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt secret: {e!s}")
            raise

    def store_secret(self, key: str, value: str, metadata: dict[str, Any] | None = None) -> StepResult:
        """Store a secret with optional metadata.

        Args:
            key: Secret identifier
            value: Secret value to store
            metadata: Optional metadata about the secret

        Returns:
            StepResult indicating success or failure
        """
        try:
            encrypted_value = self.encrypt_secret(value)
            env_key = f"CREATOR_OPS_SECRET_{key.upper()}"
            os.environ[env_key] = encrypted_value
            logger.info(f"Stored secret: {key} (metadata: {metadata})")
            return StepResult.ok(data={"key": key, "stored": True})
        except Exception as e:
            logger.error(f"Failed to store secret {key}: {e!s}")
            return StepResult.fail(f"Failed to store secret: {e!s}")

    def retrieve_secret(self, key: str) -> StepResult:
        """Retrieve a secret by key.

        Args:
            key: Secret identifier

        Returns:
            StepResult with decrypted secret or error
        """
        try:
            env_key = f"CREATOR_OPS_SECRET_{key.upper()}"
            encrypted_value = os.getenv(env_key)
            if not encrypted_value:
                return StepResult.fail(f"Secret not found: {key}")
            decrypted_value = self.decrypt_secret(encrypted_value)
            logger.info(f"Retrieved secret: {key}")
            return StepResult.ok(data={"key": key, "value": decrypted_value})
        except Exception as e:
            logger.error(f"Failed to retrieve secret {key}: {e!s}")
            return StepResult.fail(f"Failed to retrieve secret: {e!s}")

    def delete_secret(self, key: str) -> StepResult:
        """Delete a secret by key.

        Args:
            key: Secret identifier

        Returns:
            StepResult indicating success or failure
        """
        try:
            env_key = f"CREATOR_OPS_SECRET_{key.upper()}"
            if env_key in os.environ:
                del os.environ[env_key]
                logger.info(f"Deleted secret: {key}")
                return StepResult.ok(data={"key": key, "deleted": True})
            else:
                return StepResult.fail(f"Secret not found: {key}")
        except Exception as e:
            logger.error(f"Failed to delete secret {key}: {e!s}")
            return StepResult.fail(f"Failed to delete secret: {e!s}")

    def list_secrets(self) -> StepResult:
        """List all stored secret keys.

        Returns:
            StepResult with list of secret keys
        """
        try:
            secret_keys = []
            for env_key, _ in os.environ.items():
                if env_key.startswith("CREATOR_OPS_SECRET_"):
                    secret_name = env_key.replace("CREATOR_OPS_SECRET_", "").lower()
                    secret_keys.append(secret_name)
            return StepResult.ok(data={"secrets": secret_keys})
        except Exception as e:
            logger.error(f"Failed to list secrets: {e!s}")
            return StepResult.fail(f"Failed to list secrets: {e!s}")


class PlatformSecrets:
    """Platform-specific secrets management."""

    def __init__(self, vault: SecretsVault | None = None) -> None:
        """Initialize platform secrets manager.

        Args:
            vault: Secrets vault instance. If None, creates a new one.
        """
        self.vault = vault or SecretsVault()
        self.platform_secrets = {
            "youtube": {
                "api_key": "YouTube Data API key",
                "client_id": "YouTube OAuth client ID",
                "client_secret": "YouTube OAuth client secret",
            },
            "twitch": {
                "client_id": "Twitch API client ID",
                "client_secret": "Twitch API client secret",
                "webhook_secret": "Twitch webhook secret",
            },
            "tiktok": {"client_key": "TikTok API client key", "client_secret": "TikTok API client secret"},
            "instagram": {
                "access_token": "Instagram Graph API access token",
                "app_id": "Instagram app ID",
                "app_secret": "Instagram app secret",
            },
            "x": {
                "api_key": "X API key",
                "api_secret": "X API secret",
                "access_token": "X access token",
                "access_token_secret": "X access token secret",
            },
        }

    def get_platform_secret(self, platform: str, secret_type: str) -> StepResult:
        """Get a platform-specific secret.

        Args:
            platform: Platform name (youtube, twitch, etc.)
            secret_type: Type of secret (api_key, client_id, etc.)

        Returns:
            StepResult with secret value or error
        """
        if platform not in self.platform_secrets:
            return StepResult.fail(f"Unknown platform: {platform}")
        if secret_type not in self.platform_secrets[platform]:
            return StepResult.fail(f"Unknown secret type for {platform}: {secret_type}")
        secret_key = f"{platform}_{secret_type}"
        return self.vault.retrieve_secret(secret_key)

    def set_platform_secret(self, platform: str, secret_type: str, value: str) -> StepResult:
        """Set a platform-specific secret.

        Args:
            platform: Platform name
            secret_type: Type of secret
            value: Secret value

        Returns:
            StepResult indicating success or failure
        """
        if platform not in self.platform_secrets:
            return StepResult.fail(f"Unknown platform: {platform}")
        if secret_type not in self.platform_secrets[platform]:
            return StepResult.fail(f"Unknown secret type for {platform}: {secret_type}")
        secret_key = f"{platform}_{secret_type}"
        metadata = {"platform": platform, "type": secret_type}
        return self.vault.store_secret(secret_key, value, metadata)

    def validate_platform_secrets(self, platform: str) -> StepResult:
        """Validate that all required secrets are present for a platform.

        Args:
            platform: Platform name

        Returns:
            StepResult with validation results
        """
        if platform not in self.platform_secrets:
            return StepResult.fail(f"Unknown platform: {platform}")
        missing_secrets = []
        present_secrets = []
        for secret_type in self.platform_secrets[platform]:
            result = self.get_platform_secret(platform, secret_type)
            if result.success:
                present_secrets.append(secret_type)
            else:
                missing_secrets.append(secret_type)
        return StepResult.ok(
            data={
                "platform": platform,
                "missing": missing_secrets,
                "present": present_secrets,
                "complete": len(missing_secrets) == 0,
            }
        )

    def validate_all_platforms(self) -> StepResult:
        """Validate secrets for all platforms.

        Returns:
            StepResult with validation results for all platforms
        """
        results = {}
        all_complete = True
        for platform in self.platform_secrets:
            result = self.validate_platform_secrets(platform)
            if result.success:
                results[platform] = result.data
                if not result.data["complete"]:
                    all_complete = False
            else:
                results[platform] = {"error": result.error}
                all_complete = False
        return StepResult.ok(data={"platforms": results, "all_complete": all_complete})


def generate_encryption_key() -> str:
    """Generate a new encryption key for the secrets vault.

    Returns:
        Base64-encoded encryption key
    """
    from cryptography.fernet import Fernet

    key = Fernet.generate_key()
    return key.decode()


def validate_secrets_configuration() -> StepResult:
    """Validate the overall secrets configuration.

    Returns:
        StepResult indicating if secrets are properly configured
    """
    try:
        encryption_key = os.getenv("CREATOR_OPS_ENCRYPTION_KEY")
        if not encryption_key:
            return StepResult.fail(
                'CREATOR_OPS_ENCRYPTION_KEY not set. Generate one with: python -c "from creator_ops.auth.vault import generate_encryption_key; print(generate_encryption_key())"'
            )
        vault = SecretsVault(encryption_key)
        test_result = vault.store_secret("test", "test_value")
        if not test_result.success:
            return StepResult.fail(f"Vault test failed: {test_result.error}")
        vault.delete_secret("test")
        return StepResult.ok(data={"status": "valid", "vault": "operational"})
    except Exception as e:
        return StepResult.fail(f"Secrets configuration validation failed: {e!s}")
