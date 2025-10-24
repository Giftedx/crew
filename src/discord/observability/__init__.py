"""
Observability module for Discord AI chatbot.

This module provides comprehensive observability capabilities including:
- Metrics collection and monitoring
- Conversation tracing and analysis
- Personality dashboard and analytics
- Unified observability management
"""

from .conversation_tracer import ConversationTracer, create_conversation_tracer
from .metrics_collector import (
    ConversationMetrics,
    DiscordMetricsCollector,
    GuildMetrics,
    PersonalityMetrics,
    UserEngagementMetrics,
    create_discord_metrics_collector,
)
from .observability_manager import ObservabilityManager, create_observability_manager
from .personality_dashboard import (
    PersonalityAnalytics,
    PersonalityDashboard,
    PersonalityEvolution,
    PersonalityTraitSnapshot,
    UserPersonalityProfile,
    create_personality_dashboard,
)


__all__ = [
    # Metrics collection
    "DiscordMetricsCollector",
    "ConversationMetrics",
    "UserEngagementMetrics",
    "GuildMetrics",
    "PersonalityMetrics",
    "create_discord_metrics_collector",
    # Conversation tracing
    "ConversationTracer",
    "create_conversation_tracer",
    # Personality dashboard
    "PersonalityDashboard",
    "PersonalityTraitSnapshot",
    "PersonalityEvolution",
    "UserPersonalityProfile",
    "PersonalityAnalytics",
    "create_personality_dashboard",
    # Unified management
    "ObservabilityManager",
    "create_observability_manager",
]
