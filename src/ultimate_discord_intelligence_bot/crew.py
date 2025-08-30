from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from core.typing_utils import typed  # typing aid: keep precise signatures after framework decorators

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


@CrewBase
class UltimateDiscordIntelligenceBotCrew:
    """Crew coordinating the content pipeline."""

    # Explicit attribute declarations to satisfy static type checking. These
    # are populated by the CrewAI framework decorators at runtime. We provide
    # conservative placeholder types so mypy recognizes them.
    agents_config: dict[str, dict[str, Any]]  # loaded agent configurations
    tasks_config: dict[str, dict[str, Any]]   # loaded task configurations
    agents: list[Agent]
    tasks: list[Task]

    @typed  # outermost: preserves signature after crewai decorator
    @agent
    def content_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["content_manager"],
            tools=[PipelineTool(), DebateCommandTool(), TranscriptIndexTool(), TimelineTool()],
        )

    @typed
    @agent
    def content_downloader(self) -> Agent:
        return Agent(
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
        return Agent(
            config=self.agents_config["multi_platform_monitor"],
            tools=[MultiPlatformMonitorTool()],
        )

    @typed
    @agent
    def system_alert_manager(self) -> Agent:
        webhook = DISCORD_PRIVATE_WEBHOOK or "https://discord.com/api/webhooks/example"
        return Agent(
            config=self.agents_config["system_alert_manager"],
            tools=[DiscordPrivateAlertTool(webhook), SystemStatusTool()],
        )

    @typed
    @agent
    def cross_platform_intelligence_gatherer(self) -> Agent:
        return Agent(
            config=self.agents_config["cross_platform_intelligence_gatherer"],
            tools=[SocialMediaMonitorTool(), XMonitorTool(), DiscordMonitorTool()],
        )

    @typed
    @agent
    def enhanced_fact_checker(self) -> Agent:
        return Agent(
            config=self.agents_config["enhanced_fact_checker"],
            tools=[LogicalFallacyTool(), PerspectiveSynthesizerTool(), FactCheckTool()],
        )

    @typed
    @agent
    def truth_scoring_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["truth_scoring_specialist"],
            tools=[TruthScoringTool(), TrustworthinessTrackerTool(), LeaderboardTool()],
        )

    @typed
    @agent
    def steelman_argument_generator(self) -> Agent:
        return Agent(
            config=self.agents_config["steelman_argument_generator"],
            tools=[SteelmanArgumentTool()],
        )

    @typed
    @agent
    def discord_qa_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["discord_qa_manager"],
            tools=[DiscordQATool()],
        )

    @typed
    @agent
    def ethan_defender(self) -> Agent:
        return Agent(config=self.agents_config["ethan_defender"])

    @typed
    @agent
    def hasan_defender(self) -> Agent:
        return Agent(config=self.agents_config["hasan_defender"])

    @typed
    @agent
    def character_profile_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["character_profile_manager"],
            tools=[CharacterProfileTool()],
        )

    @typed
    @agent
    def personality_synthesis_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["personality_synthesis_manager"],
            tools=[CharacterProfileTool(), TextAnalysisTool(), PerspectiveSynthesizerTool()],
        )

    @typed
    @task
    def process_video(self) -> Task:
        return Task(config=self.tasks_config["process_video"])

    @typed
    @task
    def execute_multi_platform_downloads(self) -> Task:
        return Task(config=self.tasks_config["execute_multi_platform_downloads"])

    @typed
    @task
    def monitor_system(self) -> Task:
        return Task(config=self.tasks_config["monitor_system"])

    @typed
    @task
    def gather_cross_platform_intelligence(self) -> Task:
        return Task(config=self.tasks_config["gather_cross_platform_intelligence"])

    @typed
    @task
    def identify_new_content(self) -> Task:
        return Task(config=self.tasks_config["identify_new_content"])

    @typed
    @task
    def fact_check_content(self) -> Task:
        return Task(config=self.tasks_config["fact_check_content"])

    @typed
    @task
    def score_truthfulness(self) -> Task:
        return Task(config=self.tasks_config["score_truthfulness"])

    @typed
    @task
    def steelman_argument(self) -> Task:
        return Task(config=self.tasks_config["steelman_argument"])

    @typed
    @task
    def analyze_claim(self) -> Task:
        return Task(config=self.tasks_config["analyze_claim"])

    @typed
    @task
    def get_context(self) -> Task:
        return Task(config=self.tasks_config["get_context"])

    @typed
    @task
    def fact_check_claim(self) -> Task:
        return Task(config=self.tasks_config["fact_check_claim"])

    @typed
    @task
    def update_leaderboard(self) -> Task:
        return Task(config=self.tasks_config["update_leaderboard"])

    @typed
    @task
    def answer_question(self) -> Task:
        return Task(config=self.tasks_config["answer_question"])

    @typed
    @task
    def get_timeline(self) -> Task:
        return Task(config=self.tasks_config["get_timeline"])

    @typed
    @task
    def get_profile(self) -> Task:
        return Task(config=self.tasks_config["get_profile"])

    @typed
    @task
    def synthesize_personality(self) -> Task:
        return Task(config=self.tasks_config["synthesize_personality"])

    @crew
    def crew(self) -> Crew:
        """Create the project crew with enhanced features."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            # ADD THESE MODERN FEATURES:
            planning=True,  # Enable dynamic planning
            memory=True,  # Enable memory across executions
            cache=True,  # Enable tool result caching
            max_rpm=10,  # Rate limiting for API calls
            embedder={"provider": "openai"},  # Memory embeddings
            step_callback=self._log_step,  # Custom logging
            # Error handling
            max_execution_time=3600,  # 1 hour timeout
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
            if getattr(step, "tool", None) is not None:
                print(f"🤖 Agent {getattr(step.agent, 'role', 'unknown')} using {step.tool}")
            else:
                print(f"🤖 Agent {getattr(step.agent, 'role', 'unknown')} thinking...")
