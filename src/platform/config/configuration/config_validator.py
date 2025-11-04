"""Configuration validation with comprehensive checks and error reporting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from .config_schema import (
        ArchiveConfig,
        GlobalConfig,
        GroundingConfig,
        IngestConfig,
        MonitoringConfig,
        PolicyConfig,
        PollerConfig,
        RoutingConfig,
        SecurityConfig,
        TenantConfig,
    )


@dataclass
class ValidationError:
    """Configuration validation error."""

    section: str
    field: str
    message: str
    severity: str = "error"  # error, warning, info


@dataclass
class ValidationResult:
    """Configuration validation result."""

    is_valid: bool
    errors: list[ValidationError]
    warnings: list[ValidationError]

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0


class ConfigValidator:
    """Validates configuration for correctness and completeness."""

    def __init__(self) -> None:
        """Initialize validator."""
        self.valid_strategies = {"cost_optimized", "performance", "balanced"}
        self.valid_roles = {"viewer", "user", "moderator", "ops", "admin"}
        self.valid_content_types = {"images", "videos", "audio", "docs", "blobs"}
        self.valid_platforms = {"youtube", "twitch", "tiktok", "reddit"}
        self.valid_environments = {"dev", "staging", "production"}

    def validate_global_config(self, config: GlobalConfig) -> ValidationResult:
        """Validate global configuration."""
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        # Validate service metadata
        self._validate_service_metadata(config, errors, warnings)

        # Validate paths
        self._validate_paths(config, errors, warnings)

        # Validate API keys and connections
        self._validate_connections(config, errors, warnings)

        # Validate configuration sections
        self._validate_routing_config(config.routing, errors, warnings)
        self._validate_security_config(config.security, errors, warnings)
        self._validate_monitoring_config(config.monitoring, errors, warnings)
        self._validate_ingest_config(config.ingest, errors, warnings)
        self._validate_policy_config(config.policy, errors, warnings)
        self._validate_archive_config(config.archive, errors, warnings)
        self._validate_poller_config(config.poller, errors, warnings)
        self._validate_grounding_config(config.grounding, errors, warnings)

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_tenant_config(self, config: TenantConfig) -> ValidationResult:
        """Validate tenant configuration."""
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        # Validate tenant metadata
        if not config.tenant_id:
            errors.append(ValidationError("tenant", "tenant_id", "Tenant ID is required"))

        if not config.name:
            errors.append(ValidationError("tenant", "name", "Tenant name is required"))

        if config.status not in {"active", "inactive", "suspended"}:
            errors.append(ValidationError("tenant", "status", f"Invalid status: {config.status}"))

        # Validate overrides if present
        if config.routing_overrides:
            self._validate_routing_overrides(config.routing_overrides, errors, warnings)

        if config.budget_overrides:
            self._validate_budget_overrides(config.budget_overrides, errors, warnings)

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _validate_service_metadata(
        self,
        config: GlobalConfig,
        errors: list[ValidationError],
        warnings: list[ValidationError],
    ) -> None:
        """Validate service metadata."""
        if not config.service_name:
            errors.append(ValidationError("service", "service_name", "Service name is required"))

        if config.environment not in self.valid_environments:
            warnings.append(
                ValidationError(
                    "service",
                    "environment",
                    f"Unknown environment: {config.environment}",
                )
            )

        if not config.version:
            warnings.append(ValidationError("service", "version", "Version not specified"))

    def _validate_paths(
        self,
        config: GlobalConfig,
        errors: list[ValidationError],
        warnings: list[ValidationError],
    ) -> None:
        """Validate path configurations."""
        paths_to_check = [
            ("base_dir", config.base_dir),
            ("config_dir", config.config_dir),
            ("logs_dir", config.logs_dir),
            ("downloads_dir", config.downloads_dir),
            ("processing_dir", config.processing_dir),
        ]

        for path_name, path in paths_to_check:
            if not path:
                errors.append(ValidationError("paths", path_name, f"{path_name} is required"))
                continue

            # Check if path is writable
            try:
                path.mkdir(parents=True, exist_ok=True)
                if not path.is_dir():
                    errors.append(ValidationError("paths", path_name, f"{path_name} is not a directory"))
            except Exception as e:
                errors.append(ValidationError("paths", path_name, f"Cannot create/access {path_name}: {e}"))

    def _validate_connections(
        self,
        config: GlobalConfig,
        errors: list[ValidationError],
        warnings: list[ValidationError],
    ) -> None:
        """Validate database and API connections."""
        # Check for required API keys
        if not config.discord_bot_token:
            errors.append(ValidationError("connections", "discord_bot_token", "Discord bot token is required"))

        # At least one LLM API key is required
        if not config.openai_api_key and not config.openrouter_api_key:
            errors.append(ValidationError("connections", "api_keys", "At least one LLM API key is required"))

        # Qdrant connection
        if not config.qdrant_url:
            warnings.append(ValidationError("connections", "qdrant_url", "Qdrant URL not configured"))

        # Redis connection (optional)
        if not config.redis_url:
            warnings.append(
                ValidationError(
                    "connections",
                    "redis_url",
                    "Redis URL not configured (caching disabled)",
                )
            )

    def _validate_routing_config(
        self,
        config: RoutingConfig,
        errors: list[ValidationError],
        warnings: list[ValidationError],
    ) -> None:
        """Validate routing configuration."""
        if config.strategy not in self.valid_strategies:
            errors.append(
                ValidationError(
                    "routing",
                    "strategy",
                    f"Invalid routing strategy: {config.strategy}",
                )
            )

        if config.retry_attempts < 0:
            errors.append(ValidationError("routing", "retry_attempts", "Retry attempts must be non-negative"))

        if config.default_context_window <= 0:
            errors.append(
                ValidationError(
                    "routing",
                    "default_context_window",
                    "Context window must be positive",
                )
            )

        if config.max_cost_per_request <= 0:
            errors.append(
                ValidationError(
                    "routing",
                    "max_cost_per_request",
                    "Max cost per request must be positive",
                )
            )

        if not 0 <= config.cost_alert_threshold <= 1:
            errors.append(
                ValidationError(
                    "routing",
                    "cost_alert_threshold",
                    "Cost alert threshold must be between 0 and 1",
                )
            )

    def _validate_security_config(
        self,
        config: SecurityConfig,
        errors: list[ValidationError],
        warnings: list[ValidationError],
    ) -> None:
        """Validate security configuration."""
        # Validate role permissions
        for role, permissions in config.role_permissions.items():
            if not isinstance(permissions, list):
                errors.append(
                    ValidationError(
                        "security",
                        f"role_permissions.{role}",
                        "Permissions must be a list",
                    )
                )

        # Validate rate limits
        if config.default_rate_limit <= 0:
            errors.append(
                ValidationError(
                    "security",
                    "default_rate_limit",
                    "Default rate limit must be positive",
                )
            )

        for scope, limits in config.rate_limit_scopes.items():
            if "per_minute" in limits and limits["per_minute"] <= 0:
                errors.append(
                    ValidationError(
                        "security",
                        f"rate_limit_scopes.{scope}.per_minute",
                        "Rate limit must be positive",
                    )
                )
            if "burst" in limits and limits["burst"] <= 0:
                errors.append(
                    ValidationError(
                        "security",
                        f"rate_limit_scopes.{scope}.burst",
                        "Burst limit must be positive",
                    )
                )

    def _validate_monitoring_config(
        self,
        config: MonitoringConfig,
        errors: list[ValidationError],
        warnings: list[ValidationError],
    ) -> None:
        """Validate monitoring configuration."""
        # Validate target values
        for field, value in [
            ("target_bypass_rate", config.target_bypass_rate),
            ("target_early_exit_rate", config.target_early_exit_rate),
            ("target_avg_time_savings", config.target_avg_time_savings),
            ("target_quality_score", config.target_quality_score),
        ]:
            if not 0 <= value <= 1:
                errors.append(ValidationError("monitoring", field, f"{field} must be between 0 and 1"))

        # Validate intervals
        for field, value in [
            ("dashboard_refresh_interval", config.dashboard_refresh_interval),
            ("metrics_aggregation_interval", config.metrics_aggregation_interval),
            ("alert_check_interval", config.alert_check_interval),
        ]:
            if value <= 0:
                errors.append(ValidationError("monitoring", field, f"{field} must be positive"))

    def _validate_ingest_config(
        self,
        config: IngestConfig,
        errors: list[ValidationError],
        warnings: list[ValidationError],
    ) -> None:
        """Validate ingest configuration."""
        if config.max_chars_per_chunk <= 0:
            errors.append(
                ValidationError(
                    "ingest",
                    "max_chars_per_chunk",
                    "Max chars per chunk must be positive",
                )
            )

        if config.chunk_overlap < 0:
            errors.append(ValidationError("ingest", "chunk_overlap", "Chunk overlap must be non-negative"))

        if config.chunk_overlap >= config.max_chars_per_chunk:
            errors.append(
                ValidationError(
                    "ingest",
                    "chunk_overlap",
                    "Chunk overlap must be less than max chars per chunk",
                )
            )

        if config.min_content_length <= 0:
            errors.append(
                ValidationError(
                    "ingest",
                    "min_content_length",
                    "Min content length must be positive",
                )
            )

        if config.max_content_length <= config.min_content_length:
            errors.append(
                ValidationError(
                    "ingest",
                    "max_content_length",
                    "Max content length must be greater than min content length",
                )
            )

        if config.max_concurrent_downloads <= 0:
            errors.append(
                ValidationError(
                    "ingest",
                    "max_concurrent_downloads",
                    "Max concurrent downloads must be positive",
                )
            )

    def _validate_policy_config(
        self,
        config: PolicyConfig,
        errors: list[ValidationError],
        warnings: list[ValidationError],
    ) -> None:
        """Validate policy configuration."""
        if config.retention_days <= 0:
            errors.append(ValidationError("policy", "retention_days", "Retention days must be positive"))

        if config.consent_expiry_days <= 0:
            errors.append(
                ValidationError(
                    "policy",
                    "consent_expiry_days",
                    "Consent expiry days must be positive",
                )
            )

    def _validate_archive_config(
        self,
        config: ArchiveConfig,
        errors: list[ValidationError],
        warnings: list[ValidationError],
    ) -> None:
        """Validate archive configuration."""
        if config.max_retries < 0:
            errors.append(ValidationError("archive", "max_retries", "Max retries must be non-negative"))

        # Validate content type routes
        for content_type, visibility_routes in config.routes.items():
            if content_type not in self.valid_content_types:
                warnings.append(
                    ValidationError(
                        "archive",
                        f"routes.{content_type}",
                        f"Unknown content type: {content_type}",
                    )
                )

            # Handle both legacy dict structure and new route structure
            if not isinstance(visibility_routes, dict):
                continue  # Skip non-dict entries

            for visibility, route_config in visibility_routes.items():
                # Route config might be a dict with 'enabled', 'destination', etc. or old 'channel_id' structure
                if not isinstance(route_config, dict):
                    continue  # Skip non-dict route configs

                # Only validate channel_id if this looks like the old structure
                if (
                    visibility in {"public", "private"}
                    and "channel_id" not in route_config
                    and "destination" not in route_config
                ):
                    # This might be using the new structure or is incomplete
                    warnings.append(
                        ValidationError(
                            "archive",
                            f"routes.{content_type}.{visibility}",
                            "Route config should have either 'channel_id' (legacy) or 'destination' (new)",
                        )
                    )

    def _validate_poller_config(
        self,
        config: PollerConfig,
        errors: list[ValidationError],
        warnings: list[ValidationError],
    ) -> None:
        """Validate poller configuration."""
        for platform, settings in config.intervals.items():
            if platform not in self.valid_platforms:
                warnings.append(
                    ValidationError(
                        "poller",
                        f"intervals.{platform}",
                        f"Unknown platform: {platform}",
                    )
                )

            # Settings should be a dict with 'interval' and 'priority'
            if isinstance(settings, dict):
                if "interval" in settings and settings["interval"] <= 0:
                    errors.append(
                        ValidationError(
                            "poller",
                            f"intervals.{platform}.interval",
                            "Interval must be positive",
                        )
                    )
            elif not isinstance(settings, int | dict):
                warnings.append(
                    ValidationError(
                        "poller",
                        f"intervals.{platform}",
                        "Settings should be a dict with 'interval' and 'priority' keys",
                    )
                )

        if config.batch_size <= 0:
            errors.append(ValidationError("poller", "batch_size", "Batch size must be positive"))

        if config.max_concurrent_polls <= 0:
            errors.append(
                ValidationError(
                    "poller",
                    "max_concurrent_polls",
                    "Max concurrent polls must be positive",
                )
            )

    def _validate_grounding_config(
        self,
        config: GroundingConfig,
        errors: list[ValidationError],
        warnings: list[ValidationError],
    ) -> None:
        """Validate grounding configuration."""
        if config.min_citations <= 0:
            errors.append(ValidationError("grounding", "min_citations", "Min citations must be positive"))

        if not 0 <= config.confidence_threshold <= 1:
            errors.append(
                ValidationError(
                    "grounding",
                    "confidence_threshold",
                    "Confidence threshold must be between 0 and 1",
                )
            )

        if not 0 <= config.source_reliability_threshold <= 1:
            errors.append(
                ValidationError(
                    "grounding",
                    "source_reliability_threshold",
                    "Source reliability threshold must be between 0 and 1",
                )
            )

    def _validate_routing_overrides(
        self,
        overrides: dict[str, Any],
        errors: list[ValidationError],
        warnings: list[ValidationError],
    ) -> None:
        """Validate tenant routing overrides."""
        if "strategy" in overrides and overrides["strategy"] not in self.valid_strategies:
            errors.append(
                ValidationError(
                    "tenant_routing",
                    "strategy",
                    f"Invalid routing strategy: {overrides['strategy']}",
                )
            )

    def _validate_budget_overrides(
        self,
        overrides: dict[str, Any],
        errors: list[ValidationError],
        warnings: list[ValidationError],
    ) -> None:
        """Validate tenant budget overrides."""
        if "monthly_total" in overrides and overrides["monthly_total"] <= 0:
            errors.append(ValidationError("tenant_budget", "monthly_total", "Monthly total must be positive"))
