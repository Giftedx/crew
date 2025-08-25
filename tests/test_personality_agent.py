import yaml
from pathlib import Path

BASE_DIR = Path('src/ultimate_discord_intelligence_bot/config')

def test_personality_agent_config_present():
    agents = yaml.safe_load((BASE_DIR / 'agents.yaml').read_text())
    tasks = yaml.safe_load((BASE_DIR / 'tasks.yaml').read_text())
    assert 'personality_synthesis_manager' in agents
    assert 'synthesize_personality' in tasks
    assert tasks['synthesize_personality']['agent'] == 'personality_synthesis_manager'
