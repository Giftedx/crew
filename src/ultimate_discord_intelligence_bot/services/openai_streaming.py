"""OpenAI streaming service for real-time responses."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ultimate_discord_intelligence_bot.services.openai_service import OpenAIService
from platform.core.step_result import StepResult
if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

class OpenAIStreamingService(OpenAIService):
    """Service for OpenAI streaming responses."""

    def __init__(self):
        super().__init__()
        self.model = 'gpt-4o-mini'

    async def stream_response(self, prompt: str, tenant: str, workspace: str, **kwargs) -> AsyncGenerator[StepResult, None]:
        """Stream OpenAI response in real-time."""
        if not self._is_feature_enabled('ENABLE_OPENAI_STREAMING'):
            async for result in self._fallback_streaming(prompt, tenant, workspace, **kwargs):
                yield result
            return
        try:
            messages = [{'role': 'system', 'content': f'You are a helpful assistant. Tenant: {tenant}, Workspace: {workspace}'}, {'role': 'user', 'content': prompt}]
            model_config = self._get_model_config(self.model)
            model_config.update(kwargs)
            stream = await self.client.chat.completions.create(messages=messages, stream=True, **model_config)
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield StepResult.ok(data={'content': chunk.choices[0].delta.content, 'streaming': True})
            yield StepResult.ok(data={'content': '', 'streaming': False, 'complete': True})
        except Exception as e:
            yield StepResult.fail(f'Streaming failed: {e!s}')

    async def stream_content_analysis(self, content: str, analysis_type: str, tenant: str, workspace: str) -> AsyncGenerator[StepResult, None]:
        """Stream content analysis in real-time."""
        prompt = f'\n        Analyze the following content for {analysis_type}:\n\n        Content: {content}\n\n        Provide a detailed analysis including:\n        1. Overall assessment\n        2. Key findings\n        3. Bias indicators\n        4. Fact-check results\n        5. Recommendations\n        '
        async for result in self.stream_response(prompt, tenant, workspace):
            yield result

    async def _fallback_streaming(self, prompt: str, tenant: str, workspace: str, **kwargs) -> AsyncGenerator[StepResult, None]:
        """Fallback to non-streaming response when streaming is disabled."""
        try:
            from ultimate_discord_intelligence_bot.services.openai_structured_outputs import OpenAIStructuredOutputsService
            structured_service = OpenAIStructuredOutputsService()
            schema = {'name': 'content_analysis', 'type': 'object', 'properties': {'analysis': {'type': 'string'}, 'summary': {'type': 'string'}}, 'required': ['analysis', 'summary']}
            result = await structured_service.generate_structured_response(prompt=prompt, schema=schema, tenant=tenant, workspace=workspace, **kwargs)
            if result.success:
                analysis = result.data.get('analysis', '')
                summary = result.data.get('summary', '')
                chunks = [analysis[i:i + 100] for i in range(0, len(analysis), 100)]
                for chunk in chunks:
                    yield StepResult.ok(data={'content': chunk, 'streaming': True})
                yield StepResult.ok(data={'content': f'\n\nSummary: {summary}', 'streaming': True})
                yield StepResult.ok(data={'content': '', 'streaming': False, 'complete': True})
            else:
                yield StepResult.fail(f'Fallback analysis failed: {result.error}')
        except Exception as e:
            yield StepResult.fail(f'Fallback streaming failed: {e!s}')