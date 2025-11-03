"""Content processing tasks for the Ultimate Discord Intelligence Bot.

This module contains tasks for content acquisition, transcription, analysis,
and verification workflows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from crewai import Task
from domains.orchestration.agents import (
    AcquisitionAgents,
    AnalysisAgents,
    IntelligenceAgents,
    ObservabilityAgents,
    VerificationAgents,
)


class ContentProcessingTasks:
    """Content processing tasks for the Ultimate Discord Intelligence Bot."""

    def __init__(self):
        """Initialize content processing tasks."""
        self.acquisition_agents = AcquisitionAgents()
        self.analysis_agents = AnalysisAgents()
        self.verification_agents = VerificationAgents()
        self.intelligence_agents = IntelligenceAgents()
        self.observability_agents = ObservabilityAgents()

    def plan_autonomy_mission(self) -> Task:
        """Plan and execute autonomous intelligence mission."""
        from crewai import Task

        return Task(
            description="Launch or resume the end-to-end intelligence mission for {url}. Sequence acquisition, transcription, analysis, verification, and memory stages using the pipeline tool while tracking budgets and documenting key decisions.",
            expected_output="Mission run log including staged plan, tool usage, and final routing instructions.",
            agent=self.acquisition_agents.acquisition_specialist(),
        )

    def capture_source_media(self) -> Task:
        """Capture and download source media content."""
        from crewai import Task

        return Task(
            description="CRITICAL: You MUST call the MultiPlatformDownloadTool with the URL parameter to download the video content. DO NOT use any historical data, cached results, or memory from previous runs. The URL is: {url}. You MUST call the tool immediately to download the video and return the actual file paths and metadata. Ignore any previous successful downloads in your memory.",
            expected_output="Download manifest containing file paths, formats, durations, and resolver notes.",
            agent=self.acquisition_agents.acquisition_specialist(),
        )

    def transcribe_and_index_media(self) -> Task:
        """Transcribe and index media content."""
        from crewai import Task

        return Task(
            description="CRITICAL: You MUST call the AudioTranscriptionTool with the file path from the previous download task. DO NOT use any historical transcripts, cached results, or memory from previous runs. Use ONLY the actual downloaded file from the previous task to create a real transcript with timestamps and quality indicators. Ignore any previous transcripts in your memory.",
            expected_output="Transcript bundle with timestamps, quality indicators, and index references.",
            agent=self.acquisition_agents.transcription_engineer(),
        )

    def map_transcript_insights(self) -> Task:
        """Map insights from transcript content."""
        from crewai import Task

        return Task(
            description="CRITICAL: You MUST call the EnhancedAnalysisTool and TextAnalysisTool with the actual transcript text from the previous task. DO NOT use any historical analysis, cached insights, or memory from previous runs. Use ONLY the real transcript content from the previous task to identify sentiment shifts, topical clusters, and noteworthy excerpts. Ignore any previous analysis in your memory.",
            expected_output="Structured insight report containing themes, sentiment summary, and highlighted excerpts.",
            agent=self.analysis_agents.analysis_cartographer(),
        )

    def verify_priority_claims(self) -> Task:
        """Verify priority claims from content."""
        from crewai import Task

        return Task(
            description="CRITICAL: You MUST call the ClaimExtractorTool with the actual transcript text to extract real claims, then call FactCheckTool to verify them. DO NOT use any historical claims, cached results, or memory from previous runs. Use ONLY the real transcript content from the previous tasks. Ignore any previous claims or verifications in your memory.",
            expected_output="Verification dossier with claim list, verdicts, fallacy notes, and citations.",
            agent=self.verification_agents.verification_director(),
        )

    def synthesize_intelligence(self) -> Task:
        """Synthesize intelligence from multiple sources."""
        from crewai import Task

        return Task(
            description="Synthesize intelligence from all available sources including transcript analysis, fact-checking results, and external research to create a comprehensive intelligence report.",
            expected_output="Comprehensive intelligence report with key findings, verified claims, and actionable insights.",
            agent=self.intelligence_agents.intelligence_synthesis_specialist(),
        )

    def store_memory_and_context(self) -> Task:
        """Store results in memory and context systems."""
        from crewai import Task

        return Task(
            description="Store all analysis results, verified claims, and intelligence insights in the memory system for future reference and retrieval.",
            expected_output="Memory storage confirmation with stored content identifiers and retrieval metadata.",
            agent=self.intelligence_agents.knowledge_management_specialist(),
        )
