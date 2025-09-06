#!/usr/bin/env python3
"""
Fix CrewAI Configuration Issues

This script diagnoses and fixes the CrewAI @CrewBase configuration problems.
"""

import os
import sys
from pathlib import Path

import yaml

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def fix_crewai_config():
    """Fix the CrewAI configuration by removing problematic YAML multiline strings."""

    print("🔧 Fixing CrewAI Configuration Issues...")

    # Fix agents.yaml - convert multiline strings to single lines
    agents_file = Path("src/ultimate_discord_intelligence_bot/config/agents.yaml")
    tasks_file = Path("src/ultimate_discord_intelligence_bot/config/tasks.yaml")

    # Load and fix agents.yaml
    with agents_file.open("r") as f:
        agents_data = yaml.safe_load(f)

    print("✅ Loaded agents.yaml")

    # Fix multiline descriptions in agents
    for config in agents_data.values():
        if isinstance(config.get("backstory"), str):
            # Convert multiline to single line
            config["backstory"] = " ".join(config["backstory"].split())

    # Load and fix tasks.yaml
    with tasks_file.open("r") as f:
        tasks_data = yaml.safe_load(f)

    print("✅ Loaded tasks.yaml")

    # Fix multiline descriptions in tasks
    for config in tasks_data.values():
        if isinstance(config.get("description"), str):
            # Convert multiline to single line
            config["description"] = " ".join(config["description"].split())

    # Write back the fixed configurations
    with agents_file.open("w") as f:
        yaml.dump(agents_data, f, default_flow_style=False, sort_keys=False)

    with tasks_file.open("w") as f:
        yaml.dump(tasks_data, f, default_flow_style=False, sort_keys=False)

    print("✅ Fixed YAML configurations")

    # Test CrewAI loading
    print("🧪 Testing CrewAI initialization...")

    os.chdir("src/ultimate_discord_intelligence_bot")

    try:
        from crew import UltimateDiscordIntelligenceBotCrew

        crew = UltimateDiscordIntelligenceBotCrew()
        print(f"✅ CrewAI system working! {len(crew.agents)} agents, {len(crew.tasks)} tasks")
        return True
    except Exception as e:
        print(f"❌ CrewAI still has issues: {e}")
        return False


if __name__ == "__main__":
    success = fix_crewai_config()
    if success:
        print("\n🎉 CrewAI configuration fixed!")
        print("You can now use either:")
        print("  - python -m ultimate_discord_intelligence_bot.setup_cli run discord (Discord bot)")
        print("  - python -m ultimate_discord_intelligence_bot.setup_cli run crew    (Crew demo)")
    else:
        print("\n⚠️  CrewAI config issues remain, but the unified setup CLI runs correctly!")
