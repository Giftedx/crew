"""Intelligence agents for research and knowledge management.

This module contains agents responsible for research, knowledge synthesis,
and intelligence gathering across multiple sources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from crewai import Agent
from domains.intelligence.analysis import EnhancedAnalysisTool, TextAnalysisTool
from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags
from ultimate_discord_intelligence_bot.tools import (
    CrossPlatformNarrativeTrackingTool,
    GraphMemoryTool,
    InsightSharingTool,
    KnowledgeOpsTool,
    Mem0MemoryTool,
    NarrativeTrackerTool,
    RagHybridTool,
    RagIngestTool,
    RagIngestUrlTool,
    RagQueryVectorStoreTool,
    ResearchAndBriefMultiTool,
    ResearchAndBriefTool,
    StrategicPlanningTool,
    TimelineTool,
    UnifiedMemoryTool,
    VectorSearchTool,
)
from ultimate_discord_intelligence_bot.tools.memory import OfflineRagTool


_flags = FeatureFlags.from_env()


class IntelligenceAgents:
    """Intelligence agents for research and knowledge management."""

    def __init__(self):
        """Initialize intelligence agents."""
        self.flags = _flags

    def research_specialist(self) -> Agent:
        """Research and briefing specialist."""
        from crewai import Agent

        return Agent(
            role="Research Specialist",
            goal="Conduct comprehensive research and generate detailed briefings with source verification.",
            backstory="Expert in research and briefing with focus on comprehensive information gathering and analysis.",
            tools=[
                ResearchAndBriefTool(),
                ResearchAndBriefMultiTool(),
                RagHybridTool(),
                RagIngestTool(),
                RagIngestUrlTool(),
                OfflineRagTool(),
                VectorSearchTool(),
                RagQueryVectorStoreTool(),
            ],
            verbose=True,
            allow_delegation=False,
        )

    def intelligence_synthesis_specialist(self) -> Agent:
        """Intelligence synthesis specialist."""
        from crewai import Agent

        return Agent(
            role="Intelligence Synthesis Specialist",
            goal="Synthesize intelligence from multiple sources into coherent, actionable insights.",
            backstory="Specialist in intelligence synthesis with expertise in combining diverse information sources.",
            tools=[ResearchAndBriefMultiTool(), RagHybridTool(), UnifiedMemoryTool(), InsightSharingTool()],
            verbose=True,
            allow_delegation=False,
        )

    def knowledge_management_specialist(self) -> Agent:
        """Knowledge management specialist."""
        from crewai import Agent

        return Agent(
            role="Knowledge Management Specialist",
            goal="Manage knowledge base and ensure information quality and accessibility.",
            backstory="Expert in knowledge management with focus on information organization and retrieval.",
            tools=[
                UnifiedMemoryTool(),
                Mem0MemoryTool(),
                GraphMemoryTool(),
                VectorSearchTool(),
                RagQueryVectorStoreTool(),
                KnowledgeOpsTool(),
            ],
            verbose=True,
            allow_delegation=False,
        )

    def strategic_intelligence_specialist(self) -> Agent:
        """Strategic intelligence specialist."""
        from crewai import Agent

        return Agent(
            role="Strategic Intelligence Specialist",
            goal="Provide strategic intelligence and planning support with comprehensive analysis.",
            backstory="Specialist in strategic intelligence with expertise in long-term planning and analysis.",
            tools=[
                StrategicPlanningTool(),
                ResearchAndBriefMultiTool(),
                RagHybridTool(),
                TimelineTool(),
                NarrativeTrackerTool(),
                CrossPlatformNarrativeTrackingTool(),
                InsightSharingTool(),
            ],
            verbose=True,
            allow_delegation=False,
        )

    def narrative_tracking_specialist(self) -> Agent:
        """Narrative tracking specialist."""
        from crewai import Agent

        return Agent(
            role="Narrative Tracking Specialist",
            goal="Track narratives and storylines across platforms with comprehensive monitoring.",
            backstory="Expert in narrative tracking with focus on story development and cross-platform monitoring.",
            tools=[
                NarrativeTrackerTool(),
                CrossPlatformNarrativeTrackingTool(),
                TimelineTool(),
                TextAnalysisTool(),
                EnhancedAnalysisTool(),
            ],
            verbose=True,
            allow_delegation=False,
        )

    def collective_intelligence_specialist(self) -> Agent:
        """Collective intelligence specialist."""
        from crewai import Agent

        return Agent(
            role="Collective Intelligence Specialist",
            goal="Harness collective intelligence from multiple sources for comprehensive insights.",
            backstory="Specialist in collective intelligence with expertise in crowd-sourced information and analysis.",
            tools=[InsightSharingTool(), ResearchAndBriefMultiTool(), RagHybridTool(), UnifiedMemoryTool()],
            verbose=True,
            allow_delegation=False,
        )

    def memory_management_specialist(self) -> Agent:
        """Memory management specialist."""
        from crewai import Agent

        return Agent(
            role="Memory Management Specialist",
            goal="Manage memory systems and ensure optimal information storage and retrieval.",
            backstory="Expert in memory management with focus on efficient information storage and retrieval.",
            tools=[
                UnifiedMemoryTool(),
                Mem0MemoryTool(),
                GraphMemoryTool(),
                VectorSearchTool(),
                RagQueryVectorStoreTool(),
                KnowledgeOpsTool(),
            ],
            verbose=True,
            allow_delegation=False,
        )
