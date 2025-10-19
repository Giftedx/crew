"""Main configuration manager that orchestrates loading, validation, and caching."""

from __future__ import annotations

"""Main configuration manager that orchestrates loading, validation, and caching."""

from pathlib import Path
from typing import Any

from .config_cache import ConfigCache, FileWatcher
from .config_loader import ConfigLoader
from .config_schema import GlobalConfig, TenantConfig
from .config_validator import ConfigValidator, ValidationResult


class ConfigManager:
    """Central configuration manager with loading, validation, and caching."""

    def __init__(self, config_dir: Path | None = None, cache_ttl: int = 300):
        """Initialize configuration manager."""
        self.config_dir = config_dir or Path("config")
        self.tenants_dir = Path("tenants")

        # Initialize components
        self.loader = ConfigLoader(self.config_dir)
        self.validator = ConfigValidator()
        self.cache = ConfigCache(cache_ttl)
        self.file_watcher = FileWatcher(self.config_dir, self.cache)

        # Load and validate global configuration
        self._global_config: GlobalConfig | None = None
        self._validation_result: ValidationResult | None = None

    def get_global_config(self, force_reload: bool = False) -> GlobalConfig:
        """Get global configuration with caching and validation."""
        # Check cache first (unless force reload)
        if not force_reload:
            cached_config = self.cache.get_global_config()
            if cached_config is not None:
                return cached_config

        # Check for file changes
        self.file_watcher.check_for_changes()

        # Load configuration
        config = self.loader.load_global_config()

        # Validate configuration
        validation_result = self.validator.validate_global_config(config)

        # Store results
        self._global_config = config
        self._validation_result = validation_result

        # Cache valid configuration
        if validation_result.is_valid:
            self.cache.set_global_config(config)

        return config

    def get_tenant_config(self, tenant_id: str, force_reload: bool = False) -> TenantConfig | None:
        """Get tenant configuration with caching and validation."""
        # Check cache first (unless force reload)
        if not force_reload:
            cached_config = self.cache.get_tenant_config(tenant_id)
            if cached_config is not None:
                return cached_config

        # Load configuration
        config = self.loader.load_tenant_config(tenant_id)
        if config is None:
            return None

        # Validate configuration
        validation_result = self.validator.validate_tenant_config(config)

        # Cache valid configuration
        if validation_result.is_valid:
            self.cache.set_tenant_config(tenant_id, config)

        return config

    def get_config_section(self, section: str, tenant_id: str | None = None) -> Any:
        """Get specific configuration section."""
        if tenant_id:
            # Get tenant-specific configuration
            tenant_config = self.get_tenant_config(tenant_id)
            if tenant_config is None:
                return None

            # Check for tenant overrides first
            override_map = {
                "routing": tenant_config.routing_overrides,
                "budget": tenant_config.budget_overrides,
                "policy": tenant_config.policy_overrides,
                "security": tenant_config.security_overrides,
            }

            if section in override_map and override_map[section] is not None:
                return override_map[section]

        # Get from global configuration
        global_config = self.get_global_config()
        return getattr(global_config, section, None)

    def validate_configuration(self) -> ValidationResult:
        """Validate current configuration."""
        if self._validation_result is None:
            # Force reload to get fresh validation
            self.get_global_config(force_reload=True)

        return self._validation_result or ValidationResult(True, [], [])

    def get_validation_errors(self) -> list[str]:
        """Get list of validation errors."""
        result = self.validate_configuration()
        return [f"{error.section}.{error.field}: {error.message}" for error in result.errors]

    def get_validation_warnings(self) -> list[str]:
        """Get list of validation warnings."""
        result = self.validate_configuration()
        return [f"{error.section}.{error.field}: {error.message}" for error in result.warnings]

    def is_configuration_valid(self) -> bool:
        """Check if current configuration is valid."""
        return self.validate_configuration().is_valid

    def reload_configuration(self) -> GlobalConfig:
        """Force reload configuration from files."""
        # Invalidate cache
        self.cache.invalidate()

        # Force reload
        return self.get_global_config(force_reload=True)

    def get_available_tenants(self) -> list[str]:
        """Get list of available tenant IDs."""
        if not self.tenants_dir.exists():
            return []

        tenant_dirs = [d.name for d in self.tenants_dir.iterdir() if d.is_dir()]
        return sorted(tenant_dirs)

    def create_tenant_config(self, tenant_id: str, config_data: dict[str, Any]) -> bool:
        """Create new tenant configuration."""
        tenant_dir = self.tenants_dir / tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)

        # Create tenant.yaml
        tenant_file = tenant_dir / "tenant.yaml"
        import yaml

        with open(tenant_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False)

        # Invalidate cache
        self.cache.invalidate_tenant_cache(tenant_id)

        return True

    def update_tenant_config(self, tenant_id: str, section: str, config_data: dict[str, Any]) -> bool:
        """Update tenant configuration section."""
        tenant_dir = self.tenants_dir / tenant_id
        if not tenant_dir.exists():
            return False

        # Determine file name based on section
        file_map = {
            "routing": "routing.yaml",
            "budget": "budgets.yaml",
            "policy": "policy_overrides.yaml",
            "security": "security_overrides.yaml",
        }

        if section not in file_map:
            return False

        config_file = tenant_dir / file_map[section]

        import yaml

        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False)

        # Invalidate cache
        self.cache.invalidate_tenant_cache(tenant_id)

        return True

    def get_config_summary(self) -> dict[str, Any]:
        """Get configuration summary for debugging/monitoring."""
        global_config = self.get_global_config()
        validation_result = self.validate_configuration()
        cache_stats = self.cache.get_cache_stats()
        available_tenants = self.get_available_tenants()

        return {
            "service_name": global_config.service_name,
            "environment": global_config.environment,
            "version": global_config.version,
            "is_valid": validation_result.is_valid,
            "error_count": len(validation_result.errors),
            "warning_count": len(validation_result.warnings),
            "cache_stats": cache_stats,
            "available_tenants": available_tenants,
            "config_dir": str(self.config_dir),
            "tenants_dir": str(self.tenants_dir),
        }

    def get_feature_flags(self, tenant_id: str | None = None) -> dict[str, bool]:
        """Get feature flags for tenant or global."""
        global_config = self.get_global_config()

        # Start with global feature flags
        flags = {
            "enable_api": global_config.enable_api,
            "enable_tracing": global_config.enable_tracing,
            "enable_metrics": global_config.enable_metrics,
            "enable_dashboard": global_config.enable_dashboard,
            "enable_content_moderation": global_config.security.enable_content_moderation,
            "enable_pii_detection": global_config.security.enable_pii_detection,
            "youtube_enabled": global_config.ingest.youtube_enabled,
            "twitch_enabled": global_config.ingest.twitch_enabled,
            "tiktok_enabled": global_config.ingest.tiktok_enabled,
            "reddit_enabled": global_config.ingest.reddit_enabled,
        }

        # Apply tenant-specific overrides if available
        if tenant_id:
            tenant_config = self.get_tenant_config(tenant_id)
            if tenant_config and tenant_config.security_overrides:
                tenant_flags = tenant_config.security_overrides.get("feature_flags", {})
                flags.update(tenant_flags)

        return flags

    def is_feature_enabled(self, feature: str, tenant_id: str | None = None) -> bool:
        """Check if a feature is enabled for tenant or globally."""
        flags = self.get_feature_flags(tenant_id)
        return flags.get(feature, False)
