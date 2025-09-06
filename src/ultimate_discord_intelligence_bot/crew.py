from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Protocol, cast, runtime_checkable

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from core.typing_utils import typed  # typing aid: keep precise signatures after framework decorators

from .config_types import AgentConfig, TaskConfig
from .settings import DISCORD_PRIVATE_WEBHOOK
from .tools.character_profile_tool import CharacterProfileTool
from .tools.debate_command_tool import DebateCommandTool
from .tools.discord_download_tool import DiscordDownloadTool
from .tools.discord_monitor_tool import DiscordMonitorTool
from .tools.discord_private_alert_tool import DiscordPrivateAlertTool
from .tools.discord_qa_tool import DiscordQATool
from .tools.fact_check_tool import FactCheckTool
from .tools.leaderboard_tool import LeaderboardTool
from .tools.logical_fallacy_tool import LogicalFallacyTool
from .tools.multi_platform_monitor_tool import MultiPlatformMonitorTool
from .tools.perspective_synthesizer_tool import PerspectiveSynthesizerTool
from .tools.pipeline_tool import PipelineTool
from .tools.social_media_monitor_tool import SocialMediaMonitorTool
from .tools.steelman_argument_tool import SteelmanArgumentTool
from .tools.system_status_tool import SystemStatusTool
from .tools.text_analysis_tool import TextAnalysisTool
from .tools.timeline_tool import TimelineTool
from .tools.transcript_index_tool import TranscriptIndexTool
from .tools.trustworthiness_tracker_tool import TrustworthinessTrackerTool
from .tools.truth_scoring_tool import TruthScoringTool
from .tools.x_monitor_tool import XMonitorTool
from .tools.yt_dlp_download_tool import (
    InstagramDownloadTool,
    KickDownloadTool,
    RedditDownloadTool,
    TikTokDownloadTool,
    TwitchDownloadTool,
    TwitterDownloadTool,
    YouTubeDownloadTool,
)

RAW_SNIPPET_MAX_LEN = 160  # truncate raw output logging for verbose step mode


