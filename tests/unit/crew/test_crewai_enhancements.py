import json
from contextlib import redirect_stdout
from io import StringIO

import pytest


pytest.importorskip("crewai")

from src.ultimate_discord_intelligence_bot.crew import (
    RAW_SNIPPET_MAX_LEN,
    UltimateDiscordIntelligenceBotCrew,
)


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    # Ensure a clean environment for each test
    for var in [
        "ENABLE_CREW_CONFIG_VALIDATION",
        "CREW_EMBEDDER_PROVIDER",
        "CREW_EMBEDDER_CONFIG_JSON",
        "ENABLE_CREW_STEP_VERBOSE",
    ]:
        monkeypatch.delenv(var, raising=False)
    yield


def test_validation_flag_detects_missing_field(monkeypatch):
    monkeypatch.setenv("ENABLE_CREW_CONFIG_VALIDATION", "1")
    crew_instance = UltimateDiscordIntelligenceBotCrew()
    # Remove a required field from one agent config
    first_agent_name = next(iter(crew_instance.agents_config))
    crew_instance.agents_config[first_agent_name].pop("date_format", None)
    with pytest.raises(ValueError) as exc:
        crew_instance.crew()  # triggers validation
    assert "missing required fields" in str(exc.value)


def test_embedder_env_override(monkeypatch):
    monkeypatch.setenv("CREW_EMBEDDER_PROVIDER", "vectorx")
    monkeypatch.setenv(
        "CREW_EMBEDDER_CONFIG_JSON",
        json.dumps({"config": {"api_key": "dummy", "dimension": 1024}}),
    )
    crew_instance = UltimateDiscordIntelligenceBotCrew()
    c = crew_instance.crew()
    assert c.embedder is not None, "Embedder should be set on crew"
    assert c.embedder["provider"] == "vectorx"
    assert c.embedder.get("config", {}).get("dimension") == 1024


def test_verbose_step_logging_truncation(monkeypatch):
    monkeypatch.setenv("ENABLE_CREW_STEP_VERBOSE", "1")
    crew_instance = UltimateDiscordIntelligenceBotCrew()
    # Build crew to ensure agents/tasks materialized (not kicking off)
    crew_instance.crew()

    class DummyAgent:
        role = "tester"

    class DummyStep:
        agent = DummyAgent()
        tool = "ToolX"
        raw = "X" * (RAW_SNIPPET_MAX_LEN + 50)

    buf = StringIO()
    with redirect_stdout(buf):
        crew_instance._log_step(DummyStep())
    out = buf.getvalue()
    # Expect truncated raw output with ellipsis
    assert "🤖 Agent tester using ToolX" in out
    assert "raw:" in out
    # Ensure truncation happened
    assert len(out.split("raw:")[-1].strip()) < RAW_SNIPPET_MAX_LEN + 20  # includes ellipsis and formatting
    assert "..." in out
