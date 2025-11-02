"""Agent Bridge Package - Cross-agent knowledge sharing and learning

This package provides unified interfaces for agents to share insights,
learn from each other's experiences, and build collective intelligence.
"""

from .agent_bridge import AgentBridge, AgentBridgeConfig
from .collective_intelligence import (
    AgentContribution,
    CollectiveInsight,
    CollectiveIntelligenceConfig,
    CollectiveIntelligenceService,
    IntelligenceLevel,
    SynthesisRequest,
    SynthesisResponse,
    SynthesisType,
)
from .cross_agent_learning import (
    CrossAgentLearningConfig,
    CrossAgentLearningService,
    LearningPattern,
    LearningRequest,
    LearningResponse,
    LearningSource,
    LearningType,
)
from .knowledge_bridge import (
    AgentInsight,
    AgentKnowledgeBridge,
    InsightPriority,
    InsightRequest,
    InsightResponse,
    InsightType,
    KnowledgeBridgeConfig,
)


__all__ = [
    # Main bridge interface
    "AgentBridge",
    "AgentBridgeConfig",
    "AgentContribution",
    "AgentInsight",
    # Knowledge bridge
    "AgentKnowledgeBridge",
    "CollectiveInsight",
    "CollectiveIntelligenceConfig",
    # Collective intelligence
    "CollectiveIntelligenceService",
    "CrossAgentLearningConfig",
    # Cross-agent learning
    "CrossAgentLearningService",
    "InsightPriority",
    "InsightRequest",
    "InsightResponse",
    "InsightType",
    "IntelligenceLevel",
    "KnowledgeBridgeConfig",
    "LearningPattern",
    "LearningRequest",
    "LearningResponse",
    "LearningSource",
    "LearningType",
    "SynthesisRequest",
    "SynthesisResponse",
    "SynthesisType",
]
