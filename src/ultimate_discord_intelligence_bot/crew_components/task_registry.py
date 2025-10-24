"""Task registry for modular crew organization."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from crewai import Task  # type: ignore[import-not-found]


class TaskRegistry:
    """Registry for managing crew tasks with modular organization."""

    def __init__(self, agent_registry):
        self.agent_registry = agent_registry

    def plan_autonomy_mission(self) -> Task:
        """Plan and execute autonomy mission."""
        from crewai import Task

        return Task(
            description="Launch or resume the end-to-end intelligence mission for {url}. Sequence acquisition, transcription, analysis, verification, and memory stages using the pipeline tool while tracking budgets and documenting key decisions.",
            expected_output="Mission run log including staged plan, tool usage, and final routing instructions.",
            agent=self.agent_registry.mission_orchestrator(),
            human_input=False,
            async_execution=False,
        )

    def capture_source_media(self) -> Task:
        """Capture and download source media."""
        from crewai import Task

        return Task(
            description="CRITICAL: You MUST call the MultiPlatformDownloadTool with the URL parameter to download the video content. DO NOT use any historical data, cached results, or memory from previous runs. The URL is: {url}. You MUST call the tool immediately to download the video and return the actual file paths and metadata. Ignore any previous successful downloads in your memory.",
            expected_output="Download manifest containing file paths, formats, durations, and resolver notes.",
            agent=self.agent_registry.acquisition_specialist(),
            human_input=False,
            async_execution=False,
        )

    def transcribe_and_index_media(self) -> Task:
        """Transcribe and index media content."""
        from crewai import Task

        return Task(
            description="CRITICAL: You MUST call the AudioTranscriptionTool with the file path from the previous download task. DO NOT use any historical transcripts, cached results, or memory from previous runs. Use ONLY the actual downloaded file from the previous task to create a real transcript with timestamps and quality indicators. Ignore any previous transcripts in your memory.",
            expected_output="Transcript bundle with timestamps, quality indicators, and index references.",
            agent=self.agent_registry.transcription_engineer(),
            context=[self.capture_source_media()],
            human_input=False,
            async_execution=False,
        )

    def map_transcript_insights(self) -> Task:
        """Map insights from transcript analysis."""
        from crewai import Task

        return Task(
            description="CRITICAL: You MUST call the EnhancedAnalysisTool and TextAnalysisTool with the actual transcript text from the previous task. DO NOT use any historical analysis, cached insights, or memory from previous runs. Use ONLY the real transcript content from the previous task to identify sentiment shifts, topical clusters, and noteworthy excerpts. Ignore any previous analysis in your memory.",
            expected_output="Structured insight report containing themes, sentiment summary, and highlighted excerpts.",
            agent=self.agent_registry.analysis_cartographer(),
            context=[self.transcribe_and_index_media()],
            human_input=False,
            async_execution=False,
        )

    def verify_priority_claims(self) -> Task:
        """Verify priority claims from content."""
        from crewai import Task

        return Task(
            description="CRITICAL: You MUST call the ClaimExtractorTool with the actual transcript text to extract real claims, then call FactCheckTool to verify them. DO NOT use any historical claims, cached results, or memory from previous runs. Use ONLY the real transcript content from the previous tasks. Ignore any previous claims or verifications in your memory.",
            expected_output="Verification dossier with claim list, verdicts, fallacy notes, and citations.",
            agent=self.agent_registry.verification_director(),
            context=[self.map_transcript_insights()],
            human_input=False,
            async_execution=False,
        )
