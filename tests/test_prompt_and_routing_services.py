import os

import pytest

from ultimate_discord_intelligence_bot.services import (
    LearningEngine,
    OpenRouterService,
    PromptEngine,
)
from ultimate_discord_intelligence_bot.tools import PerspectiveSynthesizerTool


def test_prompt_engine_counts_tokens():
    engine = PromptEngine()
    text = "hello world"
    count = engine.count_tokens(text, model="gpt-3.5-turbo")
    assert isinstance(count, int) and count > 0


def test_prompt_engine_uses_transformers(monkeypatch):
    engine = PromptEngine()

    class DummyTokenizer:
        def encode(self, text: str):
            return [0, 1, 2]

    class DummyAutoTokenizer:
        @staticmethod
        def from_pretrained(name: str):  # pragma: no cover - simple stub
            return DummyTokenizer()

    monkeypatch.setattr(
        "ultimate_discord_intelligence_bot.services.prompt_engine.AutoTokenizer",
        DummyAutoTokenizer,
    )
    monkeypatch.setattr(
        "ultimate_discord_intelligence_bot.services.prompt_engine.tiktoken",
        None,
    )
    count = engine.count_tokens("hello", model="dummy-model")
    assert count == 3


def test_learning_engine_updates(tmp_path):
    store = tmp_path / "stats.json"
    learner = LearningEngine(store_path=str(store), epsilon=0.0)
    model = learner.select_model("task", ["a", "b"])
    assert model in {"a", "b"}
    learner.update("task", model, reward=2.0)
    learner2 = LearningEngine(store_path=str(store), epsilon=0.0)
    assert learner2.stats["task"][model]["reward"] == 2.0


def test_openrouter_service_offline_routing(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    router = OpenRouterService(models_map={"analysis": ["model-a"]})
    result = router.route("test", task_type="analysis")
    assert result["model"] == "model-a"
    assert result["response"] == "TEST"


def test_openrouter_env_model_override(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_GENERAL_MODEL", "env-model")
    router = OpenRouterService()
    result = router.route("hi")
    assert result["model"] == "env-model"


def test_openrouter_provider_options(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    router = OpenRouterService(provider_opts={"sort": "price"})
    result = router.route("hi")
    assert result["provider"] == {"sort": "price"}


def test_openrouter_provider_override(monkeypatch):
    """Call-level provider options should override service defaults."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    router = OpenRouterService(provider_opts={"sort": "price", "allow_fallbacks": True})
    result = router.route("hi", provider_opts={"sort": "latency", "only": ["p1"]})
    assert result["provider"] == {
        "sort": "latency",
        "allow_fallbacks": True,
        "only": ["p1"],
    }


def test_openrouter_provider_defaults_unchanged(monkeypatch):
    """Service defaults should remain untouched after call-level overrides."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    defaults = {"sort": "price", "only": ["p1"]}
    router = OpenRouterService(provider_opts=defaults)
    router.route("hi", provider_opts={"only": ["p2"]})
    assert defaults == {"sort": "price", "only": ["p1"]}
    assert router.provider_opts == {"sort": "price", "only": ["p1"]}


def test_openrouter_provider_deep_merge(monkeypatch):
    """Nested provider dictionaries should be merged recursively."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    defaults = {"require_parameters": {"a": 1, "b": 2}}
    router = OpenRouterService(provider_opts=defaults)
    result = router.route("hi", provider_opts={"require_parameters": {"b": 3}})
    assert result["provider"]["require_parameters"] == {"a": 1, "b": 3}
    # Ensure neither defaults nor call-level overrides were mutated
    assert defaults == {"require_parameters": {"a": 1, "b": 2}}


def test_perspective_synthesizer_integration(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    tool = PerspectiveSynthesizerTool()
    out = tool.run("piece one", "piece two")
    expected = (
        "Summarise the following information:\n" "piece one\n" "piece two"
    ).upper()
    assert out["summary"] == expected
    assert out["model"]
