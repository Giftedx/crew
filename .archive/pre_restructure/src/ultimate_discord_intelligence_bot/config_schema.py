"""Pydantic configuration schema with validation for the Ultimate Discord Intelligence Bot.

This module provides comprehensive configuration validation using Pydantic,
ensuring all environment variables and settings are properly validated at startup.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    qdrant_url: str = Field(default="", description="Qdrant vector database URL")
    qdrant_api_key: str = Field(default="", description="Qdrant API key")
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL for caching")

    @validator("qdrant_url")
    def validate_qdrant_url(cls, v: str) -> str:
        """Validate Qdrant URL format."""
        if v and not v.startswith(("http://", "https://", "qdrant://", ":memory:")):
            raise ValueError("Qdrant URL must start with http://, https://, qdrant://, or :memory:")
        return v


class DiscordConfig(BaseSettings):
    """Discord bot configuration."""

    bot_token: str = Field(default="", description="Discord bot token")
    webhook_url: str = Field(default="", description="Discord webhook URL")
    private_webhook_url: str = Field(default="", description="Private Discord webhook URL")

    @validator("bot_token")
    def validate_bot_token(cls, v: str) -> str:
        """Validate Discord bot token format."""
        if v and not v.startswith("Bot "):
            raise ValueError("Discord bot token must start with 'Bot '")
        return v


class LLMConfig(BaseSettings):
    """LLM service configuration."""

    openai_api_key: str = Field(default="", description="OpenAI API key")
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")

    # Model routing configuration
    default_model: str = Field(default="gpt-4o", description="Default LLM model")
    max_tokens: int = Field(default=4096, ge=1, le=128000, description="Maximum tokens per request")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Model temperature")

    # Cost tracking
    max_daily_cost: float = Field(default=100.0, ge=0.0, description="Maximum daily cost in USD")
    cost_alert_threshold: float = Field(default=80.0, ge=0.0, le=100.0, description="Cost alert threshold percentage")


class PathConfig(BaseSettings):
    """Path configuration for directories and files."""

    base_dir: Path = Field(default=Path.home() / "crew_data", description="Base directory for data")
    downloads_dir: Path = Field(default_factory=lambda: Path.home() / "crew_data" / "Downloads")
    config_dir: Path = Field(default_factory=lambda: Path.home() / "crew_data" / "Config")
    logs_dir: Path = Field(default_factory=lambda: Path.home() / "crew_data" / "Logs")
    processing_dir: Path = Field(default_factory=lambda: Path.home() / "crew_data" / "Processing")
    temp_dir: Path = Field(default_factory=lambda: Path.home() / "crew_data" / "Downloads" / "temp")

    # yt-dlp paths
    ytdlp_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "yt-dlp")
    ytdlp_config: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent / "yt-dlp" / "config" / "crewai-system.conf"
    )
    ytdlp_archive: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent / "yt-dlp" / "archives" / "crewai_downloads.txt"
    )

    # Google credentials
    google_credentials: Path = Field(
        default_factory=lambda: Path.home() / "crew_data" / "Config" / "google-credentials.json"
    )

    @validator("base_dir", "downloads_dir", "config_dir", "logs_dir", "processing_dir", "temp_dir")
    def ensure_directories_exist(cls, v: Path) -> Path:
        """Ensure directories exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v


class FeatureFlags(BaseSettings):
    """Feature flags for enabling/disabling functionality."""

    # Phase 1 Enhancement Flags
    enable_mem0_memory: bool = Field(default=False, description="Enable Mem0 memory system")
    enable_dspy_optimization: bool = Field(default=False, description="Enable DSPy optimization")
    enable_langgraph_pipeline: bool = Field(default=False, description="Enable LangGraph pipeline")

    # Phase 2 Enhancement Flags
    enable_hierarchical_orchestration: bool = Field(default=False, description="Enable hierarchical orchestration")
    enable_rl_model_routing: bool = Field(default=False, description="Enable RL model routing")
    enable_websocket_updates: bool = Field(default=False, description="Enable WebSocket updates")
    enable_enterprise_tenant_management: bool = Field(default=False, description="Enable enterprise tenant management")

    # Unified Knowledge Layer Flags
    enable_unified_knowledge: bool = Field(default=False, description="Enable unified knowledge layer")
    enable_unified_cache: bool = Field(default=False, description="Enable unified cache system")
    enable_unified_router: bool = Field(default=False, description="Enable unified router system")
    enable_unified_orchestration: bool = Field(default=False, description="Enable unified orchestration")

    # Unified Router System Flags
    enable_unified_cost_tracking: bool = Field(default=False, description="Enable unified cost tracking")

    # Unified Cache System Flags
    enable_cache_optimization: bool = Field(default=False, description="Enable cache optimization")

    # Unified Orchestration System Flags
    enable_task_management: bool = Field(default=False, description="Enable task management")

    # Performance and Monitoring Flags
    enable_performance_monitoring: bool = Field(default=True, description="Enable performance monitoring")
    enable_debug_logging: bool = Field(default=False, description="Enable debug logging")
    enable_metrics_collection: bool = Field(default=True, description="Enable metrics collection")

    # Security Flags
    enable_input_validation: bool = Field(default=True, description="Enable input validation")
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    enable_security_scanning: bool = Field(default=True, description="Enable security scanning")


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format string"
    )
    log_file: Path = Field(default_factory=lambda: Path.home() / "crew_data" / "Logs" / "bot.log")
    max_log_size: int = Field(default=10 * 1024 * 1024, ge=1024, description="Maximum log file size in bytes")
    backup_count: int = Field(default=5, ge=1, description="Number of backup log files to keep")


