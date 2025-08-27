import ast
from pathlib import Path
import yaml

CREW_FILE = Path("src/ultimate_discord_intelligence_bot/crew.py")
MODULE = ast.parse(CREW_FILE.read_text())


def _agent_tools(name: str) -> set[str]:
    for node in MODULE.body:
        if isinstance(node, ast.ClassDef) and node.name == "UltimateDiscordIntelligenceBotCrew":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == name:
                    for stmt in ast.walk(item):
                        if isinstance(stmt, ast.Call) and getattr(getattr(stmt, "func", None), "id", "") == "Agent":
                            for kw in stmt.keywords:
                                if kw.arg == "tools" and isinstance(kw.value, ast.List):
                                    names: set[str] = set()
                                    for elt in kw.value.elts:
                                        if isinstance(elt, ast.Call):
                                            fn = elt.func
                                            if isinstance(fn, ast.Name):
                                                names.add(fn.id)
                                            elif isinstance(fn, ast.Attribute):
                                                names.add(fn.attr)
                                    return names
    return set()


def test_content_manager_has_context_tools():
    tools = _agent_tools("content_manager")
    assert {"PipelineTool", "DebateCommandTool", "TranscriptIndexTool", "TimelineTool"} <= tools


def test_content_downloader_covers_all_platforms():
    tools = _agent_tools("content_downloader")
    expected = {
        "YouTubeDownloadTool",
        "TwitchDownloadTool",
        "KickDownloadTool",
        "TwitterDownloadTool",
        "InstagramDownloadTool",
        "TikTokDownloadTool",
        "RedditDownloadTool",
        "DiscordDownloadTool",
    }
    assert expected <= tools


def test_monitor_and_alert_agents_have_tools():
    assert _agent_tools("multi_platform_monitor") == {"MultiPlatformMonitorTool"}
    assert _agent_tools("system_alert_manager") == {
        "DiscordPrivateAlertTool",
        "SystemStatusTool",
    }


def test_cross_platform_intelligence_gatherer_tools():
    tools = _agent_tools("cross_platform_intelligence_gatherer")
    assert {
        "SocialMediaMonitorTool",
        "XMonitorTool",
        "DiscordMonitorTool",
    } <= tools


def test_fact_checker_and_scoring_tools():
    assert _agent_tools("enhanced_fact_checker") == {
        "LogicalFallacyTool",
        "PerspectiveSynthesizerTool",
        "FactCheckTool",
    }
    assert _agent_tools("truth_scoring_specialist") == {
        "TruthScoringTool",
        "TrustworthinessTrackerTool",
        "LeaderboardTool",
    }


def test_misc_agent_tool_coverage():
    assert _agent_tools("steelman_argument_generator") == {"SteelmanArgumentTool"}
    assert _agent_tools("discord_qa_manager") == {"DiscordQATool"}
    assert _agent_tools("character_profile_manager") == {"CharacterProfileTool"}
    assert _agent_tools("personality_synthesis_manager") == {
        "CharacterProfileTool",
        "TextAnalysisTool",
        "PerspectiveSynthesizerTool",
    }


def test_config_agents_and_tasks_sync():
    agents_config = yaml.safe_load(
        Path("src/ultimate_discord_intelligence_bot/config/agents.yaml").read_text()
    )
    tasks_config = yaml.safe_load(
        Path("src/ultimate_discord_intelligence_bot/config/tasks.yaml").read_text()
    )

    crew_class = next(
        node
        for node in MODULE.body
        if isinstance(node, ast.ClassDef)
        and node.name == "UltimateDiscordIntelligenceBotCrew"
    )
    agent_methods = {
        item.name
        for item in crew_class.body
        if isinstance(item, ast.FunctionDef)
        and any(
            isinstance(dec, ast.Name) and dec.id == "agent" for dec in item.decorator_list
        )
    }
    task_methods = {
        item.name
        for item in crew_class.body
        if isinstance(item, ast.FunctionDef)
        and any(
            isinstance(dec, ast.Name) and dec.id == "task" for dec in item.decorator_list
        )
    }

    assert set(agents_config) == agent_methods
    assert set(tasks_config) == task_methods

    for cfg in tasks_config.values():
        assert cfg.get("agent") in agents_config
