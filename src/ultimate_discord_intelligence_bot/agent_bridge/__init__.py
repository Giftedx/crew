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
    # Knowledge bridge
    "AgentKnowledgeBridge",
    "KnowledgeBridgeConfig",
    "InsightType",
    "InsightPriority",
    "AgentInsight",
    "InsightRequest",
    "InsightResponse",
    # Cross-agent learning
    "CrossAgentLearningService",
    "CrossAgentLearningConfig",
    "LearningType",
    "LearningSource",
    "LearningPattern",
    "LearningRequest",
    "LearningResponse",
    # Collective intelligence
    "CollectiveIntelligenceService",
    "CollectiveIntelligenceConfig",
    "SynthesisType",
    "IntelligenceLevel",
    "AgentContribution",
    "CollectiveInsight",
    "SynthesisRequest",
    "SynthesisResponse",
]
