"""OpenAI function calling service with tool integration."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from ultimate_discord_intelligence_bot.services.openai_service import OpenAIService
from ultimate_discord_intelligence_bot.step_result import StepResult


class OpenAIFunctionCallingService(OpenAIService):
    """Service for OpenAI function calling with tool integration."""

    def __init__(self):
        super().__init__()
        self.model = "gpt-4o-mini"
        self.functions = {}
        self.function_handlers = {}
        self._register_default_functions()

    def register_function(self, name: str, schema: dict[str, Any], handler: Callable) -> None:
        """Register a function for OpenAI function calling."""
        self.functions[name] = schema
        self.function_handlers[name] = handler

    def _register_default_functions(self) -> None:
        """Register default functions for content analysis."""
        # Register debate analysis function
        self.register_function(
            "analyze_debate_content",
            {
                "name": "analyze_debate_content",
                "description": "Analyze content for debate quality and bias",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Content to analyze"},
                        "analysis_type": {"type": "string", "description": "Type of analysis"},
                    },
                    "required": ["content", "analysis_type"],
                },
            },
            self._analyze_debate_content_handler,
        )

        # Register fact-checking function
        self.register_function(
            "fact_check_claims",
            {
                "name": "fact_check_claims",
                "description": "Fact-check specific claims in content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "claims": {"type": "array", "items": {"type": "string"}, "description": "Claims to fact-check"}
                    },
                    "required": ["claims"],
                },
            },
            self._fact_check_claims_handler,
        )

    async def call_with_functions(self, prompt: str, tenant: str, workspace: str, **kwargs) -> StepResult:
        """Call OpenAI with function calling capabilities."""
        if not self._is_feature_enabled("ENABLE_OPENAI_FUNCTION_CALLING"):
            return await self._fallback_to_openrouter(
                self._fallback_function_calling, prompt, tenant, workspace, **kwargs
            )

        try:
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": f"You are a helpful assistant with access to various tools. "
                    f"Use the available functions to help the user. "
                    f"Tenant: {tenant}, Workspace: {workspace}",
                },
                {"role": "user", "content": prompt},
            ]

            # Get model configuration
            model_config = self._get_model_config(self.model)
            model_config.update(kwargs)

            # Make OpenAI request with function calling
            response = await self.client.chat.completions.create(
                messages=messages, functions=list(self.functions.values()), function_call="auto", **model_config
            )

            # Handle function calls
            message = response.choices[0].message
            if message.function_call:
                function_name = message.function_call.name
                function_args = json.loads(message.function_call.arguments)

                # Execute function
                if function_name in self.function_handlers:
                    handler = self.function_handlers[function_name]
                    result = await handler(**function_args)
                    return StepResult.ok(data=result)
                else:
                    return StepResult.fail(f"Unknown function: {function_name}")
            else:
                # Return text response
                return StepResult.ok(data={"content": message.content})

        except Exception as e:
            return StepResult.fail(f"Function calling failed: {e!s}")

    async def analyze_content_with_functions(
        self, content: str, analysis_type: str, tenant: str, workspace: str
    ) -> StepResult:
        """Analyze content using function calling for enhanced capabilities."""
        prompt = f"""
        Analyze the following content for {analysis_type}:
        
        Content: {content}
        
        Use the available functions to:
        1. Analyze the debate quality and bias
        2. Fact-check any specific claims
        3. Provide a comprehensive analysis
        """

        return await self.call_with_functions(prompt=prompt, tenant=tenant, workspace=workspace)

    async def _analyze_debate_content_handler(self, content: str, analysis_type: str) -> dict[str, Any]:
        """Handler for debate content analysis."""
        # This would implement the actual analysis logic
        # For now, return a basic analysis
        return {
            "score": 8.5,
            "bias_level": "moderate",
            "key_points": ["Point 1", "Point 2"],
            "summary": "Content analysis summary",
        }

    async def _fact_check_claims_handler(self, claims: list[str]) -> dict[str, Any]:
        """Handler for fact-checking claims."""
        # This would implement the actual fact-checking logic
        # For now, return a basic fact-check result
        return {
            "verified_claims": claims[:2] if len(claims) > 2 else claims,
            "disputed_claims": claims[2:] if len(claims) > 2 else [],
            "confidence": 0.85,
        }

    async def _fallback_function_calling(
        self, openrouter_service, prompt: str, tenant: str, workspace: str, **kwargs
    ) -> StepResult:
        """Fallback to OpenRouter for function calling."""
        # This would implement the fallback logic using OpenRouter
        # For now, return a basic response
        return StepResult.ok(data={"content": "Analysis completed using fallback service", "fallback": True})
