"""Central secure configuration management."""

# ruff: noqa: I001  (optional dependency import ordering is intentional)

from __future__ import annotations

import logging
import os
from typing import Any


logger = logging.getLogger(__name__)

_HAS_PYDANTIC = False
_HAS_PYDANTIC_V2 = False

try:  # Full pydantic-settings + pydantic
    from pydantic import AliasChoices, Field as _PydField, validator
    from pydantic_settings import BaseSettings, SettingsConfigDict

    _HAS_PYDANTIC = True
    _HAS_PYDANTIC_V2 = True
except Exception:  # pragma: no cover
    try:  # Plain pydantic only
        from pydantic import AliasChoices, BaseSettings, Field as _PydField, validator  # type: ignore[no-redef]

        class _SettingsConfigDict(dict):
            pass

        SettingsConfigDict = _SettingsConfigDict  # type: ignore[assignment,misc]
        _HAS_PYDANTIC = True
        _HAS_PYDANTIC_V2 = False
    except Exception:  # Final minimal stubs

        class BaseSettings:  # type: ignore[no-redef]
            pass

        class SettingsConfigDict(dict):  # type: ignore[no-redef]
            pass

        class AliasChoices:  # type: ignore[no-redef]
            def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
                pass

        def _PydField(*_args: Any, **kw: Any) -> Any:  # type: ignore[no-redef]  # pragma: no cover
            return kw.get("default")

        def validator(*_v_args: Any, **_v_kwargs: Any):  # type: ignore[no-redef]  # pragma: no cover
            pass

        _HAS_PYDANTIC = False
        _HAS_PYDANTIC_V2 = False


# Global config instance (lazy-loaded)
_config: SecureConfig | None = None


