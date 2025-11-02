from pathlib import Path

import yaml


BASE_DIR = Path("src/ultimate_discord_intelligence_bot/config")


def test_personality_agent_config_present():
    """Verify personality agent is configured and task is planned."""
    agents = yaml.safe_load((BASE_DIR / "agents.yaml").read_text())

    # Agent should be present
    assert "personality_synthesis_manager" in agents

    # Task is planned but not yet implemented - check future_tasks.yaml
    future_tasks = yaml.safe_load((BASE_DIR / "future_tasks.yaml").read_text())
    assert "synthesize_personality" in future_tasks
    assert future_tasks["synthesize_personality"]["agent"] == "personality_synthesis_manager"
