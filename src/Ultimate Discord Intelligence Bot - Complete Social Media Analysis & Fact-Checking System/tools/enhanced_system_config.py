import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import asyncio

@dataclass
class SystemPaths:
    """System paths configuration"""
    base_dir: str = "F:/yt-auto/crewaiv2/CrewAI_Content_System"
    downloads_dir: str = "F:/yt-auto/crewaiv2/CrewAI_Content_System/Downloads"
    config_dir: str = "F:/yt-auto/crewaiv2/CrewAI_Content_System/Config"
    logs_dir: str = "F:/yt-auto/crewaiv2/CrewAI_Content_System/Logs"
    processing_dir: str = "F:/yt-auto/crewaiv2/CrewAI_Content_System/Processing"
    ytdlp_config: str = "F:/yt-auto/crewaiv2/yt-dlp/config/crewai-system.conf"
    google_credentials: str = "F:/yt-auto/crewaiv2/CrewAI_Content_System/Config/google-credentials.json"

@dataclass
class MonitoringConfig:
    """Content monitoring configuration"""
    youtube_channels: List[str]
    instagram_accounts: List[str]
    monitoring_interval: int = 300  # 5 minutes
    webhook_url: str = "https://your-domain.com/youtube-webhook"
    enable_pubsubhubbub: bool = True
    enable_fallback_polling: bool = True

@dataclass
class ProcessingConfig:
    """Content processing configuration"""
    enable_transcription: bool = True
    enable_speaker_analysis: bool = True
    enable_fact_checking: bool = True
    enable_social_media_analysis: bool = True
    max_concurrent_downloads: int = 3
    processing_timeout: int = 1800  # 30 minutes
    quality_settings: Dict[str, str] = None

@dataclass
class StorageConfig:
    """Storage configuration"""
    google_drive_enabled: bool = True
    google_sheets_enabled: bool = True
    vector_database_enabled: bool = True
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    backup_enabled: bool = True
    retention_days: int = 30

@dataclass
class DiscordConfig:
    """Discord integration configuration"""
    channels: List[Dict[str, Any]]
    default_strategy: str = "auto"
    enable_file_uploads: bool = True
    enable_embeds: bool = True
    max_file_size: int = 100 * 1024 * 1024

@dataclass
class APIConfig:
    """API keys and external service configuration"""
    openai_api_key: str = ""
    serply_api_key: str = ""
    exa_api_key: str = ""
    scrapegraph_api_key: str = ""
    browserbase_api_key: str = ""
    browserbase_project_id: str = ""
    rocket_api_key: str = ""
    huggingface_token: str = ""
    google_api_key: str = ""