class SecureConfig:
    """Secure configuration with environment variable loading and validation."""

    if _HAS_PYDANTIC_V2:
        model_config = SettingsConfigDict(
            env_prefix="",
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
            case_sensitive=False,
        )

        # Core system settings
        service_name: str = _PydField(default="ultimate-discord-intel", alias="SERVICE_NAME")
        environment: str = _PydField(default="development", alias="ENVIRONMENT")
        debug: bool = _PydField(default=False, alias="DEBUG")
        log_level: str = _PydField(default="INFO", alias="LOG_LEVEL")

        # Critical secrets / API keys
        openai_api_key: str | None = _PydField(default=None, alias="OPENAI_API_KEY")
        discord_webhook: str | None = _PydField(default=None, alias="DISCORD_WEBHOOK")

        # Feature flags
        enable_http_retry: bool = _PydField(default=False, alias="ENABLE_HTTP_RETRY")
        enable_audit_logging: bool = _PydField(default=True, alias="ENABLE_AUDIT_LOGGING")
        enable_pii_detection: bool = _PydField(default=True, alias="ENABLE_PII_DETECTION")
        enable_rate_limiting: bool = _PydField(default=True, alias="ENABLE_RATE_LIMITING")
        enable_tracing: bool = _PydField(default=False, alias="ENABLE_TRACING")

        # API keys and webhooks
        openrouter_api_key: str | None = _PydField(default=None, alias="OPENROUTER_API_KEY")
        discord_private_webhook: str | None = _PydField(default=None, alias="DISCORD_PRIVATE_WEBHOOK")
        discord_alert_webhook: str | None = _PydField(default=None, alias="DISCORD_ALERT_WEBHOOK")

        # Networking
        http_timeout: int = _PydField(default=30, alias="HTTP_TIMEOUT")
        retry_max_attempts: int = _PydField(default=3, alias="RETRY_MAX_ATTEMPTS")

        # Qdrant gRPC port with validation
        qdrant_grpc_port: int = _PydField(default=6334, alias="QDRANT_GRPC_PORT")

        # Cost management settings
        cost_max_per_request: float = _PydField(default=1.0, alias="COST_MAX_PER_REQUEST")
        cost_budget_daily: float = _PydField(default=100.0, alias="COST_BUDGET_DAILY")

        # LLM provider routing
        router_policy: str = _PydField(default="quality_first", alias="ROUTER_POLICY")
        llm_provider_allowlist: list[str] | None = _PydField(default=None, alias="LLM_PROVIDER_ALLOWLIST")
        quality_first_tasks: list[str] | None = _PydField(default=None, alias="QUALITY_FIRST_TASKS")

        # Database / paths
        archive_db_path: str = _PydField(default="./data/archive_manifest.db", alias="ARCHIVE_DB_PATH")

        @validator("qdrant_grpc_port")
        @classmethod
        def validate_qdrant_grpc_port(cls, v: Any) -> int:
            """Validate QDRANT_GRPC_PORT is a valid integer."""
            if isinstance(v, str):
                try:
                    return int(v)
                except ValueError as exc:
                    raise ValueError("Invalid QDRANT_GRPC_PORT") from exc
            return v

        @validator("llm_provider_allowlist", pre=True)
        @classmethod
        def parse_llm_provider_allowlist(cls, v: Any) -> list[str] | None:
            """Parse comma-separated LLM provider allowlist."""
            if isinstance(v, str) and v:
                return [p.strip().lower() for p in v.split(",") if p.strip()]
            return v

        @validator("quality_first_tasks", pre=True)
        @classmethod
        def parse_quality_first_tasks(cls, v: Any) -> list[str] | None:
            """Parse comma-separated quality first tasks."""
            if isinstance(v, str) and v:
                return [p.strip() for p in v.split(",") if p.strip()]
            return v

    def get_api_key(self, service: str) -> str:
        """Get API key for a service."""
        service = service.lower()
        if service == "openai":
            key = self.openai_api_key
        elif service == "openrouter":
            key = self.openrouter_api_key
        else:
            key = getattr(self, f"{service}_api_key", None)

        if not key:
            raise ValueError(f"API key for service '{service}' is not configured")
        return key

    def get_webhook(self, webhook_type: str) -> str:
        """Get webhook URL for a type."""
        webhook_type = webhook_type.lower()
        if webhook_type == "private":
            url = self.discord_private_webhook
        elif webhook_type == "alert":
            url = self.discord_alert_webhook
        else:
            url = getattr(self, f"discord_{webhook_type}_webhook", None)

        if not url:
            raise ValueError(f"Webhook URL for type '{webhook_type}' is not configured")
        return url

    def get_webhook_secret(self, webhook_type: str) -> str:
        """Get webhook secret for a type (with security validation)."""
        # For security, webhook secrets should not use default values
        secret_key = f"{webhook_type.upper()}_WEBHOOK_SECRET"
        secret = os.getenv(secret_key)

        if not secret or secret in ["CHANGE_ME", "changeme", "default", ""]:
            raise ValueError(f"Webhook secret for '{webhook_type}' must be changed from default value")

        return secret

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        feature = feature.lower().replace("-", "_")
        attr_name = f"enable_{feature}"
        return getattr(self, attr_name, False)


def get_config() -> SecureConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = SecureConfig()
    return _config


def reload_config() -> SecureConfig:
    """Reload configuration from environment (useful for testing)."""
    global _config
    _config = None
    return get_config()


# Backward compatibility helpers for gradual migration
def get_api_key(service: str) -> str:
    """Backward compatibility wrapper for get_api_key."""
    return get_config().get_api_key(service)


def get_webhook_url(webhook_type: str) -> str:
    """Backward compatibility wrapper for get_webhook."""
    return get_config().get_webhook(webhook_type)


def is_feature_enabled(feature: str) -> bool:
    """Backward compatibility wrapper for feature flags."""
    return get_config().is_feature_enabled(feature)


def get_setting(key: str, default: Any = None) -> Any:
    """Get any configuration setting by key name.

    Args:
        key: Setting key (snake_case)
        default: Default value if setting not found

    Returns:
        Configuration value or default
    """
    config = get_config()
    return getattr(config, key, default)


