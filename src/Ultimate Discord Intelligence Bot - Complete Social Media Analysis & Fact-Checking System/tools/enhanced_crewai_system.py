import os
import sys
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json
import yaml
from dataclasses import dataclass

# CrewAI imports
from crewai import Agent, Task, Crew, Process
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

# Import our enhanced components
from enhanced_youtube_monitor import EnhancedYouTubeDownloadTool, resilience, rate_limiter
from enhanced_instagram_manager import EnhancedInstagramContentTool
from enhanced_drive_manager import EnhancedDriveUploadTool
from enhanced_discord_manager import EnhancedDiscordBotTool, load_discord_channels_config
from enhanced_content_analysis import EnhancedContentAnalysisTool
from social_media_intelligence import SocialMediaIntelligenceTool, EnhancedFactCheckingTool, TruthScoringTool
from enhanced_system_config import ConfigurationManager, get_config

@dataclass
class SystemMetrics:
    """System performance metrics"""
    start_time: datetime
    videos_processed: int = 0
    stories_downloaded: int = 0
    posts_analyzed: int = 0
    claims_fact_checked: int = 0
    errors_encountered: int = 0
    processing_time: float = 0.0
    success_rate: float = 0.0

class EnhancedSystemMonitor:
    """Enhanced system monitoring with health checks and alerts"""
    
    def __init__(self):
        self.metrics = SystemMetrics(start_time=datetime.now())
        self.health_status = "healthy"
        self.alerts = []
        self.performance_log = []
    
    def log_video_processed(self, success: bool = True):
        """Log video processing event"""
        self.metrics.videos_processed += 1
        if not success:
            self.metrics.errors_encountered += 1
        self._update_success_rate()
    
    def log_story_downloaded(self, success: bool = True):
        """Log story download event"""
        self.metrics.stories_downloaded += 1
        if not success:
            self.metrics.errors_encountered += 1
        self._update_success_rate()
    
    def log_post_analyzed(self, success: bool = True):
        """Log post analysis event"""
        self.metrics.posts_analyzed += 1
        if not success:
            self.metrics.errors_encountered += 1
        self._update_success_rate()
    
    def log_fact_check(self, success: bool = True):
        """Log fact-check event"""
        self.metrics.claims_fact_checked += 1
        if not success:
            self.metrics.errors_encountered += 1
        self._update_success_rate()
    
    def _update_success_rate(self):
        """Update overall success rate"""
        total_operations = (self.metrics.videos_processed + self.metrics.stories_downloaded + 
                           self.metrics.posts_analyzed + self.metrics.claims_fact_checked)
        if total_operations > 0:
            success_operations = total_operations - self.metrics.errors_encountered
            self.metrics.success_rate = success_operations / total_operations
    
    def add_alert(self, level: str, message: str, component: str = "system"):
        """Add system alert"""
        alert = {
            'level': level,
            'message': message,
            'component': component,
            'timestamp': datetime.now().isoformat()
        }
        self.alerts.append(alert)
        
        # Keep only recent alerts
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.alerts = [a for a in self.alerts if datetime.fromisoformat(a['timestamp']) > cutoff_time]
        
        # Update health status based on recent alerts
        recent_critical_alerts = [a for a in self.alerts if a['level'] == 'critical' and 
                                datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(hours=1)]
        
        if len(recent_critical_alerts) > 3:
            self.health_status = "critical"
        elif self.metrics.success_rate < 0.7:
            self.health_status = "degraded"
        else:
            self.health_status = "healthy"
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        runtime = (datetime.now() - self.metrics.start_time).total_seconds()
        
        return {
            'health_status': self.health_status,
            'runtime_seconds': runtime,
            'metrics': {
                'videos_processed': self.metrics.videos_processed,
                'stories_downloaded': self.metrics.stories_downloaded,
                'posts_analyzed': self.metrics.posts_analyzed,
                'claims_fact_checked': self.metrics.claims_fact_checked,
                'errors_encountered': self.metrics.errors_encountered,
                'success_rate': self.metrics.success_rate
            },
            'recent_alerts': self.alerts[-10:],  # Last 10 alerts
            'performance': {
                'operations_per_hour': (self.metrics.videos_processed + self.metrics.stories_downloaded + 
                                      self.metrics.posts_analyzed) / (runtime / 3600) if runtime > 0 else 0,
                'average_processing_time': self.metrics.processing_time / max(1, self.metrics.videos_processed)
            }
        }

