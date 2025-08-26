"""Dynamic model routing via the OpenRouter API.

In production this service would query https://openrouter.ai to select a model
and execute the request.  For testing and offline development we keep the
implementation lightweight and fall back to a deterministic echo response when
no API key is configured.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Mapping
import copy

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
        provider_opts: Dict[str, Any] | None = None,
    ) -> None:
        """Initialise the router.

        Args:
            models_map: Optional mapping of task types to model lists.
            learning_engine: Bandit-based learner for model selection.
            api_key: OpenRouter API key; when absent the service operates offline.
            provider_opts: Default provider routing preferences applied to all
                requests. A deep copy is stored to avoid accidental mutation of
                caller data. Nested dictionaries are merged with call-level
                overrides when routing.
        """
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
        # Deep copy to avoid mutating caller-supplied dictionaries when merging
        self.provider_opts = copy.deepcopy(provider_opts or {})

    @staticmethod
    def _deep_merge(base: Dict[str, Any], overrides: Mapping[str, Any]) -> Dict[str, Any]:
        """Recursively merge ``overrides`` into ``base``.

        Args:
            base: Dictionary to merge values into. Modified in place.
            overrides: Mapping providing override values.

        Returns:
            The merged dictionary (identical to ``base``).
        """
        for key, value in overrides.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, Mapping):
                base[key] = OpenRouterService._deep_merge(base[key], value)
            else:
                base[key] = copy.deepcopy(value)
        return base

    def _choose_model(self, task_type: str) -> str:
        candidates = self.models_map.get(task_type) or self.models_map["general"]
        return self.learning.select_model(task_type, candidates)

    def route(
        self,
        prompt: str,
        task_type: str = "general",
        model: str | None = None,
        provider_opts: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Send ``prompt`` to a model and include provider preferences.

        ``provider_opts`` override the service defaults supplied at
        instantiation.  A deep merge preserves nested defaults while allowing
        the caller to replace specific values.
        """

        chosen = model or self._choose_model(task_type)
        provider = copy.deepcopy(self.provider_opts)
        if provider_opts:
            provider = self._deep_merge(provider, provider_opts)
        tokens = self.prompt_engine.count_tokens(prompt, chosen)
        if not self.api_key:  # offline deterministic behaviour
            response = prompt.upper()
            self.learning.update(task_type, chosen, reward=1.0)
            return {
                "status": "success",
                "model": chosen,
                "response": response,
                "tokens": tokens,
                "provider": provider,
            }
        try:  # pragma: no cover - network call
            payload: Dict[str, Any] = {
                "model": chosen,
                "messages": [{"role": "user", "content": prompt}],
            }
            if provider:
                payload["provider"] = provider
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
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
                "provider": provider,
            }
        except Exception as exc:  # pragma: no cover - network failure
            return {
                "status": "error",
                "error": str(exc),
                "model": chosen,
                "tokens": tokens,
                "provider": provider,
            }
