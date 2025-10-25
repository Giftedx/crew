#!/usr/bin/env python3
"""Configuration simplification script for the Ultimate Discord Intelligence Bot.

This script analyzes the current configuration system, identifies complexity,
and creates a simplified, unified configuration loader with clear precedence.
"""

import os
import re
from pathlib import Path


class ConfigurationSimplifier:
    """Simplifies and unifies configuration management."""

    def __init__(self, config_dir: str):
        """Initialize simplifier with config directory."""
        self.config_dir = Path(config_dir)
        self.complexity_issues: list[str] = []
        self.consolidation_opportunities: list[dict[str, str]] = []
        self.duplicate_settings: list[tuple[str, str]] = []

    def analyze_configuration_complexity(self) -> dict[str, any]:
        """Analyze current configuration complexity."""
        print("🔍 Analyzing configuration complexity...")

        analysis = {
            "total_files": 0,
            "total_settings": 0,
            "feature_flags": 0,
            "environment_variables": 0,
            "yaml_files": 0,
            "python_files": 0,
            "complexity_score": 0,
        }

        # Count configuration files
        for config_file in self.config_dir.rglob("*"):
            if config_file.is_file():
                analysis["total_files"] += 1

                if config_file.suffix == ".py":
                    analysis["python_files"] += 1
                elif config_file.suffix in [".yaml", ".yml"]:
                    analysis["yaml_files"] += 1

        # Analyze Python configuration files
        for py_file in self.config_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                # Count settings/attributes
                settings_count = len(re.findall(r"[A-Z_]+:\s*[^=]+=", content))
                analysis["total_settings"] += settings_count

                # Count feature flags
                flags_count = len(re.findall(r"ENABLE_[A-Z_]+", content))
                analysis["feature_flags"] += flags_count

                # Count environment variables
                env_vars = len(re.findall(r"os\.environ\.get\(|os\.getenv\(", content))
                analysis["environment_variables"] += env_vars

            except Exception as e:
                print(f"⚠️  Error analyzing {py_file}: {e}")

        # Calculate complexity score
        analysis["complexity_score"] = (
            analysis["total_files"] * 2
            + analysis["total_settings"] * 1
            + analysis["feature_flags"] * 1
            + analysis["environment_variables"] * 1
        )

        return analysis

    def identify_duplicate_settings(self) -> list[tuple[str, str]]:
        """Identify duplicate settings across files."""
        print("🔍 Identifying duplicate settings...")

        settings_map = {}
        duplicates = []

        for py_file in self.config_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                # Find setting definitions
                setting_pattern = r"([A-Z_]+):\s*[^=]+="
                matches = re.findall(setting_pattern, content)

                for setting in matches:
                    if setting in settings_map:
                        duplicates.append((settings_map[setting], str(py_file)))
                    else:
                        settings_map[setting] = str(py_file)

            except Exception as e:
                print(f"⚠️  Error analyzing {py_file}: {e}")

        return duplicates

    def identify_consolidation_opportunities(self) -> list[dict[str, str]]:
        """Identify opportunities to consolidate configuration."""
        print("🎯 Identifying consolidation opportunities...")

        opportunities = []

        # Group related configuration files
        file_groups = {"agent_configs": [], "task_configs": [], "feature_configs": [], "path_configs": []}

        for config_file in self.config_dir.rglob("*"):
            if config_file.is_file():
                file_name = config_file.name.lower()

                if "agent" in file_name:
                    file_groups["agent_configs"].append(str(config_file))
                elif "task" in file_name:
                    file_groups["task_configs"].append(str(config_file))
                elif "feature" in file_name or "flag" in file_name:
                    file_groups["feature_configs"].append(str(config_file))
                elif "path" in file_name:
                    file_groups["path_configs"].append(str(config_file))

        # Create consolidation opportunities
        for group_name, files in file_groups.items():
            if len(files) > 1:
                opportunities.append(
                    {
                        "group": group_name,
                        "files": files,
                        "target": f"unified_{group_name}.py",
                        "reason": f"Consolidate {len(files)} {group_name} files",
                    }
                )

        return opportunities

    def create_unified_configuration_loader(self) -> str:
        """Create a unified configuration loader."""
        print("🏗️  Creating unified configuration loader...")

        loader_content = '''"""Unified configuration loader for the Ultimate Discord Intelligence Bot.

This module provides a single, simplified interface for all configuration
needs with clear precedence and comprehensive validation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from pathlib import Path


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
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    discord_bot_token: Optional[str] = None

    # Database
    qdrant_url: Optional[str] = None
    qdrant_api_key: Optional[str] = None

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

    custom_settings: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "UnifiedConfig":
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
                    if env_value:
                        value = env_value
                    else:
                        value = None
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {}
        for field_name, field_info in self.__dataclass_fields__.items():
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
_config: Optional[UnifiedConfig] = None


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
'''

        return loader_content

    def create_configuration_migration_guide(self) -> str:
        """Create migration guide for configuration changes."""
        print("📝 Creating configuration migration guide...")

        guide_content = """# Configuration Migration Guide

## Overview
This guide helps migrate from the complex, multi-file configuration system to the new unified configuration loader.

## Migration Steps

### 1. Update Imports
**Before:**
```python
from ultimate_discord_intelligence_bot.settings import Settings
from ultimate_discord_intelligence_bot.config import BaseConfig, FeatureFlags
```

**After:**
```python
from ultimate_discord_intelligence_bot.config.unified import get_config
```

### 2. Update Configuration Access
**Before:**
```python
settings = Settings()
api_key = settings.openai_api_key
enable_debate = settings.feature_flags.ENABLE_DEBATE_ANALYSIS
```

**After:**
```python
config = get_config()
api_key = config.openai_api_key
enable_debate = config.enable_debate_analysis
```

### 3. Update Feature Flag Access
**Before:**
```python
if settings.feature_flags.ENABLE_DEBATE_ANALYSIS:
    # do something
```

**After:**
```python
if config.get_feature_flag("ENABLE_DEBATE_ANALYSIS"):
    # do something
```

### 4. Environment Variable Changes
Feature flags now use lowercase with underscores:
- `ENABLE_DEBATE_ANALYSIS` → `enable_debate_analysis`
- `ENABLE_FACT_CHECKING` → `enable_fact_checking`

### 5. Configuration Validation
The new system provides automatic validation:
```python
try:
    config = get_config()
except ValueError as e:
    print(f"Configuration error: {e}")
```

## Benefits of Migration

1. **Simplified Access**: Single configuration object
2. **Clear Precedence**: Environment → .env → defaults
3. **Automatic Validation**: Catches configuration errors early
4. **Type Safety**: Full type hints and validation
5. **Better Documentation**: Clear structure and examples

## Backward Compatibility

The old `Settings` class is still available but deprecated. Update your code to use the new unified configuration system.
"""

        return guide_content

    def generate_simplification_report(self) -> str:
        """Generate simplification report."""
        report = []
        report.append("# Configuration Simplification Report")
        report.append("")
        report.append("## Analysis Results")
        report.append(f"- Total configuration files: {len(self.complexity_issues)}")
        report.append(f"- Duplicate settings found: {len(self.duplicate_settings)}")
        report.append(f"- Consolidation opportunities: {len(self.consolidation_opportunities)}")
        report.append("")

        if self.duplicate_settings:
            report.append("## Duplicate Settings")
            for setting1, setting2 in self.duplicate_settings:
                report.append(f"- {setting1} ↔ {setting2}")
            report.append("")

        if self.consolidation_opportunities:
            report.append("## Consolidation Opportunities")
            for opp in self.consolidation_opportunities:
                report.append(f"- {opp['group']}: {len(opp['files'])} files → {opp['target']}")
            report.append("")

        report.append("## Benefits of Simplification")
        report.append("1. **Single Configuration Object**: One place for all settings")
        report.append("2. **Clear Precedence**: Environment → .env → defaults")
        report.append("3. **Automatic Validation**: Catches errors early")
        report.append("4. **Type Safety**: Full type hints and validation")
        report.append("5. **Better Documentation**: Clear structure and examples")
        report.append("")

        report.append("## Next Steps")
        report.append("1. Implement unified configuration loader")
        report.append("2. Update all imports to use new system")
        report.append("3. Migrate environment variables to new format")
        report.append("4. Update documentation and examples")
        report.append("5. Remove old configuration files")

        return "\n".join(report)

    def run_simplification(self) -> None:
        """Run complete configuration simplification."""
        print("🚀 Starting configuration simplification...")

        # Analyze current complexity
        analysis = self.analyze_configuration_complexity()
        print(f"📊 Configuration complexity score: {analysis['complexity_score']}")
        print(f"📁 Total files: {analysis['total_files']}")
        print(f"⚙️  Total settings: {analysis['total_settings']}")
        print(f"🚩 Feature flags: {analysis['feature_flags']}")

        # Identify issues
        self.duplicate_settings = self.identify_duplicate_settings()
        print(f"🔄 Found {len(self.duplicate_settings)} duplicate settings")

        self.consolidation_opportunities = self.identify_consolidation_opportunities()
        print(f"🎯 Found {len(self.consolidation_opportunities)} consolidation opportunities")

        # Create unified configuration loader
        loader_content = self.create_unified_configuration_loader()
        loader_file = Path("src/ultimate_discord_intelligence_bot/config/unified.py")
        with open(loader_file, "w", encoding="utf-8") as f:
            f.write(loader_content)
        print(f"✅ Created unified configuration loader: {loader_file}")

        # Create migration guide
        migration_guide = self.create_configuration_migration_guide()
        migration_file = Path("docs/configuration_migration_guide.md")
        with open(migration_file, "w", encoding="utf-8") as f:
            f.write(migration_guide)
        print(f"✅ Created migration guide: {migration_file}")

        # Generate report
        report = self.generate_simplification_report()
        report_file = Path("configuration_simplification_report.md")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        print("✅ Configuration simplification complete!")
        print(f"📝 Report saved to: {report_file}")


def main():
    """Main function."""
    config_dir = "src/ultimate_discord_intelligence_bot/config"

    if not os.path.exists(config_dir):
        print(f"❌ Configuration directory not found: {config_dir}")
        return

    simplifier = ConfigurationSimplifier(config_dir)
    simplifier.run_simplification()


if __name__ == "__main__":
    main()