# ---------------------------------------------------------------------------
# Lightweight fallback initialization when Pydantic is unavailable
# ---------------------------------------------------------------------------
if not _HAS_PYDANTIC:
    # Inject a basic __init__ to populate critical fields from environment and enforce
    # minimal validation expected by tests. This keeps API compatible without
    # requiring pydantic in ultra-minimal environments.
    def _fallback_init(self) -> None:
        import os as _os

        # Core system
        self.service_name = _os.getenv("SERVICE_NAME", "ultimate-discord-intel")
        self.environment = _os.getenv("ENVIRONMENT", "development")
        self.debug = _os.getenv("DEBUG", "false").lower() in ("1", "true", "yes", "on")
        self.log_level = _os.getenv("LOG_LEVEL", "INFO")

        # Critical secrets / API keys
        self.openai_api_key = _os.getenv("OPENAI_API_KEY")
        self.discord_webhook = _os.getenv("DISCORD_WEBHOOK")

        # Feature flags (commonly used ones)
        self.enable_http_retry = _os.getenv("ENABLE_HTTP_RETRY", "false").lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        self.enable_audit_logging = _os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() in ("1", "true", "yes", "on")
        self.enable_pii_detection = _os.getenv("ENABLE_PII_DETECTION", "true").lower() in ("1", "true", "yes", "on")
        self.enable_rate_limiting = _os.getenv("ENABLE_RATE_LIMITING", "true").lower() in ("1", "true", "yes", "on")
        self.enable_tracing = _os.getenv("ENABLE_TRACING", "false").lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

        # API keys and webhooks (commonly accessed)
        self.openrouter_api_key = _os.getenv("OPENROUTER_API_KEY")
        self.discord_private_webhook = _os.getenv("DISCORD_PRIVATE_WEBHOOK")
        self.discord_alert_webhook = _os.getenv("DISCORD_ALERT_WEBHOOK")

        # Networking
        self.http_timeout = int(_os.getenv("HTTP_TIMEOUT", "30"))
        self.retry_max_attempts = int(_os.getenv("RETRY_MAX_ATTEMPTS", "3"))

        # Qdrant gRPC port with validation
        grpc_val = _os.getenv("QDRANT_GRPC_PORT", "6334")
        try:
            self.qdrant_grpc_port = int(grpc_val)
        except ValueError as exc:
            # Match test expectation: invalid numeric env should raise ValueError on reload
            raise ValueError("Invalid QDRANT_GRPC_PORT") from exc

        # Cost management settings
        self.cost_max_per_request = float(_os.getenv("COST_MAX_PER_REQUEST", "1.0"))
        self.cost_budget_daily = float(_os.getenv("COST_BUDGET_DAILY", "100.0"))

        # LLM provider routing (fallback parsing)
        self.router_policy = _os.getenv("ROUTER_POLICY", "quality_first")
        self.llm_provider_allowlist_raw = _os.getenv("LLM_PROVIDER_ALLOWLIST")
        if self.llm_provider_allowlist_raw:
            self.llm_provider_allowlist = [
                p.strip().lower() for p in self.llm_provider_allowlist_raw.split(",") if p.strip()
            ]
        else:
            self.llm_provider_allowlist = None
        self.quality_first_tasks_raw = _os.getenv("QUALITY_FIRST_TASKS")
        if self.quality_first_tasks_raw:
            self.quality_first_tasks = [p.strip() for p in self.quality_first_tasks_raw.split(",") if p.strip()]
        else:
            self.quality_first_tasks = None

        # Database / paths (only those referenced in docs/tests)
        self.archive_db_path = _os.getenv("ARCHIVE_DB_PATH", "./data/archive_manifest.db")

    # Bind the lightweight initializer
    SecureConfig.__init__ = _fallback_init  # type: ignore[assignment]
