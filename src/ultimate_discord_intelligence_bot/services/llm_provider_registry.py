"""LLM Provider Registry — capability metadata and adapter skeletons.

This module centralizes a registry of provider adapters and exposes a uniform
capability surface. Adapters are intentionally lightweight and do not perform
network I/O; they only describe models and capabilities so routing layers can
build arms and policies without touching restricted directories.

Integration points for completions/streaming can be added later to proxy to
existing clients (e.g., OpenRouter, core.llm_client) without duplicating logic.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from platform.core.step_result import StepResult

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass(frozen=True)
class ModelInfo:
    provider: str
    model: str
    capabilities: set[str] = field(default_factory=set)
    context_window: int | None = None
    cost_per_1k_input: float | None = None
    cost_per_1k_output: float | None = None
    est_latency_ms: int | None = None
    quality_tier: str | None = None


class ProviderAdapter:
    """Base adapter describing a provider and its known models.

    This class purposefully avoids external calls. Subclasses should override
    `name` and `_models`.
    """

    name: str = "generic"

    def list_models(self) -> list[ModelInfo]:
        return list(self._models())

    async def complete(self, *_args: Any, **_kwargs: Any) -> StepResult:
        return StepResult.fail("completion not implemented for provider", provider=self.name)

    def _models(self) -> Iterable[ModelInfo]:
        return []


class OpenAIAdapter(ProviderAdapter):
    name = "openai"

    def _models(self) -> Iterable[ModelInfo]:
        yield ModelInfo(
            provider=self.name,
            model="gpt-4o",
            capabilities={"text", "vision", "function_calling", "json_schema"},
            context_window=128000,
            cost_per_1k_input=5.0 / 1000,
            cost_per_1k_output=15.0 / 1000,
            est_latency_ms=900,
            quality_tier="top",
        )
        yield ModelInfo(
            provider=self.name,
            model="gpt-4.1-mini",
            capabilities={"text", "function_calling", "json_schema"},
            context_window=128000,
            cost_per_1k_input=0.3 / 1000,
            cost_per_1k_output=1.2 / 1000,
            est_latency_ms=600,
            quality_tier="balanced",
        )


class AnthropicAdapter(ProviderAdapter):
    name = "anthropic"

    def _models(self) -> Iterable[ModelInfo]:
        yield ModelInfo(
            provider=self.name,
            model="claude-3-5-sonnet",
            capabilities={"text", "tool_use", "json_schema", "long_context"},
            context_window=200000,
            cost_per_1k_input=3.0 / 1000,
            cost_per_1k_output=15.0 / 1000,
            est_latency_ms=1100,
            quality_tier="top",
        )
        yield ModelInfo(
            provider=self.name,
            model="claude-3-haiku",
            capabilities={"text"},
            context_window=200000,
            cost_per_1k_input=0.25 / 1000,
            cost_per_1k_output=1.25 / 1000,
            est_latency_ms=500,
            quality_tier="fast",
        )


class GoogleAdapter(ProviderAdapter):
    name = "google"

    def _models(self) -> Iterable[ModelInfo]:
        yield ModelInfo(
            provider=self.name,
            model="gemini-1.5-pro",
            capabilities={"text", "vision", "tool_use", "long_context"},
            context_window=1000000,
            cost_per_1k_input=3.5 / 1000,
            cost_per_1k_output=10.5 / 1000,
            est_latency_ms=1200,
            quality_tier="top",
        )


class CohereAdapter(ProviderAdapter):
    name = "cohere"

    def _models(self) -> Iterable[ModelInfo]:
        yield ModelInfo(
            provider=self.name,
            model="command-r-plus",
            capabilities={"text", "tool_use"},
            context_window=128000,
            cost_per_1k_input=3.0 / 1000,
            cost_per_1k_output=15.0 / 1000,
            est_latency_ms=900,
            quality_tier="high",
        )


class MistralAdapter(ProviderAdapter):
    name = "mistral"

    def _models(self) -> Iterable[ModelInfo]:
        yield ModelInfo(
            provider=self.name,
            model="mistral-large-latest",
            capabilities={"text", "function_calling"},
            context_window=128000,
            cost_per_1k_input=2.0 / 1000,
            cost_per_1k_output=6.0 / 1000,
            est_latency_ms=800,
            quality_tier="balanced",
        )


class OpenRouterAdapter(ProviderAdapter):
    name = "openrouter"

    def _models(self) -> Iterable[ModelInfo]:
        yield ModelInfo(
            provider=self.name,
            model="meta-best",
            capabilities={"text", "function_calling", "json_schema"},
            context_window=128000,
            quality_tier="balanced",
        )


class AzureOpenAIAdapter(ProviderAdapter):
    name = "azure_openai"

    def _models(self) -> Iterable[ModelInfo]:
        yield ModelInfo(
            provider=self.name,
            model="gpt-4o",
            capabilities={"text", "vision", "function_calling", "json_schema"},
            context_window=128000,
            quality_tier="top",
        )


class BedrockAdapter(ProviderAdapter):
    name = "bedrock"

    def _models(self) -> Iterable[ModelInfo]:
        yield ModelInfo(
            provider=self.name,
            model="anthropic.claude-3-5-sonnet",
            capabilities={"text", "tool_use", "long_context"},
            context_window=200000,
            quality_tier="top",
        )


class GroqAdapter(ProviderAdapter):
    name = "groq"

    def _models(self) -> Iterable[ModelInfo]:
        yield ModelInfo(
            provider=self.name,
            model="llama-3.1-70b-instant",
            capabilities={"text"},
            context_window=128000,
            est_latency_ms=300,
            quality_tier="fast",
        )


class TogetherAdapter(ProviderAdapter):
    name = "together"

    def _models(self) -> Iterable[ModelInfo]:
        yield ModelInfo(
            provider=self.name,
            model="meta-llama-3.1-70b-instruct",
            capabilities={"text", "function_calling"},
            context_window=128000,
            quality_tier="balanced",
        )


class FireworksAdapter(ProviderAdapter):
    name = "fireworks"

    def _models(self) -> Iterable[ModelInfo]:
        yield ModelInfo(
            provider=self.name,
            model="llama-3.1-nemotron-70b-instruct",
            capabilities={"text"},
            context_window=128000,
            quality_tier="balanced",
        )


class PerplexityAdapter(ProviderAdapter):
    name = "perplexity"

    def _models(self) -> Iterable[ModelInfo]:
        yield ModelInfo(
            provider=self.name, model="llama-3.1-70b-instruct", capabilities={"text"}, quality_tier="balanced"
        )


class XAIAdapter(ProviderAdapter):
    name = "xai"

    def _models(self) -> Iterable[ModelInfo]:
        yield ModelInfo(provider=self.name, model="grok-2", capabilities={"text", "reasoning"}, quality_tier="balanced")


class DeepSeekAdapter(ProviderAdapter):
    name = "deepseek"

    def _models(self) -> Iterable[ModelInfo]:
        yield ModelInfo(provider=self.name, model="deepseek-chat", capabilities={"text"}, quality_tier="cheap")


_ADAPTERS: dict[str, ProviderAdapter] = {
    a.name: a
    for a in [
        OpenRouterAdapter(),
        OpenAIAdapter(),
        AnthropicAdapter(),
        GoogleAdapter(),
        CohereAdapter(),
        MistralAdapter(),
        AzureOpenAIAdapter(),
        BedrockAdapter(),
        GroqAdapter(),
        TogetherAdapter(),
        FireworksAdapter(),
        PerplexityAdapter(),
        XAIAdapter(),
        DeepSeekAdapter(),
    ]
}


def get_adapter(provider: str) -> ProviderAdapter | None:
    return _ADAPTERS.get(provider.lower())


def list_providers() -> list[str]:
    return sorted(_ADAPTERS.keys())


def list_models(provider_allowlist: list[str] | None = None) -> list[ModelInfo]:
    allowed = {p.lower() for p in provider_allowlist} if provider_allowlist else None
    models: list[ModelInfo] = []
    for name, adapter in _ADAPTERS.items():
        if allowed is not None and name not in allowed:
            continue
        models.extend(adapter.list_models())
    return models


def get_provider_allowlist_from_config() -> list[str] | None:
    """Parse provider allowlist from SecureConfig if present.

    Supports comma-separated env or native list when pydantic is active.
    """
    try:
        from platform.config.configuration import get_config

        cfg = get_config()
        raw = getattr(cfg, "llm_provider_allowlist", None)
        if raw is None:
            raw = getattr(cfg, "llm_provider_allowlist_raw", None)
        if isinstance(raw, list):
            return [str(x).lower() for x in raw]
        if isinstance(raw, str):
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            return [p.lower() for p in parts] or None
        return None
    except Exception:
        return None


__all__ = [
    "ModelInfo",
    "ProviderAdapter",
    "get_adapter",
    "get_provider_allowlist_from_config",
    "list_models",
    "list_providers",
]
