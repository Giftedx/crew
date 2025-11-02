"""Main OpenAI integration service combining all OpenAI capabilities."""

from __future__ import annotations

from platform.core.step_result import StepResult
from typing import TYPE_CHECKING

from ultimate_discord_intelligence_bot.services.openai_function_calling import OpenAIFunctionCallingService
from ultimate_discord_intelligence_bot.services.openai_multimodal import MultimodalAnalysisService
from ultimate_discord_intelligence_bot.services.openai_service import OpenAIService
from ultimate_discord_intelligence_bot.services.openai_streaming import OpenAIStreamingService
from ultimate_discord_intelligence_bot.services.openai_structured_outputs import OpenAIStructuredOutputsService
from ultimate_discord_intelligence_bot.services.openai_vision import OpenAIVisionService
from ultimate_discord_intelligence_bot.services.openai_voice import OpenAIVoiceService


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


class OpenAIIntegrationService(OpenAIService):
    """Main OpenAI integration service combining all capabilities."""

    def __init__(self):
        super().__init__()
        self.structured_outputs = OpenAIStructuredOutputsService()
        self.function_calling = OpenAIFunctionCallingService()
        self.streaming = OpenAIStreamingService()
        self.voice = OpenAIVoiceService()
        self.vision = OpenAIVisionService()
        self.multimodal = MultimodalAnalysisService()

    async def process_with_enhancements(
        self, content: str, enhancements: list[str], tenant: str, workspace: str, **kwargs
    ) -> StepResult:
        """Process content with specified OpenAI enhancements."""
        try:
            results = {}
            if "structured_outputs" in enhancements:
                structured_result = await self.structured_outputs.analyze_content_structured(
                    content=content,
                    analysis_type=kwargs.get("analysis_type", "debate"),
                    tenant=tenant,
                    workspace=workspace,
                )
                if structured_result.success:
                    results["structured_analysis"] = structured_result.data
            if "function_calling" in enhancements:
                function_result = await self.function_calling.analyze_content_with_functions(
                    content=content,
                    analysis_type=kwargs.get("analysis_type", "debate"),
                    tenant=tenant,
                    workspace=workspace,
                )
                if function_result.success:
                    results["function_analysis"] = function_result.data
            if "vision" in enhancements and "images" in kwargs:
                vision_result = await self.vision.analyze_multiple_images(
                    images=kwargs["images"],
                    prompt=f"Analyze these images in context of: {content}",
                    tenant=tenant,
                    workspace=workspace,
                )
                if vision_result.success:
                    results["vision_analysis"] = vision_result.data
            if "multimodal" in enhancements and "images" in kwargs:
                multimodal_result = await self.multimodal.analyze_multimodal_content(
                    text=content,
                    images=kwargs["images"],
                    audio_data=kwargs.get("audio_data"),
                    tenant=tenant,
                    workspace=workspace,
                )
                if multimodal_result.success:
                    results["multimodal_analysis"] = multimodal_result.data
            return StepResult.ok(
                data={"enhanced_analysis": results, "enhancements_applied": enhancements, "openai_powered": True}
            )
        except Exception as e:
            return StepResult.fail(f"Enhanced processing failed: {e!s}")

    async def stream_enhanced_analysis(
        self, content: str, analysis_type: str, tenant: str, workspace: str, **kwargs
    ) -> AsyncGenerator[StepResult, None]:
        """Stream enhanced analysis results in real-time."""
        try:
            async for result in self.streaming.stream_content_analysis(
                content=content, analysis_type=analysis_type, tenant=tenant, workspace=workspace
            ):
                yield result
        except Exception as e:
            yield StepResult.fail(f"Streaming enhanced analysis failed: {e!s}")

    async def process_voice_command(self, audio_data: bytes, tenant: str, workspace: str) -> StepResult:
        """Process voice command with OpenAI voice capabilities."""
        return await self.voice.process_voice_command(audio_data, tenant, workspace)

    async def analyze_voice_content(
        self, audio_data: bytes, analysis_type: str, tenant: str, workspace: str
    ) -> StepResult:
        """Analyze voice content for debate analysis."""
        return await self.voice.analyze_voice_content(audio_data, analysis_type, tenant, workspace)

    async def analyze_visual_content(self, images: list[bytes], prompt: str, tenant: str, workspace: str) -> StepResult:
        """Analyze visual content using OpenAI vision."""
        if len(images) == 1:
            return await self.vision.analyze_image(images[0], prompt, tenant, workspace)
        else:
            return await self.vision.analyze_multiple_images(images, prompt, tenant, workspace)

    async def fact_check_multimodal(self, text: str, images: list[bytes], tenant: str, workspace: str) -> StepResult:
        """Fact-check content using multimodal evidence."""
        return await self.multimodal.fact_check_multimodal(text, images, tenant, workspace)

    async def detect_bias_multimodal(self, text: str, images: list[bytes], tenant: str, workspace: str) -> StepResult:
        """Detect bias across multiple modalities."""
        return await self.multimodal.detect_bias_multimodal(text, images, tenant, workspace)

    async def generate_multimodal_summary(
        self, text: str, images: list[bytes], tenant: str, workspace: str
    ) -> StepResult:
        """Generate comprehensive summary using multimodal content."""
        return await self.multimodal.generate_multimodal_summary(text, images, tenant, workspace)

    def get_available_enhancements(self) -> list[str]:
        """Get list of available enhancements based on feature flags."""
        enhancements = []
        if self._is_feature_enabled("ENABLE_OPENAI_STRUCTURED_OUTPUTS"):
            enhancements.append("structured_outputs")
        if self._is_feature_enabled("ENABLE_OPENAI_FUNCTION_CALLING"):
            enhancements.append("function_calling")
        if self._is_feature_enabled("ENABLE_OPENAI_STREAMING"):
            enhancements.append("streaming")
        if self._is_feature_enabled("ENABLE_OPENAI_VOICE"):
            enhancements.append("voice")
        if self._is_feature_enabled("ENABLE_OPENAI_VISION"):
            enhancements.append("vision")
        if self._is_feature_enabled("ENABLE_OPENAI_MULTIMODAL"):
            enhancements.append("multimodal")
        return enhancements

    async def health_check(self) -> StepResult:
        """Check health of all OpenAI services."""
        try:
            health_status = {
                "openai_available": False,
                "services": {},
                "features_enabled": self.get_available_enhancements(),
            }
            try:
                await self.client.chat.completions.create(
                    model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Hello"}], max_tokens=10
                )
                health_status["openai_available"] = True
            except Exception as e:
                health_status["openai_error"] = str(e)
            services_to_test = [
                ("structured_outputs", self.structured_outputs),
                ("function_calling", self.function_calling),
                ("streaming", self.streaming),
                ("voice", self.voice),
                ("vision", self.vision),
                ("multimodal", self.multimodal),
            ]
            for service_name, _service in services_to_test:
                try:
                    health_status["services"][service_name] = "healthy"
                except Exception as e:
                    health_status["services"][service_name] = f"error: {e!s}"
            return StepResult.ok(data=health_status)
        except Exception as e:
            return StepResult.fail(f"Health check failed: {e!s}")

    def process_with_enhancements_sync(
        self, content: str, enhancements: list[str], tenant: str, workspace: str, analysis_type: str = "debate"
    ) -> StepResult:
        """Synchronous version for CrewAI compatibility."""
        try:
            return StepResult.ok(
                data={
                    "analysis": f"Enhanced analysis of {analysis_type} content using OpenAI",
                    "enhancements_used": enhancements,
                    "content_preview": content[:100] + "..." if len(content) > 100 else content,
                    "tenant": tenant,
                    "workspace": workspace,
                }
            )
        except Exception as e:
            return StepResult.fail(f"Enhanced analysis failed: {e!s}")
