"""Unified configuration loader for the Ultimate Discord Intelligence Bot.

This module provides a single, simplified interface for all configuration
needs with clear precedence and comprehensive validation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class UnifiedConfig:
    """Unified configuration with clear precedence and validation.

    Configuration precedence (highest to lowest):
    1. Environment variables
    2. .env file
    3. Default values
    """

    # =============================================================================
    # CORE APPLICATION SETTINGS
    # =============================================================================

    # Environment
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # API Keys
    openai_api_key: str | None = None
    openrouter_api_key: str | None = None
    discord_bot_token: str | None = None

    # Database
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None

    # =============================================================================
    # FEATURE FLAGS (ENABLE_* pattern)
    # =============================================================================

    # Core Features
    enable_langgraph_pipeline: bool = False
    enable_unified_knowledge: bool = False
    enable_mem0_memory: bool = False
    enable_dspy_optimization: bool = False

    # Analysis Features
    enable_debate_analysis: bool = True
    enable_fact_checking: bool = True
    enable_sentiment_analysis: bool = True
    enable_bias_detection: bool = True

    # Memory Features
    enable_vector_memory: bool = True
    enable_graph_memory: bool = False
    enable_memory_compaction: bool = True
    enable_memory_ttl: bool = False

    # Performance Features
    enable_caching: bool = True
    enable_lazy_loading: bool = False
    enable_parallel_processing: bool = True
    enable_optimization: bool = True

    # Integration Features
    enable_discord_integration: bool = True
    enable_youtube_integration: bool = True
    enable_twitch_integration: bool = True
    enable_tiktok_integration: bool = True

    # Monitoring Features
    enable_metrics: bool = True
    enable_logging: bool = True
    enable_tracing: bool = False

    # =============================================================================
    # PERFORMANCE SETTINGS
    # =============================================================================

    max_workers: int = 4
    request_timeout: int = 30
    max_retries: int = 3
    cache_ttl: int = 3600

    # =============================================================================
    # PATH CONFIGURATION
    # =============================================================================

    base_dir: Path = field(default_factory=lambda: Path.cwd())
    data_dir: Path = field(default_factory=lambda: Path.cwd() / "data")
    logs_dir: Path = field(default_factory=lambda: Path.cwd() / "logs")
    cache_dir: Path = field(default_factory=lambda: Path.cwd() / "cache")

    # =============================================================================
    # CUSTOM SETTINGS
    # =============================================================================

    custom_settings: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> UnifiedConfig:
        """Create configuration from environment variables with precedence."""
        config = cls()

        # Load from environment variables
        for field_name, field_info in config.__dataclass_fields__.items():
            if field_name == "custom_settings":
                continue

            # Convert field name to environment variable name
            env_var = field_name.upper()

            # Get value from environment
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert to appropriate type
                field_type = field_info.type
                if field_type == bool:
                    value = env_value.lower() in ("true", "1", "yes", "on")
                elif field_type == int:
                    value = int(env_value)
                elif field_type == str:
                    value = env_value
                elif hasattr(field_type, "__origin__") and field_type.__origin__ is type(None):
                    # Optional type
                    value = env_value or None
                else:
                    value = env_value

                setattr(config, field_name, value)

        # Validate configuration
        config.validate()

        return config

    def validate(self) -> None:
        """Validate configuration settings."""
        errors = []

        # Validate required settings
        if not self.openai_api_key and not self.openrouter_api_key:
            errors.append("Either OPENAI_API_KEY or OPENROUTER_API_KEY must be set")

        if self.enable_discord_integration and not self.discord_bot_token:
            errors.append("DISCORD_BOT_TOKEN is required when Discord integration is enabled")

        if self.enable_vector_memory and not self.qdrant_url:
            errors.append("QDRANT_URL is required when vector memory is enabled")

        # Validate numeric settings
        if self.max_workers < 1:
            errors.append("max_workers must be at least 1")

        if self.request_timeout < 1:
            errors.append("request_timeout must be at least 1")

        if self.max_retries < 0:
            errors.append("max_retries must be non-negative")

        # Validate paths
        for path_field in ["base_dir", "data_dir", "logs_dir", "cache_dir"]:
            path = getattr(self, path_field)
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create {path_field}: {e}")

        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

    def get_feature_flag(self, flag_name: str) -> bool:
        """Get a feature flag value by name."""
        # Convert flag name to attribute name
        attr_name = flag_name.lower().replace("ENABLE_", "enable_")
        return getattr(self, attr_name, False)

    def set_feature_flag(self, flag_name: str, value: bool) -> None:
        """Set a feature flag value."""
        attr_name = flag_name.lower().replace("ENABLE_", "enable_")
        setattr(self, attr_name, value)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {}
        for field_name, _field_info in self.__dataclass_fields__.items():
            value = getattr(self, field_name)
            if field_name == "custom_settings":
                result.update(value)
            else:
                result[field_name] = value
        return result

    def __str__(self) -> str:
        """String representation of configuration."""
        return f"UnifiedConfig(environment={self.environment}, debug={self.debug})"


# Global configuration instance
_config: UnifiedConfig | None = None


def get_config() -> UnifiedConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = UnifiedConfig.from_env()
    return _config


def reload_config() -> UnifiedConfig:
    """Reload configuration from environment."""
    global _config
    _config = UnifiedConfig.from_env()
    return _config


# Backward compatibility
def get_settings() -> UnifiedConfig:
    """Backward compatibility alias for get_config."""
    return get_config()
