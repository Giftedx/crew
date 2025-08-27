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
from .tools.trustworthiness_tracker_tool import TrustworthinessTrackerTool
from .tools.fact_check_tool import FactCheckTool
from .tools.leaderboard_tool import LeaderboardTool
from .tools.debate_command_tool import DebateCommandTool
from .tools.discord_qa_tool import DiscordQATool
from .tools.steelman_argument_tool import SteelmanArgumentTool
from .tools.text_analysis_tool import TextAnalysisTool
from .tools.yt_dlp_download_tool import (
    YouTubeDownloadTool,
    TwitchDownloadTool,
    KickDownloadTool,
    TwitterDownloadTool,
    InstagramDownloadTool,
    TikTokDownloadTool,
    RedditDownloadTool,
)
from .tools.discord_download_tool import DiscordDownloadTool
from .tools.character_profile_tool import CharacterProfileTool
from .tools.x_monitor_tool import XMonitorTool
from .tools.discord_monitor_tool import DiscordMonitorTool
from .tools.transcript_index_tool import TranscriptIndexTool
from .tools.timeline_tool import TimelineTool
from .settings import DISCORD_PRIVATE_WEBHOOK


@CrewBase
class UltimateDiscordIntelligenceBotCrew:
    """Crew coordinating the content pipeline."""

    @agent
    def content_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["content_manager"],
            tools=[PipelineTool(), DebateCommandTool(), TranscriptIndexTool(), TimelineTool()],
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
                InstagramDownloadTool(),
                TikTokDownloadTool(),
                RedditDownloadTool(),
                DiscordDownloadTool(),
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
            tools=[SocialMediaMonitorTool(), XMonitorTool(), DiscordMonitorTool()],
        )

    @agent
    def enhanced_fact_checker(self) -> Agent:
        return Agent(
            config=self.agents_config["enhanced_fact_checker"],
            tools=[LogicalFallacyTool(), PerspectiveSynthesizerTool(), FactCheckTool()],
        )

    @agent
    def truth_scoring_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["truth_scoring_specialist"],
            tools=[TruthScoringTool(), TrustworthinessTrackerTool(), LeaderboardTool()],
        )

    @agent
    def steelman_argument_generator(self) -> Agent:
        return Agent(
            config=self.agents_config["steelman_argument_generator"],
            tools=[SteelmanArgumentTool()],
        )

    @agent
    def discord_qa_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["discord_qa_manager"],
            tools=[DiscordQATool()],
        )

    @agent
    def ethan_defender(self) -> Agent:
        return Agent(config=self.agents_config["ethan_defender"])

    @agent
    def hasan_defender(self) -> Agent:
        return Agent(config=self.agents_config["hasan_defender"])

    @agent
    def character_profile_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["character_profile_manager"],
            tools=[CharacterProfileTool()],
        )

    @agent
    def personality_synthesis_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["personality_synthesis_manager"],
            tools=[CharacterProfileTool(), TextAnalysisTool(), PerspectiveSynthesizerTool()],
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

    @task
    def steelman_argument(self) -> Task:
        return Task(config=self.tasks_config["steelman_argument"])

    @task
    def analyze_claim(self) -> Task:
        return Task(config=self.tasks_config["analyze_claim"])

    @task
    def get_context(self) -> Task:
        return Task(config=self.tasks_config["get_context"])

    @task
    def fact_check_claim(self) -> Task:
        return Task(config=self.tasks_config["fact_check_claim"])

    @task
    def update_leaderboard(self) -> Task:
        return Task(config=self.tasks_config["update_leaderboard"])

    @task
    def answer_question(self) -> Task:
        return Task(config=self.tasks_config["answer_question"])

    @task
    def get_timeline(self) -> Task:
        return Task(config=self.tasks_config["get_timeline"])

    @task
    def get_profile(self) -> Task:
        return Task(config=self.tasks_config["get_profile"])

    @task
    def synthesize_personality(self) -> Task:
        return Task(config=self.tasks_config["synthesize_personality"])

    @crew
    def crew(self) -> Crew:
        """Create the project crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
