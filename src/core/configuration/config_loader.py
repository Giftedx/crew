"""Configuration loader with support for YAML files and environment variables."""

from __future__ import annotations

"""Configuration loader with support for YAML files and environment variables."""

import os
from pathlib import Path
from typing import Any

import yaml

from .config_schema import (
    ArchiveConfig,
    DeprecationsConfig,
    GlobalConfig,
    GroundingConfig,
    IngestConfig,
    MonitoringConfig,
    PolicyConfig,
    PollerConfig,
    ProfilesConfig,
    RoutingConfig,
    SecurityConfig,
    TenantConfig,
)


class ConfigLoader:
    """Loads configuration from YAML files and environment variables."""

    def __init__(self, config_dir: Path | None = None):
        """Initialize config loader with optional config directory."""
        self.config_dir = config_dir or Path("config")
        self.tenants_dir = Path("tenants")

    def load_global_config(self) -> GlobalConfig:
        """Load global configuration from files and environment."""
        # Start with default configuration
        config = GlobalConfig()

        # Load from YAML files if they exist
        config = self._load_config_sections(config)

        # Apply environment variable overrides
        config = self._apply_env_overrides(config)

        return config

    def load_tenant_config(self, tenant_id: str) -> TenantConfig | None:
        """Load tenant-specific configuration."""
        tenant_dir = self.tenants_dir / tenant_id
        if not tenant_dir.exists():
            return None

        # Load tenant metadata
        tenant_file = tenant_dir / "tenant.yaml"
        if not tenant_file.exists():
            return None

        tenant_data = self._load_yaml_file(tenant_file) or {}

        # Load tenant-specific overrides
        routing_overrides = self._load_yaml_file(tenant_dir / "routing.yaml")
        budget_overrides = self._load_yaml_file(tenant_dir / "budgets.yaml")
        policy_overrides = self._load_yaml_file(tenant_dir / "policy_overrides.yaml")
        security_overrides = self._load_yaml_file(
            tenant_dir / "security_overrides.yaml"
        )

        return TenantConfig(
            tenant_id=tenant_id,
            name=tenant_data.get("name", tenant_id),
            status=tenant_data.get("status", "active"),
            routing_overrides=routing_overrides,
            budget_overrides=budget_overrides,
            policy_overrides=policy_overrides,
            security_overrides=security_overrides,
            workspaces=tenant_data.get("workspaces", {}),
        )

    def _load_config_sections(self, config: GlobalConfig) -> GlobalConfig:
        """Load configuration sections from YAML files."""
        # Load routing configuration
        routing_data = self._load_yaml_file(self.config_dir / "routing.yaml")
        if routing_data:
            config.routing = self._dict_to_routing_config(routing_data)

        # Load security configuration
        security_data = self._load_yaml_file(self.config_dir / "security.yaml")
        if security_data:
            config.security = self._dict_to_security_config(security_data)

        # Load monitoring configuration
        monitoring_data = self._load_yaml_file(self.config_dir / "monitoring.yaml")
        if monitoring_data:
            config.monitoring = self._dict_to_monitoring_config(monitoring_data)

        # Load ingest configuration
        ingest_data = self._load_yaml_file(self.config_dir / "ingest.yaml")
        if ingest_data:
            config.ingest = self._dict_to_ingest_config(ingest_data)

        # Load policy configuration
        policy_data = self._load_yaml_file(self.config_dir / "policy.yaml")
        if policy_data:
            config.policy = self._dict_to_policy_config(policy_data)

        # Load archive configuration
        archive_data = self._load_yaml_file(self.config_dir / "archive_routes.yaml")
        if archive_data:
            config.archive = self._dict_to_archive_config(archive_data)

        # Load poller configuration
        poller_data = self._load_yaml_file(self.config_dir / "poller.yaml")
        if poller_data:
            config.poller = self._dict_to_poller_config(poller_data)

        # Load grounding configuration
        grounding_data = self._load_yaml_file(self.config_dir / "grounding.yaml")
        if grounding_data:
            config.grounding = self._dict_to_grounding_config(grounding_data)

        # Load profiles configuration
        profiles_data = self._load_yaml_file(self.config_dir / "profiles.yaml")
        if profiles_data:
            config.profiles = self._dict_to_profiles_config(profiles_data)

        # Load deprecations configuration
        deprecations_data = self._load_yaml_file(self.config_dir / "deprecations.yaml")
        if deprecations_data:
            config.deprecations = self._dict_to_deprecations_config(deprecations_data)

        return config

    def _apply_env_overrides(self, config: GlobalConfig) -> GlobalConfig:
        """Apply environment variable overrides to configuration."""
        # Override routing settings
        if env_val := os.getenv("ROUTING_STRATEGY"):
            config.routing.strategy = env_val
        if env_val := os.getenv("DEFAULT_MODEL"):
            config.routing.default_model = env_val
        if env_val := os.getenv("MAX_COST_PER_REQUEST"):
            config.routing.max_cost_per_request = float(env_val)

        # Override security settings
        if env_val := os.getenv("ENABLE_CONTENT_MODERATION"):
            config.security.enable_content_moderation = env_val.lower() in (
                "true",
                "1",
                "yes",
            )
        if env_val := os.getenv("ENABLE_PII_DETECTION"):
            config.security.enable_pii_detection = env_val.lower() in (
                "true",
                "1",
                "yes",
            )

        # Override monitoring settings
        if env_val := os.getenv("TARGET_BYPASS_RATE"):
            config.monitoring.target_bypass_rate = float(env_val)
        if env_val := os.getenv("TARGET_QUALITY_SCORE"):
            config.monitoring.target_quality_score = float(env_val)

        # Override ingest settings
        if env_val := os.getenv("YOUTUBE_ENABLED"):
            config.ingest.youtube_enabled = env_val.lower() in ("true", "1", "yes")
        if env_val := os.getenv("TWITCH_ENABLED"):
            config.ingest.twitch_enabled = env_val.lower() in ("true", "1", "yes")
        if env_val := os.getenv("MAX_CHARS_PER_CHUNK"):
            config.ingest.max_chars_per_chunk = int(env_val)

        return config

    def _load_yaml_file(self, file_path: Path) -> dict[str, Any] | None:
        """Load and parse a YAML file."""
        if not file_path.exists():
            return None

        try:
            with open(file_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load config file {file_path}: {e}")
            return None

    def _dict_to_routing_config(self, data: dict[str, Any]) -> RoutingConfig:
        """Convert dictionary to RoutingConfig."""
        return RoutingConfig(
            default_model=data.get("models", {}).get(
                "default", "anthropic/claude-3-sonnet"
            ),
            debate_model=data.get("models", {}).get("debate", "openai/gpt-4"),
            summarization_model=data.get("models", {}).get(
                "summarization", "anthropic/claude-3-haiku"
            ),
            code_model=data.get("models", {}).get("code", "anthropic/claude-3-sonnet"),
            creative_model=data.get("models", {}).get("creative", "openai/gpt-4"),
            strategy=data.get("routing", {}).get("strategy", "cost_optimized"),
            fallback_enabled=data.get("routing", {}).get("fallback_enabled", True),
            retry_attempts=data.get("routing", {}).get("retry_attempts", 3),
            default_context_window=data.get("context_limits", {}).get("default", 32000),
            long_context_window=data.get("context_limits", {}).get(
                "long_context", 128000
            ),
            max_cost_per_request=data.get("budgets", {})
            .get("limits", {})
            .get("max_per_request", 5.00),
            cost_alert_threshold=data.get("budgets", {})
            .get("tracking", {})
            .get("alert_thresholds", [0.8])[0],
        )

    def _dict_to_security_config(self, data: dict[str, Any]) -> SecurityConfig:
        """Convert dictionary to SecurityConfig."""
        return SecurityConfig(
            role_permissions=data.get("role_permissions", {}),
            default_rate_limit=data.get("rate_limits", {}).get(
                "default_per_minute", 60
            ),
            rate_limit_scopes=data.get("rate_limits", {}).get("scopes", {}),
            enable_content_moderation=data.get("enable_content_moderation", True),
            enable_pii_detection=data.get("enable_pii_detection", True),
            pii_types=data.get("pii_types", {}),
            pii_masks=data.get("masks", {}),
        )

    def _dict_to_monitoring_config(self, data: dict[str, Any]) -> MonitoringConfig:
        """Convert dictionary to MonitoringConfig."""
        overall_metrics = data.get("overall_metrics", {})
        return MonitoringConfig(
            target_bypass_rate=overall_metrics.get("bypass_rate", {}).get(
                "target", 0.60
            ),
            target_early_exit_rate=overall_metrics.get("early_exit_rate", {}).get(
                "target", 0.40
            ),
            target_avg_time_savings=overall_metrics.get("avg_time_savings", {}).get(
                "target", 0.70
            ),
            target_quality_score=overall_metrics.get("quality_score_avg", {}).get(
                "target", 0.75
            ),
            warning_bypass_rate_low=overall_metrics.get("bypass_rate", {}).get(
                "warning_low", 0.50
            ),
            critical_bypass_rate_low=overall_metrics.get("bypass_rate", {}).get(
                "critical_low", 0.40
            ),
            warning_bypass_rate_high=overall_metrics.get("bypass_rate", {}).get(
                "warning_high", 0.80
            ),
            dashboard_refresh_interval=data.get("monitoring_intervals", {}).get(
                "dashboard_refresh", 30
            ),
            metrics_aggregation_interval=data.get("monitoring_intervals", {}).get(
                "metrics_aggregation", 3600
            ),
            alert_check_interval=data.get("monitoring_intervals", {}).get(
                "alert_check", 300
            ),
            quality_trends_retention=data.get("data_retention", {}).get(
                "quality_trends", 168
            ),
            detailed_metrics_retention=data.get("data_retention", {}).get(
                "detailed_metrics", 48
            ),
            warning_cooldown=data.get("alert_cooldown", {}).get("warning", 1800),
            critical_cooldown=data.get("alert_cooldown", {}).get("critical", 600),
        )

    def _dict_to_ingest_config(self, data: dict[str, Any]) -> IngestConfig:
        """Convert dictionary to IngestConfig."""
        return IngestConfig(
            youtube_enabled=data.get("youtube", {}).get("enabled", True),
            twitch_enabled=data.get("twitch", {}).get("enabled", True),
            tiktok_enabled=data.get("tiktok", {}).get("enabled", True),
            reddit_enabled=data.get("reddit", {}).get("enabled", True),
            max_chars_per_chunk=data.get("chunk", {}).get("max_chars", 800),
            chunk_overlap=data.get("chunk", {}).get("overlap", 200),
            min_content_length=data.get("min_content_length", 100),
            max_content_length=data.get("max_content_length", 1000000),
            max_concurrent_downloads=data.get("max_concurrent_downloads", 5),
            download_timeout=data.get("download_timeout", 300),
            retry_attempts=data.get("retry_attempts", 3),
        )

    def _dict_to_policy_config(self, data: dict[str, Any]) -> PolicyConfig:
        """Convert dictionary to PolicyConfig."""
        return PolicyConfig(
            allowed_sources=data.get("allowed_sources", {}),
            forbidden_types=data.get("forbidden_types", []),
            retention_days=data.get("retention_days", 30),
            auto_cleanup=data.get("auto_cleanup", True),
            require_explicit_consent=data.get("require_explicit_consent", True),
            consent_expiry_days=data.get("consent_expiry_days", 365),
            per_command_policies=data.get("per_command", {}),
        )

    def _dict_to_archive_config(self, data: dict[str, Any]) -> ArchiveConfig:
        """Convert dictionary to ArchiveConfig."""
        return ArchiveConfig(
            max_retries=data.get("defaults", {}).get("max_retries", 3),
            chunking_enabled=data.get("defaults", {}).get("chunking", True),
            routes=data.get("routes", {}),
            per_tenant_overrides=data.get("per_tenant_overrides", {}),
        )

    def _dict_to_poller_config(self, data: dict[str, Any]) -> PollerConfig:
        """Convert dictionary to PollerConfig."""
        return PollerConfig(
            intervals=data.get("intervals", {}),
            high_priority_sources=data.get("priority", {}).get(
                "high_priority_sources", []
            ),
            batch_size=data.get("batch_size", 10),
            max_concurrent_polls=data.get("max_concurrent_polls", 3),
            max_consecutive_failures=data.get("max_consecutive_failures", 5),
            backoff_multiplier=data.get("backoff_multiplier", 2.0),
        )

    def _dict_to_grounding_config(self, data: dict[str, Any]) -> GroundingConfig:
        """Convert dictionary to GroundingConfig."""
        return GroundingConfig(
            min_citations=data.get("defaults", {}).get("min_citations", 1),
            require_timestamped=data.get("defaults", {}).get(
                "require_timestamped", False
            ),
            command_requirements=data.get("commands", {}),
            confidence_threshold=data.get("confidence_threshold", 0.75),
            source_reliability_threshold=data.get("source_reliability_threshold", 0.80),
        )

    def _dict_to_profiles_config(self, data: dict[str, Any]) -> ProfilesConfig:
        """Convert dictionary to ProfilesConfig."""
        return ProfilesConfig(profiles=data.get("profiles", []))

    def _dict_to_deprecations_config(self, data: dict[str, Any]) -> DeprecationsConfig:
        """Convert dictionary to DeprecationsConfig."""
        return DeprecationsConfig(flags=data.get("flags", []))
