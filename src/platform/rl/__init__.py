"""
AI Module for Ultimate Discord Intelligence Bot

Advanced AI capabilities including:
- Contextual bandits with DoublyRobust and OffsetTree algorithms
- Multi-domain orchestration and optimization
- A/B testing framework and performance monitoring
- AI-enhanced routing and performance optimization
"""

from .advanced_contextual_bandits import (
    AdvancedBanditsOrchestrator,
    BanditAction,
    BanditContext,
    BanditFeedback,
    DoublyRobustBandit,
    OffsetTreeBandit,
    create_bandit_context,
    get_orchestrator,
    initialize_advanced_bandits,
    simulate_reward,
)


__all__ = [
    "AdvancedBanditsOrchestrator",
    "BanditAction",
    "BanditContext",
    "BanditFeedback",
    "DoublyRobustBandit",
    "OffsetTreeBandit",
    "create_bandit_context",
    "get_orchestrator",
    "initialize_advanced_bandits",
    "simulate_reward",
]
