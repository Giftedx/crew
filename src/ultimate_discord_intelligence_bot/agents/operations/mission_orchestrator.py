"""Mission Orchestrator Agent.

This agent coordinates end-to-end missions, sequencing depth, specialists, and budgets.
"""

from __future__ import annotations

from ultimate_discord_intelligence_bot.agents.base import BaseAgent
from ultimate_discord_intelligence_bot.agents.registry import register_agent
from ultimate_discord_intelligence_bot.settings import (
    ENABLE_AGENT_BRIDGE,
    ENABLE_DASHBOARD_INTEGRATION,
    ENABLE_INTELLIGENT_ALERTING,
    ENABLE_UNIFIED_CACHE,
    ENABLE_UNIFIED_KNOWLEDGE,
    ENABLE_UNIFIED_METRICS,
    ENABLE_UNIFIED_ORCHESTRATION,
    ENABLE_UNIFIED_ROUTER,
)
from ultimate_discord_intelligence_bot.tools import (
    AdvancedPerformanceAnalyticsTool,
    CheckpointManagementTool,
    MCPCallTool,
    Mem0MemoryTool,
    MultimodalAnalysisTool,
    PerspectiveSynthesizerTool,
    PipelineTool,
    TimelineTool,
)
from ultimate_discord_intelligence_bot.tools._base import BaseTool
from ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool import (
    UnifiedContextTool,
    UnifiedMemoryStoreTool,
    UnifiedMemoryTool,
)
from ultimate_discord_intelligence_bot.tools.observability.agent_bridge_tool import (
    AgentBridgeTool,
    InsightSharingTool,
    LearningTool,
)
from ultimate_discord_intelligence_bot.tools.observability.observability_tool import (
    DashboardIntegrationTool,
    IntelligentAlertingTool,
    UnifiedMetricsTool,
)
from ultimate_discord_intelligence_bot.tools.observability.unified_cache_tool import (
    CacheOptimizationTool,
    CacheStatusTool,
    UnifiedCacheTool,
)
from ultimate_discord_intelligence_bot.tools.observability.unified_orchestration_tool import (
    OrchestrationStatusTool,
    TaskManagementTool,
    UnifiedOrchestrationTool,
)
from ultimate_discord_intelligence_bot.tools.observability.unified_router_tool import (
    CostTrackingTool,
    RouterStatusTool,
    UnifiedRouterTool,
)


@register_agent("mission_orchestrator")
class MissionOrchestratorAgent(BaseAgent):
    """Mission Orchestrator Agent for autonomous intelligence operations."""

    def __init__(self):
        """Initialize the mission orchestrator with its tools."""
        tools = self._get_core_tools()
        super().__init__(tools)

    @property
    def role(self) -> str:
        """Agent role."""
        return "Autonomy Mission Orchestrator"

    @property
    def goal(self) -> str:
        """Agent goal."""
        return "Coordinate end-to-end missions, sequencing depth, specialists, and budgets."

    @property
    def backstory(self) -> str:
        """Agent backstory."""
        return "Mission orchestration and strategic control with multimodal planning capabilities."

    @property
    def allow_delegation(self) -> bool:
        """Allow delegation to other agents."""
        return True

    def _get_core_tools(self) -> list[BaseTool]:
        """Get core tools for mission orchestration."""
        tools = [
            # Core orchestration tools
            PipelineTool(),
            AdvancedPerformanceAnalyticsTool(),
            TimelineTool(),
            PerspectiveSynthesizerTool(),
            MCPCallTool(),
            MultimodalAnalysisTool(),
            Mem0MemoryTool(),
            CheckpointManagementTool(),
        ]

        # Add conditional tools based on feature flags
        if ENABLE_UNIFIED_KNOWLEDGE:
            tools.extend(
                [
                    UnifiedMemoryTool(),
                    UnifiedMemoryStoreTool(),
                    UnifiedContextTool(),
                ]
            )

        if ENABLE_UNIFIED_ROUTER:
            tools.extend(
                [
                    UnifiedRouterTool(),
                    CostTrackingTool(),
                    RouterStatusTool(),
                ]
            )

        if ENABLE_UNIFIED_CACHE:
            tools.extend(
                [
                    UnifiedCacheTool(),
                    CacheOptimizationTool(),
                    CacheStatusTool(),
                ]
            )

        if ENABLE_UNIFIED_ORCHESTRATION:
            tools.extend(
                [
                    UnifiedOrchestrationTool(),
                    TaskManagementTool(),
                    OrchestrationStatusTool(),
                ]
            )

        if ENABLE_AGENT_BRIDGE:
            tools.extend(
                [
                    AgentBridgeTool(),
                    InsightSharingTool(),
                    LearningTool(),
                ]
            )

        if ENABLE_UNIFIED_METRICS or ENABLE_INTELLIGENT_ALERTING or ENABLE_DASHBOARD_INTEGRATION:
            tools.extend(
                [
                    UnifiedMetricsTool(),
                    IntelligentAlertingTool(),
                    DashboardIntegrationTool(),
                ]
            )

        return tools
