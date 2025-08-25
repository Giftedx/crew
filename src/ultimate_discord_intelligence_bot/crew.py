from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from .tools.pipeline_tool import PipelineTool
from .tools.discord_private_alert_tool import DiscordPrivateAlertTool
from .tools.system_status_tool import SystemStatusTool
from .tools.logical_fallacy_tool import LogicalFallacyTool
from .tools.perspective_synthesizer_tool import PerspectiveSynthesizerTool
from .tools.social_media_monitor_tool import SocialMediaMonitorTool
from .tools.multi_platform_monitor_tool import MultiPlatformMonitorTool
from .tools.truth_scoring_tool import TruthScoringTool
from .tools.yt_dlp_download_tool import (
    YouTubeDownloadTool,
    TwitchDownloadTool,
    KickDownloadTool,
    TwitterDownloadTool,
)
from .settings import DISCORD_PRIVATE_WEBHOOK


@CrewBase
class UltimateDiscordIntelligenceBotCrew:
    """Crew coordinating the content pipeline."""

    @agent
    def content_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["content_manager"],
            tools=[PipelineTool()],
        )

    @agent
    def content_downloader(self) -> Agent:
        return Agent(
            config=self.agents_config["content_downloader"],
            tools=[
                YouTubeDownloadTool(),
                TwitchDownloadTool(),
                KickDownloadTool(),
                TwitterDownloadTool(),
            ],
        )

    @agent
    def multi_platform_monitor(self) -> Agent:
        return Agent(
            config=self.agents_config["multi_platform_monitor"],
            tools=[MultiPlatformMonitorTool()],
        )

    @agent
    def system_alert_manager(self) -> Agent:
        webhook = DISCORD_PRIVATE_WEBHOOK or "https://discord.com/api/webhooks/example"
        return Agent(
            config=self.agents_config["system_alert_manager"],
            tools=[DiscordPrivateAlertTool(webhook), SystemStatusTool()],
        )

    @agent
    def cross_platform_intelligence_gatherer(self) -> Agent:
        return Agent(
            config=self.agents_config["cross_platform_intelligence_gatherer"],
            tools=[SocialMediaMonitorTool()],
        )

    @agent
    def enhanced_fact_checker(self) -> Agent:
        return Agent(
            config=self.agents_config["enhanced_fact_checker"],
            tools=[LogicalFallacyTool(), PerspectiveSynthesizerTool()],
        )

    @agent
    def truth_scoring_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["truth_scoring_specialist"],
            tools=[TruthScoringTool()],
        )


    @task
    def process_video(self) -> Task:
        return Task(config=self.tasks_config["process_video"])

    @task
    def execute_multi_platform_downloads(self) -> Task:
        return Task(config=self.tasks_config["execute_multi_platform_downloads"])

    @task
    def monitor_system(self) -> Task:
        return Task(config=self.tasks_config["monitor_system"])

    @task
    def gather_cross_platform_intelligence(self) -> Task:
        return Task(config=self.tasks_config["gather_cross_platform_intelligence"])

    @task
    def identify_new_content(self) -> Task:
        return Task(config=self.tasks_config["identify_new_content"])

    @task
    def fact_check_content(self) -> Task:
        return Task(config=self.tasks_config["fact_check_content"])

    @task
    def score_truthfulness(self) -> Task:
        return Task(config=self.tasks_config["score_truthfulness"])

    @crew
    def crew(self) -> Crew:
        """Create the project crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
