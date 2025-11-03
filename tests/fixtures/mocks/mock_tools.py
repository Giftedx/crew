"""Mock tools for testing."""

from platform.core.step_result import StepResult

from ultimate_discord_intelligence_bot.tools._base import BaseTool


class MockDownloadTool(BaseTool):
    """Mock download tool for testing."""

    def _run(self, url: str, **kwargs) -> StepResult:
        """Mock download functionality."""
        return StepResult.ok(
            data={
                "file_path": f"/tmp/mock_download_{hash(url)}.mp4",
                "format": "mp4",
                "duration": 120,
                "title": "Mock Video Title",
            }
        )


class MockTranscriptionTool(BaseTool):
    """Mock transcription tool for testing."""

    def _run(self, file_path: str, **kwargs) -> StepResult:
        """Mock transcription functionality."""
        return StepResult.ok(
            data={
                "transcript": "This is a mock transcript for testing purposes.",
                "timestamps": [(0, 5, "This is a mock transcript")],
                "confidence": 0.95,
            }
        )


class MockAnalysisTool(BaseTool):
    """Mock analysis tool for testing."""

    def _run(self, content: str, **kwargs) -> StepResult:
        """Mock analysis functionality."""
        return StepResult.ok(
            data={
                "sentiment": {"positive": 0.7, "negative": 0.1, "neutral": 0.2},
                "topics": ["technology", "testing"],
                "summary": "Mock analysis summary",
            }
        )


class MockVerificationTool(BaseTool):
    """Mock verification tool for testing."""

    def _run(self, claims: list, **kwargs) -> StepResult:
        """Mock verification functionality."""
        return StepResult.ok(
            data={
                "verified_claims": [{"claim": "Test claim", "verdict": "true", "confidence": 0.8}],
                "total_claims": len(claims),
                "verification_score": 0.85,
            }
        )


class MockMemoryTool(BaseTool):
    """Mock memory tool for testing."""

    def _run(self, content: str, **kwargs) -> StepResult:
        """Mock memory functionality."""
        return StepResult.ok(
            data={"stored": True, "memory_id": f"mock_memory_{hash(content)}", "similarity_score": 0.9}
        )


def create_mock_tools():
    """Create a set of mock tools for testing."""
    return {
        "download": MockDownloadTool(),
        "transcription": MockTranscriptionTool(),
        "analysis": MockAnalysisTool(),
        "verification": MockVerificationTool(),
        "memory": MockMemoryTool(),
    }
