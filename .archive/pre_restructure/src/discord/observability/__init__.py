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
    "ConversationMetrics",
    # Conversation tracing
    "ConversationTracer",
    # Metrics collection
    "DiscordMetricsCollector",
    "GuildMetrics",
    # Unified management
    "ObservabilityManager",
    "PersonalityAnalytics",
    # Personality dashboard
    "PersonalityDashboard",
    "PersonalityEvolution",
    "PersonalityMetrics",
    "PersonalityTraitSnapshot",
    "UserEngagementMetrics",
    "UserPersonalityProfile",
    "create_conversation_tracer",
    "create_discord_metrics_collector",
    "create_observability_manager",
    "create_personality_dashboard",
]
