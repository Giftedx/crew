"""
Configuration management for Creator Operations.

This module handles platform configuration, feature flags, rate limits,
and other settings for the Creator Operations system.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


@dataclass
class PlatformConfig:
    """Configuration for a specific platform."""

    name: str
    api_base_url: str
    rate_limit_requests_per_minute: int
    rate_limit_requests_per_hour: int
    rate_limit_requests_per_day: int
    quota_units_per_request: dict[str, int] = field(default_factory=dict)
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_backoff_factor: float = 1.0
    enabled: bool = True


@dataclass
class CreatorOpsConfig:
    """Main configuration for Creator Operations."""

    # Feature flags
    enabled: bool = False
    real_apis: bool = False
    fixture_mode: bool = True

    # Platform configurations
    platforms: dict[str, PlatformConfig] = field(default_factory=dict)

    # Processing settings
    max_workers: int = 4
    batch_size: int = 10
    processing_timeout_seconds: int = 3600

    # Storage settings
    database_url: str = ""
    minio_endpoint: str = ""
    minio_access_key: str = ""
    minio_secret_key: str = ""
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    redis_url: str = ""

    # ML settings
    whisper_model: str = "large-v3"
    use_gpu: bool = True
    embedding_model: str = "text-embedding-3-large"

    # Security settings
    encryption_key: str = ""
    data_retention_days: int = 90
    enable_audit_logging: bool = True

    def __post_init__(self) -> None:
        """Initialize configuration from environment variables."""
        # Feature flags
        self.enabled = os.getenv("ENABLE_CREATOR_OPS", "false").lower() == "true"
        self.real_apis = os.getenv("ENABLE_REAL_APIS", "false").lower() == "true"
        self.fixture_mode = not self.real_apis

        # Processing settings
        self.max_workers = int(os.getenv("MAX_WORKERS", "4"))
        self.batch_size = int(os.getenv("BATCH_SIZE", "10"))
        self.processing_timeout_seconds = int(os.getenv("PROCESSING_TIMEOUT_SECONDS", "3600"))

        # Storage settings
        self.database_url = os.getenv("DATABASE_URL", "")
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        self.minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY", "")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        # ML settings
        self.whisper_model = os.getenv("WHISPER_MODEL", "large-v3")
        self.use_gpu = os.getenv("USE_GPU", "true").lower() == "true"
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")

        # Security settings
        self.encryption_key = os.getenv("CREATOR_OPS_ENCRYPTION_KEY", "")
        self.data_retention_days = int(os.getenv("DATA_RETENTION_DAYS", "90"))
        self.enable_audit_logging = os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"

        # Initialize platform configurations
        self._initialize_platform_configs()

    def _initialize_platform_configs(self) -> None:
        """Initialize platform-specific configurations."""
        # YouTube configuration
        self.platforms["youtube"] = PlatformConfig(
            name="youtube",
            api_base_url="https://www.googleapis.com/youtube/v3",
            rate_limit_requests_per_minute=100,
            rate_limit_requests_per_hour=10000,
            rate_limit_requests_per_day=100000,
            quota_units_per_request={
                "search": 100,
                "videos": 1,
                "channels": 1,
                "comments": 1,
                "live_chat": 1,
                "captions": 1,
            },
            timeout_seconds=30,
            retry_attempts=3,
            retry_backoff_factor=1.0,
            enabled=os.getenv("ENABLE_YOUTUBE", "true").lower() == "true",
        )

        # Twitch configuration
        self.platforms["twitch"] = PlatformConfig(
            name="twitch",
            api_base_url="https://api.twitch.tv/helix",
            rate_limit_requests_per_minute=800,
            rate_limit_requests_per_hour=8000,
            rate_limit_requests_per_day=80000,
            timeout_seconds=30,
            retry_attempts=3,
            retry_backoff_factor=1.0,
            enabled=os.getenv("ENABLE_TWITCH", "true").lower() == "true",
        )

        # TikTok configuration
        self.platforms["tiktok"] = PlatformConfig(
            name="tiktok",
            api_base_url="https://open-api.tiktok.com",
            rate_limit_requests_per_minute=60,
            rate_limit_requests_per_hour=1000,
            rate_limit_requests_per_day=10000,
            timeout_seconds=30,
            retry_attempts=3,
            retry_backoff_factor=2.0,
            enabled=os.getenv("ENABLE_TIKTOK", "true").lower() == "true",
        )

        # Instagram configuration
        self.platforms["instagram"] = PlatformConfig(
            name="instagram",
            api_base_url="https://graph.facebook.com/v18.0",
            rate_limit_requests_per_minute=200,
            rate_limit_requests_per_hour=4800,
            rate_limit_requests_per_day=50000,
            timeout_seconds=30,
            retry_attempts=3,
            retry_backoff_factor=1.0,
            enabled=os.getenv("ENABLE_INSTAGRAM", "true").lower() == "true",
        )

        # X (Twitter) configuration
        self.platforms["x"] = PlatformConfig(
            name="x",
            api_base_url="https://api.twitter.com/2",
            rate_limit_requests_per_minute=15,  # Basic tier
            rate_limit_requests_per_hour=300,
            rate_limit_requests_per_day=30000,
            timeout_seconds=30,
            retry_attempts=3,
            retry_backoff_factor=1.0,
            enabled=os.getenv("ENABLE_X", "true").lower() == "true",
        )

    def get_platform_config(self, platform: str) -> PlatformConfig | None:
        """Get configuration for a specific platform.

        Args:
            platform: Platform name

        Returns:
            PlatformConfig or None if not found
        """
        return self.platforms.get(platform)

    def validate_configuration(self) -> StepResult:
        """Validate the current configuration.

        Returns:
            StepResult with validation results
        """
        try:
            errors = []
            warnings = []

            # Check if Creator Operations is enabled
            if not self.enabled:
                return StepResult.ok(
                    data={
                        "status": "disabled",
                        "message": "Creator Operations disabled",
                    }
                )

            # Validate required settings
            if not self.database_url:
                errors.append("DATABASE_URL not configured")

            if not self.minio_endpoint:
                errors.append("MINIO_ENDPOINT not configured")

            if not self.qdrant_url:
                errors.append("QDRANT_URL not configured")

            if not self.encryption_key:
                errors.append("CREATOR_OPS_ENCRYPTION_KEY not configured")

            # Validate platform configurations
            enabled_platforms = [name for name, config in self.platforms.items() if config.enabled]
            if not enabled_platforms:
                warnings.append("No platforms enabled")

            # Check for missing API credentials in real API mode
            if self.real_apis:
                required_env_vars = {
                    "youtube": ["YOUTUBE_API_KEY"],
                    "twitch": ["TWITCH_CLIENT_ID", "TWITCH_CLIENT_SECRET"],
                    "tiktok": ["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET"],
                    "instagram": ["INSTAGRAM_ACCESS_TOKEN"],
                    "x": ["X_API_KEY", "X_API_SECRET"],
                }

                for platform in enabled_platforms:
                    if platform in required_env_vars:
                        for env_var in required_env_vars[platform]:
                            if not os.getenv(env_var):
                                errors.append(f"Missing {env_var} for {platform}")

            # Validate processing settings
            if self.max_workers < 1:
                errors.append("MAX_WORKERS must be at least 1")

            if self.batch_size < 1:
                errors.append("BATCH_SIZE must be at least 1")

            if self.processing_timeout_seconds < 60:
                warnings.append("PROCESSING_TIMEOUT_SECONDS is very low")

            # Validate ML settings
            valid_whisper_models = [
                "tiny",
                "base",
                "small",
                "medium",
                "large",
                "large-v2",
                "large-v3",
            ]
            if self.whisper_model not in valid_whisper_models:
                warnings.append(f"Unknown Whisper model: {self.whisper_model}")

            valid_embedding_models = [
                "text-embedding-3-large",
                "text-embedding-3-small",
                "bge-large-en-v1.5",
            ]
            if self.embedding_model not in valid_embedding_models:
                warnings.append(f"Unknown embedding model: {self.embedding_model}")

            # Validate security settings
            if self.data_retention_days < 1:
                errors.append("DATA_RETENTION_DAYS must be at least 1")

            if len(errors) > 0:
                return StepResult.fail(f"Configuration validation failed: {'; '.join(errors)}")

            return StepResult.ok(
                data={
                    "status": "valid",
                    "enabled_platforms": enabled_platforms,
                    "warnings": warnings,
                    "fixture_mode": self.fixture_mode,
                }
            )

        except Exception as e:
            return StepResult.fail(f"Configuration validation error: {e!s}")

    def get_rate_limit_config(self, platform: str) -> dict[str, int]:
        """Get rate limit configuration for a platform.

        Args:
            platform: Platform name

        Returns:
            Dictionary with rate limit settings
        """
        config = self.get_platform_config(platform)
        if not config:
            return {}

        return {
            "requests_per_minute": config.rate_limit_requests_per_minute,
            "requests_per_hour": config.rate_limit_requests_per_hour,
            "requests_per_day": config.rate_limit_requests_per_day,
            "timeout_seconds": config.timeout_seconds,
            "retry_attempts": config.retry_attempts,
            "retry_backoff_factor": config.retry_backoff_factor,
        }

    def is_platform_enabled(self, platform: str) -> bool:
        """Check if a platform is enabled.

        Args:
            platform: Platform name

        Returns:
            True if platform is enabled
        """
        config = self.get_platform_config(platform)
        return config is not None and config.enabled

    def get_enabled_platforms(self) -> list[str]:
        """Get list of enabled platforms.

        Returns:
            List of enabled platform names
        """
        return [name for name, config in self.platforms.items() if config.enabled]

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        return {
            "enabled": self.enabled,
            "real_apis": self.real_apis,
            "fixture_mode": self.fixture_mode,
            "platforms": {
                name: {
                    "name": config.name,
                    "api_base_url": config.api_base_url,
                    "rate_limit_requests_per_minute": config.rate_limit_requests_per_minute,
                    "rate_limit_requests_per_hour": config.rate_limit_requests_per_hour,
                    "rate_limit_requests_per_day": config.rate_limit_requests_per_day,
                    "enabled": config.enabled,
                }
                for name, config in self.platforms.items()
            },
            "processing": {
                "max_workers": self.max_workers,
                "batch_size": self.batch_size,
                "processing_timeout_seconds": self.processing_timeout_seconds,
            },
            "ml": {
                "whisper_model": self.whisper_model,
                "use_gpu": self.use_gpu,
                "embedding_model": self.embedding_model,
            },
            "security": {
                "data_retention_days": self.data_retention_days,
                "enable_audit_logging": self.enable_audit_logging,
            },
        }


# Global configuration instance
config = CreatorOpsConfig()


def get_config() -> CreatorOpsConfig:
    """Get the global Creator Operations configuration.

    Returns:
        CreatorOpsConfig instance
    """
    return config


def reload_config() -> CreatorOpsConfig:
    """Reload configuration from environment variables.

    Returns:
        New CreatorOpsConfig instance
    """
    global config
    config = CreatorOpsConfig()
    return config


def validate_environment() -> StepResult:
    """Validate the environment configuration.

    Returns:
        StepResult with validation results
    """
    return config.validate_configuration()