class SecurityConfig(BaseSettings):
    """Security configuration."""

    secret_key: str = Field(default="", description="Secret key for encryption")
    jwt_secret: str = Field(default="", description="JWT secret key")
    encryption_key: str = Field(default="", description="Encryption key for sensitive data")

    # Rate limiting
    rate_limit_requests_per_minute: int = Field(default=60, ge=1, description="Rate limit requests per minute")
    rate_limit_burst_allowance: int = Field(default=10, ge=0, description="Rate limit burst allowance")

    # Input validation
    max_input_length: int = Field(default=10000, ge=1, description="Maximum input length")
    max_file_size: int = Field(default=100 * 1024 * 1024, ge=1024, description="Maximum file size in bytes")

    @validator("secret_key", "jwt_secret", "encryption_key")
    def validate_secrets(cls, v: str) -> str:
        """Validate secret keys are not empty in production."""
        if not v and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("Secret keys must be set in production environment")
        return v


class UltimateDiscordIntelligenceBotConfig(BaseSettings):
    """Main configuration class for the Ultimate Discord Intelligence Bot."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    # Sub-configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    paths: PathConfig = Field(default_factory=PathConfig)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # Environment
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Environment"
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    @validator("environment")
    def validate_environment(cls, v: str) -> str:
        """Validate environment setting."""
        if v not in ["development", "staging", "production"]:
            raise ValueError("Environment must be one of: development, staging, production")
        return v

    def validate_required_settings(self) -> list[str]:
        """Validate that all required settings are present."""
        errors = []

        # Check required API keys
        if not self.discord.bot_token:
            errors.append("Discord bot token is required")

        if not self.llm.openai_api_key and not self.llm.openrouter_api_key:
            errors.append("Either OpenAI or OpenRouter API key is required")

        # Check required URLs
        if not self.database.qdrant_url:
            errors.append("Qdrant URL is required")

        # Check production requirements
        if self.environment == "production":
            if not self.security.secret_key:
                errors.append("Secret key is required in production")
            if not self.security.jwt_secret:
                errors.append("JWT secret is required in production")

        return errors

    def get_feature_flag(self, flag_name: str) -> bool:
        """Get a feature flag value."""
        return getattr(self.features, flag_name, False)

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


def get_config() -> UltimateDiscordIntelligenceBotConfig:
    """Get the application configuration."""
    return UltimateDiscordIntelligenceBotConfig()


def validate_config() -> tuple[UltimateDiscordIntelligenceBotConfig, list[str]]:
    """Validate configuration and return config with any errors."""
    config = get_config()
    errors = config.validate_required_settings()
    return config, errors


def print_config_summary(config: UltimateDiscordIntelligenceBotConfig) -> None:
    """Print a summary of the current configuration."""
    print("🔧 Ultimate Discord Intelligence Bot Configuration")
    print("=" * 50)
    print(f"Environment: {config.environment}")
    print(f"Debug Mode: {config.debug}")
    print(f"Base Directory: {config.paths.base_dir}")
    print(f"Log Level: {config.logging.log_level}")
    print()

    print("🔑 API Keys Status:")
    print(f"  Discord Bot Token: {'✅ Set' if config.discord.bot_token else '❌ Missing'}")
    print(f"  OpenAI API Key: {'✅ Set' if config.llm.openai_api_key else '❌ Missing'}")
    print(f"  OpenRouter API Key: {'✅ Set' if config.llm.openrouter_api_key else '❌ Missing'}")
    print(f"  Anthropic API Key: {'✅ Set' if config.llm.anthropic_api_key else '❌ Missing'}")
    print()

    print("🗄️ Database Status:")
    print(f"  Qdrant URL: {'✅ Set' if config.database.qdrant_url else '❌ Missing'}")
    print(f"  Redis URL: {config.database.redis_url}")
    print()

    print("🚩 Feature Flags:")
    enabled_flags = [name for name, value in config.features.__dict__.items() if value]
    if enabled_flags:
        for flag in enabled_flags:
            print(f"  ✅ {flag}")
    else:
        print("  No feature flags enabled")
    print()


if __name__ == "__main__":
    """Run configuration validation when executed directly."""
    config, errors = validate_config()

    if errors:
        print("❌ Configuration Validation Failed:")
        for error in errors:
            print(f"  • {error}")
        print()
        print("Please set the required environment variables or update your .env file.")
        exit(1)
    else:
        print("✅ Configuration Validation Passed")
        print_config_summary(config)
