"""Configuration schema definitions with type safety and validation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel


if TYPE_CHECKING:
    from datetime import datetime


class ConfigSchema(BaseModel):
    """Base configuration schema with common validation."""

    class Config:
        """Pydantic configuration."""

        extra = "forbid"  # Reject unknown fields
        validate_assignment = True  # Validate on assignment
        use_enum_values = True  # Use enum values in serialization


@dataclass
class RoutingConfig:
    """Router configuration with model preferences and policies."""

    # Model preferences by use case
    default_model: str = "anthropic/claude-3-sonnet"
    debate_model: str = "openai/gpt-4"
    summarization_model: str = "anthropic/claude-3-haiku"
    code_model: str = "anthropic/claude-3-sonnet"
    creative_model: str = "openai/gpt-4"

    # Routing policies
    strategy: str = "cost_optimized"  # cost_optimized, performance, balanced
    fallback_enabled: bool = True
    retry_attempts: int = 3

    # Context windows
    default_context_window: int = 32000
    long_context_window: int = 128000

    # Cost optimization
    max_cost_per_request: float = 5.00
    cost_alert_threshold: float = 0.80  # Alert at 80% of budget


@dataclass
class SecurityConfig:
    """Security configuration including RBAC and rate limiting."""

    # Role-based permissions
    role_permissions: dict[str, list[str]] = field(
        default_factory=lambda: {
            "viewer": [],
            "user": [],
            "moderator": ["security.view"],
            "ops": ["security.view", "ingest.backfill"],
            "admin": ["*"],
        }
    )

    # Rate limiting
    default_rate_limit: int = 60  # requests per minute
    rate_limit_scopes: dict[str, dict[str, int]] = field(
        default_factory=lambda: {
            "user": {"per_minute": 60, "burst": 90},
            "api": {"per_minute": 300, "burst": 500},
            "ingest": {"per_minute": 10, "burst": 20},
        }
    )

    # Content moderation
    enable_content_moderation: bool = True
    enable_pii_detection: bool = True
    pii_types: dict[str, str] = field(
        default_factory=lambda: {
            "email": "Email Address",
            "phone": "Phone Number",
            "address": "Physical Address",
        }
    )
    pii_masks: dict[str, str] = field(
        default_factory=lambda: {
            "email": "[redacted-email]",
            "phone": "[redacted-phone]",
            "address": "[redacted-address]",
        }
    )


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""

    # Overall performance targets
    target_bypass_rate: float = 0.60
    target_early_exit_rate: float = 0.40
    target_avg_time_savings: float = 0.70
    target_quality_score: float = 0.75

    # Alert thresholds
    warning_bypass_rate_low: float = 0.50
    critical_bypass_rate_low: float = 0.40
    warning_bypass_rate_high: float = 0.80

    # Monitoring intervals
    dashboard_refresh_interval: int = 30  # seconds
    metrics_aggregation_interval: int = 3600  # seconds
    alert_check_interval: int = 300  # seconds

    # Data retention
    quality_trends_retention: int = 168  # hours (1 week)
    detailed_metrics_retention: int = 48  # hours (2 days)

    # Alert cooldowns
    warning_cooldown: int = 1800  # seconds (30 minutes)
    critical_cooldown: int = 600  # seconds (10 minutes)


@dataclass
class IngestConfig:
    """Content ingestion configuration."""

    # Platform settings
    youtube_enabled: bool = True
    twitch_enabled: bool = True
    tiktok_enabled: bool = True
    reddit_enabled: bool = True

    # Chunking settings
    max_chars_per_chunk: int = 800
    chunk_overlap: int = 200

    # Quality thresholds
    min_content_length: int = 100
    max_content_length: int = 1000000

    # Processing limits
    max_concurrent_downloads: int = 5
    download_timeout: int = 300  # seconds
    retry_attempts: int = 3


@dataclass
class PolicyConfig:
    """Content policy and governance configuration."""

    # Source control
    allowed_sources: dict[str, list[str]] = field(default_factory=dict)
    forbidden_types: list[str] = field(default_factory=list)

    # Storage policies
    retention_days: int = 30
    auto_cleanup: bool = True

    # Consent management
    require_explicit_consent: bool = True
    consent_expiry_days: int = 365

    # Command-specific policies
    per_command_policies: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class ArchiveConfig:
    """Discord archiver routing configuration."""

    # Default settings
    max_retries: int = 3
    chunking_enabled: bool = True

    # Content type routing
    routes: dict[str, dict[str, dict[str, str]]] = field(
        default_factory=lambda: {
            "images": {
                "public": {"channel_id": "000000000000000000"},
                "private": {"channel_id": "000000000000000000"},
            },
            "videos": {
                "public": {"channel_id": "000000000000000000"},
                "private": {"channel_id": "000000000000000000"},
            },
            "audio": {
                "public": {"channel_id": "000000000000000000"},
                "private": {"channel_id": "000000000000000000"},
            },
            "docs": {
                "public": {"channel_id": "000000000000000000"},
                "private": {"channel_id": "000000000000000000"},
            },
            "blobs": {
                "public": {"channel_id": "000000000000000000"},
                "private": {"channel_id": "000000000000000000"},
            },
        }
    )

    # Per-tenant overrides
    per_tenant_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class PollerConfig:
    """Content polling and scheduling configuration."""

    # Polling intervals by source
    intervals: dict[str, dict[str, int]] = field(
        default_factory=lambda: {
            "youtube": {"interval": 3600, "priority": 0},
            "twitch": {"interval": 3600, "priority": 0},
        }
    )

    # Priority settings
    high_priority_sources: list[str] = field(default_factory=lambda: ["official_channels", "verified_creators"])

    # Batch processing
    batch_size: int = 10
    max_concurrent_polls: int = 3

    # Error handling
    max_consecutive_failures: int = 5
    backoff_multiplier: float = 2.0


@dataclass
class GroundingConfig:
    """Fact verification and grounding configuration."""

    # Default citation requirements
    min_citations: int = 1
    require_timestamped: bool = False

    # Command-specific requirements
    command_requirements: dict[str, dict[str, Any]] = field(
        default_factory=lambda: {"context": {"min_citations": 3, "require_timestamped": False}}
    )

    # Verification thresholds
    confidence_threshold: float = 0.75
    source_reliability_threshold: float = 0.80


@dataclass
class ProfilesConfig:
    """Creator profiles and seed data configuration."""

    profiles: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DeprecationsConfig:
    """Deprecation tracking configuration."""

    flags: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TenantConfig:
    """Tenant-specific configuration overrides."""

    tenant_id: str
    name: str
    status: str = "active"
    created_at: datetime | None = None

    # Tenant-specific overrides
    routing_overrides: dict[str, Any] | None = None
    budget_overrides: dict[str, Any] | None = None
    policy_overrides: dict[str, Any] | None = None
    security_overrides: dict[str, Any] | None = None

    # Workspaces
    workspaces: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class GlobalConfig:
    """Global system configuration."""

    # Service metadata
    service_name: str = "ultimate-discord-intelligence-bot"
    environment: str = "dev"
    version: str = "1.0.0"

    # Core features
    enable_api: bool = False
    enable_tracing: bool = False
    enable_metrics: bool = True
    enable_dashboard: bool = False

    # Paths
    base_dir: Path = field(default_factory=lambda: Path.home() / "crew_data")
    config_dir: Path = field(default_factory=lambda: Path.home() / "crew_data" / "Config")
    logs_dir: Path = field(default_factory=lambda: Path.home() / "crew_data" / "Logs")
    downloads_dir: Path = field(default_factory=lambda: Path.home() / "crew_data" / "Downloads")
    processing_dir: Path = field(default_factory=lambda: Path.home() / "crew_data" / "Processing")

    # Database connections
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    redis_url: str = ""

    # API keys
    discord_bot_token: str = ""
    openai_api_key: str = ""
    openrouter_api_key: str = ""

    # Configuration sections
    routing: RoutingConfig = field(default_factory=RoutingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    ingest: IngestConfig = field(default_factory=IngestConfig)
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    archive: ArchiveConfig = field(default_factory=ArchiveConfig)
    poller: PollerConfig = field(default_factory=PollerConfig)
    grounding: GroundingConfig = field(default_factory=GroundingConfig)
    profiles: ProfilesConfig = field(default_factory=ProfilesConfig)
    deprecations: DeprecationsConfig = field(default_factory=DeprecationsConfig)

    def __post_init__(self) -> None:
        """Post-initialization setup."""
        # Ensure directories exist
        for path in [
            self.base_dir,
            self.config_dir,
            self.logs_dir,
            self.downloads_dir,
            self.processing_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

        # Load environment overrides
        self._load_env_overrides()

    def _load_env_overrides(self) -> None:
        """Load configuration from environment variables."""
        # Core settings
        if env_val := os.getenv("SERVICE_NAME"):
            self.service_name = env_val
        if env_val := os.getenv("ENVIRONMENT"):
            self.environment = env_val
        if env_val := os.getenv("VERSION"):
            self.version = env_val

        # Feature flags
        if env_val := os.getenv("ENABLE_API"):
            self.enable_api = env_val.lower() in ("true", "1", "yes")
        if env_val := os.getenv("ENABLE_TRACING"):
            self.enable_tracing = env_val.lower() in ("true", "1", "yes")
        if env_val := os.getenv("ENABLE_METRICS"):
            self.enable_metrics = env_val.lower() in ("true", "1", "yes")
        if env_val := os.getenv("ENABLE_DASHBOARD"):
            self.enable_dashboard = env_val.lower() in ("true", "1", "yes")

        # Paths
        if env_val := os.getenv("BASE_DIR"):
            self.base_dir = Path(env_val)
        if env_val := os.getenv("CONFIG_DIR"):
            self.config_dir = Path(env_val)
        if env_val := os.getenv("LOGS_DIR"):
            self.logs_dir = Path(env_val)
        if env_val := os.getenv("DOWNLOADS_DIR"):
            self.downloads_dir = Path(env_val)
        if env_val := os.getenv("PROCESSING_DIR"):
            self.processing_dir = Path(env_val)

        # Database connections
        if env_val := os.getenv("QDRANT_URL"):
            self.qdrant_url = env_val
        if env_val := os.getenv("QDRANT_API_KEY"):
            self.qdrant_api_key = env_val
        if env_val := os.getenv("REDIS_URL"):
            self.redis_url = env_val

        # API keys
        if env_val := os.getenv("DISCORD_BOT_TOKEN"):
            self.discord_bot_token = env_val
        if env_val := os.getenv("OPENAI_API_KEY"):
            self.openai_api_key = env_val
        if env_val := os.getenv("OPENROUTER_API_KEY"):
            self.openrouter_api_key = env_val

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting with fallback to environment variable.

        Args:
            key: Setting key (lowercase with underscores)
            default: Default value if setting not found

        Returns:
            Configuration value, environment variable, or default
        """
        # First try to get from instance attributes
        value = getattr(self, key, None)
        if value is not None:
            return value

        # Fall back to environment variable (uppercase)
        env_key = key.upper()
        env_value = os.getenv(env_key, default)

        # Convert string environment values to appropriate types if needed
        if env_value and isinstance(env_value, str):
            if env_value.lower() in ("1", "true", "yes", "on"):
                return True
            elif env_value.lower() in ("0", "false", "no", "off"):
                return False

        return env_value
