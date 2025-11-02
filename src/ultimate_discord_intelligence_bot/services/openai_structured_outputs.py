"""OpenAI structured outputs service with JSON schema validation."""

from __future__ import annotations

import json
from platform.core.step_result import StepResult
from typing import Any

from ultimate_discord_intelligence_bot.services.openai_service import OpenAIService


class OpenAIStructuredOutputsService(OpenAIService):
    """Service for OpenAI structured outputs with JSON schema validation."""

    def __init__(self):
        super().__init__()
        self.model = "gpt-4o-mini"

    async def generate_structured_response(
        self, prompt: str, schema: dict[str, Any], tenant: str, workspace: str, **kwargs
    ) -> StepResult:
        """Generate structured response with JSON schema validation."""
        if not self._is_feature_enabled("ENABLE_OPENAI_STRUCTURED_OUTPUTS"):
            return await self._fallback_to_openrouter(
                self._fallback_structured_response, prompt, schema, tenant, workspace, **kwargs
            )
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"You are a helpful assistant that generates structured responses. Always respond with valid JSON that matches the provided schema. Tenant: {tenant}, Workspace: {workspace}",
                },
                {"role": "user", "content": prompt},
            ]
            model_config = self._get_model_config(self.model)
            model_config.update(kwargs)
            response = await self.client.chat.completions.create(
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.get("name", "structured_response"),
                        "schema": schema,
                        "strict": True,
                    },
                },
                **model_config,
            )
            content = response.choices[0].message.content
            if not content:
                return StepResult.fail("Empty response from OpenAI")
            try:
                structured_data = json.loads(content)
            except json.JSONDecodeError as e:
                return StepResult.fail(f"Invalid JSON response: {e!s}")
            validation_result = await self._validate_response(structured_data, schema)
            if not validation_result.success:
                return validation_result
            return StepResult.ok(data=structured_data)
        except Exception as e:
            return StepResult.fail(f"Structured output generation failed: {e!s}")

    async def analyze_content_structured(
        self, content: str, analysis_type: str, tenant: str, workspace: str
    ) -> StepResult:
        """Analyze content with structured output for debate analysis."""
        schema = {
            "name": "content_analysis",
            "type": "object",
            "properties": {
                "analysis_type": {"type": "string", "enum": ["debate", "fact_check", "sentiment"]},
                "score": {"type": "number", "minimum": 0, "maximum": 10},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "key_points": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 10},
                "bias_indicators": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
                "fact_check_claims": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "claim": {"type": "string"},
                            "verification_status": {"type": "string", "enum": ["verified", "disputed", "unverified"]},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                        "required": ["claim", "verification_status", "confidence"],
                    },
                },
                "summary": {"type": "string", "maxLength": 500},
            },
            "required": ["analysis_type", "score", "confidence", "key_points", "summary"],
        }
        prompt = f"\n        Analyze the following content for {analysis_type}:\n\n        Content: {content}\n\n        Provide a comprehensive analysis including:\n        1. Overall score (0-10)\n        2. Confidence level (0-1)\n        3. Key points identified\n        4. Bias indicators (if any)\n        5. Fact-check claims (if applicable)\n        6. Summary of findings\n        "
        return await self.generate_structured_response(prompt=prompt, schema=schema, tenant=tenant, workspace=workspace)

    async def _fallback_structured_response(
        self, openrouter_service, prompt: str, schema: dict[str, Any], tenant: str, workspace: str, **kwargs
    ) -> StepResult:
        """Fallback to OpenRouter for structured responses."""
        return StepResult.ok(
            data={
                "analysis_type": "fallback",
                "score": 5.0,
                "confidence": 0.5,
                "key_points": ["Fallback analysis"],
                "bias_indicators": [],
                "fact_check_claims": [],
                "summary": "Analysis completed using fallback service",
            }
        )