class EnhancedSystemConfig:
    """Enhanced system configuration manager"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or "F:/yt-auto/crewaiv2/CrewAI_Content_System/Config/system_config.yaml"
        self.config = self._load_or_create_config()
        self._setup_logging()
        self._validate_config()
    
    def _load_or_create_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        
        config_path = Path(self.config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                logging.info(f"Loaded configuration from {config_path}")
                return config
            except Exception as e:
                logging.error(f"Error loading config file: {e}")
                return self._create_default_config()
        else:
            config = self._create_default_config()
            self.save_config(config)
            return config
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        
        return {
            'system': {
                'version': '2.0.0',
                'created_at': datetime.now().isoformat(),
                'environment': 'development',
                'debug': True
            },
            'paths': asdict(SystemPaths()),
            'monitoring': asdict(MonitoringConfig(
                youtube_channels=[],
                instagram_accounts=[],
                webhook_url="https://your-domain.com/youtube-webhook"
            )),
            'processing': asdict(ProcessingConfig(
                quality_settings={
                    'video': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]',
                    'audio': 'bestaudio[ext=m4a]',
                    'fallback': 'best[ext=mp4]/best'
                }
            )),
            'storage': asdict(StorageConfig()),
            'discord': asdict(DiscordConfig(
                channels=[
                    {
                        'name': 'general',
                        'id': 'YOUR_CHANNEL_ID',
                        'webhook_url': 'YOUR_WEBHOOK_URL',
                        'max_file_size': 100 * 1024 * 1024,
                        'allowed_types': ['video/*', 'image/*']
                    }
                ]
            )),
            'apis': asdict(APIConfig()),
            'rate_limits': {
                'youtube_api': {'requests': 10000, 'window': 86400},
                'instagram_requests': {'requests': 200, 'window': 3600},
                'drive_api_writes': {'requests': 3, 'window': 1},
                'discord_webhook': {'requests': 5, 'window': 2}
            },
            'error_handling': {
                'max_retries': 3,
                'backoff_strategy': 'exponential',
                'circuit_breaker_threshold': 5,
                'enable_fallbacks': True
            }
        }
    
    def _setup_logging(self):
        """Setup logging configuration"""
        
        logs_dir = Path(self.config.get('paths', {}).get('logs_dir', 'logs'))
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        log_level = logging.DEBUG if self.config.get('system', {}).get('debug') else logging.INFO
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(logs_dir / 'system.log'),
                logging.StreamHandler()
            ]
        )
        
        # Create specialized loggers
        loggers = {
            'downloads': logs_dir / 'downloads.log',
            'uploads': logs_dir / 'uploads.log',
            'discord': logs_dir / 'discord.log',
            'social_media': logs_dir / 'social_media.log',
            'fact_checking': logs_dir / 'fact_checking.log'
        }
        
        for logger_name, log_file in loggers.items():
            logger = logging.getLogger(logger_name)
            handler = logging.FileHandler(log_file)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(log_level)
    
    def _validate_config(self):
        """Validate configuration and warn about missing required settings"""
        
        validation_results = []
        
        # Check required API keys
        api_config = self.config.get('apis', {})
        required_apis = {
            'openai_api_key': 'OpenAI (required for LLM functionality)',
            'serply_api_key': 'Serply (required for fact-checking and research)',
            'exa_api_key': 'EXA (required for advanced search capabilities)'
        }
        
        for api_key, description in required_apis.items():
            if not api_config.get(api_key) and not os.getenv(api_key.upper()):
                validation_results.append(f"Missing {api_key}: {description}")
        
        # Check file paths
        paths_config = self.config.get('paths', {})
        critical_paths = ['base_dir', 'config_dir', 'downloads_dir']
        
        for path_key in critical_paths:
            path_value = paths_config.get(path_key)
            if path_value:
                path_obj = Path(path_value)
                if not path_obj.exists():
                    try:
                        path_obj.mkdir(parents=True, exist_ok=True)
                        validation_results.append(f"Created directory: {path_value}")
                    except Exception as e:
                        validation_results.append(f"Cannot create directory {path_value}: {e}")
        
        # Check Google credentials
        google_creds = paths_config.get('google_credentials')
        if google_creds and not Path(google_creds).exists():
            validation_results.append(f"Google credentials file not found: {google_creds}")
        
        # Check Discord configuration
        discord_config = self.config.get('discord', {})
        channels = discord_config.get('channels', [])
        for channel in channels:
            if not channel.get('webhook_url'):
                validation_results.append(f"Missing webhook URL for Discord channel: {channel.get('name')}")
        
        # Log validation results
        if validation_results:
            logging.warning("Configuration validation issues found:")
            for issue in validation_results:
                logging.warning(f"  - {issue}")
        else:
            logging.info("Configuration validation passed")
    
    def save_config(self, config: Dict[str, Any] = None):
        """Save configuration to file"""
        
        config_to_save = config or self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_to_save, f, default_flow_style=False, indent=2)
            logging.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value using dot notation"""
        
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key from config or environment"""
        
        # Try config first
        api_key = self.get(f'apis.{service}_api_key')
        if api_key:
            return api_key
        
        # Try environment variable
        env_key = f"{service.upper()}_API_KEY"
        return os.getenv(env_key)
    
    def get_paths(self) -> SystemPaths:
        """Get system paths configuration"""
        paths_dict = self.get('paths', {})
        return SystemPaths(**paths_dict)
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration"""
        monitoring_dict = self.get('monitoring', {})
        return MonitoringConfig(**monitoring_dict)
    
    def get_processing_config(self) -> ProcessingConfig:
        """Get processing configuration"""
        processing_dict = self.get('processing', {})
        return ProcessingConfig(**processing_dict)
    
    def get_storage_config(self) -> StorageConfig:
        """Get storage configuration"""
        storage_dict = self.get('storage', {})
        return StorageConfig(**storage_dict)
    
    def get_discord_config(self) -> DiscordConfig:
        """Get Discord configuration"""
        discord_dict = self.get('discord', {})
        return DiscordConfig(**discord_dict)
    
    def get_rate_limits(self) -> Dict[str, Dict[str, int]]:
        """Get rate limiting configuration"""
        return self.get('rate_limits', {})
    
    def create_environment_template(self) -> str:
        """Create .env template file"""
        
        template = """# CrewAI Content System Environment Variables
# Copy this to .env and fill in your actual values

# OpenAI API Key (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Search and Research APIs (Critical for fact-checking)
SERPLY_API_KEY=your_serply_api_key_here
EXA_API_KEY=your_exa_api_key_here

# Web Scraping (Optional, enhances capabilities)
SCRAPEGRAPH_API_KEY=your_scrapegraph_api_key_here
BROWSERBASE_API_KEY=your_browserbase_api_key_here
BROWSERBASE_PROJECT_ID=your_browserbase_project_id_here

# Instagram Enhanced Access (Optional)
ROCKET_API_KEY=your_rocket_api_key_here
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password

# AI Services (Optional)
HUGGINGFACE_TOKEN=your_huggingface_token_here
GOOGLE_API_KEY=your_google_api_key_here

# Discord Integration
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here

# System Configuration
ENVIRONMENT=development
DEBUG=true
"""
        
        env_file = Path(".env")
        if not env_file.exists():
            with open(env_file, 'w') as f:
                f.write(template)
            logging.info("Created .env template file")
        
        return template
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check system health and configuration status"""
        
        health_check = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'issues': [],
            'components': {}
        }
        
        # Check API keys
        api_status = {}
        required_apis = ['openai_api_key', 'serply_api_key', 'exa_api_key']
        
        for api in required_apis:
            api_key = self.get_api_key(api.replace('_api_key', ''))
            api_status[api] = 'configured' if api_key else 'missing'
            
            if not api_key:
                health_check['issues'].append(f"Missing {api}")
        
        health_check['components']['apis'] = api_status
        
        # Check directories
        paths = self.get_paths()
        directory_status = {}
        
        for attr in ['base_dir', 'downloads_dir', 'config_dir', 'logs_dir']:
            path = getattr(paths, attr)
            if Path(path).exists():
                directory_status[attr] = 'exists'
            else:
                directory_status[attr] = 'missing'
                health_check['issues'].append(f"Missing directory: {path}")
        
        health_check['components']['directories'] = directory_status
        
        # Check Google credentials
        google_creds_status = 'not_found'
        if Path(paths.google_credentials).exists():
            google_creds_status = 'found'
        else:
            health_check['issues'].append("Google credentials file not found")
        
        health_check['components']['google_credentials'] = google_creds_status
        
        # Check Discord configuration
        discord_config = self.get_discord_config()
        discord_status = {
            'channels_configured': len(discord_config.channels),
            'webhooks_configured': sum(1 for ch in discord_config.channels if ch.get('webhook_url'))
        }
        
        if discord_status['webhooks_configured'] == 0:
            health_check['issues'].append("No Discord webhooks configured")
        
        health_check['components']['discord'] = discord_status
        
        # Overall status
        if health_check['issues']:
            health_check['overall_status'] = 'degraded' if len(health_check['issues']) < 3 else 'unhealthy'
        
        return health_check

class ConfigurationManager:
    """Centralized configuration manager for the entire system"""
    
    _instance = None
    
    def __new__(cls, config_file: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config = EnhancedSystemConfig(config_file)
        return cls._instance
    
    def get_config(self) -> EnhancedSystemConfig:
        return self.config
    
    def reload_config(self):
        """Reload configuration from file"""
        self.config = EnhancedSystemConfig(self.config.config_file)
    
    def get_crew_inputs(self) -> Dict[str, Any]:
        """Get inputs formatted for CrewAI crew kickoff"""
        
        monitoring = self.config.get_monitoring_config()
        
        return {
            'channel_urls': monitoring.youtube_channels,
            'instagram_accounts': monitoring.instagram_accounts,
            'channel_name': 'CrewAI_Content_System'
        }
    
    def get_tool_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get configuration for all tools"""
        
        paths = self.config.get_paths()
        storage = self.config.get_storage_config()
        discord = self.config.get_discord_config()
        
        return {
            'youtube_download': {
                'config_file': paths.ytdlp_config,
                'output_dir': f"{paths.downloads_dir}/YouTube"
            },
            'instagram_content': {
                'output_dir': f"{paths.downloads_dir}/Instagram",
                'rocket_api_key': self.config.get_api_key('rocket')
            },
            'drive_upload': {
                'credentials_path': paths.google_credentials,
                'base_folder': 'CrewAI_Content_System'
            },
            'discord_bot': {
                'channels': discord.channels,
                'default_strategy': discord.default_strategy
            },
            'vector_database': {
                'url': storage.qdrant_url,
                'api_key': storage.qdrant_api_key
            }
        }

# Global configuration instance
def get_config() -> EnhancedSystemConfig:
    """Get global configuration instance"""
    return ConfigurationManager().get_config()

# CLI utilities for configuration management
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='CrewAI System Configuration Manager')
    parser.add_argument('--check-health', action='store_true', help='Check system health')
    parser.add_argument('--create-env', action='store_true', help='Create .env template')
    parser.add_argument('--validate', action='store_true', help='Validate configuration')
    parser.add_argument('--config-file', help='Configuration file path')
    
    args = parser.parse_args()
    
    config = EnhancedSystemConfig(args.config_file)
    
    if args.check_health:
        health = config.check_system_health()
        print(json.dumps(health, indent=2))
        
        if health['overall_status'] != 'healthy':
            print(f"\n⚠️  System Status: {health['overall_status'].upper()}")
            print("Issues found:")
            for issue in health['issues']:
                print(f"  - {issue}")
            sys.exit(1)
        else:
            print("✅ System is healthy")
    
    elif args.create_env:
        template = config.create_environment_template()
        print("Created .env template file")
        print("Please edit .env with your actual API keys and configuration")
    
    elif args.validate:
        print("Configuration validation completed. Check logs for details.")
    
    else:
        print("Use --help for available options")
