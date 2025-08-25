from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from .tools.pipeline_tool import PipelineTool
from .tools.discord_private_alert_tool import DiscordPrivateAlertTool
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
    def system_alert_manager(self) -> Agent:
        webhook = DISCORD_PRIVATE_WEBHOOK or "https://discord.com/api/webhooks/example"
        return Agent(
            config=self.agents_config["system_alert_manager"],
            tools=[DiscordPrivateAlertTool(webhook)],
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

    @crew
    def crew(self) -> Crew:
        """Create the project crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
