"""Configuration factory for creating and managing configuration instances."""

from __future__ import annotations

"""Configuration factory for creating and managing configuration instances."""

from pathlib import Path
from typing import Any

from .config_manager import ConfigManager
from .config_schema import GlobalConfig, TenantConfig


class ConfigFactory:
    """Factory for creating configuration instances with different strategies."""

    _instance: ConfigManager | None = None
    _initialized = False

    @classmethod
    def get_instance(cls, config_dir: Path | None = None, cache_ttl: int = 300) -> ConfigManager:
        """Get singleton configuration manager instance."""
        if cls._instance is None or not cls._initialized:
            cls._instance = ConfigManager(config_dir, cache_ttl)
            cls._initialized = True
        return cls._instance

    @classmethod
    def create_fresh_instance(cls, config_dir: Path | None = None, cache_ttl: int = 300) -> ConfigManager:
        """Create a fresh configuration manager instance."""
        return ConfigManager(config_dir, cache_ttl)

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (useful for testing)."""
        cls._instance = None
        cls._initialized = False

    @classmethod
    def create_from_dict(cls, config_data: dict[str, Any]) -> GlobalConfig:
        """Create GlobalConfig from dictionary data."""
        # This would be used for testing or dynamic configuration
        # Implementation would map dictionary keys to GlobalConfig attributes
        return GlobalConfig()

    @classmethod
    def create_minimal_config(cls) -> GlobalConfig:
        """Create minimal valid configuration for testing."""
        return GlobalConfig(
            service_name="test-service", environment="test", discord_bot_token="test-token", openai_api_key="test-key"
        )

    @classmethod
    def create_production_config(cls) -> GlobalConfig:
        """Create production-ready configuration template."""
        config = GlobalConfig(
            service_name="ultimate-discord-intelligence-bot",
            environment="production",
            enable_api=True,
            enable_tracing=True,
            enable_metrics=True,
            enable_dashboard=True,
        )

        # Set production-specific defaults
        config.monitoring.target_bypass_rate = 0.65
        config.monitoring.target_quality_score = 0.80
        config.routing.strategy = "cost_optimized"
        config.security.enable_content_moderation = True
        config.security.enable_pii_detection = True

        return config

    @classmethod
    def create_development_config(cls) -> GlobalConfig:
        """Create development configuration template."""
        config = GlobalConfig(
            service_name="ultimate-discord-intelligence-bot-dev",
            environment="dev",
            enable_api=False,
            enable_tracing=False,
            enable_metrics=True,
            enable_dashboard=False,
        )

        # Set development-specific defaults
        config.monitoring.target_bypass_rate = 0.50
        config.monitoring.target_quality_score = 0.70
        config.routing.strategy = "performance"
        config.security.enable_content_moderation = False
        config.security.enable_pii_detection = False

        return config

    @classmethod
    def create_tenant_template(cls, tenant_id: str, name: str) -> TenantConfig:
        """Create tenant configuration template."""
        return TenantConfig(
            tenant_id=tenant_id,
            name=name,
            status="active",
            workspaces={
                "default": {
                    "name": "Default Workspace",
                    "description": "Default workspace for tenant",
                    "routing": {"allowed_models": ["anthropic/claude-3-sonnet", "openai/gpt-4"]},
                }
            },
        )


# Convenience functions for common operations
def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    return ConfigFactory.get_instance()


def get_global_config() -> GlobalConfig:
    """Get global configuration."""
    return ConfigFactory.get_instance().get_global_config()


def get_tenant_config(tenant_id: str) -> TenantConfig | None:
    """Get tenant configuration."""
    return ConfigFactory.get_instance().get_tenant_config(tenant_id)


def get_config_section(section: str, tenant_id: str | None = None) -> Any:
    """Get configuration section."""
    return ConfigFactory.get_instance().get_config_section(section, tenant_id)


def is_feature_enabled(feature: str, tenant_id: str | None = None) -> bool:
    """Check if feature is enabled."""
    return ConfigFactory.get_instance().is_feature_enabled(feature, tenant_id)


def get_feature_flags(tenant_id: str | None = None) -> dict[str, bool]:
    """Get feature flags."""
    return ConfigFactory.get_instance().get_feature_flags(tenant_id)


def validate_configuration() -> bool:
    """Validate current configuration."""
    return ConfigFactory.get_instance().is_configuration_valid()


def reload_configuration() -> GlobalConfig:
    """Reload configuration from files."""
    return ConfigFactory.get_instance().reload_configuration()
