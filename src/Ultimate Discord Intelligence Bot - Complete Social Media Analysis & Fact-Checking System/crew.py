import os
from crewai import LLM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
	ScrapegraphScrapeTool,
	FileReadTool,
	StagehandTool,
	ScrapeWebsiteTool,
	SerplyScholarSearchTool,
	EXASearchTool,
	SerplyNewsSearchTool,
	SerperDevTool,
	QdrantVectorSearchTool
)
from crewai_tools import CrewaiEnterpriseTools


@CrewBase
class UltimateDiscordIntelligenceBotCompleteSocialMediaAnalysisFactCheckingSystemCrew:
    """UltimateDiscordIntelligenceBotCompleteSocialMediaAnalysisFactCheckingSystem crew"""

    
    @agent
    def youtube_channel_monitor(self) -> Agent:
        
        return Agent(
            config=self.agents_config["youtube_channel_monitor"],
            tools=[
				ScrapeWebsiteTool()
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def instagram_content_downloader(self) -> Agent:
        
        return Agent(
            config=self.agents_config["instagram_content_downloader"],
            tools=[
				ScrapegraphScrapeTool()
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def file_system_manager(self) -> Agent:
        
        return Agent(
            config=self.agents_config["file_system_manager"],
            tools=[
				FileReadTool()
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def cloud_storage_manager(self) -> Agent:
        enterprise_actions_tool = CrewaiEnterpriseTools(
            actions_list=[
                
                "google_drive_save_file",
                
                "google_drive_create_folder",
                
                "google_drive_get_file_by_id",
                
            ],
        )
        
        return Agent(
            config=self.agents_config["cloud_storage_manager"],
            tools=[
				*enterprise_actions_tool
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def discord_channel_router(self) -> Agent:
        
        return Agent(
            config=self.agents_config["discord_channel_router"],
            tools=[
				FileReadTool()
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def discord_bot_manager(self) -> Agent:
        
        return Agent(
            config=self.agents_config["discord_bot_manager"],
            tools=[
				StagehandTool()
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def content_transcription_specialist(self) -> Agent:
        
        return Agent(
            config=self.agents_config["content_transcription_specialist"],
            tools=[
				FileReadTool(),
				ScrapeWebsiteTool()
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def speaker_analysis_expert(self) -> Agent:
        
        return Agent(
            config=self.agents_config["speaker_analysis_expert"],
            tools=[
				FileReadTool(),
				ScrapeWebsiteTool()
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def content_intelligence_analyst(self) -> Agent:
        
        return Agent(
            config=self.agents_config["content_intelligence_analyst"],
            tools=[
				FileReadTool(),
				ScrapeWebsiteTool()
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def steelman_argument_generator(self) -> Agent:
        
        return Agent(
            config=self.agents_config["steelman_argument_generator"],
            tools=[
				SerplyScholarSearchTool(),
				EXASearchTool(),
				ScrapeWebsiteTool(),
				FileReadTool()
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def multi_platform_social_monitor(self) -> Agent:
        
        return Agent(
            config=self.agents_config["multi_platform_social_monitor"],
            tools=[
				ScrapegraphScrapeTool(),
				ScrapeWebsiteTool(),
				EXASearchTool(),
				SerplyNewsSearchTool()
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def discord_q_a_thread_manager(self) -> Agent:
        
        return Agent(
            config=self.agents_config["discord_q_a_thread_manager"],
            tools=[
				StagehandTool(),
				FileReadTool(),
				ScrapeWebsiteTool(),
				QdrantVectorSearchTool(qdrant_url="https://8082ab03-adbf-4d11-bade-7d9affd7cae6.europe-west3-0.gcp.cloud.qdrant.io:6333", qdrant_api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.X9jlrRDpLUn2kw-e81zknWmiacGfCtiJR8Oqn1ULF9U")
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def truth_scoring_algorithm_specialist(self) -> Agent:
        enterprise_actions_tool = CrewaiEnterpriseTools(
            actions_list=[
                
                "google_sheets_create_row",
                
                "google_sheets_update_row",
                
                "google_sheets_get_row",
                
            ],
        )
        
        return Agent(
            config=self.agents_config["truth_scoring_algorithm_specialist"],
            tools=[
				FileReadTool(),
				*enterprise_actions_tool
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def knowledge_database_organizer(self) -> Agent:
        enterprise_actions_tool = CrewaiEnterpriseTools(
            actions_list=[
                
                "google_drive_save_file",
                
                "google_drive_create_folder",
                
                "google_drive_get_file_by_id",
                
                "google_sheets_create_row",
                
                "google_sheets_update_row",
                
                "google_sheets_get_row",
                
            ],
        )
        
        return Agent(
            config=self.agents_config["knowledge_database_organizer"],
            tools=[
				StagehandTool(),
				FileReadTool(),
				*enterprise_actions_tool
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def social_media_discovery_specialist(self) -> Agent:
        
        return Agent(
            config=self.agents_config["social_media_discovery_specialist"],
            tools=[
				EXASearchTool(),
				ScrapeWebsiteTool(),
				ScrapegraphScrapeTool(),
				SerperDevTool()
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def reddit_intelligence_gatherer(self) -> Agent:
        
        return Agent(
            config=self.agents_config["reddit_intelligence_gatherer"],
            tools=[
				ScrapeWebsiteTool(),
				ScrapegraphScrapeTool(),
				FileReadTool(),
				SerperDevTool()
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def social_media_content_analyzer(self) -> Agent:
        enterprise_actions_tool = CrewaiEnterpriseTools(
            actions_list=[
                
                "google_sheets_create_row",
                
                "google_sheets_update_row",
                
                "google_sheets_get_row",
                
            ],
        )
        
        return Agent(
            config=self.agents_config["social_media_content_analyzer"],
            tools=[
				FileReadTool(),
				ScrapeWebsiteTool(),
				EXASearchTool(),
				*enterprise_actions_tool
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def cross_platform_data_integrator(self) -> Agent:
        enterprise_actions_tool = CrewaiEnterpriseTools(
            actions_list=[
                
                "google_drive_save_file",
                
                "google_drive_create_folder",
                
                "google_drive_get_file_by_id",
                
                "google_sheets_create_row",
                
                "google_sheets_update_row",
                
                "google_sheets_get_row",
                
            ],
        )
        
        return Agent(
            config=self.agents_config["cross_platform_data_integrator"],
            tools=[
				FileReadTool(),
				StagehandTool(),
				*enterprise_actions_tool
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def social_media_enhanced_fact_checker(self) -> Agent:
        enterprise_actions_tool = CrewaiEnterpriseTools(
            actions_list=[
                
                "google_sheets_create_row",
                
                "google_sheets_update_row",
                
                "google_sheets_get_row",
                
            ],
        )
        
        return Agent(
            config=self.agents_config["social_media_enhanced_fact_checker"],
            tools=[
				ScrapeWebsiteTool(),
				SerplyScholarSearchTool(),
				SerplyNewsSearchTool(),
				EXASearchTool(),
				FileReadTool(),
				*enterprise_actions_tool
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def content_analysis_coordinator(self) -> Agent:
        enterprise_actions_tool = CrewaiEnterpriseTools(
            actions_list=[
                
                "google_drive_save_file",
                
                "google_drive_create_folder",
                
                "google_drive_get_file_by_id",
                
                "google_sheets_create_row",
                
                "google_sheets_update_row",
                
                "google_sheets_get_row",
                
            ],
        )
        
        return Agent(
            config=self.agents_config["content_analysis_coordinator"],
            tools=[
				FileReadTool(),
				StagehandTool(),
				*enterprise_actions_tool
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def vector_database_manager(self) -> Agent:
        enterprise_actions_tool = CrewaiEnterpriseTools(
            actions_list=[
                
                "google_drive_save_file",
                
                "google_drive_create_folder",
                
                "google_drive_get_file_by_id",
                
            ],
        )
        
        return Agent(
            config=self.agents_config["vector_database_manager"],
            tools=[
				FileReadTool(),
				QdrantVectorSearchTool(qdrant_url="https://8082ab03-adbf-4d11-bade-7d9affd7cae6.europe-west3-0.gcp.cloud.qdrant.io:6333", qdrant_api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.X9jlrRDpLUn2kw-e81zknWmiacGfCtiJR8Oqn1ULF9U"),
				*enterprise_actions_tool
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def system_monitoring_alert_manager(self) -> Agent:
        enterprise_actions_tool = CrewaiEnterpriseTools(
            actions_list=[
                
                "google_sheets_create_row",
                
                "google_sheets_update_row",
                
                "google_sheets_get_row",
                
                "slack_send_message",
                
            ],
        )
        
        return Agent(
            config=self.agents_config["system_monitoring_alert_manager"],
            tools=[
				FileReadTool(),
				*enterprise_actions_tool
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    
    @agent
    def real_time_processing_coordinator(self) -> Agent:
        enterprise_actions_tool = CrewaiEnterpriseTools(
            actions_list=[
                
                "slack_send_message",
                
            ],
        )
        
        return Agent(
            config=self.agents_config["real_time_processing_coordinator"],
            tools=[
				StagehandTool(),
				ScrapeWebsiteTool(),
				FileReadTool(),
				*enterprise_actions_tool
            ],
            reasoning=False,
            inject_date=True,
            llm=LLM(
                model="gpt-4o-mini",
                temperature=0.7,
            ),
        )
    

    
    @task
    def monitor_youtube_channels(self) -> Task:
        return Task(
            config=self.tasks_config["monitor_youtube_channels"],
        )
    
    @task
    def monitor_instagram_accounts(self) -> Task:
        return Task(
            config=self.tasks_config["monitor_instagram_accounts"],
        )
    
    @task
    def coordinate_real_time_processing(self) -> Task:
        return Task(
            config=self.tasks_config["coordinate_real_time_processing"],
        )
    
    @task
    def execute_downloads_and_file_management(self) -> Task:
        return Task(
            config=self.tasks_config["execute_downloads_and_file_management"],
        )
    
    @task
    def upload_content_to_cloud_storage(self) -> Task:
        return Task(
            config=self.tasks_config["upload_content_to_cloud_storage"],
        )
    
    @task
    def generate_audio_transcripts(self) -> Task:
        return Task(
            config=self.tasks_config["generate_audio_transcripts"],
        )
    
    @task
    def determine_discord_channel_routing(self) -> Task:
        return Task(
            config=self.tasks_config["determine_discord_channel_routing"],
        )
    
    @task
    def analyze_speaker_profiles(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_speaker_profiles"],
        )
    
    @task
    def extract_topics_and_opinions(self) -> Task:
        return Task(
            config=self.tasks_config["extract_topics_and_opinions"],
        )
    
    @task
    def discover_social_media_ecosystem(self) -> Task:
        return Task(
            config=self.tasks_config["discover_social_media_ecosystem"],
        )
    
    @task
    def monitor_cross_platform_discussions(self) -> Task:
        return Task(
            config=self.tasks_config["monitor_cross_platform_discussions"],
        )
    
    @task
    def extract_reddit_intelligence(self) -> Task:
        return Task(
            config=self.tasks_config["extract_reddit_intelligence"],
        )
    
    @task
    def analyze_social_media_content(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_social_media_content"],
        )
    
    @task
    def enhanced_fact_check_with_social_media_intelligence(self) -> Task:
        return Task(
            config=self.tasks_config["enhanced_fact_check_with_social_media_intelligence"],
        )
    
    @task
    def calculate_truth_scores(self) -> Task:
        return Task(
            config=self.tasks_config["calculate_truth_scores"],
        )
    
    @task
    def generate_steelman_arguments(self) -> Task:
        return Task(
            config=self.tasks_config["generate_steelman_arguments"],
        )
    
    @task
    def integrate_cross_platform_intelligence(self) -> Task:
        return Task(
            config=self.tasks_config["integrate_cross_platform_intelligence"],
        )
    
    @task
    def coordinate_comprehensive_analysis(self) -> Task:
        return Task(
            config=self.tasks_config["coordinate_comprehensive_analysis"],
        )
    
    @task
    def manage_vector_database_operations(self) -> Task:
        return Task(
            config=self.tasks_config["manage_vector_database_operations"],
        )
    
    @task
    def monitor_system_health_and_send_alerts(self) -> Task:
        return Task(
            config=self.tasks_config["monitor_system_health_and_send_alerts"],
        )
    
    @task
    def organize_knowledge_database(self) -> Task:
        return Task(
            config=self.tasks_config["organize_knowledge_database"],
        )
    
    @task
    def post_to_discord_channels(self) -> Task:
        return Task(
            config=self.tasks_config["post_to_discord_channels"],
        )
    
    @task
    def manage_discord_q_a_system(self) -> Task:
        return Task(
            config=self.tasks_config["manage_discord_q_a_system"],
        )
    

    @crew
    def crew(self) -> Crew:
        """Creates the UltimateDiscordIntelligenceBotCompleteSocialMediaAnalysisFactCheckingSystem crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
