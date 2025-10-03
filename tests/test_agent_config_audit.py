import ast
from pathlib import Path

import yaml

CREW_FILE = Path("src/ultimate_discord_intelligence_bot/crew.py")
MODULE = ast.parse(CREW_FILE.read_text())


def _agent_tools(name: str) -> set[str]:
    """Extract tool names from an agent method, handling wrap_tool_for_crewai() wrappers."""
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
                                        # Handle wrap_tool_for_crewai(ToolClass()) pattern
                                        if isinstance(elt, ast.Call):
                                            fn = elt.func
                                            # If it's wrap_tool_for_crewai, extract the inner tool
                                            if isinstance(fn, ast.Name) and fn.id == "wrap_tool_for_crewai":
                                                if elt.args and isinstance(elt.args[0], ast.Call):
                                                    inner_call = elt.args[0]
                                                    inner_fn = inner_call.func
                                                    if isinstance(inner_fn, ast.Name):
                                                        names.add(inner_fn.id)
                                                    elif isinstance(inner_fn, ast.Attribute):
                                                        names.add(inner_fn.attr)
                                            # Handle direct tool calls (backward compatibility)
                                            elif isinstance(fn, ast.Name):
                                                names.add(fn.id)
                                            elif isinstance(fn, ast.Attribute):
                                                names.add(fn.attr)
                                    return names
    return set()


def test_mission_orchestrator_has_core_tools():
    tools = _agent_tools("mission_orchestrator")
    assert {
        "PipelineTool",
        "AdvancedPerformanceAnalyticsTool",
        "TimelineTool",
        "PerspectiveSynthesizerTool",
        "MCPCallTool",
    } <= tools


def test_acquisition_specialist_covers_platforms():
    tools = _agent_tools("acquisition_specialist")
    expected = {
        "YouTubeDownloadTool",
        "TwitchDownloadTool",
        "KickDownloadTool",
        "TwitterDownloadTool",
        "InstagramDownloadTool",
        "TikTokDownloadTool",
        "RedditDownloadTool",
        "DiscordDownloadTool",
        "MultiPlatformDownloadTool",
        "DriveUploadTool",
        "DriveUploadToolBypass",
    }
    assert expected <= tools


def test_signal_and_reliability_agents_have_tools():
    signal_tools = _agent_tools("signal_recon_specialist")
    assert {"SocialMediaMonitorTool", "XMonitorTool", "DiscordMonitorTool", "SentimentTool"} <= signal_tools

    reliability_tools = _agent_tools("system_reliability_officer")
    assert {
        "DiscordPrivateAlertTool",
        "SystemStatusTool",
        "AdvancedPerformanceAnalyticsTool",
        "PipelineTool",
    } <= reliability_tools


def test_trend_intelligence_scout_tools():
    tools = _agent_tools("trend_intelligence_scout")
    assert {
        "MultiPlatformMonitorTool",
        "ResearchAndBriefTool",
        "ResearchAndBriefMultiTool",
        "SocialResolverTool",
    } <= tools


def test_fact_checker_and_scoring_tools():
    assert _agent_tools("verification_director") == {
        "FactCheckTool",
        "LogicalFallacyTool",
        "ClaimExtractorTool",
        "ContextVerificationTool",
        "PerspectiveSynthesizerTool",
    }
    assert _agent_tools("risk_intelligence_analyst") == {
        "DeceptionScoringTool",
        "TruthScoringTool",
        "TrustworthinessTrackerTool",
        "LeaderboardTool",
    }


def test_misc_agent_tool_coverage():
    assert _agent_tools("argument_strategist") == {
        "SteelmanArgumentTool",
        "DebateCommandTool",
        "FactCheckTool",
        "PerspectiveSynthesizerTool",
    }
    assert _agent_tools("community_liaison") == {
        "DiscordQATool",
        "DiscordPostTool",
        "VectorSearchTool",
    }
    assert _agent_tools("persona_archivist") == {
        "CharacterProfileTool",
        "TimelineTool",
        "SentimentTool",
        "TrustworthinessTrackerTool",
    }
    assert _agent_tools("knowledge_integrator") == {
        "MemoryStorageTool",
        "GraphMemoryTool",
        "HippoRagContinualMemoryTool",
        "MemoryCompactionTool",
        "RagIngestTool",
        "RagIngestUrlTool",
        "RagHybridTool",
        "VectorSearchTool",
    }
    assert _agent_tools("intelligence_briefing_curator") == {
        "LCSummarizeTool",
        "PerspectiveSynthesizerTool",
        "RagQueryVectorStoreTool",
        "VectorSearchTool",
        "TimelineTool",
        "DriveUploadTool",
    }
    assert _agent_tools("research_synthesist") == {
        "ResearchAndBriefTool",
        "ResearchAndBriefMultiTool",
        "RagHybridTool",
        "RagQueryVectorStoreTool",
        "LCSummarizeTool",
        "OfflineRAGTool",
        "VectorSearchTool",
    }


