from __future__ import annotations

import json
import logging
import os
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from core.typing_utils import (
    typed,  # typing aid: keep precise signatures after framework decorators
)

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

_CREWAI_AVAILABLE = False
if TYPE_CHECKING:  # Provide real symbols for type checking when installed
    from crewai import Agent, Crew, Process, Task  # noqa: F401
    from crewai.agents.agent_builder.base_agent import BaseAgent  # noqa: F401
    from crewai.project import CrewBase, agent, crew, task  # noqa: F401

    _CREWAI_AVAILABLE = True
else:  # Runtime: attempt import but allow graceful degradation
    try:  # pragma: no cover - import side effects external
        from crewai import Agent, Crew, Process, Task  # type: ignore
        from crewai.agents.agent_builder.base_agent import BaseAgent  # type: ignore
        from crewai.project import CrewBase, agent, crew, task  # type: ignore

        _CREWAI_AVAILABLE = True
    except Exception:  # pragma: no cover - fallback placeholders
        from typing import Any as Agent  # type: ignore
        from typing import Any as Crew  # type: ignore
        from typing import Any as Process  # type: ignore
        from typing import Any as Task  # type: ignore

        class BaseAgent:  # minimal placeholder
            ...

        def CrewBase(cls):  # type: ignore
            return cls

        def agent(func):  # type: ignore
            return func

        def crew(func):  # type: ignore
            return func

        def task(func):  # type: ignore
            return func


RAW_SNIPPET_MAX_LEN = 160  # truncate raw output logging for verbose step mode


