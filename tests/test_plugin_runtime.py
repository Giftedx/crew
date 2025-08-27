import pathlib

from ultimate_discord_intelligence_bot.plugins.runtime.executor import PluginExecutor
from core import rl


class DummyLLM:
    def generate(self, text: str) -> str:  # pragma: no cover - trivial
        return f"summary:{text[:5]}"


def test_manifest_validation_and_execution(tmp_path: pathlib.Path) -> None:
    plugin_dir = pathlib.Path(
        "src/ultimate_discord_intelligence_bot/plugins/example_summarizer"
    )
    schema = (
        pathlib.Path("src/ultimate_discord_intelligence_bot/plugins/manifest.schema.json")
    )
    executor = PluginExecutor(schema)
    result = executor.run(
        plugin_dir,
        granted_scopes={"llm.call"},
        adapters={"svc_llm": DummyLLM()},
        args={"text": "hello world"},
    )
    assert result.success, result.error
    assert result.output == "summary:hello"
    from core import rl
    rl.feature_store._cost_usd_history.clear()
    rl.feature_store._latency_history.clear()


def test_missing_permission_raises(tmp_path: pathlib.Path) -> None:
    plugin_dir = pathlib.Path(
        "src/ultimate_discord_intelligence_bot/plugins/example_summarizer"
    )
    schema = (
        pathlib.Path("src/ultimate_discord_intelligence_bot/plugins/manifest.schema.json")
    )
    executor = PluginExecutor(schema)
    result = executor.run(
        plugin_dir,
        granted_scopes=set(),
        adapters={"svc_llm": DummyLLM()},
        args={"text": "hi"},
    )
    assert not result.success
    assert "Missing permission" in (result.error or "")
    rl.feature_store._cost_usd_history.clear()
    rl.feature_store._latency_history.clear()
