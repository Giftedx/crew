"""Tool registry for modular crew organization."""

from __future__ import annotations

from ultimate_discord_intelligence_bot.tools import (
    AdvancedPerformanceAnalyticsTool,
    AudioTranscriptionTool,
    ClaimExtractorTool,
    EnhancedAnalysisTool,
    FactCheckTool,
    MCPCallTool,
    MultiPlatformDownloadTool,
    PerspectiveSynthesizerTool,
    PipelineTool,
    TextAnalysisTool,
    TimelineTool,
)
from ultimate_discord_intelligence_bot.tools.crewai_tool_wrappers import (
    wrap_tool_for_crewai,  # type: ignore[import-not-found]
)


class ToolRegistry:
    """Registry for managing crew tools with modular organization."""

    def __init__(self):
        self._tools = {}
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize all available tools."""
        self._tools = {
            "pipeline_tool": wrap_tool_for_crewai(PipelineTool()),
            "advanced_performance_analytics_tool": wrap_tool_for_crewai(AdvancedPerformanceAnalyticsTool()),
            "timeline_tool": wrap_tool_for_crewai(TimelineTool()),
            "perspective_synthesizer_tool": wrap_tool_for_crewai(PerspectiveSynthesizerTool()),
            "mcp_call_tool": wrap_tool_for_crewai(MCPCallTool()),
            "multi_platform_download_tool": wrap_tool_for_crewai(MultiPlatformDownloadTool()),
            "audio_transcription_tool": wrap_tool_for_crewai(AudioTranscriptionTool()),
            "enhanced_analysis_tool": wrap_tool_for_crewai(EnhancedAnalysisTool()),
            "text_analysis_tool": wrap_tool_for_crewai(TextAnalysisTool()),
            "claim_extractor_tool": wrap_tool_for_crewai(ClaimExtractorTool()),
            "fact_check_tool": wrap_tool_for_crewai(FactCheckTool()),
        }

    def get_tool(self, tool_name: str):
        """Get a tool by name."""
        return self._tools.get(tool_name)

    def get_all_tools(self):
        """Get all available tools."""
        return list(self._tools.values())

    def get_tools_for_agent(self, agent_role: str) -> list:
        """Get tools appropriate for a specific agent role."""
        tool_mapping = {
            "mission_orchestrator": [
                "pipeline_tool",
                "advanced_performance_analytics_tool",
                "timeline_tool",
                "perspective_synthesizer_tool",
                "mcp_call_tool",
            ],
            "executive_supervisor": [
                "advanced_performance_analytics_tool",
                "timeline_tool",
                "perspective_synthesizer_tool",
            ],
            "workflow_manager": [
                "timeline_tool",
                "advanced_performance_analytics_tool",
            ],
            "acquisition_specialist": [
                "multi_platform_download_tool",
                "timeline_tool",
            ],
            "transcription_engineer": [
                "audio_transcription_tool",
                "timeline_tool",
            ],
            "analysis_cartographer": [
                "enhanced_analysis_tool",
                "text_analysis_tool",
                "timeline_tool",
            ],
            "verification_director": [
                "claim_extractor_tool",
                "fact_check_tool",
                "timeline_tool",
            ],
            "risk_intelligence_analyst": [
                "enhanced_analysis_tool",
                "text_analysis_tool",
                "timeline_tool",
            ],
            "persona_archivist": [
                "enhanced_analysis_tool",
                "text_analysis_tool",
                "timeline_tool",
            ],
            "knowledge_integrator": [
                "enhanced_analysis_tool",
                "text_analysis_tool",
                "timeline_tool",
            ],
            "signal_recon_specialist": [
                "enhanced_analysis_tool",
                "text_analysis_tool",
                "timeline_tool",
            ],
            "trend_intelligence_scout": [
                "enhanced_analysis_tool",
                "text_analysis_tool",
                "timeline_tool",
            ],
            "research_synthesist": [
                "enhanced_analysis_tool",
                "text_analysis_tool",
                "timeline_tool",
            ],
            "intelligence_briefing_curator": [
                "enhanced_analysis_tool",
                "text_analysis_tool",
                "timeline_tool",
            ],
            "argument_strategist": [
                "enhanced_analysis_tool",
                "text_analysis_tool",
                "timeline_tool",
            ],
            "system_reliability_officer": [
                "advanced_performance_analytics_tool",
                "timeline_tool",
            ],
            "community_liaison": [
                "enhanced_analysis_tool",
                "text_analysis_tool",
                "timeline_tool",
            ],
            "autonomous_mission_coordinator": [
                "pipeline_tool",
                "advanced_performance_analytics_tool",
                "timeline_tool",
                "perspective_synthesizer_tool",
                "mcp_call_tool",
            ],
        }

        # Get tools for the specific role, or return all tools if role not found
        tool_names = tool_mapping.get(agent_role, list(self._tools.keys()))
        return [self._tools[name] for name in tool_names if name in self._tools]

    def register_tool(self, name: str, tool):
        """Register a new tool."""
        self._tools[name] = tool

    def unregister_tool(self, name: str):
        """Unregister a tool."""
        if name in self._tools:
            del self._tools[name]

    def list_tools(self) -> list[str]:
        """List all available tool names."""
        return list(self._tools.keys())

    def get_tool_count(self) -> int:
        """Get the total number of registered tools."""
        return len(self._tools)