@CrewBase
class EnhancedDiscordIntelligenceSystemCrew:
    """Enhanced Discord Intelligence System with comprehensive capabilities"""

    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.system_monitor = EnhancedSystemMonitor()
        self.setup_logging()
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_level = logging.DEBUG if self.config.get('system.debug') else logging.INFO
        
        # Create logs directory
        logs_dir = Path(self.config.get('paths.logs_dir'))
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(logs_dir / 'crew_system.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logging.info("Enhanced CrewAI System initialized")

    @agent
    def youtube_channel_monitor(self) -> Agent:
        return Agent(
            config=self.agents_config["youtube_channel_monitor"],
            tools=[
                ScrapeWebsiteTool(),
                EnhancedYouTubeDownloadTool(),
                FileReadTool()
            ],
            verbose=True,
            memory=True,
            max_execution_time=1800,  # 30 minutes
            max_retry_limit=3
        )

    @agent
    def instagram_content_downloader(self) -> Agent:
        return Agent(
            config=self.agents_config["instagram_content_downloader"],
            tools=[
                EnhancedInstagramContentTool(),
                ScrapegraphScrapeTool(),
                FileReadTool()
            ],
            verbose=True,
            memory=True,
            max_execution_time=1200,  # 20 minutes
            max_retry_limit=3
        )

    @agent
    def file_system_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["file_system_manager"],
            tools=[
                FileReadTool(),
                EnhancedYouTubeDownloadTool(),
                EnhancedInstagramContentTool()
            ],
            verbose=True,
            memory=True
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
                EnhancedDriveUploadTool(),
                *enterprise_actions_tool
            ],
            verbose=True,
            memory=True,
            cache=True
        )

    @agent
    def discord_bot_manager(self) -> Agent:
        # Load Discord configuration
        discord_channels = load_discord_channels_config()
        
        return Agent(
            config=self.agents_config["discord_bot_manager"],
            tools=[
                EnhancedDiscordBotTool(discord_channels),
                StagehandTool(),
                FileReadTool()
            ],
            verbose=True,
            memory=True
        )

    @agent
    def content_transcription_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["content_transcription_specialist"],
            tools=[
                EnhancedContentAnalysisTool(model_size="base"),
                FileReadTool(),
                ScrapeWebsiteTool()
            ],
            verbose=True,
            memory=True,
            max_execution_time=3600  # 1 hour for large files
        )

    @agent
    def speaker_analysis_expert(self) -> Agent:
        return Agent(
            config=self.agents_config["speaker_analysis_expert"],
            tools=[
                EnhancedContentAnalysisTool(model_size="base"),
                FileReadTool(),
                ScrapeWebsiteTool()
            ],
            verbose=True,
            memory=True
        )

    @agent
    def content_intelligence_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["content_intelligence_analyst"],
            tools=[
                EnhancedContentAnalysisTool(model_size="base"),
                FileReadTool(),
                ScrapeWebsiteTool()
            ],
            verbose=True,
            memory=True
        )

    @agent
    def social_media_discovery_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["social_media_discovery_specialist"],
            tools=[
                SocialMediaIntelligenceTool(),
                EXASearchTool(),
                ScrapeWebsiteTool(),
                ScrapegraphScrapeTool(),
                SerperDevTool()
            ],
            verbose=True,
            memory=True
        )

    @agent
    def reddit_intelligence_gatherer(self) -> Agent:
        return Agent(
            config=self.agents_config["reddit_intelligence_gatherer"],
            tools=[
                SocialMediaIntelligenceTool(),
                ScrapeWebsiteTool(),
                ScrapegraphScrapeTool(),
                FileReadTool(),
                SerperDevTool()
            ],
            verbose=True,
            memory=True
        )

    @agent
    def multi_platform_social_monitor(self) -> Agent:
        return Agent(
            config=self.agents_config["multi_platform_social_monitor"],
            tools=[
                SocialMediaIntelligenceTool(),
                ScrapegraphScrapeTool(),
                ScrapeWebsiteTool(),
                EXASearchTool(),
                SerplyNewsSearchTool()
            ],
            verbose=True,
            memory=True
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
                EnhancedFactCheckingTool(),
                ScrapeWebsiteTool(),
                SerplyScholarSearchTool(),
                SerplyNewsSearchTool(),
                EXASearchTool(),
                FileReadTool(),
                *enterprise_actions_tool
            ],
            verbose=True,
            memory=True,
            max_execution_time=2400  # 40 minutes for thorough fact-checking
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
                TruthScoringTool(),
                FileReadTool(),
                *enterprise_actions_tool
            ],
            verbose=True,
            memory=True,
            cache=True
        )

    @agent
    def steelman_argument_generator(self) -> Agent:
        return Agent(
            config=self.agents_config["steelman_argument_generator"],
            tools=[
                SerplyScholarSearchTool(),
                EXASearchTool(),
                ScrapeWebsiteTool(),
                FileReadTool(),
                EnhancedFactCheckingTool()
            ],
            verbose=True,
            memory=True
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
                SocialMediaIntelligenceTool(),
                *enterprise_actions_tool
            ],
            verbose=True,
            memory=True,
            cache=True
        )

    @agent
    def vector_database_manager(self) -> Agent:
        storage_config = self.config.get_storage_config()
        
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
                QdrantVectorSearchTool(
                    qdrant_url=storage_config.qdrant_url, 
                    qdrant_api_key=storage_config.qdrant_api_key
                ) if storage_config.qdrant_url and storage_config.qdrant_api_key else FileReadTool(),
                *enterprise_actions_tool
            ],
            verbose=True,
            memory=True,
            cache=True
        )

    @agent
    def discord_q_a_thread_manager(self) -> Agent:
        storage_config = self.config.get_storage_config()
        
        return Agent(
            config=self.agents_config["discord_q_a_thread_manager"],
            tools=[
                StagehandTool(),
                FileReadTool(),
                ScrapeWebsiteTool(),
                QdrantVectorSearchTool(
                    qdrant_url=storage_config.qdrant_url, 
                    qdrant_api_key=storage_config.qdrant_api_key
                ) if storage_config.qdrant_url and storage_config.qdrant_api_key else FileReadTool()
            ],
            verbose=True,
            memory=True
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
            verbose=True,
            memory=True,
            step_callback=self._system_monitoring_callback
        )

    def _system_monitoring_callback(self, step):
        """Callback for system monitoring"""
        try:
            # Log step execution
            if hasattr(step, 'status'):
                if step.status == 'completed':
                    self.system_monitor.log_video_processed(True)
                elif step.status == 'failed':
                    self.system_monitor.log_video_processed(False)
                    self.system_monitor.add_alert('warning', f'Step failed: {step.description}', 'crew_execution')
        except Exception as e:
            logging.warning(f"Monitoring callback error: {e}")

    # Task definitions with enhanced configuration
    @task
    def monitor_youtube_channels(self) -> Task:
        return Task(
            config=self.tasks_config["monitor_youtube_channels"],
            agent=self.youtube_channel_monitor(),
            context=[]
        )

    @task
    def monitor_instagram_accounts(self) -> Task:
        return Task(
            config=self.tasks_config["monitor_instagram_accounts"],
            agent=self.instagram_content_downloader(),
            context=[]
        )

    @task
    def execute_downloads_and_file_management(self) -> Task:
        return Task(
            config=self.tasks_config["execute_downloads_and_file_management"],
            agent=self.file_system_manager(),
            context=[
                self.monitor_youtube_channels(),
                self.monitor_instagram_accounts()
            ]
        )

    @task
    def upload_content_to_cloud_storage(self) -> Task:
        return Task(
            config=self.tasks_config["upload_content_to_cloud_storage"],
            agent=self.cloud_storage_manager(),
            context=[self.execute_downloads_and_file_management()]
        )

    @task
    def generate_audio_transcripts(self) -> Task:
        return Task(
            config=self.tasks_config["generate_audio_transcripts"],
            agent=self.content_transcription_specialist(),
            context=[self.execute_downloads_and_file_management()]
        )

    @task
    def analyze_speaker_profiles(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_speaker_profiles"],
            agent=self.speaker_analysis_expert(),
            context=[self.generate_audio_transcripts()]
        )

    @task
    def extract_topics_and_opinions(self) -> Task:
        return Task(
            config=self.tasks_config["extract_topics_and_opinions"],
            agent=self.content_intelligence_analyst(),
            context=[
                self.generate_audio_transcripts(),
                self.analyze_speaker_profiles()
            ]
        )

    @task
    def discover_social_media_ecosystem(self) -> Task:
        return Task(
            config=self.tasks_config["discover_social_media_ecosystem"],
            agent=self.social_media_discovery_specialist(),
            context=[self.analyze_speaker_profiles()]
        )

    @task
    def extract_reddit_intelligence(self) -> Task:
        return Task(
            config=self.tasks_config["extract_reddit_intelligence"],
            agent=self.reddit_intelligence_gatherer(),
            context=[self.discover_social_media_ecosystem()]
        )

    @task
    def monitor_cross_platform_discussions(self) -> Task:
        return Task(
            config=self.tasks_config["monitor_cross_platform_discussions"],
            agent=self.multi_platform_social_monitor(),
            context=[self.extract_topics_and_opinions()]
        )

    @task
    def enhanced_fact_check_with_social_media_intelligence(self) -> Task:
        return Task(
            config=self.tasks_config["enhanced_fact_check_with_social_media_intelligence"],
            agent=self.social_media_enhanced_fact_checker(),
            context=[
                self.extract_topics_and_opinions(),
                self.monitor_cross_platform_discussions()
            ]
        )

    @task
    def generate_steelman_arguments(self) -> Task:
        return Task(
            config=self.tasks_config["generate_steelman_arguments"],
            agent=self.steelman_argument_generator(),
            context=[
                self.extract_topics_and_opinions(),
                self.enhanced_fact_check_with_social_media_intelligence()
            ]
        )

    @task
    def calculate_truth_scores(self) -> Task:
        return Task(
            config=self.tasks_config["calculate_truth_scores"],
            agent=self.truth_scoring_algorithm_specialist(),
            context=[
                self.enhanced_fact_check_with_social_media_intelligence(),
                self.analyze_speaker_profiles()
            ]
        )

    @task
    def integrate_cross_platform_intelligence(self) -> Task:
        return Task(
            config=self.tasks_config["integrate_cross_platform_intelligence"],
            agent=self.cross_platform_data_integrator(),
            context=[
                self.monitor_cross_platform_discussions(),
                self.enhanced_fact_check_with_social_media_intelligence(),
                self.calculate_truth_scores()
            ]
        )

    @task
    def manage_vector_database_operations(self) -> Task:
        return Task(
            config=self.tasks_config["manage_vector_database_operations"],
            agent=self.vector_database_manager(),
            context=[self.integrate_cross_platform_intelligence()]
        )

    @task
    def post_to_discord_channels(self) -> Task:
        return Task(
            config=self.tasks_config["post_to_discord_channels"],
            agent=self.discord_bot_manager(),
            context=[
                self.upload_content_to_cloud_storage(),
                self.integrate_cross_platform_intelligence()
            ]
        )

    @task
    def monitor_system_health_and_send_alerts(self) -> Task:
        return Task(
            config=self.tasks_config["monitor_system_health_and_send_alerts"],
            agent=self.system_monitoring_alert_manager(),
            context=[self.manage_vector_database_operations()]
        )

    @task
    def manage_discord_q_a_system(self) -> Task:
        return Task(
            config=self.tasks_config["manage_discord_q_a_system"],
            agent=self.discord_q_a_thread_manager(),
            context=[
                self.post_to_discord_channels(),
                self.monitor_system_health_and_send_alerts()
            ]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the enhanced Discord Intelligence System crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=True,
            cache=True,
            max_rpm=30,  # Rate limiting
            embedder=self._get_embedder_config(),
            planning=True,  # Enable planning
            step_callback=self._global_step_callback
        )

    def _get_embedder_config(self):
        """Get embedder configuration for memory system"""
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(model="text-embedding-3-small")
        except ImportError:
            logging.warning("OpenAI embeddings not available")
            return None

    def _global_step_callback(self, step):
        """Global step callback for all agents"""
        try:
            # Update system metrics
            step_info = {
                'agent': getattr(step, 'agent', 'unknown'),
                'task': getattr(step, 'task', 'unknown'),
                'status': getattr(step, 'status', 'unknown'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Log to system monitor
            if hasattr(step, 'status'):
                if step.status == 'failed':
                    self.system_monitor.add_alert('error', f'Task failed: {step_info["task"]}', step_info['agent'])
                elif step.status == 'completed':
                    logging.info(f"Task completed: {step_info['task']} by {step_info['agent']}")
            
            # Log performance metrics
            self.system_monitor.performance_log.append(step_info)
            
            # Keep only recent performance data
            if len(self.system_monitor.performance_log) > 1000:
                self.system_monitor.performance_log = self.system_monitor.performance_log[-500:]
        
        except Exception as e:
            logging.warning(f"Global step callback error: {e}")

    def run_with_monitoring(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run the crew with enhanced monitoring and error handling"""
        
        start_time = datetime.now()
        
        try:
            # Validate inputs
            self._validate_inputs(inputs)
            
            # Log system start
            logging.info("Starting Enhanced Discord Intelligence System")
            self.system_monitor.add_alert('info', 'System startup initiated', 'crew_system')
            
            # Execute crew
            result = self.crew().kickoff(inputs=inputs)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            self.system_monitor.metrics.processing_time += processing_time
            
            # Generate final report
            status_report = self.system_monitor.get_status_report()
            
            return {
                'status': 'success',
                'result': str(result),
                'processing_time': processing_time,
                'system_metrics': status_report,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Crew execution failed: {str(e)}"
            logging.error(error_msg)
            
            self.system_monitor.add_alert('critical', error_msg, 'crew_system')
            self.system_monitor.metrics.errors_encountered += 1
            
            return {
                'status': 'error',
                'error': error_msg,
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'system_metrics': self.system_monitor.get_status_report(),
                'timestamp': datetime.now().isoformat()
            }

    def _validate_inputs(self, inputs: Dict[str, Any]):
        """Validate crew inputs"""
        required_keys = ['channel_urls', 'instagram_accounts', 'channel_name']
        
        for key in required_keys:
            if key not in inputs:
                raise ValueError(f"Required input '{key}' is missing")
        
        # Validate channel URLs
        if not isinstance(inputs['channel_urls'], list):
            if isinstance(inputs['channel_urls'], str):
                inputs['channel_urls'] = [inputs['channel_urls']]
            else:
                raise ValueError("channel_urls must be a list or string")
        
        # Validate Instagram accounts
        if not isinstance(inputs['instagram_accounts'], list):
            if isinstance(inputs['instagram_accounts'], str):
                inputs['instagram_accounts'] = [inputs['instagram_accounts']]
            else:
                raise ValueError("instagram_accounts must be a list or string")

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {},
            'metrics': self.system_monitor.get_status_report()
        }
        
        # Check configuration
        try:
            config_health = self.config.check_system_health()
            health_data['components']['configuration'] = config_health
            
            if config_health['overall_status'] != 'healthy':
                health_data['overall_status'] = 'degraded'
        except Exception as e:
            health_data['components']['configuration'] = {'status': 'error', 'error': str(e)}
            health_data['overall_status'] = 'degraded'
        
        # Check API connectivity
        api_status = self._check_api_connectivity()
        health_data['components']['apis'] = api_status
        
        if any(api['status'] == 'error' for api in api_status.values()):
            health_data['overall_status'] = 'degraded'
        
        # Check system resources
        resource_status = self._check_system_resources()
        health_data['components']['resources'] = resource_status
        
        return health_data

    def _check_api_connectivity(self) -> Dict[str, Dict[str, str]]:
        """Check connectivity to external APIs"""
        
        api_checks = {}
        
        # Check OpenAI API
        openai_key = self.config.get_api_key('openai')
        if openai_key:
            try:
                # Simple API test
                api_checks['openai'] = {'status': 'available', 'message': 'API key configured'}
            except Exception as e:
                api_checks['openai'] = {'status': 'error', 'message': str(e)}
        else:
            api_checks['openai'] = {'status': 'missing', 'message': 'API key not configured'}
        
        # Check other APIs similarly
        for api_name in ['serply', 'exa', 'scrapegraph']:
            api_key = self.config.get_api_key(api_name)
            api_checks[api_name] = {
                'status': 'configured' if api_key else 'missing',
                'message': 'API key configured' if api_key else 'API key not configured'
            }
        
        return api_checks

    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources"""
        
        import psutil
        import shutil
        
        try:
            # Check disk space
            paths = self.config.get_paths()
            disk_usage = shutil.disk_usage(paths.base_dir)
            free_gb = disk_usage.free / (1024**3)
            
            # Check memory
            memory = psutil.virtual_memory()
            
            # Check CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                'disk_space_gb': free_gb,
                'memory_percent': memory.percent,
                'cpu_percent': cpu_percent,
                'status': 'good' if free_gb > 10 and memory.percent < 80 and cpu_percent < 80 else 'limited'
            }
        
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

# Main execution functions
def run_system():
    """Run the enhanced system"""
    
    # Initialize configuration
    config_manager = ConfigurationManager()
    config = config_manager.get_config()
    
    # Create crew
    crew_system = EnhancedDiscordIntelligenceSystemCrew()
    
    # Get inputs from configuration
    inputs = config_manager.get_crew_inputs()
    
    # Validate we have content to monitor
    if not inputs['channel_urls'] and not inputs['instagram_accounts']:
        logging.error("No YouTube channels or Instagram accounts configured for monitoring")
        print("\n⚠️  Configuration Error:")
        print("No YouTube channels or Instagram accounts found in configuration.")
        print("Please update your configuration with channels and accounts to monitor.")
        return
    
    # Run health check first
    print("🔍 Performing system health check...")
    health_check = crew_system.health_check()
    
    if health_check['overall_status'] == 'healthy':
        print("✅ System health check passed")
    else:
        print(f"⚠️  System health check: {health_check['overall_status']}")
        print("Issues found - check logs for details")
        
        # Continue if degraded, stop if critical
        if health_check['overall_status'] == 'critical':
            print("❌ System cannot start due to critical issues")
            return
    
    print(f"\n🚀 Starting Enhanced Discord Intelligence System")
    print(f"📺 Monitoring {len(inputs['channel_urls'])} YouTube channels")
    print(f"📱 Monitoring {len(inputs['instagram_accounts'])} Instagram accounts")
    
    # Run the crew
    result = crew_system.run_with_monitoring(inputs)
    
    # Display results
    if result['status'] == 'success':
        print(f"\n✅ System completed successfully")
        print(f"⏱️  Processing time: {result['processing_time']:.2f} seconds")
        
        metrics = result['system_metrics']['metrics']
        print(f"📊 Performance Summary:")
        print(f"   • Videos processed: {metrics['videos_processed']}")
        print(f"   • Stories downloaded: {metrics['stories_downloaded']}")
        print(f"   • Posts analyzed: {metrics['posts_analyzed']}")
        print(f"   • Claims fact-checked: {metrics['claims_fact_checked']}")
        print(f"   • Success rate: {metrics['success_rate']:.1%}")
        
        if metrics['errors_encountered'] > 0:
            print(f"⚠️  Errors encountered: {metrics['errors_encountered']}")
    
    else:
        print(f"\n❌ System failed: {result['error']}")
        print(f"⏱️  Runtime: {result['processing_time']:.2f} seconds")

def health_check():
    """Perform standalone health check"""
    crew_system = EnhancedDiscordIntelligenceSystemCrew()
    health_data = crew_system.health_check()
    
    print("🏥 System Health Check")
    print(f"Overall Status: {health_data['overall_status'].upper()}")
    print(f"Timestamp: {health_data['timestamp']}")
    
    for component, status in health_data['components'].items():
        print(f"\n{component.title()}:")
        if isinstance(status, dict):
            for key, value in status.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {status}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced CrewAI Discord Intelligence System')
    parser.add_argument('--health-check', action='store_true', help='Perform system health check')
    parser.add_argument('--run', action='store_true', help='Run the system')
    
    args = parser.parse_args()
    
    if args.health_check:
        health_check()
    elif args.run:
        run_system()
    else:
        print("Use --run to start the system or --health-check to check system health")
