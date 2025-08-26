"""Dynamic model routing via the OpenRouter API.

In production this service would query https://openrouter.ai to select a model
and execute the request.  For testing and offline development we keep the
implementation lightweight and fall back to a deterministic echo response when
no API key is configured.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import requests

from .learning_engine import LearningEngine
from .prompt_engine import PromptEngine


class OpenRouterService:
    """Route prompts to the best model and provider available."""

    def __init__(
        self,
        models_map: Dict[str, List[str]] | None = None,
        learning_engine: LearningEngine | None = None,
        api_key: str | None = None,
    ) -> None:
        # Environment variables allow deployment-time model overrides without
        # changing source. ``OPENROUTER_GENERAL_MODEL`` sets the default model
        # for unspecified task types while ``OPENROUTER_ANALYSIS_MODEL`` can
        # specialise the analysis route.
        env_general = os.getenv("OPENROUTER_GENERAL_MODEL")
        env_analysis = os.getenv("OPENROUTER_ANALYSIS_MODEL")
        default_map = {
            "general": [env_general or "openai/gpt-3.5-turbo"],
            "analysis": [env_analysis or env_general or "openai/gpt-3.5-turbo"],
        }
        if models_map:
            default_map.update(models_map)
        self.models_map = default_map
        self.learning = learning_engine or LearningEngine()
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.prompt_engine = PromptEngine()

    def _choose_model(self, task_type: str) -> str:
        candidates = self.models_map.get(task_type) or self.models_map["general"]
        return self.learning.select_model(task_type, candidates)

    def route(self, prompt: str, task_type: str = "general", model: str | None = None) -> Dict[str, Any]:
        """Send ``prompt`` to the selected model and return the response metadata."""
        chosen = model or self._choose_model(task_type)
        tokens = self.prompt_engine.count_tokens(prompt, chosen)
        if not self.api_key:  # offline deterministic behaviour
            response = prompt.upper()
            self.learning.update(task_type, chosen, reward=1.0)
            return {
                "status": "success",
                "model": chosen,
                "response": response,
                "tokens": tokens,
            }
        try:  # pragma: no cover - network call
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": chosen, "messages": [{"role": "user", "content": prompt}]},
                timeout=30,
            )
            data = resp.json()
            message = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            self.learning.update(task_type, chosen, reward=1.0)
            return {
                "status": "success",
                "model": chosen,
                "response": message,
                "tokens": tokens,
            }
        except Exception as exc:  # pragma: no cover - network failure
            return {"status": "error", "error": str(exc), "model": chosen, "tokens": tokens}
