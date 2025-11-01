"""Configuration validation for the Ultimate Discord Intelligence Bot."""

from __future__ import annotations

import os
from typing import Any


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field


class ConfigValidator:
    """Configuration validator with comprehensive validation rules."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_base_config(self, config: Any) -> bool:
        """Validate base configuration."""
        self.errors.clear()
        self.warnings.clear()

        # Validate required fields
        required_fields = ["environment", "log_level", "max_workers", "request_timeout", "max_retries"]

        for field in required_fields:
            if not hasattr(config, field):
                self.errors.append(f"Missing required field: {field}")

        # Validate environment
        if hasattr(config, "environment"):
            valid_environments = ["development", "staging", "production"]
            if config.environment not in valid_environments:
                self.errors.append(
                    f"Invalid environment: {config.environment}. Must be one of: {', '.join(valid_environments)}"
                )

        # Validate log level
        if hasattr(config, "log_level"):
            valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if config.log_level.upper() not in valid_log_levels:
                self.errors.append(
                    f"Invalid log level: {config.log_level}. Must be one of: {', '.join(valid_log_levels)}"
                )

        # Validate numeric fields
        numeric_fields = [
            ("max_workers", 1, 100),
            ("request_timeout", 1, 300),
            ("max_retries", 0, 10),
        ]

        for field, min_val, max_val in numeric_fields:
            if hasattr(config, field):
                value = getattr(config, field)
                if not isinstance(value, int) or not (min_val <= value <= max_val):
                    self.errors.append(f"Invalid {field}: {value}. Must be between {min_val} and {max_val}")

        return len(self.errors) == 0

    def validate_feature_flags(self, flags: Any) -> bool:
        """Validate feature flags configuration."""
        self.errors.clear()
        self.warnings.clear()

        # Check for conflicting flags
        if (
            hasattr(flags, "ENABLE_DEBUG_MODE")
            and hasattr(flags, "ENABLE_TEST_MODE")
            and flags.ENABLE_DEBUG_MODE
            and flags.ENABLE_TEST_MODE
        ):
            self.warnings.append("Both DEBUG_MODE and TEST_MODE are enabled")

        # Check for missing dependencies
        if (
            hasattr(flags, "ENABLE_UNIFIED_KNOWLEDGE")
            and hasattr(flags, "ENABLE_VECTOR_MEMORY")
            and flags.ENABLE_UNIFIED_KNOWLEDGE
            and not flags.ENABLE_VECTOR_MEMORY
        ):
            self.warnings.append("ENABLE_UNIFIED_KNOWLEDGE requires ENABLE_VECTOR_MEMORY")

        if (
            hasattr(flags, "ENABLE_GRAPH_MEMORY")
            and hasattr(flags, "ENABLE_VECTOR_MEMORY")
            and flags.ENABLE_GRAPH_MEMORY
            and not flags.ENABLE_VECTOR_MEMORY
        ):
            self.warnings.append("ENABLE_GRAPH_MEMORY requires ENABLE_VECTOR_MEMORY")

        if (
            hasattr(flags, "ENABLE_ALERTS")
            and hasattr(flags, "ENABLE_METRICS")
            and flags.ENABLE_ALERTS
            and not flags.ENABLE_METRICS
        ):
            self.warnings.append("ENABLE_ALERTS requires ENABLE_METRICS")

        return len(self.errors) == 0

    def validate_paths(self, paths: Any) -> bool:
        """Validate path configuration."""
        self.errors.clear()
        self.warnings.clear()

        # Check required paths
        required_paths = ["base_dir", "downloads_dir", "config_dir", "logs_dir", "processing_dir", "temp_dir"]

        for path_name in required_paths:
            if hasattr(paths, path_name):
                path = getattr(paths, path_name)
                if not path:
                    self.errors.append(f"Missing required path: {path_name}")
                elif not isinstance(path, type(paths.base_dir)):
                    self.errors.append(f"Invalid path type for {path_name}")

        # Check path permissions
        if hasattr(paths, "base_dir") and paths.base_dir:
            try:
                # Check if we can create directories
                test_dir = paths.base_dir / "test_permissions"
                test_dir.mkdir(parents=True, exist_ok=True)
                test_dir.rmdir()
            except PermissionError:
                self.errors.append("Insufficient permissions for base directory")
            except Exception as e:
                self.errors.append(f"Path validation error: {e}")

        return len(self.errors) == 0

    def validate_environment(self) -> bool:
        """Validate environment variables."""
        self.errors.clear()
        self.warnings.clear()

        # Check for required environment variables
        required_env_vars = [
            "DISCORD_BOT_TOKEN",
            "OPENAI_API_KEY",  # or OPENROUTER_API_KEY
        ]

        for var in required_env_vars:
            if not os.getenv(var):
                self.errors.append(f"Missing required environment variable: {var}")

        # Check for API key conflicts
        openai_key = os.getenv("OPENAI_API_KEY")
        openrouter_key = os.getenv("OPENROUTER_API_KEY")

        if not openai_key and not openrouter_key:
            self.errors.append("Either OPENAI_API_KEY or OPENROUTER_API_KEY must be set")

        if openai_key and openrouter_key:
            self.warnings.append("Both OPENAI_API_KEY and OPENROUTER_API_KEY are set")

        return len(self.errors) == 0

    def get_validation_report(self) -> dict[str, Any]:
        """Get validation report with errors and warnings."""
        return {"errors": self.errors.copy(), "warnings": self.warnings.copy(), "is_valid": len(self.errors) == 0}


def validate_configuration() -> bool:
    """Validate entire configuration system.

    Returns:
        bool: True if configuration is valid, False otherwise
    """
    validator = ConfigValidator()

    # Validate environment variables
    env_valid = validator.validate_environment()

    # Import and validate configuration classes
    try:
        from .base import BaseConfig
        from .feature_flags import FeatureFlags
        from .paths import PathConfig

        # Create configuration instances
        base_config = BaseConfig.from_env()
        feature_flags = FeatureFlags.from_env()
        path_config = PathConfig.from_env()

        # Validate each component
        base_valid = validator.validate_base_config(base_config)
        flags_valid = validator.validate_feature_flags(feature_flags)
        paths_valid = validator.validate_paths(path_config)

        # Get validation report
        report = validator.get_validation_report()

        if report["errors"]:
            print("Configuration validation errors:")
            for error in report["errors"]:
                print(f"  - {error}")

        if report["warnings"]:
            print("Configuration validation warnings:")
            for warning in report["warnings"]:
                print(f"  - {warning}")

        return env_valid and base_valid and flags_valid and paths_valid

    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False
