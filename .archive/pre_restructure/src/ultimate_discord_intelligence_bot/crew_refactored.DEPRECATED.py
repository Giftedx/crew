"""DEPRECATED: This file is deprecated and will be removed in a future version.
Please use ultimate_discord_intelligence_bot.crew_core instead.

Migration guide:
- Import from crew_core instead of this module
- Use UnifiedCrewExecutor for crew execution
- Use CrewErrorHandler for error handling
- Use CrewInsightGenerator for insight generation

Example:
    from ultimate_discord_intelligence_bot.crew_core import (
        UnifiedCrewExecutor,
        CrewConfig,
        CrewTask,
    )

Refactored crew orchestrator with modular organization.

This module provides a clean, modular interface to the UltimateDiscordIntelligenceBotCrew
using the new crew_components architecture. This replaces the monolithic crew.py file
with a more maintainable, testable, and extensible design.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.crew_components import (
    AgentRegistry,
    CrewExecutor,
    CrewMonitor,
    TaskRegistry,
    ToolRegistry,
)
from ultimate_discord_intelligence_bot.settings import get_settings


warnings.warn(
    "This module is deprecated. Use ultimate_discord_intelligence_bot.crew_core instead.",
    DeprecationWarning,
    stacklevel=2,
)


if TYPE_CHECKING:
    from crewai import Agent, Crew, Task


class UltimateDiscordIntelligenceBotCrew:
    """Refactored autonomous intelligence crew with modular organization."""

    def __init__(self):
        self.settings = get_settings()

        # Initialize modular components
        self.agent_registry = AgentRegistry()
        self.task_registry = TaskRegistry(self.agent_registry)
        self.tool_registry = ToolRegistry()
        self.crew_executor = CrewExecutor(self.agent_registry, self.task_registry, self.tool_registry)
        self.crew_monitor = CrewMonitor()

    # ========================================
    # LEGACY COMPATIBILITY METHODS
    # ========================================
    # These methods maintain compatibility with existing code
    # while delegating to the modular components

    def run_langgraph_if_enabled(self, url: str, quality: str = "1080p") -> dict:
        """Optional LangGraph execution path controlled by feature flag."""
        return self.crew_executor.run_langgraph_if_enabled(url, quality)

    # Agent methods for backward compatibility
    def mission_orchestrator(self) -> Agent:
        """Mission orchestrator agent."""
        return self.agent_registry.mission_orchestrator()

    def executive_supervisor(self) -> Agent:
        """Executive supervisor agent."""
        return self.agent_registry.executive_supervisor()

    def workflow_manager(self) -> Agent:
        """Workflow manager agent."""
        return self.agent_registry.workflow_manager()

    def acquisition_specialist(self) -> Agent:
        """Acquisition specialist agent."""
        return self.agent_registry.acquisition_specialist()

    def transcription_engineer(self) -> Agent:
        """Transcription engineer agent."""
        return self.agent_registry.transcription_engineer()

    def analysis_cartographer(self) -> Agent:
        """Analysis cartographer agent."""
        return self.agent_registry.analysis_cartographer()

    def verification_director(self) -> Agent:
        """Verification director agent."""
        return self.agent_registry.verification_director()

    def risk_intelligence_analyst(self) -> Agent:
        """Risk intelligence analyst agent."""
        return self.agent_registry.risk_intelligence_analyst()

    def persona_archivist(self) -> Agent:
        """Persona archivist agent."""
        return self.agent_registry.persona_archivist()

    def knowledge_integrator(self) -> Agent:
        """Knowledge integrator agent."""
        return self.agent_registry.knowledge_integrator()

    def signal_recon_specialist(self) -> Agent:
        """Signal recon specialist agent."""
        return self.agent_registry.signal_recon_specialist()

    def trend_intelligence_scout(self) -> Agent:
        """Trend intelligence scout agent."""
        return self.agent_registry.trend_intelligence_scout()

    def research_synthesist(self) -> Agent:
        """Research synthesist agent."""
        return self.agent_registry.research_synthesist()

    def intelligence_briefing_curator(self) -> Agent:
        """Intelligence briefing curator agent."""
        return self.agent_registry.intelligence_briefing_curator()

    def argument_strategist(self) -> Agent:
        """Argument strategist agent."""
        return self.agent_registry.argument_strategist()

    def system_reliability_officer(self) -> Agent:
        """System reliability officer agent."""
        return self.agent_registry.system_reliability_officer()

    def community_liaison(self) -> Agent:
        """Community liaison agent."""
        return self.agent_registry.community_liaison()

    def autonomous_mission_coordinator(self) -> Agent:
        """Autonomous mission coordinator agent."""
        return self.agent_registry.autonomous_mission_coordinator()

    def multi_platform_acquisition_specialist(self) -> Agent:
        """Multi-platform acquisition specialist agent."""
        return self.agent_registry.multi_platform_acquisition_specialist()

    def advanced_transcription_engineer(self) -> Agent:
        """Advanced transcription engineer agent."""
        return self.agent_registry.advanced_transcription_engineer()

    def comprehensive_linguistic_analyst(self) -> Agent:
        """Comprehensive linguistic analyst agent."""
        return self.agent_registry.comprehensive_linguistic_analyst()

    def information_verification_director(self) -> Agent:
        """Information verification director agent."""
        return self.agent_registry.information_verification_director()

    def threat_intelligence_analyst(self) -> Agent:
        """Threat intelligence analyst agent."""
        return self.agent_registry.threat_intelligence_analyst()

    def behavioral_profiling_specialist(self) -> Agent:
        """Behavioral profiling specialist agent."""
        return self.agent_registry.behavioral_profiling_specialist()

    def knowledge_integration_architect(self) -> Agent:
        """Knowledge integration architect agent."""
        return self.agent_registry.knowledge_integration_architect()

    def social_intelligence_coordinator(self) -> Agent:
        """Social intelligence coordinator agent."""
        return self.agent_registry.social_intelligence_coordinator()

    def trend_analysis_scout(self) -> Agent:
        """Trend analysis scout agent."""
        return self.agent_registry.trend_analysis_scout()

    def research_synthesis_specialist(self) -> Agent:
        """Research synthesis specialist agent."""
        return self.agent_registry.research_synthesis_specialist()

    def intelligence_briefing_director(self) -> Agent:
        """Intelligence briefing director agent."""
        return self.agent_registry.intelligence_briefing_director()

    def strategic_argument_analyst(self) -> Agent:
        """Strategic argument analyst agent."""
        return self.agent_registry.strategic_argument_analyst()

    def system_operations_manager(self) -> Agent:
        """System operations manager agent."""
        return self.agent_registry.system_operations_manager()

    def community_engagement_coordinator(self) -> Agent:
        """Community engagement coordinator agent."""
        return self.agent_registry.community_engagement_coordinator()

    def personality_synthesis_manager(self) -> Agent:
        """Personality synthesis manager agent."""
        return self.agent_registry.personality_synthesis_manager()

    def visual_intelligence_specialist(self) -> Agent:
        """Visual intelligence specialist agent."""
        return self.agent_registry.visual_intelligence_specialist()

    def audio_intelligence_specialist(self) -> Agent:
        """Audio intelligence specialist agent."""
        return self.agent_registry.audio_intelligence_specialist()

    def trend_intelligence_specialist(self) -> Agent:
        """Trend intelligence specialist agent."""
        return self.agent_registry.trend_intelligence_specialist()

    def content_generation_specialist(self) -> Agent:
        """Content generation specialist agent."""
        return self.agent_registry.content_generation_specialist()

    def cross_platform_intelligence_specialist(self) -> Agent:
        """Cross-platform intelligence specialist agent."""
        return self.agent_registry.cross_platform_intelligence_specialist()

    # Task methods for backward compatibility
    def plan_autonomy_mission(self) -> Task:
        """Plan autonomy mission task."""
        return self.task_registry.plan_autonomy_mission()

    def capture_source_media(self) -> Task:
        """Capture source media task."""
        return self.task_registry.capture_source_media()

    def transcribe_and_index_media(self) -> Task:
        """Transcribe and index media task."""
        return self.task_registry.transcribe_and_index_media()

    def map_transcript_insights(self) -> Task:
        """Map transcript insights task."""
        return self.task_registry.map_transcript_insights()

    def verify_priority_claims(self) -> Task:
        """Verify priority claims task."""
        return self.task_registry.verify_priority_claims()

    # Crew method for backward compatibility
    def crew(self) -> Crew:
        """Get the configured crew."""
        return self.crew_executor.create_crew()

    # ========================================
    # ENHANCED MODULAR INTERFACE
    # ========================================
    # New methods that provide enhanced functionality

    def execute_with_monitoring(self, inputs: dict[str, Any]) -> Any:
        """Execute crew with comprehensive monitoring."""
        self.crew_monitor.start_execution(inputs)

        try:
            result = self.crew_executor.execute_crew(inputs)
            self.crew_monitor.end_execution(result, success=True)
            return result
        except Exception:
            self.crew_monitor.end_execution(None, success=False)
            raise

    def get_crew_info(self) -> dict[str, Any]:
        """Get comprehensive crew information."""
        return self.crew_executor.get_crew_info()

    def get_execution_summary(self) -> dict[str, Any]:
        """Get execution summary and metrics."""
        return self.crew_monitor.get_execution_summary()

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics."""
        return self.crew_monitor.get_performance_metrics()

    def get_health_status(self) -> dict[str, Any]:
        """Get crew health status."""
        return self.crew_monitor.get_health_status()

    def reset_monitoring(self) -> None:
        """Reset monitoring metrics."""
        self.crew_monitor.reset_metrics()

    # ========================================
    # COMPONENT ACCESS
    # ========================================
    # Direct access to components for advanced usage

    @property
    def agents(self) -> AgentRegistry:
        """Access to agent registry."""
        return self.agent_registry

    @property
    def tasks(self) -> TaskRegistry:
        """Access to task registry."""
        return self.task_registry

    @property
    def tools(self) -> ToolRegistry:
        """Access to tool registry."""
        return self.tool_registry

    @property
    def executor(self) -> CrewExecutor:
        """Access to crew executor."""
        return self.crew_executor

    @property
    def monitor(self) -> CrewMonitor:
        """Access to crew monitor."""
        return self.crew_monitor
