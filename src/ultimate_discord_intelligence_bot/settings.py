"""Layered configuration system for the Ultimate Discord Intelligence Bot.

This module provides a clean, type-safe configuration system that replaces
the monolithic settings.py with a layered approach:

1. BaseConfig: Core application settings
2. FeatureFlags: Feature toggles and flags
3. PathConfig: File and directory paths
4. Validation: Configuration validation

Usage:
    from ultimate_discord_intelligence_bot.settings import Settings

    # Create settings instance
    settings = Settings()

    # Access configuration
    print(settings.openai_api_key)
    print(settings.feature_flags.enable_debate_analysis)
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

# Import the new configuration system
from .config import BaseConfig, FeatureFlags, PathConfig, validate_configuration


if TYPE_CHECKING:
    from pathlib import Path


class Settings:
    """Unified settings class that provides backward compatibility.

    This class acts as a bridge between the old settings.py and the new
    layered configuration system, providing the same interface while
    using the new configuration classes internally.
    """

    def __init__(self):
        """Initialize settings with layered configuration."""
        # Create configuration instances
        self.base_config = BaseConfig.from_env()
        self.feature_flags = FeatureFlags.from_env()
        self.path_config = PathConfig.from_env()

        # Validate configuration
        self.is_valid = validate_configuration()

    # Base configuration properties
    @property
    def environment(self) -> str:
        """Get environment setting."""
        return self.base_config.environment

    @property
    def debug(self) -> bool:
        """Get debug setting."""
        return self.base_config.debug

    @property
    def log_level(self) -> str:
        """Get log level setting."""
        return self.base_config.log_level

    @property
    def openai_api_key(self) -> str | None:
        """Get OpenAI API key."""
        return self.base_config.openai_api_key

    @property
    def openrouter_api_key(self) -> str | None:
        """Get OpenRouter API key."""
        return self.base_config.openrouter_api_key

    @property
    def discord_bot_token(self) -> str | None:
        """Get Discord bot token."""
        return self.base_config.discord_bot_token

    @property
    def qdrant_url(self) -> str | None:
        """Get Qdrant URL."""
        return self.base_config.qdrant_url

    @property
    def qdrant_api_key(self) -> str | None:
        """Get Qdrant API key."""
        return self.base_config.qdrant_api_key

    # Path configuration properties
    @property
    def base_dir(self) -> Path:
        """Get base directory."""
        return self.path_config.base_dir

    @property
    def downloads_dir(self) -> Path:
        """Get downloads directory."""
        return self.path_config.downloads_dir

    @property
    def config_dir(self) -> Path:
        """Get config directory."""
        return self.path_config.config_dir

    @property
    def logs_dir(self) -> Path:
        """Get logs directory."""
        return self.path_config.logs_dir

    @property
    def processing_dir(self) -> Path:
        """Get processing directory."""
        return self.path_config.processing_dir

    @property
    def temp_dir(self) -> Path:
        """Get temp directory."""
        return self.path_config.temp_dir

    @property
    def ytdlp_archive(self) -> Path:
        """Get ytdlp archive path."""
        return self.path_config.ytdlp_archive

    @property
    def ytdlp_config(self) -> Path:
        """Get ytdlp config path."""
        return self.path_config.ytdlp_config

    # Feature flags properties
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return self.feature_flags.is_enabled(feature_name)

    def get_enabled_features(self) -> dict[str, bool]:
        """Get all enabled features."""
        return self.feature_flags.get_enabled_flags()

    def get_disabled_features(self) -> dict[str, bool]:
        """Get all disabled features."""
        return self.feature_flags.get_disabled_flags()

    # Backward compatibility methods
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value with backward compatibility."""
        # Check base config first
        if hasattr(self.base_config, key):
            return getattr(self.base_config, key)

        # Check feature flags
        if hasattr(self.feature_flags, key):
            return getattr(self.feature_flags, key)

        # Check path config
        if hasattr(self.path_config, key):
            return getattr(self.path_config, key)

        # Fallback to environment variable
        return os.getenv(key.upper(), default)

    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value."""
        if hasattr(self.base_config, key):
            setattr(self.base_config, key, value)
        elif hasattr(self.feature_flags, key):
            setattr(self.feature_flags, key, value)
        elif hasattr(self.path_config, key):
            setattr(self.path_config, key, value)
        else:
            # Set as environment variable
            os.environ[key.upper()] = str(value)

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary."""
        result = {}

        result.update(self.base_config.to_dict())
        result.update(self.feature_flags.__dict__)
        result.update(
            {
                "base_dir": str(self.path_config.base_dir),
                "downloads_dir": str(self.path_config.downloads_dir),
                "config_dir": str(self.path_config.config_dir),
                "logs_dir": str(self.path_config.logs_dir),
                "processing_dir": str(self.path_config.processing_dir),
                "temp_dir": str(self.path_config.temp_dir),
            }
        )

        return result


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Backward compatibility exports
def _get_setting(key: str, default: str = "") -> str:
    """Get a setting value with backward compatibility."""
    settings = get_settings()
    value = settings.get_setting(key, default)
    return str(value) if value is not None else default


def _get_path_setting(key: str, default_path: Path) -> Path:
    """Get a path setting with backward compatibility."""
    settings = get_settings()
    if key == "crewai_base_dir":
        return settings.base_dir
    elif key == "crewai_downloads_dir":
        return settings.downloads_dir
    elif key == "crewai_config_dir":
        return settings.config_dir
    elif key == "crewai_logs_dir":
        return settings.logs_dir
    elif key == "crewai_processing_dir":
        return settings.processing_dir
    elif key == "crewai_temp_dir":
        return settings.temp_dir
    else:
        return default_path


# Export commonly used settings for backward compatibility
def _export_settings():
    """Export commonly used settings for backward compatibility."""
    settings = get_settings()

    # Export base configuration
    globals().update(
        {
            "ENVIRONMENT": settings.environment,
            "DEBUG": settings.debug,
            "LOG_LEVEL": settings.log_level,
            "OPENAI_API_KEY": settings.openai_api_key,
            "OPENROUTER_API_KEY": settings.openrouter_api_key,
            "DISCORD_BOT_TOKEN": settings.discord_bot_token,
            "QDRANT_URL": settings.qdrant_url,
            "QDRANT_API_KEY": settings.qdrant_api_key,
        }
    )

    # Export paths
    globals().update(
        {
            "BASE_DIR": settings.base_dir,
            "DOWNLOADS_DIR": settings.downloads_dir,
            "CONFIG_DIR": settings.config_dir,
            "LOGS_DIR": settings.logs_dir,
            "PROCESSING_DIR": settings.processing_dir,
            "TEMP_DIR": settings.temp_dir,
            "YTDLP_ARCHIVE": settings.ytdlp_archive,
            "YTDLP_CONFIG": settings.ytdlp_config,
        }
    )

    # Export feature flags
    for flag_name, flag_value in settings.feature_flags.__dict__.items():
        if flag_name.startswith("ENABLE_"):
            globals()[flag_name] = flag_value


# Export settings for backward compatibility
_export_settings()
