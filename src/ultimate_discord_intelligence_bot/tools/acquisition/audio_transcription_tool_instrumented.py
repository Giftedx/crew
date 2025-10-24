"""Example of AudioTranscriptionTool with Metrics Instrumentation.

This file demonstrates how to add comprehensive metrics collection
to existing tools using the observability infrastructure.
"""

from __future__ import annotations

from ultimate_discord_intelligence_bot.observability.metrics_decorator import (
    comprehensive_instrumentation,
    instrument_tool,
    track_errors,
    track_memory_usage,
)
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools.acquisition.audio_transcription_tool import AudioTranscriptionTool


class InstrumentedAudioTranscriptionTool(AudioTranscriptionTool):
    """AudioTranscriptionTool with comprehensive metrics instrumentation."""

    @instrument_tool("AudioTranscriptionTool")
    def _run(self, audio_file: str, tenant: str = "default", workspace: str = "default") -> StepResult:
        """Transcribe audio with metrics collection."""
        return super()._run(audio_file, tenant, workspace)

    @track_memory_usage("AudioTranscriptionTool")
    def _transcribe_audio(self, audio_file: str) -> str:
        """Transcribe audio with memory tracking."""
        return super()._transcribe_audio(audio_file)

    @track_errors("AudioTranscriptionTool")
    def _validate_audio_file(self, audio_file: str) -> bool:
        """Validate audio file with error tracking."""
        return super()._validate_audio_file(audio_file)


# Alternative: Use comprehensive instrumentation decorator
@comprehensive_instrumentation("AudioTranscriptionTool")
class FullyInstrumentedAudioTranscriptionTool(AudioTranscriptionTool):
    """AudioTranscriptionTool with comprehensive instrumentation applied to the class."""

    def _run(self, audio_file: str, tenant: str = "default", workspace: str = "default") -> StepResult:
        """Transcribe audio with full metrics, memory, and error tracking."""
        return super()._run(audio_file, tenant, workspace)


# Example of how to instrument existing tools without modifying them
def create_instrumented_tool(original_tool_class):
    """Create an instrumented version of any tool class."""

    class InstrumentedTool(original_tool_class):
        @instrument_tool()
        def _run(self, *args, **kwargs) -> StepResult:
            return super()._run(*args, **kwargs)

    return InstrumentedTool


# Usage example:
# InstrumentedAudioTranscription = create_instrumented_tool(AudioTranscriptionTool)
