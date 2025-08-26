import os

import pytest

from ultimate_discord_intelligence_bot.services import (
    LearningEngine,
    MemoryService,
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


def test_memory_service_store_and_retrieve():
    memory = MemoryService()
    memory.add("The sky is blue", {"source": "test"})
    assert memory.retrieve("sky") == [{"text": "The sky is blue", "metadata": {"source": "test"}}]


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


def test_perspective_synthesizer_integration(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    tool = PerspectiveSynthesizerTool()
    out = tool.run("piece one", "piece two")
    expected = (
        "Summarise the following information:\n" "piece one\n" "piece two"
    ).upper()
    assert out["summary"] == expected
    assert out["model"]