@CrewBase
class UltimateDiscordIntelligenceBotCrew:
    """Crew coordinating the content pipeline."""

    # Explicit attribute declarations to satisfy static type checking. These
    # are populated by the CrewAI framework decorators at runtime. We provide
    # conservative placeholder types so mypy recognizes them.
    agents_config: dict[str, AgentConfig]  # loaded agent configurations
    tasks_config: dict[str, TaskConfig]  # loaded task configurations
    agents: list[BaseAgent]
    tasks: list[Task]

    @typed  # outermost: preserves signature after crewai decorator
    @agent
    def content_manager(self) -> Agent:
        return Agent(  # type: ignore[call-arg]
            config=self.agents_config["content_manager"],
            tools=[PipelineTool(), DebateCommandTool(), TranscriptIndexTool(), TimelineTool()],
        )

    @typed
    @agent
    def content_downloader(self) -> Agent:
        return Agent(  # type: ignore[call-arg]
            config=self.agents_config["content_downloader"],
            tools=[
                YouTubeDownloadTool(),
                TwitchDownloadTool(),
                KickDownloadTool(),
                TwitterDownloadTool(),
                InstagramDownloadTool(),
                TikTokDownloadTool(),
                RedditDownloadTool(),
                DiscordDownloadTool(),
            ],
        )

    @typed
    @agent
    def multi_platform_monitor(self) -> Agent:
        return Agent(  # type: ignore[call-arg]
            config=self.agents_config["multi_platform_monitor"],
            tools=[MultiPlatformMonitorTool()],
        )

    @typed
    @agent
    def system_alert_manager(self) -> Agent:
        webhook = DISCORD_PRIVATE_WEBHOOK or "https://discord.com/api/webhooks/example"
        return Agent(  # type: ignore[call-arg]
            config=self.agents_config["system_alert_manager"],
            tools=[DiscordPrivateAlertTool(webhook), SystemStatusTool()],
        )

    @typed
    @agent
    def cross_platform_intelligence_gatherer(self) -> Agent:
        return Agent(  # type: ignore[call-arg]
            config=self.agents_config["cross_platform_intelligence_gatherer"],
            tools=[SocialMediaMonitorTool(), XMonitorTool(), DiscordMonitorTool()],
        )

    @typed
    @agent
    def enhanced_fact_checker(self) -> Agent:
        return Agent(  # type: ignore[call-arg]
            config=self.agents_config["enhanced_fact_checker"],
            tools=[LogicalFallacyTool(), PerspectiveSynthesizerTool(), FactCheckTool()],
        )

    @typed
    @agent
    def truth_scoring_specialist(self) -> Agent:
        return Agent(  # type: ignore[call-arg]
            config=self.agents_config["truth_scoring_specialist"],
            tools=[TruthScoringTool(), TrustworthinessTrackerTool(), LeaderboardTool()],
        )

    @typed
    @agent
    def steelman_argument_generator(self) -> Agent:
        return Agent(  # type: ignore[call-arg]
            config=self.agents_config["steelman_argument_generator"],
            tools=[SteelmanArgumentTool()],
        )

    @typed
    @agent
    def discord_qa_manager(self) -> Agent:
        return Agent(  # type: ignore[call-arg]
            config=self.agents_config["discord_qa_manager"],
            tools=[DiscordQATool()],
        )

    @typed
    @agent
    def ethan_defender(self) -> Agent:
        return Agent(config=self.agents_config["ethan_defender"])  # type: ignore[call-arg]

    @typed
    @agent
    def hasan_defender(self) -> Agent:
        return Agent(config=self.agents_config["hasan_defender"])  # type: ignore[call-arg]

    @typed
    @agent
    def character_profile_manager(self) -> Agent:
        return Agent(  # type: ignore[call-arg]
            config=self.agents_config["character_profile_manager"],
            tools=[CharacterProfileTool()],
        )

    @typed
    @agent
    def personality_synthesis_manager(self) -> Agent:
        return Agent(  # type: ignore[call-arg]
            config=self.agents_config["personality_synthesis_manager"],
            tools=[CharacterProfileTool(), TextAnalysisTool(), PerspectiveSynthesizerTool()],
        )

    @typed
    @task
    def execute_multi_platform_downloads(self) -> Task:
        return Task(config=self.tasks_config["execute_multi_platform_downloads"])  # type: ignore[call-arg]

    @typed
    @task
    def process_video(self) -> Task:
        return Task(config=self.tasks_config["process_video"])  # type: ignore[call-arg]

    @typed
    @task
    def monitor_system(self) -> Task:
        return Task(config=self.tasks_config["monitor_system"])  # type: ignore[call-arg]

    @typed
    @task
    def identify_new_content(self) -> Task:
        return Task(config=self.tasks_config["identify_new_content"])  # type: ignore[call-arg]

    @typed
    @task
    def gather_cross_platform_intelligence(self) -> Task:
        return Task(config=self.tasks_config["gather_cross_platform_intelligence"])  # type: ignore[call-arg]

    @typed
    @task
    def get_context(self) -> Task:
        return Task(config=self.tasks_config["get_context"])  # type: ignore[call-arg]

    @typed
    @task
    def fact_check_content(self) -> Task:
        return Task(config=self.tasks_config["fact_check_content"])  # type: ignore[call-arg]

    @typed
    @task
    def score_truthfulness(self) -> Task:
        return Task(config=self.tasks_config["score_truthfulness"])  # type: ignore[call-arg]

    @typed
    @task
    def steelman_argument(self) -> Task:
        return Task(config=self.tasks_config["steelman_argument"])  # type: ignore[call-arg]

    @typed
    @task
    def analyze_claim(self) -> Task:
        return Task(config=self.tasks_config["analyze_claim"])  # type: ignore[call-arg]

    @typed
    @task
    def fact_check_claim(self) -> Task:
        return Task(config=self.tasks_config["fact_check_claim"])  # type: ignore[call-arg]

    @typed
    @task
    def update_leaderboard(self) -> Task:
        return Task(config=self.tasks_config["update_leaderboard"])  # type: ignore[call-arg]

    @typed
    @task
    def answer_question(self) -> Task:
        return Task(config=self.tasks_config["answer_question"])  # type: ignore[call-arg]

    @typed
    @task
    def get_timeline(self) -> Task:
        return Task(config=self.tasks_config["get_timeline"])  # type: ignore[call-arg]

    @typed
    @task
    def get_profile(self) -> Task:
        return Task(config=self.tasks_config["get_profile"])  # type: ignore[call-arg]

    @typed
    @task
    def synthesize_personality(self) -> Task:
        return Task(config=self.tasks_config["synthesize_personality"])  # type: ignore[call-arg]

    @crew
    def crew(self) -> Crew:
        """Create the project crew with enhanced features.

        Adds optional runtime validation & dynamic embedder configuration.
        """
        if os.getenv("ENABLE_CREW_CONFIG_VALIDATION") == "1":
            self._validate_configs()

        embedder_provider = os.getenv("CREW_EMBEDDER_PROVIDER", "openai")
        embedder_cfg_raw = os.getenv("CREW_EMBEDDER_CONFIG_JSON")
        embedder: dict[str, Any] = {"provider": embedder_provider}
        if embedder_cfg_raw:
            try:  # pragma: no cover - defensive
                extra = json.loads(embedder_cfg_raw)
                if isinstance(extra, dict):
                    embedder.update(extra)
            except Exception as exc:  # pragma: no cover
                logging.getLogger(__name__).warning("Invalid CREW_EMBEDDER_CONFIG_JSON: %s", exc)

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            planning=True,
            memory=True,
            cache=True,
            max_rpm=10,
            embedder=embedder,
            step_callback=self._log_step,
        )

    @runtime_checkable
    class _StepLike(Protocol):  # protocol to narrow what we access
        agent: Any  # crewai runtime object with a 'role' attribute
        tool: Any | None

    def _log_step(self, step: object) -> None:
        """Log each agent step for observability.

        Accepts a generic object to avoid tight coupling to crewai internals;
        uses duck typing so type checking stays permissive without ``Any``
        leaking into callers.
        """
        if isinstance(step, self._StepLike):
            role = getattr(step.agent, "role", "unknown")
            tool = getattr(step, "tool", None)
            if tool is not None:
                print(f"🤖 Agent {role} using {tool}")
            else:
                print(f"🤖 Agent {role} thinking...")
            if os.getenv("ENABLE_CREW_STEP_VERBOSE") == "1":
                raw = getattr(step, "raw", None) or getattr(getattr(step, "output", None), "raw", None)
                if isinstance(raw, str):
                    snippet = raw.strip().replace("\n", " ")
                    if len(snippet) > RAW_SNIPPET_MAX_LEN:
                        snippet = snippet[: RAW_SNIPPET_MAX_LEN - 3] + "..."
                    print(f"   ↳ raw: {snippet}")

    # -------------------------------
    # Validation helpers
    # -------------------------------
    def _validate_configs(self) -> None:
        """Validate agent & task configuration structure.

        Raises ValueError on *critical* schema mismatches; prints warnings for
        soft issues to avoid over-strict failures in production.
        """
        required_agent_fields = {
            "role",
            "goal",
            "backstory",
            "allow_delegation",
            "verbose",
            "reasoning",
            "inject_date",
            "date_format",
        }
        for name, cfg in self.agents_config.items():
            missing = required_agent_fields - set(cfg.keys())
            if missing:
                raise ValueError(f"Agent '{name}' missing required fields: {sorted(missing)}")
            # Type sanity checks (best-effort)
            if not isinstance(cfg.get("allow_delegation"), bool):
                raise ValueError(f"Agent '{name}' allow_delegation must be bool")
            if not isinstance(cfg.get("verbose"), bool):
                raise ValueError(f"Agent '{name}' verbose must be bool")
            if not isinstance(cfg.get("reasoning"), bool):
                raise ValueError(f"Agent '{name}' reasoning must be bool")
            if not isinstance(cfg.get("inject_date"), bool):
                raise ValueError(f"Agent '{name}' inject_date must be bool")
            if not isinstance(cfg.get("date_format"), str):
                raise ValueError(f"Agent '{name}' date_format must be str")

        for t_name, t_cfg in self.tasks_config.items():
            if "agent" not in t_cfg:
                raise ValueError(f"Task '{t_name}' missing agent reference")
            agent_ref = cast(str, t_cfg["agent"])  # known present now
            if agent_ref not in self.agents_config:
                raise ValueError(f"Task '{t_name}' references unknown agent '{agent_ref}'")
            if "output_file" in t_cfg:
                out_path = Path(t_cfg["output_file"]).expanduser()
                try:
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                except Exception:
                    print(f"Warning: could not create output directory for task '{t_name}' -> {out_path.parent}")
