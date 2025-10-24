"""Feature flags configuration for the Ultimate Discord Intelligence Bot."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class FeatureFlags:
    """Feature flags configuration with type safety and validation.

    Manages all feature flags for the system, providing a centralized
    way to enable/disable features across the application.
    """

    # Core system features
    ENABLE_LANGGRAPH_PIPELINE: bool = False
    ENABLE_UNIFIED_KNOWLEDGE: bool = False
    ENABLE_MEM0_MEMORY: bool = False
    ENABLE_DSPY_OPTIMIZATION: bool = False
    ENABLE_AGENT_BRIDGE: bool = False
    ENABLE_DASHBOARD_INTEGRATION: bool = False
    ENABLE_INTELLIGENT_ALERTING: bool = False
    ENABLE_UNIFIED_CACHE: bool = False
    ENABLE_UNIFIED_METRICS: bool = False
    ENABLE_UNIFIED_ORCHESTRATION: bool = False
    ENABLE_UNIFIED_ROUTER: bool = False

    # Analysis features
    ENABLE_DEBATE_ANALYSIS: bool = True
    ENABLE_FACT_CHECKING: bool = True
    ENABLE_SENTIMENT_ANALYSIS: bool = True
    ENABLE_BIAS_DETECTION: bool = True

    # Memory features
    ENABLE_VECTOR_MEMORY: bool = True
    ENABLE_GRAPH_MEMORY: bool = False
    ENABLE_MEMORY_COMPACTION: bool = True
    ENABLE_MEMORY_TTL: bool = False

    # Performance features
    ENABLE_CACHING: bool = True
    ENABLE_RESULT_CACHING: bool = True
    ENABLE_SMART_CACHING: bool = True
    ENABLE_CACHE_OPTIMIZATION: bool = True
    ENABLE_MEMORY_OPTIMIZATION: bool = True
    ENABLE_MEMORY_POOLING: bool = True
    ENABLE_MEMORY_ANALYSIS: bool = True
    ENABLE_LAZY_LOADING: bool = False
    ENABLE_LAZY_PRELOAD_CRITICAL: bool = True
    ENABLE_LAZY_CACHING: bool = True
    ENABLE_LAZY_METRICS: bool = True
    ENABLE_PARALLEL_PROCESSING: bool = True
    ENABLE_OPTIMIZATION: bool = True

    # OpenAI integration features
    ENABLE_OPENAI_STRUCTURED_OUTPUTS: bool = True
    ENABLE_OPENAI_STREAMING: bool = True
    ENABLE_OPENAI_VOICE: bool = False
    ENABLE_OPENAI_VISION: bool = False
    ENABLE_OPENAI_MULTIMODAL: bool = False
    ENABLE_OPENAI_FUNCTION_CALLING: bool = True
    ENABLE_OPENAI_FALLBACK: bool = True

    # Integration features
    ENABLE_DISCORD_INTEGRATION: bool = True
    ENABLE_YOUTUBE_INTEGRATION: bool = True
    ENABLE_TWITCH_INTEGRATION: bool = True
    ENABLE_TIKTOK_INTEGRATION: bool = True

    # Discord AI Features
    ENABLE_DISCORD_AI_RESPONSES: bool = True
    ENABLE_DISCORD_PERSONALITY_RL: bool = True
    ENABLE_DISCORD_MESSAGE_EVALUATION: bool = True
    ENABLE_DISCORD_OPT_IN_SYSTEM: bool = True
    ENABLE_DISCORD_CONVERSATIONAL_PIPELINE: bool = True

    # Personality Evolution
    ENABLE_PERSONALITY_ADAPTATION: bool = True
    ENABLE_REWARD_COMPUTATION: bool = True
    ENABLE_PERSONALITY_MEMORY: bool = True

    # MCP Integration
    ENABLE_MCP_MEMORY: bool = True
    ENABLE_MCP_KG: bool = True
    ENABLE_MCP_CREWAI: bool = True
    ENABLE_MCP_ROUTER: bool = True
    ENABLE_MCP_CREATOR_INTELLIGENCE: bool = True
    ENABLE_MCP_OBS: bool = True
    ENABLE_MCP_INGEST: bool = True
    ENABLE_MCP_HTTP: bool = True
    ENABLE_MCP_A2A: bool = True

    # Model routing features
    ENABLE_RL_MODEL_ROUTING: bool = False

    # OpenRouter Service Enhancement Features
    ENABLE_OPENROUTER_CONNECTION_POOLING: bool = False
    ENABLE_OPENROUTER_REQUEST_BATCHING: bool = False
    ENABLE_OPENROUTER_CIRCUIT_BREAKER: bool = False
    ENABLE_OPENROUTER_ADVANCED_CACHING: bool = False
    ENABLE_OPENROUTER_ASYNC_ROUTING: bool = False
    ENABLE_OPENROUTER_OBJECT_POOLING: bool = False
    ENABLE_OPENROUTER_METRICS_COLLECTION: bool = True
    ENABLE_OPENROUTER_HEALTH_CHECKS: bool = True
    ENABLE_OPENROUTER_SERVICE_REGISTRY: bool = True
    ENABLE_OPENROUTER_FACADE_PATTERN: bool = True

    # Monitoring features
    ENABLE_METRICS: bool = True
    ENABLE_LOGGING: bool = True
    ENABLE_TRACING: bool = False
    ENABLE_ALERTS: bool = True
    ENABLE_OBSERVABILITY_WRAPPER: bool = True
    ENABLE_OTEL_EXPORT: bool = False

    # Security features
    ENABLE_PRIVACY_FILTER: bool = True
    ENABLE_CONTENT_MODERATION: bool = True
    ENABLE_RATE_LIMITING: bool = True

    # Development features
    ENABLE_DEBUG_MODE: bool = False
    ENABLE_TEST_MODE: bool = False
    ENABLE_DEVELOPMENT_TOOLS: bool = False

    # Enterprise features
    ENABLE_ENTERPRISE_TENANT_MANAGEMENT: bool = False

    # WebSocket features
    ENABLE_WEBSOCKET_UPDATES: bool = False

    # Orchestration features
    ENABLE_HIERARCHICAL_ORCHESTRATION: bool = False

    # Crew Consolidation Flags
    ENABLE_LEGACY_CREW: bool = False
    ENABLE_CREW_MODULAR: bool = False
    ENABLE_CREW_REFACTORED: bool = False
    ENABLE_CREW_NEW: bool = False

    # Agent Collaboration Features
    ENABLE_AGENT_COLLABORATION: bool = False
    ENABLE_MEMORY_COORDINATION: bool = False
    ENABLE_CREW_ANALYTICS: bool = False

    # Model Spec Governance
    ENABLE_MODEL_SPEC_ENFORCEMENT: bool = True
    ENABLE_RED_LINE_GUARDS: bool = True
    ENABLE_CONTENT_SAFETY_CLASSIFICATION: bool = True
    ENABLE_CHAIN_OF_COMMAND: bool = True

    # Political Bias Detection
    ENABLE_POLITICAL_BIAS_DETECTION: bool = True
    ENABLE_BIAS_METRICS_TRACKING: bool = True
    ENABLE_BIAS_DASHBOARD: bool = True
    ENABLE_BIAS_MITIGATION: bool = True

    # Transparency & Audit
    ENABLE_GOVERNANCE_AUDIT_TRAIL: bool = True
    ENABLE_TRANSPARENCY_REPORTS: bool = True
    ENABLE_EXPLAINABILITY: bool = True

    # Evaluation
    ENABLE_CONTINUOUS_BIAS_EVAL: bool = True
    ENABLE_MODEL_SPEC_COMPLIANCE_CHECKS: bool = True

    def __post_init__(self):
        """Validate feature flags after initialization."""
        self._validate_flags()

    def _validate_flags(self) -> None:
        """Validate feature flag combinations."""
        # Ensure core dependencies are enabled if dependent features are enabled
        if self.ENABLE_UNIFIED_KNOWLEDGE and not self.ENABLE_VECTOR_MEMORY:
            self.ENABLE_VECTOR_MEMORY = True

        if self.ENABLE_GRAPH_MEMORY and not self.ENABLE_VECTOR_MEMORY:
            self.ENABLE_VECTOR_MEMORY = True

        # Ensure monitoring is enabled if alerts are enabled
        if self.ENABLE_ALERTS and not self.ENABLE_METRICS:
            self.ENABLE_METRICS = True

    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled."""
        return getattr(self, flag_name, False)

    def enable(self, flag_name: str) -> None:
        """Enable a feature flag."""
        if hasattr(self, flag_name):
            setattr(self, flag_name, True)

    def disable(self, flag_name: str) -> None:
        """Disable a feature flag."""
        if hasattr(self, flag_name):
            setattr(self, flag_name, False)

    def toggle(self, flag_name: str) -> bool:
        """Toggle a feature flag and return its new state."""
        if hasattr(self, flag_name):
            current_value = getattr(self, flag_name)
            setattr(self, flag_name, not current_value)
            return not current_value
        return False

    def get_enabled_flags(self) -> dict[str, bool]:
        """Get all enabled feature flags."""
        return {name: value for name, value in self.__dict__.items() if name.startswith("ENABLE_") and value}

    def get_disabled_flags(self) -> dict[str, bool]:
        """Get all disabled feature flags."""
        return {name: value for name, value in self.__dict__.items() if name.startswith("ENABLE_") and not value}

    @classmethod
    def from_env(cls) -> FeatureFlags:
        """Create feature flags from environment variables."""

        def get_bool_env(key: str, default: bool = False) -> bool:
            value = os.getenv(key, str(default)).lower()
            return value in ("true", "1", "yes", "on")

        return cls(
            # Core system features
            ENABLE_LANGGRAPH_PIPELINE=get_bool_env("ENABLE_LANGGRAPH_PIPELINE", False),
            ENABLE_UNIFIED_KNOWLEDGE=get_bool_env("ENABLE_UNIFIED_KNOWLEDGE", False),
            ENABLE_MEM0_MEMORY=get_bool_env("ENABLE_MEM0_MEMORY", False),
            ENABLE_DSPY_OPTIMIZATION=get_bool_env("ENABLE_DSPY_OPTIMIZATION", False),
            ENABLE_AGENT_BRIDGE=get_bool_env("ENABLE_AGENT_BRIDGE", False),
            ENABLE_DASHBOARD_INTEGRATION=get_bool_env("ENABLE_DASHBOARD_INTEGRATION", False),
            ENABLE_INTELLIGENT_ALERTING=get_bool_env("ENABLE_INTELLIGENT_ALERTING", False),
            ENABLE_UNIFIED_CACHE=get_bool_env("ENABLE_UNIFIED_CACHE", False),
            ENABLE_UNIFIED_METRICS=get_bool_env("ENABLE_UNIFIED_METRICS", False),
            ENABLE_UNIFIED_ORCHESTRATION=get_bool_env("ENABLE_UNIFIED_ORCHESTRATION", False),
            ENABLE_UNIFIED_ROUTER=get_bool_env("ENABLE_UNIFIED_ROUTER", False),
            # Analysis features
            ENABLE_DEBATE_ANALYSIS=get_bool_env("ENABLE_DEBATE_ANALYSIS", True),
            ENABLE_FACT_CHECKING=get_bool_env("ENABLE_FACT_CHECKING", True),
            ENABLE_SENTIMENT_ANALYSIS=get_bool_env("ENABLE_SENTIMENT_ANALYSIS", True),
            ENABLE_BIAS_DETECTION=get_bool_env("ENABLE_BIAS_DETECTION", True),
            # Memory features
            ENABLE_VECTOR_MEMORY=get_bool_env("ENABLE_VECTOR_MEMORY", True),
            ENABLE_GRAPH_MEMORY=get_bool_env("ENABLE_GRAPH_MEMORY", False),
            ENABLE_MEMORY_COMPACTION=get_bool_env("ENABLE_MEMORY_COMPACTION", True),
            ENABLE_MEMORY_TTL=get_bool_env("ENABLE_MEMORY_TTL", False),
            # Performance features
            ENABLE_CACHING=get_bool_env("ENABLE_CACHING", True),
            ENABLE_RESULT_CACHING=get_bool_env("ENABLE_RESULT_CACHING", True),
            ENABLE_SMART_CACHING=get_bool_env("ENABLE_SMART_CACHING", True),
            ENABLE_CACHE_OPTIMIZATION=get_bool_env("ENABLE_CACHE_OPTIMIZATION", True),
            ENABLE_MEMORY_OPTIMIZATION=get_bool_env("ENABLE_MEMORY_OPTIMIZATION", True),
            ENABLE_MEMORY_POOLING=get_bool_env("ENABLE_MEMORY_POOLING", True),
            ENABLE_MEMORY_ANALYSIS=get_bool_env("ENABLE_MEMORY_ANALYSIS", True),
            ENABLE_LAZY_LOADING=get_bool_env("ENABLE_LAZY_LOADING", False),
            ENABLE_LAZY_PRELOAD_CRITICAL=get_bool_env("ENABLE_LAZY_PRELOAD_CRITICAL", True),
            ENABLE_LAZY_CACHING=get_bool_env("ENABLE_LAZY_CACHING", True),
            ENABLE_LAZY_METRICS=get_bool_env("ENABLE_LAZY_METRICS", True),
            ENABLE_PARALLEL_PROCESSING=get_bool_env("ENABLE_PARALLEL_PROCESSING", True),
            ENABLE_OPTIMIZATION=get_bool_env("ENABLE_OPTIMIZATION", True),
            # OpenAI integration features
            ENABLE_OPENAI_STRUCTURED_OUTPUTS=get_bool_env("ENABLE_OPENAI_STRUCTURED_OUTPUTS", True),
            ENABLE_OPENAI_STREAMING=get_bool_env("ENABLE_OPENAI_STREAMING", True),
            ENABLE_OPENAI_VOICE=get_bool_env("ENABLE_OPENAI_VOICE", False),
            ENABLE_OPENAI_VISION=get_bool_env("ENABLE_OPENAI_VISION", False),
            ENABLE_OPENAI_MULTIMODAL=get_bool_env("ENABLE_OPENAI_MULTIMODAL", False),
            ENABLE_OPENAI_FUNCTION_CALLING=get_bool_env("ENABLE_OPENAI_FUNCTION_CALLING", True),
            ENABLE_OPENAI_FALLBACK=get_bool_env("ENABLE_OPENAI_FALLBACK", True),
            # Integration features
            ENABLE_DISCORD_INTEGRATION=get_bool_env("ENABLE_DISCORD_INTEGRATION", True),
            ENABLE_YOUTUBE_INTEGRATION=get_bool_env("ENABLE_YOUTUBE_INTEGRATION", True),
            ENABLE_TWITCH_INTEGRATION=get_bool_env("ENABLE_TWITCH_INTEGRATION", True),
            ENABLE_TIKTOK_INTEGRATION=get_bool_env("ENABLE_TIKTOK_INTEGRATION", True),
            # Discord AI Features
            ENABLE_DISCORD_AI_RESPONSES=get_bool_env("ENABLE_DISCORD_AI_RESPONSES", True),
            ENABLE_DISCORD_PERSONALITY_RL=get_bool_env("ENABLE_DISCORD_PERSONALITY_RL", True),
            ENABLE_DISCORD_MESSAGE_EVALUATION=get_bool_env("ENABLE_DISCORD_MESSAGE_EVALUATION", True),
            ENABLE_DISCORD_OPT_IN_SYSTEM=get_bool_env("ENABLE_DISCORD_OPT_IN_SYSTEM", True),
            ENABLE_DISCORD_CONVERSATIONAL_PIPELINE=get_bool_env("ENABLE_DISCORD_CONVERSATIONAL_PIPELINE", True),
            # Personality Evolution
            ENABLE_PERSONALITY_ADAPTATION=get_bool_env("ENABLE_PERSONALITY_ADAPTATION", True),
            ENABLE_REWARD_COMPUTATION=get_bool_env("ENABLE_REWARD_COMPUTATION", True),
            ENABLE_PERSONALITY_MEMORY=get_bool_env("ENABLE_PERSONALITY_MEMORY", True),
            # MCP Integration
            ENABLE_MCP_MEMORY=get_bool_env("ENABLE_MCP_MEMORY", True),
            ENABLE_MCP_KG=get_bool_env("ENABLE_MCP_KG", True),
            ENABLE_MCP_CREWAI=get_bool_env("ENABLE_MCP_CREWAI", True),
            ENABLE_MCP_ROUTER=get_bool_env("ENABLE_MCP_ROUTER", True),
            ENABLE_MCP_CREATOR_INTELLIGENCE=get_bool_env("ENABLE_MCP_CREATOR_INTELLIGENCE", True),
            ENABLE_MCP_OBS=get_bool_env("ENABLE_MCP_OBS", True),
            ENABLE_MCP_INGEST=get_bool_env("ENABLE_MCP_INGEST", True),
            ENABLE_MCP_HTTP=get_bool_env("ENABLE_MCP_HTTP", True),
            ENABLE_MCP_A2A=get_bool_env("ENABLE_MCP_A2A", True),
            # Model routing features
            ENABLE_RL_MODEL_ROUTING=get_bool_env("ENABLE_RL_MODEL_ROUTING", False),
            # Monitoring features
            ENABLE_METRICS=get_bool_env("ENABLE_METRICS", True),
            ENABLE_LOGGING=get_bool_env("ENABLE_LOGGING", True),
            ENABLE_TRACING=get_bool_env("ENABLE_TRACING", False),
            ENABLE_ALERTS=get_bool_env("ENABLE_ALERTS", True),
            ENABLE_OBSERVABILITY_WRAPPER=get_bool_env("ENABLE_OBSERVABILITY_WRAPPER", True),
            ENABLE_OTEL_EXPORT=get_bool_env("ENABLE_OTEL_EXPORT", False),
            # Security features
            ENABLE_PRIVACY_FILTER=get_bool_env("ENABLE_PRIVACY_FILTER", True),
            ENABLE_CONTENT_MODERATION=get_bool_env("ENABLE_CONTENT_MODERATION", True),
            ENABLE_RATE_LIMITING=get_bool_env("ENABLE_RATE_LIMITING", True),
            # Development features
            ENABLE_DEBUG_MODE=get_bool_env("ENABLE_DEBUG_MODE", False),
            ENABLE_TEST_MODE=get_bool_env("ENABLE_TEST_MODE", False),
            ENABLE_DEVELOPMENT_TOOLS=get_bool_env("ENABLE_DEVELOPMENT_TOOLS", False),
            # Enterprise features
            ENABLE_ENTERPRISE_TENANT_MANAGEMENT=get_bool_env("ENABLE_ENTERPRISE_TENANT_MANAGEMENT", False),
            # WebSocket features
            ENABLE_WEBSOCKET_UPDATES=get_bool_env("ENABLE_WEBSOCKET_UPDATES", False),
            # Orchestration features
            ENABLE_HIERARCHICAL_ORCHESTRATION=get_bool_env("ENABLE_HIERARCHICAL_ORCHESTRATION", False),
            # Crew Consolidation Flags
            ENABLE_LEGACY_CREW=get_bool_env("ENABLE_LEGACY_CREW", False),
            ENABLE_CREW_MODULAR=get_bool_env("ENABLE_CREW_MODULAR", False),
            ENABLE_CREW_REFACTORED=get_bool_env("ENABLE_CREW_REFACTORED", False),
            ENABLE_CREW_NEW=get_bool_env("ENABLE_CREW_NEW", False),
            # Agent Collaboration Features
            ENABLE_AGENT_COLLABORATION=get_bool_env("ENABLE_AGENT_COLLABORATION", False),
            ENABLE_MEMORY_COORDINATION=get_bool_env("ENABLE_MEMORY_COORDINATION", False),
            ENABLE_CREW_ANALYTICS=get_bool_env("ENABLE_CREW_ANALYTICS", False),
            # Model Spec Governance
            ENABLE_MODEL_SPEC_ENFORCEMENT=get_bool_env("ENABLE_MODEL_SPEC_ENFORCEMENT", True),
            ENABLE_RED_LINE_GUARDS=get_bool_env("ENABLE_RED_LINE_GUARDS", True),
            ENABLE_CONTENT_SAFETY_CLASSIFICATION=get_bool_env("ENABLE_CONTENT_SAFETY_CLASSIFICATION", True),
            ENABLE_CHAIN_OF_COMMAND=get_bool_env("ENABLE_CHAIN_OF_COMMAND", True),
            # Political Bias Detection
            ENABLE_POLITICAL_BIAS_DETECTION=get_bool_env("ENABLE_POLITICAL_BIAS_DETECTION", True),
            ENABLE_BIAS_METRICS_TRACKING=get_bool_env("ENABLE_BIAS_METRICS_TRACKING", True),
            ENABLE_BIAS_DASHBOARD=get_bool_env("ENABLE_BIAS_DASHBOARD", True),
            ENABLE_BIAS_MITIGATION=get_bool_env("ENABLE_BIAS_MITIGATION", True),
            # Transparency & Audit
            ENABLE_GOVERNANCE_AUDIT_TRAIL=get_bool_env("ENABLE_GOVERNANCE_AUDIT_TRAIL", True),
            ENABLE_TRANSPARENCY_REPORTS=get_bool_env("ENABLE_TRANSPARENCY_REPORTS", True),
            ENABLE_EXPLAINABILITY=get_bool_env("ENABLE_EXPLAINABILITY", True),
            # Evaluation
            ENABLE_CONTINUOUS_BIAS_EVAL=get_bool_env("ENABLE_CONTINUOUS_BIAS_EVAL", True),
            ENABLE_MODEL_SPEC_COMPLIANCE_CHECKS=get_bool_env("ENABLE_MODEL_SPEC_COMPLIANCE_CHECKS", True),
        )
