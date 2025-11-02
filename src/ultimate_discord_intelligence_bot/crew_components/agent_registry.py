"""Agent registry for modular crew organization."""
from __future__ import annotations
from typing import TYPE_CHECKING
from app.config.settings import get_settings
from ultimate_discord_intelligence_bot.tools import AdvancedPerformanceAnalyticsTool, AudioTranscriptionTool, ClaimExtractorTool, EnhancedAnalysisTool, FactCheckTool, MCPCallTool, MultiPlatformDownloadTool, PerspectiveSynthesizerTool, PipelineTool, TextAnalysisTool, TimelineTool
from ultimate_discord_intelligence_bot.tools.crewai_tool_wrappers import wrap_tool_for_crewai
if TYPE_CHECKING:
    from crewai import Agent

class AgentRegistry:
    """Registry for managing crew agents with modular organization."""

    def __init__(self):
        self.settings = get_settings()

    def mission_orchestrator(self) -> Agent:
        """Mission orchestrator agent for end-to-end coordination."""
        from crewai import Agent
        return Agent(role='Autonomy Mission Orchestrator', goal='Coordinate end-to-end missions, sequencing depth, specialists, and budgets.', backstory='Mission orchestration and strategic control with multimodal planning capabilities.', tools=[wrap_tool_for_crewai(PipelineTool()), wrap_tool_for_crewai(AdvancedPerformanceAnalyticsTool()), wrap_tool_for_crewai(TimelineTool()), wrap_tool_for_crewai(PerspectiveSynthesizerTool()), wrap_tool_for_crewai(MCPCallTool())], verbose=True, allow_delegation=True, max_iter=3, memory=True)

    def executive_supervisor(self) -> Agent:
        """Executive supervisor for high-level oversight."""
        from crewai import Agent
        return Agent(role='Executive Supervisor', goal='Provide strategic oversight and quality assurance for intelligence operations.', backstory='Senior executive with deep experience in intelligence operations and strategic planning.', tools=[wrap_tool_for_crewai(AdvancedPerformanceAnalyticsTool()), wrap_tool_for_crewai(TimelineTool()), wrap_tool_for_crewai(PerspectiveSynthesizerTool())], verbose=True, allow_delegation=True, max_iter=2, memory=True)

    def workflow_manager(self) -> Agent:
        """Workflow manager for operational coordination."""
        from crewai import Agent
        return Agent(role='Workflow Manager', goal='Manage operational workflows and resource allocation.', backstory='Experienced operations manager with expertise in workflow optimization.', tools=[wrap_tool_for_crewai(TimelineTool()), wrap_tool_for_crewai(AdvancedPerformanceAnalyticsTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def acquisition_specialist(self) -> Agent:
        """Specialist for content acquisition across platforms."""
        from crewai import Agent
        return Agent(role='Multi-Platform Acquisition Specialist', goal='Download and acquire content from various platforms with optimal quality and format selection.', backstory='Expert in content acquisition with deep knowledge of platform APIs and download optimization.', tools=[wrap_tool_for_crewai(MultiPlatformDownloadTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def transcription_engineer(self) -> Agent:
        """Engineer for audio/video transcription."""
        from crewai import Agent
        return Agent(role='Transcription Engineer', goal='Convert audio/video content to accurate, timestamped transcripts with quality indicators.', backstory='Expert in audio processing and transcription with focus on accuracy and quality.', tools=[wrap_tool_for_crewai(AudioTranscriptionTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def analysis_cartographer(self) -> Agent:
        """Analyst for mapping content insights and themes."""
        from crewai import Agent
        return Agent(role='Analysis Cartographer', goal='Map content insights, identify themes, and create structured analysis reports.', backstory='Expert analyst with deep understanding of content analysis and insight mapping.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def verification_director(self) -> Agent:
        """Director for claim verification and fact-checking."""
        from crewai import Agent
        return Agent(role='Verification Director', goal='Extract and verify claims, identify fallacies, and provide fact-checking analysis.', backstory='Expert in verification and fact-checking with deep knowledge of logical fallacies and verification methods.', tools=[wrap_tool_for_crewai(ClaimExtractorTool()), wrap_tool_for_crewai(FactCheckTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def risk_intelligence_analyst(self) -> Agent:
        """Analyst for risk assessment and threat intelligence."""
        from crewai import Agent
        return Agent(role='Risk Intelligence Analyst', goal='Assess risks, identify threats, and provide intelligence on potential issues.', backstory='Expert in risk assessment and threat intelligence with focus on security and safety.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def persona_archivist(self) -> Agent:
        """Archivist for persona and behavioral analysis."""
        from crewai import Agent
        return Agent(role='Persona Archivist', goal='Analyze personas, behavioral patterns, and create comprehensive personality profiles.', backstory='Expert in behavioral analysis and persona profiling with deep understanding of human psychology.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def knowledge_integrator(self) -> Agent:
        """Integrator for knowledge synthesis and integration."""
        from crewai import Agent

        def embedding_function(text: str) -> list[float]:
            """Simple embedding function for knowledge integration."""
            import hashlib
            digest = hashlib.sha256(text.encode('utf-8')).digest() if text else b'\x00'
            vector: list[float] = []
            for idx in range(384):
                byte = digest[idx % len(digest)]
                vector.append(byte / 255.0)
            return vector
        return Agent(role='Knowledge Integrator', goal='Integrate knowledge from multiple sources and create comprehensive intelligence reports.', backstory='Expert in knowledge integration and synthesis with focus on creating comprehensive intelligence.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True, embedding_function=embedding_function)

    def signal_recon_specialist(self) -> Agent:
        """Specialist for signal reconnaissance and intelligence gathering."""
        from crewai import Agent
        return Agent(role='Signal Reconnaissance Specialist', goal='Gather intelligence from signals, communications, and digital sources.', backstory='Expert in signal intelligence and reconnaissance with deep technical knowledge.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def trend_intelligence_scout(self) -> Agent:
        """Scout for trend analysis and intelligence gathering."""
        from crewai import Agent
        return Agent(role='Trend Intelligence Scout', goal='Identify trends, patterns, and emerging intelligence from content analysis.', backstory='Expert in trend analysis and pattern recognition with focus on emerging intelligence.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def research_synthesist(self) -> Agent:
        """Synthesist for research integration and synthesis."""
        from crewai import Agent
        return Agent(role='Research Synthesist', goal='Synthesize research findings and create comprehensive intelligence reports.', backstory='Expert in research synthesis and intelligence reporting with focus on comprehensive analysis.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def intelligence_briefing_curator(self) -> Agent:
        """Curator for intelligence briefing and presentation."""
        from crewai import Agent
        return Agent(role='Intelligence Briefing Curator', goal='Create comprehensive intelligence briefings and presentations for stakeholders.', backstory='Expert in intelligence presentation and briefing with focus on clear communication.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def argument_strategist(self) -> Agent:
        """Strategist for argument analysis and strategy development."""
        from crewai import Agent
        return Agent(role='Argument Strategist', goal='Analyze arguments, identify strategies, and provide strategic intelligence.', backstory='Expert in argument analysis and strategic thinking with focus on logical reasoning.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def system_reliability_officer(self) -> Agent:
        """Officer for system reliability and performance monitoring."""
        from crewai import Agent
        return Agent(role='System Reliability Officer', goal='Monitor system performance, ensure reliability, and optimize operations.', backstory='Expert in system reliability and performance optimization with focus on operational excellence.', tools=[wrap_tool_for_crewai(AdvancedPerformanceAnalyticsTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def community_liaison(self) -> Agent:
        """Liaison for community engagement and communication."""
        from crewai import Agent
        return Agent(role='Community Liaison', goal='Engage with communities, gather feedback, and facilitate communication.', backstory='Expert in community engagement and communication with focus on stakeholder relations.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def autonomous_mission_coordinator(self) -> Agent:
        """Coordinator for autonomous mission execution."""
        from crewai import Agent
        return Agent(role='Autonomous Mission Coordinator', goal='Coordinate autonomous missions and ensure successful execution.', backstory='Expert in autonomous mission coordination with focus on independent operation.', tools=[wrap_tool_for_crewai(PipelineTool()), wrap_tool_for_crewai(AdvancedPerformanceAnalyticsTool()), wrap_tool_for_crewai(TimelineTool()), wrap_tool_for_crewai(PerspectiveSynthesizerTool()), wrap_tool_for_crewai(MCPCallTool())], verbose=True, allow_delegation=True, max_iter=3, memory=True)

    def multi_platform_acquisition_specialist(self) -> Agent:
        """Specialist for multi-platform content acquisition."""
        from crewai import Agent
        return Agent(role='Multi-Platform Acquisition Specialist', goal='Acquire content from multiple platforms with optimal quality and efficiency.', backstory='Expert in multi-platform content acquisition with deep knowledge of various platforms.', tools=[wrap_tool_for_crewai(MultiPlatformDownloadTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def advanced_transcription_engineer(self) -> Agent:
        """Advanced engineer for sophisticated transcription tasks."""
        from crewai import Agent
        return Agent(role='Advanced Transcription Engineer', goal='Perform advanced transcription with high accuracy and quality indicators.', backstory='Expert in advanced transcription techniques with focus on accuracy and quality.', tools=[wrap_tool_for_crewai(AudioTranscriptionTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def comprehensive_linguistic_analyst(self) -> Agent:
        """Analyst for comprehensive linguistic analysis."""
        from crewai import Agent
        return Agent(role='Comprehensive Linguistic Analyst', goal='Perform comprehensive linguistic analysis with deep language understanding.', backstory='Expert in linguistic analysis with deep understanding of language patterns and structures.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def information_verification_director(self) -> Agent:
        """Director for comprehensive information verification."""
        from crewai import Agent
        return Agent(role='Information Verification Director', goal='Direct comprehensive information verification and fact-checking operations.', backstory='Expert in information verification with focus on accuracy and reliability.', tools=[wrap_tool_for_crewai(ClaimExtractorTool()), wrap_tool_for_crewai(FactCheckTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def threat_intelligence_analyst(self) -> Agent:
        """Analyst for threat intelligence and security assessment."""
        from crewai import Agent
        return Agent(role='Threat Intelligence Analyst', goal='Assess threats, analyze security risks, and provide threat intelligence.', backstory='Expert in threat intelligence with focus on security and risk assessment.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def behavioral_profiling_specialist(self) -> Agent:
        """Specialist for behavioral profiling and analysis."""
        from crewai import Agent
        return Agent(role='Behavioral Profiling Specialist', goal='Profile behaviors, analyze patterns, and create behavioral intelligence.', backstory='Expert in behavioral analysis with focus on profiling and pattern recognition.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def knowledge_integration_architect(self) -> Agent:
        """Architect for knowledge integration and synthesis."""
        from crewai import Agent
        return Agent(role='Knowledge Integration Architect', goal='Architect knowledge integration systems and create comprehensive intelligence frameworks.', backstory='Expert in knowledge architecture with focus on integration and synthesis.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def social_intelligence_coordinator(self) -> Agent:
        """Coordinator for social intelligence and community analysis."""
        from crewai import Agent
        return Agent(role='Social Intelligence Coordinator', goal='Coordinate social intelligence gathering and community analysis.', backstory='Expert in social intelligence with focus on community and social dynamics.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def trend_analysis_scout(self) -> Agent:
        """Scout for trend analysis and pattern recognition."""
        from crewai import Agent
        return Agent(role='Trend Analysis Scout', goal='Scout for trends, analyze patterns, and identify emerging intelligence.', backstory='Expert in trend analysis with focus on pattern recognition and emerging intelligence.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def research_synthesis_specialist(self) -> Agent:
        """Specialist for research synthesis and integration."""
        from crewai import Agent
        return Agent(role='Research Synthesis Specialist', goal='Synthesize research findings and create comprehensive intelligence reports.', backstory='Expert in research synthesis with focus on comprehensive analysis and reporting.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def intelligence_briefing_director(self) -> Agent:
        """Director for intelligence briefing and presentation."""
        from crewai import Agent
        return Agent(role='Intelligence Briefing Director', goal='Direct intelligence briefing operations and create comprehensive presentations.', backstory='Expert in intelligence presentation with focus on clear communication and briefing.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def strategic_argument_analyst(self) -> Agent:
        """Analyst for strategic argument analysis and development."""
        from crewai import Agent
        return Agent(role='Strategic Argument Analyst', goal='Analyze strategic arguments and develop argumentation strategies.', backstory='Expert in strategic argumentation with focus on logical reasoning and strategy.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def system_operations_manager(self) -> Agent:
        """Manager for system operations and performance optimization."""
        from crewai import Agent
        return Agent(role='System Operations Manager', goal='Manage system operations and optimize performance across all systems.', backstory='Expert in system operations with focus on performance optimization and reliability.', tools=[wrap_tool_for_crewai(AdvancedPerformanceAnalyticsTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def community_engagement_coordinator(self) -> Agent:
        """Coordinator for community engagement and stakeholder relations."""
        from crewai import Agent
        return Agent(role='Community Engagement Coordinator', goal='Coordinate community engagement and manage stakeholder relations.', backstory='Expert in community engagement with focus on stakeholder relations and communication.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def personality_synthesis_manager(self) -> Agent:
        """Manager for personality synthesis and behavioral analysis."""
        from crewai import Agent
        return Agent(role='Personality Synthesis Manager', goal='Manage personality synthesis and create comprehensive behavioral profiles.', backstory='Expert in personality analysis with focus on synthesis and behavioral profiling.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def visual_intelligence_specialist(self) -> Agent:
        """Specialist for visual intelligence and image analysis."""
        from crewai import Agent
        return Agent(role='Visual Intelligence Specialist', goal='Analyze visual content and extract visual intelligence.', backstory='Expert in visual analysis with focus on image and video intelligence.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def audio_intelligence_specialist(self) -> Agent:
        """Specialist for audio intelligence and sound analysis."""
        from crewai import Agent
        return Agent(role='Audio Intelligence Specialist', goal='Analyze audio content and extract audio intelligence.', backstory='Expert in audio analysis with focus on sound and speech intelligence.', tools=[wrap_tool_for_crewai(AudioTranscriptionTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def trend_intelligence_specialist(self) -> Agent:
        """Specialist for trend intelligence and pattern analysis."""
        from crewai import Agent
        return Agent(role='Trend Intelligence Specialist', goal='Analyze trends and provide trend intelligence.', backstory='Expert in trend analysis with focus on pattern recognition and intelligence.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def content_generation_specialist(self) -> Agent:
        """Specialist for content generation and creation."""
        from crewai import Agent
        return Agent(role='Content Generation Specialist', goal='Generate content and create comprehensive intelligence reports.', backstory='Expert in content generation with focus on creating comprehensive reports.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)

    def cross_platform_intelligence_specialist(self) -> Agent:
        """Specialist for cross-platform intelligence gathering."""
        from crewai import Agent
        return Agent(role='Cross-Platform Intelligence Specialist', goal='Gather intelligence across multiple platforms and sources.', backstory='Expert in cross-platform intelligence with focus on multi-source analysis.', tools=[wrap_tool_for_crewai(EnhancedAnalysisTool()), wrap_tool_for_crewai(TextAnalysisTool()), wrap_tool_for_crewai(TimelineTool())], verbose=True, allow_delegation=False, max_iter=2, memory=True)