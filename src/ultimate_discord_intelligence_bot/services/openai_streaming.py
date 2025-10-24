"""OpenAI streaming service for real-time responses."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from ultimate_discord_intelligence_bot.services.openai_service import OpenAIService
from ultimate_discord_intelligence_bot.step_result import StepResult


class OpenAIStreamingService(OpenAIService):
    """Service for OpenAI streaming responses."""

    def __init__(self):
        super().__init__()
        self.model = "gpt-4o-mini"

    async def stream_response(
        self, prompt: str, tenant: str, workspace: str, **kwargs
    ) -> AsyncGenerator[StepResult, None]:
        """Stream OpenAI response in real-time."""
        if not self._is_feature_enabled("ENABLE_OPENAI_STREAMING"):
            # Fallback to non-streaming response
            async for result in self._fallback_streaming(prompt, tenant, workspace, **kwargs):
                yield result
            return

        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": f"You are a helpful assistant. Tenant: {tenant}, Workspace: {workspace}"},
                {"role": "user", "content": prompt},
            ]

            # Get model configuration
            model_config = self._get_model_config(self.model)
            model_config.update(kwargs)

            # Stream response
            stream = await self.client.chat.completions.create(messages=messages, stream=True, **model_config)

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield StepResult.ok(data={"content": chunk.choices[0].delta.content, "streaming": True})

            # Final chunk
            yield StepResult.ok(data={"content": "", "streaming": False, "complete": True})

        except Exception as e:
            yield StepResult.fail(f"Streaming failed: {e!s}")

    async def stream_content_analysis(
        self, content: str, analysis_type: str, tenant: str, workspace: str
    ) -> AsyncGenerator[StepResult, None]:
        """Stream content analysis in real-time."""
        prompt = f"""
        Analyze the following content for {analysis_type}:
        
        Content: {content}
        
        Provide a detailed analysis including:
        1. Overall assessment
        2. Key findings
        3. Bias indicators
        4. Fact-check results
        5. Recommendations
        """

        async for result in self.stream_response(prompt, tenant, workspace):
            yield result

    async def _fallback_streaming(
        self, prompt: str, tenant: str, workspace: str, **kwargs
    ) -> AsyncGenerator[StepResult, None]:
        """Fallback to non-streaming response when streaming is disabled."""
        try:
            # Use structured outputs service for fallback
            from ultimate_discord_intelligence_bot.services.openai_structured_outputs import (
                OpenAIStructuredOutputsService,
            )

            structured_service = OpenAIStructuredOutputsService()

            # Create a basic analysis schema
            schema = {
                "name": "content_analysis",
                "type": "object",
                "properties": {"analysis": {"type": "string"}, "summary": {"type": "string"}},
                "required": ["analysis", "summary"],
            }

            result = await structured_service.generate_structured_response(
                prompt=prompt, schema=schema, tenant=tenant, workspace=workspace, **kwargs
            )

            if result.success:
                # Simulate streaming by yielding chunks
                analysis = result.data.get("analysis", "")
                summary = result.data.get("summary", "")

                # Split analysis into chunks for streaming effect
                chunks = [analysis[i : i + 100] for i in range(0, len(analysis), 100)]

                for chunk in chunks:
                    yield StepResult.ok(data={"content": chunk, "streaming": True})

                # Final summary
                yield StepResult.ok(data={"content": f"\n\nSummary: {summary}", "streaming": True})

                # Complete
                yield StepResult.ok(data={"content": "", "streaming": False, "complete": True})
            else:
                yield StepResult.fail(f"Fallback analysis failed: {result.error}")

        except Exception as e:
            yield StepResult.fail(f"Fallback streaming failed: {e!s}")