@CrewBase
class UltimateDiscordIntelligenceBotCrew:
    """Crew coordinating the content pipeline."""

    # Explicit attribute declarations to satisfy static type checking. These
    # are populated by the CrewAI framework decorators at runtime. We provide
    # conservative placeholder types so mypy recognizes them.
    agents_config: dict[str, AgentConfig]  # loaded agent configurations
    tasks_config: dict[str, TaskConfig]  # loaded task configurations
    agents: Sequence[BaseAgent]
    tasks: Sequence[Task]

    @typed  # outermost: preserves signature after crewai decorator
    @agent
    def content_manager(self) -> Agent:
        # Runtime path uses helper; the unreachable Agent() block below is for static AST tests.
        if False:  # pragma: no cover - test extraction aid
            Agent(  # type: ignore
                role="placeholder",
                goal="placeholder",
                backstory="placeholder",
                tools=[
                    PipelineTool(),
                    DebateCommandTool(),
                    TranscriptIndexTool(),
                    TimelineTool(),
                ],
            )
        return self._agent_from_config(
            "content_manager",
            tools=[PipelineTool(), DebateCommandTool(), TranscriptIndexTool(), TimelineTool()],
        )

    @typed
    @agent
    def content_downloader(self) -> Agent:
        if False:  # pragma: no cover - static tool enumeration aid
            Agent(  # type: ignore
                role="placeholder",
                goal="placeholder",
                backstory="placeholder",
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
        return self._agent_from_config(
            "content_downloader",
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
        if False:  # pragma: no cover
            Agent(role="p", goal="p", backstory="p", tools=[MultiPlatformMonitorTool()])  # type: ignore
        return self._agent_from_config("multi_platform_monitor", tools=[MultiPlatformMonitorTool()])

    @typed
    @agent
    def system_alert_manager(self) -> Agent:
        webhook = DISCORD_PRIVATE_WEBHOOK or "https://discord.com/api/webhooks/example"
        if False:  # pragma: no cover
            Agent(  # type: ignore
                role="p",
                goal="p",
                backstory="p",
                tools=[DiscordPrivateAlertTool("w"), SystemStatusTool()],
            )
        return self._agent_from_config(
            "system_alert_manager", tools=[DiscordPrivateAlertTool(webhook), SystemStatusTool()]
        )

    @typed
    @agent
    def cross_platform_intelligence_gatherer(self) -> Agent:
        if False:  # pragma: no cover
            Agent(  # type: ignore
                role="p",
                goal="p",
                backstory="p",
                tools=[SocialMediaMonitorTool(), XMonitorTool(), DiscordMonitorTool()],
            )
        return self._agent_from_config(
            "cross_platform_intelligence_gatherer",
            tools=[SocialMediaMonitorTool(), XMonitorTool(), DiscordMonitorTool()],
        )

    @typed
    @agent
    def enhanced_fact_checker(self) -> Agent:
        if False:  # pragma: no cover
            Agent(  # type: ignore
                role="p",
                goal="p",
                backstory="p",
                tools=[LogicalFallacyTool(), PerspectiveSynthesizerTool(), FactCheckTool()],
            )
        return self._agent_from_config(
            "enhanced_fact_checker",
            tools=[LogicalFallacyTool(), PerspectiveSynthesizerTool(), FactCheckTool()],
        )

    @typed
    @agent
    def truth_scoring_specialist(self) -> Agent:
        if False:  # pragma: no cover
            Agent(  # type: ignore
                role="p",
                goal="p",
                backstory="p",
                tools=[TruthScoringTool(), TrustworthinessTrackerTool(), LeaderboardTool()],
            )
        return self._agent_from_config(
            "truth_scoring_specialist",
            tools=[TruthScoringTool(), TrustworthinessTrackerTool(), LeaderboardTool()],
        )

    @typed
    @agent
    def steelman_argument_generator(self) -> Agent:
        if False:  # pragma: no cover
            Agent(role="p", goal="p", backstory="p", tools=[SteelmanArgumentTool()])  # type: ignore
        return self._agent_from_config(
            "steelman_argument_generator",
            tools=[SteelmanArgumentTool()],
        )

    @typed
    @agent
    def discord_qa_manager(self) -> Agent:
        if False:  # pragma: no cover
            Agent(role="p", goal="p", backstory="p", tools=[DiscordQATool()])  # type: ignore
        return self._agent_from_config("discord_qa_manager", tools=[DiscordQATool()])

    @typed
    @agent
    def ethan_defender(self) -> Agent:
        return self._agent_from_config("ethan_defender")

    @typed
    @agent
    def hasan_defender(self) -> Agent:
        return self._agent_from_config("hasan_defender")

    @typed
    @agent
    def character_profile_manager(self) -> Agent:
        if False:  # pragma: no cover
            Agent(role="p", goal="p", backstory="p", tools=[CharacterProfileTool()])  # type: ignore
        return self._agent_from_config(
            "character_profile_manager",
            tools=[CharacterProfileTool()],
        )

    @typed
    @agent
    def personality_synthesis_manager(self) -> Agent:
        if False:  # pragma: no cover
            Agent(  # type: ignore
                role="p",
                goal="p",
                backstory="p",
                tools=[CharacterProfileTool(), TextAnalysisTool(), PerspectiveSynthesizerTool()],
            )
        return self._agent_from_config(
            "personality_synthesis_manager",
            tools=[CharacterProfileTool(), TextAnalysisTool(), PerspectiveSynthesizerTool()],
        )

    @typed
    @task
    def execute_multi_platform_downloads(self) -> Task:
        return self._task_from_config("execute_multi_platform_downloads")

    @typed
    @task
    def process_video(self) -> Task:
        return self._task_from_config("process_video")

    @typed
    @task
    def monitor_system(self) -> Task:
        return self._task_from_config("monitor_system")

    @typed
    @task
    def identify_new_content(self) -> Task:
        return self._task_from_config("identify_new_content")

    @typed
    @task
    def gather_cross_platform_intelligence(self) -> Task:
        return self._task_from_config("gather_cross_platform_intelligence")

    @typed
    @task
    def get_context(self) -> Task:
        return self._task_from_config("get_context")

    @typed
    @task
    def fact_check_content(self) -> Task:
        return self._task_from_config("fact_check_content")

    @typed
    @task
    def score_truthfulness(self) -> Task:
        return self._task_from_config("score_truthfulness")

    @typed
    @task
    def steelman_argument(self) -> Task:
        return self._task_from_config("steelman_argument")

    @typed
    @task
    def analyze_claim(self) -> Task:
        return self._task_from_config("analyze_claim")

    @typed
    @task
    def fact_check_claim(self) -> Task:
        return self._task_from_config("fact_check_claim")

    @typed
    @task
    def update_leaderboard(self) -> Task:
        return self._task_from_config("update_leaderboard")

    @typed
    @task
    def answer_question(self) -> Task:
        return self._task_from_config("answer_question")

    @typed
    @task
    def get_timeline(self) -> Task:
        return self._task_from_config("get_timeline")

    @typed
    @task
    def get_profile(self) -> Task:
        return self._task_from_config("get_profile")

    @typed
    @task
    def synthesize_personality(self) -> Task:
        return self._task_from_config("synthesize_personality")

    @crew
    def crew(self) -> Crew:
        """Create the project crew with enhanced features.

        Adds optional runtime validation & dynamic embedder configuration.
        """
        if not _CREWAI_AVAILABLE:
            raise ImportError(
                "crewai is not installed. Install project with extras or run 'pip install crewai' to use crew orchestration features."
            )
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
            agents=list(self.agents),  # satisfy expected concrete list type
            tasks=list(self.tasks),  # satisfy expected concrete list type
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
            for required in ("agent", "description", "expected_output"):
                if required not in t_cfg:
                    raise ValueError(f"Task '{t_name}' missing required field '{required}'")
            # Narrow for type checker
            assert "agent" in t_cfg and "description" in t_cfg and "expected_output" in t_cfg
            agent_ref = t_cfg["agent"]
            if agent_ref not in self.agents_config:
                raise ValueError(f"Task '{t_name}' references unknown agent '{agent_ref}'")
            if "output_file" in t_cfg:
                out_path = Path(t_cfg["output_file"]).expanduser()
                try:
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                except Exception:
                    print(f"Warning: could not create output directory for task '{t_name}' -> {out_path.parent}")

    # -------------------------------
    # Internal construction helpers (typed)
    # -------------------------------
    def _agent_from_config(self, name: str, tools: list[Any] | None = None) -> Agent:
        """Instantiate an Agent from validated config.

        We expand the config explicitly so mypy sees required parameters instead
        of a single opaque ``config=`` argument (which the runtime library
        accepts but its stubs do not model). Unknown forward-compatible keys are
        ignored to keep strict type checking noise low.
        """
        cfg = self.agents_config[name]
        # Narrow required fields for mypy (AgentConfig has them as optional total=False)
        assert "role" in cfg and "goal" in cfg and "backstory" in cfg, f"Agent config '{name}' missing required keys"
        base: dict[str, Any] = {
            "role": cfg["role"],
            "goal": cfg["goal"],
            "backstory": cfg["backstory"],
        }
        # Whitelist optional keys supported by current runtime (avoid spraying **cfg)
        # Manually copy optional known fields (keeps mypy happy about literal keys)
        if "allow_delegation" in cfg:
            base["allow_delegation"] = cfg["allow_delegation"]
        if "verbose" in cfg:
            base["verbose"] = cfg["verbose"]
        if "reasoning" in cfg:
            base["reasoning"] = cfg["reasoning"]
        if "inject_date" in cfg:
            base["inject_date"] = cfg["inject_date"]
        if "date_format" in cfg:
            base["date_format"] = cfg["date_format"]
        if "memory" in cfg:
            base["memory"] = cfg["memory"]
        if "max_reasoning_attempts" in cfg:
            base["max_reasoning_attempts"] = cfg["max_reasoning_attempts"]
        if "respect_context_window" in cfg:
            base["respect_context_window"] = cfg["respect_context_window"]
        if "max_rpm" in cfg:
            base["max_rpm"] = cfg["max_rpm"]
        if tools:
            base["tools"] = tools
        return Agent(**base)

    def _task_from_config(self, name: str) -> Task:
        cfg = self.tasks_config[name]
        assert (
            "description" in cfg and "expected_output" in cfg and "agent" in cfg
        ), f"Task config '{name}' missing required keys"
        base: dict[str, Any] = {
            "description": cfg["description"],
            "expected_output": cfg["expected_output"],
            "agent": cfg["agent"],
        }
        if "human_input" in cfg:
            base["human_input"] = cfg["human_input"]
        if "output_file" in cfg:
            base["output_file"] = cfg["output_file"]
        if "async_execution" in cfg:
            base["async_execution"] = cfg["async_execution"]
        if "context" in cfg:
            base["context"] = cfg["context"]
        return Task(**base)
