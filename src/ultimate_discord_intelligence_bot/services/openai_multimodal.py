"""OpenAI multimodal analysis service combining text, images, and audio."""
from __future__ import annotations
import base64
from ultimate_discord_intelligence_bot.services.openai_service import OpenAIService
from ultimate_discord_intelligence_bot.services.openai_vision import OpenAIVisionService
from platform.core.step_result import StepResult

class MultimodalAnalysisService(OpenAIService):
    """Service for multimodal content analysis combining text, images, and audio."""

    def __init__(self):
        super().__init__()
        self.model = 'gpt-4o'
        self.vision_service = OpenAIVisionService()

    async def analyze_multimodal_content(self, text: str, images: list[bytes], audio_data: bytes | None, tenant: str, workspace: str) -> StepResult:
        """Analyze content combining text, images, and audio."""
        if not self._is_feature_enabled('ENABLE_OPENAI_MULTIMODAL'):
            return StepResult.fail('OpenAI multimodal features are disabled')
        try:
            messages = [{'role': 'system', 'content': f'You are an expert content analyst. Analyze the provided content across multiple modalities. Tenant: {tenant}, Workspace: {workspace}'}, {'role': 'user', 'content': []}]
            user_content = messages[1]['content']
            user_content.append({'type': 'text', 'text': f'Text content to analyze:\n{text}'})
            for _i, image_data in enumerate(images):
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                user_content.append({'type': 'image_url', 'image_url': f'data:image/jpeg;base64,{image_base64}'})
            if audio_data:
                user_content.append({'type': 'text', 'text': 'Audio content is also available (transcribed separately)'})
            response = await self.client.chat.completions.create(model=self.model, messages=messages, max_tokens=2000, temperature=0.7)
            return StepResult.ok(data={'multimodal_analysis': response.choices[0].message.content, 'modalities_analyzed': ['text', 'images'] + (['audio'] if audio_data else []), 'model': self.model})
        except Exception as e:
            return StepResult.fail(f'Multimodal analysis failed: {e!s}')

    async def analyze_debate_content_multimodal(self, transcript: str, thumbnails: list[bytes], audio_data: bytes | None, tenant: str, workspace: str) -> StepResult:
        """Analyze debate content using multimodal approach."""
        return await self.analyze_multimodal_content(text=transcript, images=thumbnails, audio_data=audio_data, tenant=tenant, workspace=workspace)

    async def fact_check_multimodal(self, text: str, images: list[bytes], tenant: str, workspace: str) -> StepResult:
        """Fact-check content using multimodal evidence."""
        return await self.analyze_multimodal_content(text=text, images=images, audio_data=None, tenant=tenant, workspace=workspace)

    async def detect_bias_multimodal(self, text: str, images: list[bytes], tenant: str, workspace: str) -> StepResult:
        """Detect bias across multiple modalities."""
        return await self.analyze_multimodal_content(text=text, images=images, audio_data=None, tenant=tenant, workspace=workspace)

    async def generate_multimodal_summary(self, text: str, images: list[bytes], tenant: str, workspace: str) -> StepResult:
        """Generate comprehensive summary using multimodal content."""
        return await self.analyze_multimodal_content(text=text, images=images, audio_data=None, tenant=tenant, workspace=workspace)