def test_config_agents_and_tasks_sync():
    agents_config = yaml.safe_load(Path("src/ultimate_discord_intelligence_bot/config/agents.yaml").read_text())
    tasks_config = yaml.safe_load(Path("src/ultimate_discord_intelligence_bot/config/tasks.yaml").read_text())

    crew_class = next(
        node
        for node in MODULE.body
        if isinstance(node, ast.ClassDef) and node.name == "UltimateDiscordIntelligenceBotCrew"
    )
    agent_methods = {
        item.name
        for item in crew_class.body
        if isinstance(item, ast.FunctionDef)
        and any(isinstance(dec, ast.Name) and dec.id == "agent" for dec in item.decorator_list)
    }
    task_methods = {
        item.name
        for item in crew_class.body
        if isinstance(item, ast.FunctionDef)
        and any(isinstance(dec, ast.Name) and dec.id == "task" for dec in item.decorator_list)
    }

    assert set(agents_config) == agent_methods
    assert set(tasks_config) == task_methods

    for cfg in tasks_config.values():
        assert cfg.get("agent") in agents_config


def test_agents_have_modern_config_fields():
    """Verify all agents have modern CrewAI configuration fields."""
    agents_config = yaml.safe_load(Path("src/ultimate_discord_intelligence_bot/config/agents.yaml").read_text())

    required_fields = {"allow_delegation", "verbose", "reasoning", "inject_date", "date_format"}

    for agent_name, config in agents_config.items():
        missing_fields = required_fields - set(config.keys())
        assert not missing_fields, f"Agent {agent_name} missing fields: {missing_fields}"

        # Validate field types and values
        assert isinstance(config["allow_delegation"], bool), f"Agent {agent_name}: allow_delegation must be bool"
        assert isinstance(config["verbose"], bool), f"Agent {agent_name}: verbose must be bool"
        assert isinstance(config["reasoning"], bool), f"Agent {agent_name}: reasoning must be bool"
        assert isinstance(config["inject_date"], bool), f"Agent {agent_name}: inject_date must be bool"
        assert isinstance(config["date_format"], str), f"Agent {agent_name}: date_format must be string"


def test_tasks_have_modern_config_fields():
    """Verify key tasks have enhanced configuration."""
    tasks_config = yaml.safe_load(Path("src/ultimate_discord_intelligence_bot/config/tasks.yaml").read_text())

    enhanced_tasks = {
        "plan_autonomy_mission",
        "capture_source_media",
        "transcribe_and_index_media",
        "map_transcript_insights",
        "verify_priority_claims",
        "score_risk_and_truth",
        "persist_mission_intelligence",
        "curate_intelligence_briefing",
        "respond_to_community",
        "craft_argument_brief",
        "system_health_watch",
    }

    for task_name in enhanced_tasks:
        if task_name in tasks_config:
            config = tasks_config[task_name]
            assert "human_input" in config, f"Task {task_name} missing human_input field"
            assert isinstance(config["human_input"], bool), f"Task {task_name}: human_input must be bool"

            if "context" in config:
                assert isinstance(config["context"], list), f"Task {task_name}: context must be a list"
                assert all(isinstance(dep, str) for dep in config["context"]), (
                    f"Task {task_name}: context items must be strings"
                )

            if "output_file" in config:
                assert isinstance(config["output_file"], str), f"Task {task_name}: output_file must be string"


def test_crew_has_enhanced_features():
    """Verify crew configuration includes modern features."""
    crew_file = Path("src/ultimate_discord_intelligence_bot/crew.py").read_text()

    # Check for modern crew features in the crew method
    assert "planning=True" in crew_file, "Crew missing planning=True"
    assert "memory=True" in crew_file, "Crew missing memory=True"
    assert "cache=True" in crew_file, "Crew missing cache=True"
    assert "max_rpm=" in crew_file, "Crew missing max_rpm configuration"
    assert "step_callback=" in crew_file, "Crew missing step_callback configuration"
    assert "embedder=" in crew_file, "Crew missing embedder configuration"
    # max_execution_time parameter was removed from Crew instantiation (not supported by current CrewAI Crew API)
    # Retain other feature assertions only.

    # Check that _log_step method exists
    assert "def _log_step" in crew_file, "Crew missing _log_step method"


def test_task_context_dependencies():
    """Verify task context dependencies are properly configured."""
    tasks_config = yaml.safe_load(Path("src/ultimate_discord_intelligence_bot/config/tasks.yaml").read_text())

    # Define expected dependencies
    expected_dependencies = {
        "transcribe_and_index_media": ["capture_source_media"],
        "map_transcript_insights": ["transcribe_and_index_media"],
        "verify_priority_claims": ["map_transcript_insights"],
        "score_risk_and_truth": ["verify_priority_claims"],
        "update_persona_dossiers": ["score_risk_and_truth"],
        "persist_mission_intelligence": [
            "map_transcript_insights",
            "verify_priority_claims",
            "score_risk_and_truth",
        ],
        "curate_intelligence_briefing": [
            "verify_priority_claims",
            "score_risk_and_truth",
            "update_persona_dossiers",
            "persist_mission_intelligence",
        ],
        "respond_to_community": ["verify_priority_claims", "update_persona_dossiers", "curate_intelligence_briefing"],
        "craft_argument_brief": ["verify_priority_claims", "map_transcript_insights"],
    }

    for task_name, expected_deps in expected_dependencies.items():
        if task_name in tasks_config:
            config = tasks_config[task_name]
            if "context" in config:
                actual_deps = config["context"]
                for dep in expected_deps:
                    assert dep in actual_deps, f"Task {task_name} missing dependency {dep}"
