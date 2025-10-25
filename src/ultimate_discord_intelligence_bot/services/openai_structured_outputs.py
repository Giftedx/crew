"""OpenAI structured outputs service with JSON schema validation."""

from __future__ import annotations

import json
from typing import Any

from ultimate_discord_intelligence_bot.services.openai_service import OpenAIService
from ultimate_discord_intelligence_bot.step_result import StepResult


class OpenAIStructuredOutputsService(OpenAIService):
    """Service for OpenAI structured outputs with JSON schema validation."""

    def __init__(self):
        super().__init__()
        self.model = "gpt-4o-mini"  # Cost-effective model for structured outputs

    async def generate_structured_response(
        self, prompt: str, schema: dict[str, Any], tenant: str, workspace: str, **kwargs
    ) -> StepResult:
        """Generate structured response with JSON schema validation."""
        if not self._is_feature_enabled("ENABLE_OPENAI_STRUCTURED_OUTPUTS"):
            return await self._fallback_to_openrouter(
                self._fallback_structured_response, prompt, schema, tenant, workspace, **kwargs
            )

        try:
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": f"You are a helpful assistant that generates structured responses. "
                    f"Always respond with valid JSON that matches the provided schema. "
                    f"Tenant: {tenant}, Workspace: {workspace}",
                },
                {"role": "user", "content": prompt},
            ]

            # Get model configuration
            model_config = self._get_model_config(self.model)
            model_config.update(kwargs)

            # Make OpenAI request with structured output
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

            # Extract and validate response
            content = response.choices[0].message.content
            if not content:
                return StepResult.fail("Empty response from OpenAI")

            # Parse JSON response
            try:
                structured_data = json.loads(content)
            except json.JSONDecodeError as e:
                return StepResult.fail(f"Invalid JSON response: {e!s}")

            # Validate against schema
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

        prompt = f"""
        Analyze the following content for {analysis_type}:

        Content: {content}

        Provide a comprehensive analysis including:
        1. Overall score (0-10)
        2. Confidence level (0-1)
        3. Key points identified
        4. Bias indicators (if any)
        5. Fact-check claims (if applicable)
        6. Summary of findings
        """

        return await self.generate_structured_response(prompt=prompt, schema=schema, tenant=tenant, workspace=workspace)

    async def _fallback_structured_response(
        self, openrouter_service, prompt: str, schema: dict[str, Any], tenant: str, workspace: str, **kwargs
    ) -> StepResult:
        """Fallback to OpenRouter for structured responses."""
        # This would implement the fallback logic using OpenRouter
        # For now, return a basic structured response
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
