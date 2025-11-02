"""Base configuration with validation and type safety."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


# Import validation error class
class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field


@dataclass
class BaseConfig:
    """Base configuration with validation and type safety.

    Provides a foundation for all configuration classes with common
    validation patterns and type safety guarantees.
    """

    # Environment and runtime settings
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # API and service settings
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.7
    openrouter_api_key: str | None = None
    discord_bot_token: str | None = None

    # Database and storage settings
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None

    # Performance settings
    max_workers: int = 4
    request_timeout: int = 30
    max_retries: int = 3

    # Custom settings
    custom_settings: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate configuration values."""
        # Validate environment
        if self.environment not in ["development", "staging", "production"]:
            raise ConfigValidationError(
                f"Invalid environment: {self.environment}. Must be one of: development, staging, production"
            )

        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ConfigValidationError(
                f"Invalid log level: {self.log_level}. Must be one of: {', '.join(valid_log_levels)}"
            )

        # Validate numeric settings
        if self.max_workers < 1:
            raise ConfigValidationError("max_workers must be >= 1")

        if self.request_timeout < 1:
            raise ConfigValidationError("request_timeout must be >= 1")

        if self.max_retries < 0:
            raise ConfigValidationError("max_retries must be >= 0")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting with fallback to default."""
        return getattr(self, key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """Set a configuration setting."""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self.custom_settings[key] = value

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                result[key] = value
        return result

    @classmethod
    def from_env(cls) -> BaseConfig:
        """Create configuration from environment variables."""
        return cls(
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")),
            openai_temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            discord_bot_token=os.getenv("DISCORD_BOT_TOKEN"),
            qdrant_url=os.getenv("QDRANT_URL"),
            qdrant_api_key=os.getenv("QDRANT_API_KEY"),
            max_workers=int(os.getenv("MAX_WORKERS", "4")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
        )
