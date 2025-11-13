"""Feature flag registry and lifecycle management.

Provides centralized feature flag discovery, validation, and runtime introspection
with lifecycle documentation and deprecation tracking.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from platform.core.step_result import ErrorCategory, StepResult
from typing import Any


class FlagStatus(Enum):
    """Feature flag lifecycle status."""

    EXPERIMENTAL = "experimental"  # Under development, unstable
    BETA = "beta"  # Stable enough for testing, may change
    STABLE = "stable"  # Production-ready
    DEPRECATED = "deprecated"  # Scheduled for removal
    REMOVED = "removed"  # No longer available


class FlagCategory(Enum):
    """Feature flag category for organization."""

    CORE = "core"
    CACHE = "cache"
    LLM = "llm"
    MEMORY = "memory"
    OBSERVABILITY = "observability"
    SECURITY = "security"
    DISCORD = "discord"
    INGESTION = "ingestion"
    MCP = "mcp"
    EXPERIMENTAL = "experimental"


@dataclass
class FeatureFlag:
    """Feature flag definition with lifecycle metadata."""

    name: str
    description: str
    category: FlagCategory
    status: FlagStatus
    default: bool
    added_date: str  # ISO 8601 date
    deprecated_date: str | None = None
    removal_date: str | None = None
    dependencies: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    docs_url: str | None = None
    owner: str | None = None


class FeatureFlagRegistry:
    """Centralized feature flag registry with validation and introspection."""

    _FLAGS: dict[str, FeatureFlag] = {
        # ===== CORE SYSTEM =====
        "ENABLE_API": FeatureFlag(
            name="ENABLE_API",
            description="Enable FastAPI REST API server",
            category=FlagCategory.CORE,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-01-01",
        ),
        "ENABLE_TRACING": FeatureFlag(
            name="ENABLE_TRACING",
            description="Enable distributed tracing",
            category=FlagCategory.OBSERVABILITY,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-01-01",
        ),
        "ENABLE_PROMETHEUS_ENDPOINT": FeatureFlag(
            name="ENABLE_PROMETHEUS_ENDPOINT",
            description="Expose Prometheus metrics endpoint at /metrics",
            category=FlagCategory.OBSERVABILITY,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-01-01",
        ),
        "ENABLE_HTTP_METRICS": FeatureFlag(
            name="ENABLE_HTTP_METRICS",
            description="Collect HTTP client metrics",
            category=FlagCategory.OBSERVABILITY,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-01-01",
        ),
        # ===== CACHING =====
        "ENABLE_GPTCACHE": FeatureFlag(
            name="ENABLE_GPTCACHE",
            description="Enable GPTCache for LLM response caching",
            category=FlagCategory.CACHE,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-06-01",
        ),
        "ENABLE_SEMANTIC_CACHE": FeatureFlag(
            name="ENABLE_SEMANTIC_CACHE",
            description="Enable semantic similarity-based cache lookups",
            category=FlagCategory.CACHE,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-06-01",
        ),
        "ENABLE_SEMANTIC_CACHE_SHADOW": FeatureFlag(
            name="ENABLE_SEMANTIC_CACHE_SHADOW",
            description="Shadow mode: log cache hits without serving",
            category=FlagCategory.CACHE,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-06-01",
            dependencies=["ENABLE_SEMANTIC_CACHE"],
        ),
        "ENABLE_GPTCACHE_ANALYSIS_SHADOW": FeatureFlag(
            name="ENABLE_GPTCACHE_ANALYSIS_SHADOW",
            description="Shadow mode for analysis-specific GPTCache",
            category=FlagCategory.CACHE,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-06-01",
            dependencies=["ENABLE_GPTCACHE"],
        ),
        "ENABLE_HTTP_CACHE": FeatureFlag(
            name="ENABLE_HTTP_CACHE",
            description="Enable HTTP response caching",
            category=FlagCategory.CACHE,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-01-01",
        ),
        # ===== LLM & ROUTING =====
        "ENABLE_INSTRUCTOR": FeatureFlag(
            name="ENABLE_INSTRUCTOR",
            description="Enable Instructor for structured LLM outputs",
            category=FlagCategory.LLM,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-03-01",
        ),
        "ENABLE_LITELLM_ROUTER": FeatureFlag(
            name="ENABLE_LITELLM_ROUTER",
            description="Enable LiteLLM multi-provider routing",
            category=FlagCategory.LLM,
            status=FlagStatus.BETA,
            default=False,
            added_date="2024-08-01",
        ),
        "ENABLE_RL_ROUTING": FeatureFlag(
            name="ENABLE_RL_ROUTING",
            description="Enable reinforcement learning for model routing",
            category=FlagCategory.LLM,
            status=FlagStatus.BETA,
            default=True,
            added_date="2024-07-01",
        ),
        "ENABLE_BANDIT_ROUTING": FeatureFlag(
            name="ENABLE_BANDIT_ROUTING",
            description="Enable bandit algorithms for model selection",
            category=FlagCategory.LLM,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-07-01",
        ),
        "ENABLE_CONTEXTUAL_BANDIT": FeatureFlag(
            name="ENABLE_CONTEXTUAL_BANDIT",
            description="Enable LinUCB contextual bandit routing",
            category=FlagCategory.LLM,
            status=FlagStatus.BETA,
            default=True,
            added_date="2024-09-01",
        ),
        "ENABLE_PROMPT_COMPRESSION": FeatureFlag(
            name="ENABLE_PROMPT_COMPRESSION",
            description="Enable prompt compression (LLMLingua)",
            category=FlagCategory.LLM,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-06-01",
        ),
        # ===== MEMORY =====
        "ENABLE_GRAPH_MEMORY": FeatureFlag(
            name="ENABLE_GRAPH_MEMORY",
            description="Enable Neo4j graph memory storage",
            category=FlagCategory.MEMORY,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-05-01",
        ),
        "ENABLE_HIPPORAG_MEMORY": FeatureFlag(
            name="ENABLE_HIPPORAG_MEMORY",
            description="Enable HippoRAG continual learning memory",
            category=FlagCategory.MEMORY,
            status=FlagStatus.BETA,
            default=True,
            added_date="2024-08-01",
        ),
        "ENABLE_VECTOR_SEARCH": FeatureFlag(
            name="ENABLE_VECTOR_SEARCH",
            description="Enable Qdrant vector search",
            category=FlagCategory.MEMORY,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-01-01",
        ),
        # ===== OBSERVABILITY =====
        "ENABLE_TRAJECTORY_EVALUATION": FeatureFlag(
            name="ENABLE_TRAJECTORY_EVALUATION",
            description="Enable LangSmith trajectory evaluation",
            category=FlagCategory.OBSERVABILITY,
            status=FlagStatus.BETA,
            default=False,
            added_date="2024-09-01",
        ),
        "ENABLE_TRAJECTORY_FEEDBACK_LOOP": FeatureFlag(
            name="ENABLE_TRAJECTORY_FEEDBACK_LOOP",
            description="Push trajectory scores into RL router",
            category=FlagCategory.OBSERVABILITY,
            status=FlagStatus.EXPERIMENTAL,
            default=False,
            added_date="2024-09-01",
            dependencies=["ENABLE_TRAJECTORY_EVALUATION", "ENABLE_RL_ROUTING"],
        ),
        "ENABLE_LOGFIRE": FeatureFlag(
            name="ENABLE_LOGFIRE",
            description="Enable Pydantic Logfire observability",
            category=FlagCategory.OBSERVABILITY,
            status=FlagStatus.BETA,
            default=False,
            added_date="2024-08-01",
        ),
        "ENABLE_AGENT_METRICS": FeatureFlag(
            name="ENABLE_AGENT_METRICS",
            description="Enable Prometheus metrics for agent executions",
            category=FlagCategory.OBSERVABILITY,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2025-11-12",
        ),
        # ===== SECURITY =====
        "ENABLE_PII_DETECTION": FeatureFlag(
            name="ENABLE_PII_DETECTION",
            description="Enable PII detection and redaction",
            category=FlagCategory.SECURITY,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-01-01",
        ),
        "ENABLE_RATE_LIMITING": FeatureFlag(
            name="ENABLE_RATE_LIMITING",
            description="Enable rate limiting for API endpoints",
            category=FlagCategory.SECURITY,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-01-01",
        ),
        "ENABLE_CONTENT_MODERATION": FeatureFlag(
            name="ENABLE_CONTENT_MODERATION",
            description="Enable content moderation checks",
            category=FlagCategory.SECURITY,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-01-01",
        ),
        # ===== DISCORD =====
        "ENABLE_DISCORD_GATEWAY": FeatureFlag(
            name="ENABLE_DISCORD_GATEWAY",
            description="Enable Discord gateway connection",
            category=FlagCategory.DISCORD,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-01-01",
        ),
        "ENABLE_DISCORD_COMMANDS": FeatureFlag(
            name="ENABLE_DISCORD_COMMANDS",
            description="Enable Discord slash commands",
            category=FlagCategory.DISCORD,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-01-01",
        ),
        "ENABLE_DISCORD_AI_RESPONSES": FeatureFlag(
            name="ENABLE_DISCORD_AI_RESPONSES",
            description="Enable AI-powered Discord responses",
            category=FlagCategory.DISCORD,
            status=FlagStatus.BETA,
            default=True,
            added_date="2024-07-01",
        ),
        # ===== MCP =====
        "ENABLE_MCP_MEMORY": FeatureFlag(
            name="ENABLE_MCP_MEMORY",
            description="Enable MCP memory server",
            category=FlagCategory.MCP,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-06-01",
        ),
        "ENABLE_MCP_ROUTER": FeatureFlag(
            name="ENABLE_MCP_ROUTER",
            description="Enable MCP routing server",
            category=FlagCategory.MCP,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-06-01",
        ),
        "ENABLE_MCP_CREWAI": FeatureFlag(
            name="ENABLE_MCP_CREWAI",
            description="Enable MCP CrewAI integration",
            category=FlagCategory.MCP,
            status=FlagStatus.BETA,
            default=True,
            added_date="2024-08-01",
        ),
        # ===== INGESTION =====
        "ENABLE_INGEST_YOUTUBE": FeatureFlag(
            name="ENABLE_INGEST_YOUTUBE",
            description="Enable YouTube content ingestion",
            category=FlagCategory.INGESTION,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-01-01",
        ),
        "ENABLE_INGEST_CONCURRENT": FeatureFlag(
            name="ENABLE_INGEST_CONCURRENT",
            description="Enable concurrent ingestion processing",
            category=FlagCategory.INGESTION,
            status=FlagStatus.STABLE,
            default=True,
            added_date="2024-03-01",
        ),
        # ===== TOOL VALIDATION =====
        "ENABLE_TOOL_CONTRACT_VALIDATION": FeatureFlag(
            name="ENABLE_TOOL_CONTRACT_VALIDATION",
            description="Validate tool contracts (StepResult, TenantContext)",
            category=FlagCategory.CORE,
            status=FlagStatus.BETA,
            default=False,  # Shadow mode
            added_date="2025-11-12",
        ),
    }

    @classmethod
    def get(cls, name: str, default: bool | None = None) -> bool:
        """Get feature flag value from environment.

        Args:
            name: Flag name (e.g., "ENABLE_API")
            default: Override default if flag not in env

        Returns:
            Flag value (True/False)
        """
        flag_def = cls._FLAGS.get(name)
        if flag_def is None:
            # Unknown flag - return env value or False
            return cls._parse_bool(os.getenv(name, "false"))

        # Use provided default, flag default, or env value
        effective_default = default if default is not None else flag_def.default
        raw_value = os.getenv(name)

        if raw_value is None:
            return effective_default

        return cls._parse_bool(raw_value)

    @classmethod
    def list_all(cls, category: FlagCategory | None = None, status: FlagStatus | None = None) -> list[FeatureFlag]:
        """List all registered flags with optional filtering.

        Args:
            category: Filter by category
            status: Filter by status

        Returns:
            List of matching flags
        """
        flags = list(cls._FLAGS.values())

        if category:
            flags = [f for f in flags if f.category == category]

        if status:
            flags = [f for f in flags if f.status == status]

        return sorted(flags, key=lambda f: f.name)

    @classmethod
    def validate(cls) -> StepResult:
        """Validate current environment against flag definitions.

        Returns:
            StepResult with validation results
        """
        issues = []

        # Check for deprecated flags in use
        for name, flag in cls._FLAGS.items():
            if flag.status == FlagStatus.DEPRECATED and os.getenv(name):
                issues.append(f"{name} is DEPRECATED (removal: {flag.removal_date}). Migrate to alternative or remove.")

        # Check dependencies
        for name, flag in cls._FLAGS.items():
            if cls.get(name) and flag.dependencies:
                for dep in flag.dependencies:
                    if not cls.get(dep):
                        issues.append(f"{name} requires {dep} to be enabled")

        # Check conflicts
        for name, flag in cls._FLAGS.items():
            if cls.get(name) and flag.conflicts:
                for conflict in flag.conflicts:
                    if cls.get(conflict):
                        issues.append(f"{name} conflicts with {conflict}")

        if issues:
            return StepResult.fail(
                "\n".join(issues),
                error_category=ErrorCategory.VALIDATION,
                metadata={"issues": issues, "count": len(issues)},
            )

        return StepResult.ok(
            result={
                "enabled_count": sum(1 for name in cls._FLAGS if cls.get(name)),
                "total_count": len(cls._FLAGS),
            }
        )

    @classmethod
    def get_metadata(cls, name: str) -> dict[str, Any] | None:
        """Get flag metadata.

        Args:
            name: Flag name

        Returns:
            Flag metadata dict or None if not found
        """
        flag = cls._FLAGS.get(name)
        if not flag:
            return None

        return {
            "name": flag.name,
            "description": flag.description,
            "category": flag.category.value,
            "status": flag.status.value,
            "default": flag.default,
            "current": cls.get(name),
            "added_date": flag.added_date,
            "deprecated_date": flag.deprecated_date,
            "removal_date": flag.removal_date,
            "dependencies": flag.dependencies,
            "conflicts": flag.conflicts,
            "docs_url": flag.docs_url,
            "owner": flag.owner,
        }

    @classmethod
    def sync_with_env_example(cls, env_example_path: str) -> StepResult:
        """Check sync status with .env.example.

        Args:
            env_example_path: Path to .env.example

        Returns:
            StepResult with sync status
        """
        try:
            with open(env_example_path, encoding="utf-8") as f:
                content = f.read()

            # Extract ENABLE_* flags from .env.example
            env_flags = set()
            for line in content.splitlines():
                line = line.strip()
                if line.startswith(("ENABLE_", "#ENABLE_")):
                    flag_name = line.lstrip("#").split("=")[0].strip()
                    if flag_name.startswith("ENABLE_"):
                        env_flags.add(flag_name)

            # Find flags in registry but not in .env.example
            registry_flags = set(cls._FLAGS.keys())
            missing_in_env = registry_flags - env_flags
            missing_in_registry = env_flags - registry_flags

            issues = []
            if missing_in_env:
                issues.append(f"Missing in .env.example: {sorted(missing_in_env)}")
            if missing_in_registry:
                issues.append(f"Missing in registry: {sorted(missing_in_registry)}")

            if issues:
                return StepResult.uncertain(
                    result={"issues": issues, "env_flags": len(env_flags), "registry_flags": len(registry_flags)}
                )

            return StepResult.ok(result={"synced": True, "flag_count": len(registry_flags)})

        except Exception as e:
            return StepResult.fail(
                f"Failed to sync with .env.example: {e}",
                error_category=ErrorCategory.EXTERNAL_SERVICE_ERROR,
            )

    @staticmethod
    def _parse_bool(value: str) -> bool:
        """Parse boolean from string.

        Args:
            value: String value

        Returns:
            Boolean value
        """
        return value.lower() in {"1", "true", "yes", "on", "enabled"}
