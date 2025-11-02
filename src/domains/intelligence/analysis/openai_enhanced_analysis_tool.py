"""Enhanced analysis tool with OpenAI capabilities."""

from __future__ import annotations
from typing import TYPE_CHECKING
from ultimate_discord_intelligence_bot.services.openai_integration_service import OpenAIIntegrationService
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


class OpenAIEnhancedAnalysisTool(BaseTool):
    """Enhanced analysis tool with OpenAI capabilities."""

    def __init__(self):
        super().__init__()
        self.openai_service = OpenAIIntegrationService()

    def _run(self, content: str, analysis_type: str, tenant: str, workspace: str) -> StepResult:
        """Run enhanced analysis with OpenAI capabilities."""
        try:
            enhancements = self.openai_service.get_available_enhancements()
            result = self.openai_service.process_with_enhancements_sync(
                content=content,
                enhancements=enhancements,
                tenant=tenant,
                workspace=workspace,
                analysis_type=analysis_type,
            )
            if not result.success:
                return result
            return StepResult.ok(
                data={
                    "analysis": result.data,
                    "enhanced": True,
                    "openai_powered": True,
                    "enhancements_used": enhancements,
                }
            )
        except Exception as e:
            return StepResult.fail(f"Enhanced analysis failed: {e!s}")

    async def stream_analysis(
        self, content: str, analysis_type: str, tenant: str, workspace: str
    ) -> AsyncGenerator[StepResult, None]:
        """Stream analysis results in real-time."""
        try:
            async for result in self.openai_service.stream_enhanced_analysis(
                content=content, analysis_type=analysis_type, tenant=tenant, workspace=workspace
            ):
                yield result
        except Exception as e:
            yield StepResult.fail(f"Streaming analysis failed: {e!s}")

    async def analyze_with_images(
        self, content: str, images: list[bytes], analysis_type: str, tenant: str, workspace: str
    ) -> StepResult:
        """Analyze content with images using multimodal capabilities."""
        try:
            enhancements = ["structured_outputs", "vision", "multimodal"]
            result = await self.openai_service.process_with_enhancements(
                content=content,
                enhancements=enhancements,
                tenant=tenant,
                workspace=workspace,
                analysis_type=analysis_type,
                images=images,
            )
            if not result.success:
                return result
            return StepResult.ok(
                data={
                    "multimodal_analysis": result.data,
                    "enhanced": True,
                    "openai_powered": True,
                    "images_analyzed": len(images),
                }
            )
        except Exception as e:
            return StepResult.fail(f"Multimodal analysis failed: {e!s}")

    async def analyze_voice_content(
        self, audio_data: bytes, analysis_type: str, tenant: str, workspace: str
    ) -> StepResult:
        """Analyze voice content using OpenAI voice capabilities."""
        try:
            result = await self.openai_service.analyze_voice_content(
                audio_data=audio_data, analysis_type=analysis_type, tenant=tenant, workspace=workspace
            )
            if not result.success:
                return result
            return StepResult.ok(data={"voice_analysis": result.data, "enhanced": True, "openai_powered": True})
        except Exception as e:
            return StepResult.fail(f"Voice analysis failed: {e!s}")

    async def fact_check_multimodal(self, text: str, images: list[bytes], tenant: str, workspace: str) -> StepResult:
        """Fact-check content using multimodal evidence."""
        try:
            result = await self.openai_service.fact_check_multimodal(
                text=text, images=images, tenant=tenant, workspace=workspace
            )
            if not result.success:
                return result
            return StepResult.ok(data={"fact_check": result.data, "enhanced": True, "openai_powered": True})
        except Exception as e:
            return StepResult.fail(f"Multimodal fact-checking failed: {e!s}")

    async def detect_bias_multimodal(self, text: str, images: list[bytes], tenant: str, workspace: str) -> StepResult:
        """Detect bias across multiple modalities."""
        try:
            result = await self.openai_service.detect_bias_multimodal(
                text=text, images=images, tenant=tenant, workspace=workspace
            )
            if not result.success:
                return result
            return StepResult.ok(data={"bias_analysis": result.data, "enhanced": True, "openai_powered": True})
        except Exception as e:
            return StepResult.fail(f"Multimodal bias detection failed: {e!s}")

    async def generate_summary(self, text: str, images: list[bytes], tenant: str, workspace: str) -> StepResult:
        """Generate comprehensive summary using multimodal content."""
        try:
            result = await self.openai_service.generate_multimodal_summary(
                text=text, images=images, tenant=tenant, workspace=workspace
            )
            if not result.success:
                return result
            return StepResult.ok(data={"summary": result.data, "enhanced": True, "openai_powered": True})
        except Exception as e:
            return StepResult.fail(f"Summary generation failed: {e!s}")

    async def health_check(self) -> StepResult:
        """Check health of OpenAI services."""
        try:
            result = await self.openai_service.health_check()
            return result
        except Exception as e:
            return StepResult.fail(f"Health check failed: {e!s}")
